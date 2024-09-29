import requests
from bs4 import BeautifulSoup
import os
from agent import Agent
import time
import re

def split_content(content, max_length=4000):
    """Split content into chunks of maximum length."""
    return [content[i:i+max_length] for i in range(0, len(content), max_length)]

def clean_html(html):
    """Remove script and style elements"""
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text()

def scrape_blog(url, output_dir):
    # Create an Agent instance
    agent = Agent(model="gpt-4o", provider="openai")

    # Fetch the webpage
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the title
    title = soup.title.string if soup.title else "Untitled"

    # Clean and split the HTML content
    cleaned_content = clean_html(str(soup))
    content_chunks = split_content(cleaned_content)

    # Use the Agent to extract the main content from each chunk
    system_prompt = "You are an intelligent web scraper. Extract the main blog content from the following text, ignoring navigation, headers, footers, and sidebars. Return only the main article text."
    full_content = ""
    for chunk in content_chunks:
        content = agent.generate_response(system_prompt, chunk)
        full_content += content + "\n\n"

    # Create a filename from the title
    filename = re.sub(r'[^\w\-_\. ]', '_', title)
    filename = f"{filename[:50]}.txt"
    filepath = os.path.join(output_dir, filename)

    # Save the content to a file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_content)

    print(f"Scraped and saved: {filename}")

def main():
    # Ensure the output directory exists
    output_dir = "scraped_blogs"
    os.makedirs(output_dir, exist_ok=True)

    # Your list of blog URLs
    urls = [
    "https://www.theverge.com/2024/7/25/ai-chatbot-chatgpt-openai-investigation-reveals-security-concerns",
    "https://www.theverge.com/2024/7/24/ai-chatbot-chatgpt-openai-investigation-reveals-security-concerns",
    ]

    for url in urls:
        try:
            scrape_blog(url, output_dir)
            time.sleep(2)  # Be polite to the server
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")

if __name__ == "__main__":
    main()