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
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_sitemap(base_url):
    sitemap_url = urljoin(base_url, '/sitemap.xml')
    try:
        response = requests.get(sitemap_url)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            return [elem.text for elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    except Exception as e:
        logging.warning(f"Error fetching sitemap: {e}")
    return []

def is_allowed_by_robots(url, user_agent='*'):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_url = urljoin(base_url, '/robots.txt')
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logging.warning(f"Error checking robots.txt: {e}")
        return True  # Assume allowed if there's an error

def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def is_same_domain(url, domain):
    return urlparse(url).netloc == domain

def crawl_page(url, agent, driver, domain):
    if not is_allowed_by_robots(url):
        logging.info(f"Skipping {url} - Disallowed by robots.txt")
        return None, "Disallowed by robots.txt", None

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        page_source = driver.page_source
        
        system_prompt = "You are a web scraping expert. Analyze the given HTML and determine if Selenium will be required for scraping. Also, provide any additional notes about the page structure or potential challenges. Respond in the format: 'Selenium required: Yes/No. Additional notes: [your notes here]'"
        agent_response = agent.generate_response(system_prompt, page_source)
        
        selenium_required = "Yes" if "selenium required: yes" in agent_response.lower() else "No"
        additional_notes = agent_response.split("Additional notes:")[-1].strip() if "Additional notes:" in agent_response else ""
        
        links = []
        for element in driver.find_elements(By.TAG_NAME, "a"):
            href = element.get_attribute("href")
            if href and is_same_domain(href, domain):
                links.append(urljoin(url, href))
        
        return links, selenium_required, additional_notes
    except TimeoutException:
        logging.error(f"Timeout while loading {url}")
        return None, f"Error: Timeout while loading page", None
    except Exception as e:
        logging.error(f"Error crawling {url}: {str(e)}")
        return None, f"Error: {str(e)}", None

def crawl_website(start_url):
    agent = Agent(model="gemini-pro", provider="openrouter")
    driver = setup_selenium()
    visited = set()
    to_visit = [start_url]
    results = []
    domain = urlparse(start_url).netloc

    sitemap_urls = get_sitemap(start_url)
    to_visit.extend([url for url in sitemap_urls if is_same_domain(url, domain)])

    try:
        while to_visit:
            url = to_visit.pop(0)
            if url in visited:
                continue

            logging.info(f"Crawling: {url}")
            links, selenium_required, additional_notes = crawl_page(url, agent, driver, domain)
            visited.add(url)

            if links is not None:
                results.append({
                    'url': url,
                    'links': ', '.join(links),
                    'selenium_required': selenium_required,
                    'additional_notes': additional_notes
                })
                # Add all new links to the beginning of to_visit list (depth-first approach)
                new_links = [link for link in links if link not in visited and link not in to_visit]
                to_visit = new_links + to_visit

            time.sleep(1)  # Be polite to the server

        # Create a DataFrame and save to CSV
        df = pd.DataFrame(results)
        csv_filename = f"{domain}_crawl_results_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        df.to_csv(csv_filename, index=False, quoting=csv.QUOTE_ALL)
        logging.info(f"Crawl results saved to {csv_filename}")
        logging.info(f"Total pages crawled: {len(results)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    start_url = "https://webscraper.io/test-sites/e-commerce/static"  # Replace with your desired starting URL
    crawl_website(start_url)