import requests
from bs4 import BeautifulSoup
import os
from agent import Agent
import time
import re
from datetime import datetime
import pandas as pd
import ast
import json
import hashlib
from db import DatabaseManager
import asyncio

class DynamicBlogScraper:
    """A class for dynamically scraping blog content using AI-generated instructions."""

    def __init__(self, export_to_db=False):
        self.bs_docs = '''
        You need to identify the content on the page that is not a link unless the link is in the body of an article.
        You need to identify the title of the article.
        You must return a list of instructions for the beautifulsoup library.
        The first element of the list should be the type of instruction, which is "find_one", "find_all", or "find_all_alt".
        The second element of the list should be the tag type, which is a string.
        The third element of the list should be the class name, which is a string.
        The fourth element of the list should be the kind of text that the element contains, such as "title" or "body", which is a string.
        If you are looking for a tag that has no class, use an empty string as the class name.
        Example: ["find_one", "h1", "class_name", "title"] or ["find_all", "p", "", "body"]
        '''
        self.output_dir = "scraped_blogs"
        self.ensure_cache_dir()
        self.df = pd.DataFrame(columns=['URL', 'Title', 'Content', 'Full Text'])
        self.system_prompt_articles = f"You are an intelligent web scraper. Make a list of the elements beautifulsoup would need to use to get all pertinent information from the following text, ignoring navigation, headers, footers, and sidebars. Please format your response as follows please put the python list within three asterisks or it will be rejected: <your main response as a string>, ***<a relevant list in python format>*** \n{self.bs_docs}"
        self.sleep_time = 0.5
        self.export_to_db = export_to_db
        self.db_manager = None
        if self.export_to_db:
            self.db_manager = DatabaseManager()

    async def initialize_db(self):
        if self.export_to_db:
            await self.db_manager.create_pool()
            await self.db_manager.create_scraped_data_table()

    async def export_to_database(self, data):
        if self.export_to_db:
            await self.db_manager.insert_scraped_data(data[0], data[1], data[2], data[3])

    async def get_urls_from_database(self):
        if self.export_to_db:
            async with self.db_manager.db_pool.acquire() as conn:
                rows = await conn.fetch('SELECT url FROM scraped_data')
                return [row['url'] for row in rows]
        return []

    async def get_scraped_data_from_database(self):
        if self.export_to_db:
            async with self.db_manager.db_pool.acquire() as conn:
                rows = await conn.fetch('SELECT * FROM scraped_data')
                return [dict(row) for row in rows]
        return []

    def split_content(self, content, max_length=4000):
        """Split content into chunks of maximum length."""
        return [content[i:i+max_length] for i in range(0, len(content), max_length)]

    def clean_html(self, html):
        """Remove script and style elements from HTML content."""
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text()

    def process_instructions(self, instructions, html_content):
        """Process BeautifulSoup instructions to extract content from HTML."""
        print(f"Debug: instructions = {instructions}")  # Add this line
        
        if not instructions:
            print("Debug: instructions is empty")  # Add this line
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        content = ""
        
        if instructions[0] == "find_one":
            element = soup.find(instructions[1], class_=instructions[2])
            if element:
                content = element.get_text()
        elif instructions[0] == "find_all":
            elements = soup.find_all(instructions[1])
            content = '\n'.join([x.get_text() for x in elements])
        elif instructions[0] == "find_all_alt":
            elements = soup.find_all(instructions[1])
            content = '\n'.join([x[instructions[2]].get_text() for x in elements if instructions[2] in x.attrs])
        else:
            return None
        return content

    def get_cache_key(self, url):
        """Generate a cache key for a given URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def save_to_cache(self, url, instructions):
        """Save scraping instructions to cache."""
        cache_key = self.get_cache_key(url)
        cache_file = f"cache/{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(instructions, f)

    def load_from_cache(self, url):
        """Load scraping instructions from cache."""
        cache_key = self.get_cache_key(url)
        cache_file = f"cache/{cache_key}.json"
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def scrape_blog(self, url):
        """Scrape a blog post using AI-generated or cached instructions."""
        system_prompt_articles = self.system_prompt_articles
        
        def get_new_instructions(url, soup):
            agent = Agent(model="Cohere: Command R+", provider="openrouter")
            agent_response = agent.generate_response(system_prompt_articles, soup.get_text())
            
            if not agent_response or '***' not in agent_response:
                print(f"Warning: Agent response for {url} does not contain the expected format: {agent_response}")
                return [['find_all', 'p', '']]
            else:
                try:
                    paragraphs_parts = agent_response.split('***')
                    return ast.literal_eval(paragraphs_parts[1])
                except (IndexError, SyntaxError, ValueError) as e:
                    print(f"Error parsing agent response for {url}: {e}")
                    return [['find_all', 'p', '']]

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            cached_instructions = self.load_from_cache(url)
            if cached_instructions:
                print(f"Using cached instructions for {url}")
                paragraphs = cached_instructions
            else:
                paragraphs = get_new_instructions(url, soup)
                if paragraphs:
                    self.save_to_cache(url, paragraphs)

            content_parts = [self.process_instructions(x, response.text) for x in paragraphs]
            content_parts = [part for part in content_parts if part]

            if not content_parts:
                print(f"No content extracted for {url} using cached/initial instructions. Trying new instructions.")
                paragraphs = get_new_instructions(url, soup)
                content_parts = [self.process_instructions(x, response.text) for x in paragraphs]
                content_parts = [part for part in content_parts if part]

                if not content_parts:
                    raise ValueError(f"No content extracted for {url} even with new instructions")
                else:
                    self.save_to_cache(url, paragraphs)  # Update cache with new instructions

            title = soup.title.string if soup.title else "Untitled"
            if title == "Untitled":
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text(strip=True)

            full_content = '\n\n'.join(content_parts)
            cleaned_content = self.clean_html(full_content)
            is_valid, validation_message = self.validate_content(url, title, cleaned_content)

            if not is_valid:
                raise ValueError(f"Validation failed for {url}: {validation_message}")

            return [url, title, cleaned_content, soup.get_text()]

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {str(e)}")
            return [url, "Error", f"Request failed: {str(e)}", ""]

        except ValueError as e:
            print(f"Error processing {url}: {str(e)}")
            return [url, "Error", str(e), ""]

        except Exception as e:
            print(f"Unexpected error scraping {url}: {str(e)}")
            import traceback
            traceback.print_exc()
            return [url, "Error", f"Unexpected error: {str(e)}", ""]

    def get_unique_filepath(self, directory, filename):
        """Generate a unique filepath by adding a number to the end of the filename if it already exists."""
        name, ext = os.path.splitext(filename)
        filepath = os.path.join(directory, filename)
        counter = 1
        while os.path.exists(filepath):
            new_filename = f"{name}_{counter}{ext}"
            filepath = os.path.join(directory, new_filename)
            counter += 1
        return filepath

    def ensure_cache_dir(self):
        """Create the cache directory if it doesn't exist."""
        cache_dir = "cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def validate_content(self, url, title, content):
        """Validate the scraped content."""
        if not content.strip():
            return False, "Empty content"
        if len(content) < 100:
            return False, "Content too short"
        if not title or title == "Untitled":
            return False, "Missing or generic title"
        if content.count('<') > len(content) / 10:
            return False, "Content appears to be HTML"
        return True, "Content validated"

    async def run(self, urls=None):
        """Run the scraper on a list of URLs or fetch from database if not provided."""
        os.makedirs(self.output_dir, exist_ok=True)

        if self.export_to_db:
            await self.initialize_db()

        if urls is None and self.export_to_db:
            urls = await self.get_urls_from_database()

        try:
            for url in urls:
                try:
                    # Check if URL has already been scraped
                    if self.export_to_db:
                        existing_data = await self.db_manager.conn.fetchrow(
                            'SELECT * FROM scraped_data WHERE url = $1', url
                        )
                        if existing_data:
                            print(f"Skipping {url}, already scraped.")
                            continue

                    # Fetch and process the content
                    data = self.scrape_blog(url)
                    
                    if data:
                        new_row = pd.DataFrame({
                            'URL': [data[0]], 
                            'Title': [data[1]], 
                            'Content': [data[2]], 
                            'Full Text': [data[3]]
                        })
                        self.df = pd.concat([self.df, new_row], ignore_index=True)
                        
                        if self.export_to_db:
                            await self.export_to_database(data)
                    else:
                        print(f"No data returned for {url}")

                except Exception as e:
                    print(f"Error processing {url}: {str(e)}")

                time.sleep(self.sleep_time)  # Be polite to the server

            # Save the DataFrame to CSV
            csv_filename = os.path.join(self.output_dir, f"scraped_data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
            self.df.to_csv(csv_filename, index=False)
            print(f"All data saved to: {csv_filename}")
        except KeyboardInterrupt:
            print("\nScript interrupted by user. Saving current progress...")
            csv_filename = os.path.join(self.output_dir, f"scraped_data_interrupted_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
            self.df.to_csv(csv_filename, index=False)
            print(f"Partial data saved to: {csv_filename}")

    def get_urls_from_source(self, source):
        """
        Create a list of URLs from various source types:
        - CSV file
        - pandas DataFrame
        - Text file (.txt) with URLs separated by newlines or commas
        - Markdown file (.md) with URLs separated by newlines or commas
        
        :param source: Path to a file (CSV, TXT, MD) or a pandas DataFrame
        :return: List of URLs
        """
        if isinstance(source, str):
            file_extension = os.path.splitext(source)[1].lower()
            
            if file_extension == '.csv':
                try:
                    df = pd.read_csv(source)
                except FileNotFoundError:
                    print(f"Error: File '{source}' not found.")
                    return []
                except pd.errors.EmptyDataError:
                    print(f"Error: File '{source}' is empty.")
                    return []
                except Exception as e:
                    print(f"Error reading CSV file: {str(e)}")
                    return []
                
                if 'URL' not in df.columns:
                    if 'url' not in df.columns:
                        print("Error: The CSV file does not contain a 'URL' column.")
                        return []
                    else:
                        urls = df['url'].tolist()
                else:
                    urls = df['URL'].tolist()
                
            
            elif file_extension in ['.txt', '.md']:
                try:
                    with open(source, 'r') as file:
                        content = file.read()
                    # Split by newlines and commas, then flatten the list
                    urls = [url.strip() for line in content.split('\n') for url in line.split(',') if url.strip()]
                except FileNotFoundError:
                    print(f"Error: File '{source}' not found.")
                    return []
                except Exception as e:
                    print(f"Error reading file: {str(e)}")
                    return []
            
            else:
                print(f"Error: Unsupported file type '{file_extension}'. Please provide a CSV, TXT, or MD file.")
                return []
        
        elif isinstance(source, pd.DataFrame):
            if 'URL' not in source.columns:
                print("Error: The DataFrame does not contain a 'URL' column.")
                return []
            urls = source['URL'].tolist()
        
        else:
            print("Error: Invalid source type. Please provide a file path (CSV, TXT, MD) or a pandas DataFrame.")
            return []

        # Filter out any non-string or empty entries
        return [url for url in urls if isinstance(url, str) and url.strip()]

    def extract_content_fallback(self, soup):
        # Try to extract content from common tags
        for tag in ['article', 'main', 'div.content', 'div.post']:
            content = soup.select_one(tag)
            if content:
                return str(content)
        
        # If no specific content area found, try paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            return '\n'.join(str(p) for p in paragraphs)
        
        return None

if __name__ == "__main__":
    scraper = DynamicBlogScraper(export_to_db=True)
    
    # Example usage with various file types
    urls_from_csv = scraper.get_urls_from_source("scrape_errors.csv")
    
    
    # Example of fetching all scraped data from the database
    # scraped_data = asyncio.run(scraper.get_scraped_data_from_database())
    # print(f"Fetched {len(scraped_data)} records from the database")
    
    # Example usage with various file types
    # urls_from_csv = scraper.get_urls_from_source("scrape_errors.csv")
    # urls_from_txt = scraper.get_urls_from_source("path/to/your/urls.txt")
    # urls_from_md = scraper.get_urls_from_source("path/to/your/urls.md")
    
    # Example usage with a DataFrame
    # df = pd.DataFrame({'URL': ['https://example.com', 'https://example.org']})
    # urls_from_df = scraper.get_urls_from_source(df)
    
    # Use the URLs
    asyncio.run(scraper.run(urls_from_csv))  # or scraper.run(urls_from_df)