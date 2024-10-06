import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import pandas as pd
from agent import Agent
import xml.etree.ElementTree as ET
import time
import csv
import logging
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import re
import ast

class WebCrawler:
    def __init__(self, start_url, chunk_size=100, total_chunks=None, deep_analysis=False, deep_analysis_on_level_change=False):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.agent = Agent(model="Cohere: Command R+", provider="openrouter")
        self.agent.max_tokens = 50000
        self.driver = self.setup_selenium()
        self.visited = set()
        self.to_visit = [start_url]
        self.results = []
        self.throttle = .5
        self.chunk_size = chunk_size
        self.total_chunks = total_chunks
        self.current_chunk = 0
        self.deep_dive = None
        self.deep_analysis = deep_analysis
        self.deep_analysis_on_level_change = deep_analysis_on_level_change
        self.current_directory_level = self.get_directory_level(start_url)
        self.df = pd.DataFrame({'url': [],
                                'links': [],
                                'selenium_required': [],
                                'description': [],
                                'errors': [],
                                'additional_notes': []})

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def setup_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def get_sitemap(self):
        sitemap_url = urljoin(self.start_url, '/sitemap.xml')
        try:
            response = requests.get(sitemap_url)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                return [elem.text for elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        except Exception as e:
            logging.warning(f"Error fetching sitemap: {e}")
        return []

    def is_allowed_by_robots(self, url, user_agent='*'):
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = urljoin(base_url, '/robots.txt')
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        crawl_delay = rp.crawl_delay('*')
        if crawl_delay:
            self.throttle = max(self.throttle, crawl_delay)
            df2 = pd.DataFrame({'url': [base_url + robots_url], 'crawl_delay': [crawl_delay]})
            self.df = pd.concat([self.df, df2], ignore_index=True)
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            return rp.can_fetch(user_agent, url)
        except Exception as e:
            logging.warning(f"Error checking robots.txt: {e}")
            return True

    def is_same_domain(self, url):
        parsed_url = urlparse(url)
        parsed_start_url = urlparse(self.start_url)
        return (parsed_url.netloc == parsed_start_url.netloc and 
                parsed_url.path.startswith(parsed_start_url.path))

    def normalize_url(self, url):
        return url.rstrip('/').lower()

    def analyze_page(self, page_source, url):
        system_prompt = """You are a web scraping expert. Analyze the given HTML and provide the following information:
        1. Determine if Selenium will be required for scraping.
        2. Provide a brief description of the page content.
        3. Note any potential challenges or errors in scraping this page.
        4. Provide any additional notes about the page structure.
        
        Respond in the following format:
        Selenium required: Yes/No
        Page description: [brief description]
        Potential errors: [list any potential errors or 'None' if no errors detected]
        Additional notes: [your notes here]"""
        
        agent_response = self.agent.generate_response(system_prompt, page_source)
        
        selenium_required = "Yes" if "selenium required: yes" in agent_response.lower() else "No"
        
        description = ""
        errors = ""
        additional_notes = ""
        
        for line in agent_response.split('\n'):
            if line.startswith("Page description:"):
                description = line.split(":", 1)[1].strip()
            elif line.startswith("Potential errors:"):
                errors = line.split(":", 1)[1].strip()
            elif line.startswith("Additional notes:"):
                additional_notes = line.split(":", 1)[1].strip()
        
        return selenium_required, description, errors, additional_notes

    def clean_and_parse_dict(self, text):
        text = re.sub(r'```python\s*\n', '', text)
        text = re.sub(r'```\s*$', '', text)
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
        try:
            return ast.literal_eval(text)
        except (SyntaxError, ValueError) as e:
            print(f"Error parsing dict: {e}")
            print("Cleaned text:")
            print(text)
            return None

    def deep_page_analysis(self, url):
        logging.info(f"Starting deep_page_analysis for URL: {url}")
        
        system_prompt = """You are a web scraping expert. Analyze the given HTML and provide the following information:
        1. Determine if Selenium will be required for scraping.
        2. List out each HTML element and provide a description of what it contains.
        3. Note any potential challenges or errors in scraping this page.
        4. Provide any additional notes about the page structure.
        5. Note which elements you believe are the most important for scraping.

        Format your response as a Python dictionary with the following structure:
        {
            'selenium_required': True/False,
            'elements': [
                {'tag': 'element_tag', 'description': 'description of content'},
                ...
            ],
            'challenges': ['challenge1', 'challenge2', ...],
            'notes': 'additional notes about page structure',
            'important_elements': ['element1', 'element2', ...]
        }
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            page_source = response.text
            soup = BeautifulSoup(page_source, 'html.parser')
            
            if len(soup.find_all()) < 10:
                raise Exception("Page content seems incomplete")
            
        except Exception as e:
            logging.warning(f"BeautifulSoup failed for {url}. Error: {str(e)}. Trying Selenium...")
            
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)
            
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                page_source = driver.page_source
            finally:
                driver.quit()
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text()
        
        relevant_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'img', 'ul', 'ol', 'li', 'table'])
        
        page_structure = {
            'text_content': text_content,
            'relevant_tags': [
                {
                    'name': tag.name,
                    'content': tag.get_text().strip() if tag.name != 'img' else tag.get('src', ''),
                    'attributes': tag.attrs
                } for tag in relevant_tags
            ]
        }
        
        page_structure_str = json.dumps(page_structure, indent=2)
        
        logging.info(f"Sending request to agent with system_prompt and page_structure_str")
        agent_response = self.agent.generate_response(system_prompt, page_structure_str)
        
        logging.info(f"agent_response type: {type(agent_response)}")
        logging.info(f"agent_response content: {agent_response!r}")  # Use !r for a debug-friendly representation

        if isinstance(agent_response, str):
            cleaned_response = self.clean_and_parse_dict(agent_response)
            if cleaned_response:
                agent_response = cleaned_response
            else:
                logging.error("Failed to parse cleaned agent_response as a dictionary")
                agent_response = {
                    "selenium_required": False,
                    "elements": [],
                    "challenges": ["Failed to parse agent response"],
                    "notes": "Error: Could not parse response as a dictionary",
                    "important_elements": []
                }
        elif not agent_response:
            logging.warning("agent_response is empty or None")
            agent_response = {
                "selenium_required": False,
                "elements": [],
                "challenges": [],
                "notes": "No response from agent",
                "important_elements": []
            }

        default_keys = ["selenium_required", "elements", "challenges", "notes", "important_elements"]
        for key in default_keys:
            if key not in agent_response:
                agent_response[key] = [] if key in ["elements", "challenges", "important_elements"] else ""

        selenium_required = "Yes" if agent_response.get("selenium_required", False) else "No"
        
        analysis_data = {
            'url': [url],
            'selenium_required': [selenium_required],
            'description': [json.dumps(agent_response.get('elements', []))],
            'challenges': [json.dumps(agent_response.get('challenges', []))],
            'notes': [agent_response.get('notes', '')],
            'important_elements': [json.dumps(agent_response.get('important_elements', []))]
        }
        if self.deep_dive is None:
            analysis_df = pd.DataFrame(analysis_data)
        else:
            analysis_df = pd.concat([self.deep_dive, pd.DataFrame(analysis_data)], ignore_index=True)
        
        csv_filename = f"{self.domain}_page_analysis_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        analysis_df.to_csv(csv_filename, index=False, quoting=csv.QUOTE_ALL)
        self.deep_dive = analysis_df
        logging.info(f"Page analysis for {url} saved to {csv_filename}")
        
        return selenium_required, analysis_df['description'][0], analysis_df['challenges'][0], analysis_df['notes'][0]
        

    def crawl_page(self, url):
        normalized_url = self.normalize_url(url)
        if normalized_url in self.visited:
            logging.info(f"Skipping {url} - Already visited")
            return None, None, None, None, None

        if not self.is_allowed_by_robots(url):
            logging.info(f"Skipping {url} - Disallowed by robots.txt")
            return None, "Disallowed by robots.txt", None, None, None

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            page_source = self.driver.page_source
            
            selenium_required, description, errors, additional_notes = self.analyze_page(page_source, url)
            
            links = []
            for element in self.driver.find_elements(By.TAG_NAME, "a"):
                href = element.get_attribute("href")
                if href and self.is_same_domain(href):
                    normalized_href = self.normalize_url(href)
                    if normalized_href not in self.visited:
                        links.append(href)
            
            return links, selenium_required, description, errors, additional_notes
        except TimeoutException:
            logging.error(f"Timeout while loading {url}")
            return None, None, None, f"Error: Timeout while loading page", None
        except Exception as e:
            logging.error(f"Error crawling {url}: {str(e)}")
            return None, None, None, f"Error: {str(e)}", None

    def save_chunk(self):
        df = pd.DataFrame(self.results)
        csv_filename = f"{self.domain}_crawl_results_chunk_{self.current_chunk}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        df.to_csv(csv_filename, index=False, quoting=csv.QUOTE_ALL)
        logging.info(f"Chunk {self.current_chunk} saved to {csv_filename}")
        self.results = []

    def get_directory_level(self, url):
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/')
        return len(path.split('/'))

    def crawl_website(self):
        sitemap_urls = self.get_sitemap()
        self.to_visit.extend([url for url in sitemap_urls if self.is_same_domain(url)])

        try:
            while self.to_visit:
                if self.total_chunks is not None and self.current_chunk >= self.total_chunks:
                    logging.info(f"Reached total chunks limit of {self.total_chunks}. Stopping crawl.")
                    break

                url = self.to_visit.pop(0)
                normalized_url = self.normalize_url(url)
                if normalized_url in self.visited:
                    continue

                logging.info(f"Crawling: {url}")
                links, selenium_required, description, errors, additional_notes = self.crawl_page(url)
                self.visited.add(normalized_url)

                if links is not None:
                    self.results.append({
                        'url': url,
                        'links': ', '.join(links),
                        'selenium_required': selenium_required,
                        'description': description,
                        'errors': errors,
                        'additional_notes': additional_notes
                    })
                    self.to_visit.extend([link for link in links if self.normalize_url(link) not in self.visited])

                if len(self.results) >= self.chunk_size:
                    self.current_chunk += 1
                    self.save_chunk()
                    
                new_directory_level = self.get_directory_level(url)
                if self.deep_analysis:
                    self.deep_page_analysis(url)
                elif self.deep_analysis_on_level_change and new_directory_level != self.current_directory_level:
                    logging.info(f"Directory level changed from {self.current_directory_level} to {new_directory_level}. Running deep analysis.")
                    self.deep_page_analysis(url)
                    self.current_directory_level = new_directory_level

                time.sleep(self.throttle)

            if self.results:
                self.current_chunk += 1
                self.save_chunk()

            logging.info(f"Crawl completed. Total pages crawled: {len(self.visited)}")
        finally:
            self.driver.quit()

    def write_to_csv(self, url, description):
        logging.info(f"Writing to CSV - URL: {url}, Description length: {len(description)}")
        logging.info("Data successfully written to CSV")

if __name__ == "__main__":
    start_url = "https://www.erowid.org/"  # Replace with your desired starting URL
    crawler = WebCrawler(start_url, chunk_size=50, total_chunks=None)  # Set to None for indefinite crawling
    # crawler.crawl_website()
    crawler.deep_page_analysis("https://www.erowid.org/")