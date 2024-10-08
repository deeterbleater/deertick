# DeerTick Data Processing Tool User Guide

## Overview

The DeerTick Data Processing Tool is a web-based interface that combines three powerful modules:
1. Dataset Generator
2. Web Crawler
3. Dynamic Blog Scraper

This tool allows users to generate datasets, crawl websites, and scrape blogs through a simple user interface.

## Getting Started

1. Ensure you have Python installed on your system.
2. Install the required dependencies:
   ```
   pip install flask pandas requests beautifulsoup4 datasets huggingface_hub selenium
   ```
3. Save the `data_tool.py` file in your project directory.
4. Create a `templates` folder in the same directory and save the `index.html` file inside it.

## Running the Tool

1. Open a terminal or command prompt.
2. Navigate to the directory containing `data_tool.py`.
3. Run the following command:
   ```
   python data_tool.py
   ```
4. Open a web browser and go to `http://127.0.0.1:5000/` or `http://localhost:5000/`.

## Using the Tool

### Generate Dataset

This feature uses the DatasetGenerator module to create datasets from various input sources.

Fields:
- Input Path: Path to the input directory or file
- Text Column: Name of the text column for tabular files (optional)
- HuggingFace Repo Name: Name of the HuggingFace repository to upload to (optional)
- HuggingFace Token: Your HuggingFace API token (optional)
- Upload to HuggingFace: Check to upload the dataset to HuggingFace
- Preprocess: Check to preprocess the text data
- Generate Stats: Check to generate dataset statistics
- Split Data: Check to split the dataset into train/val/test sets

Click "Generate Dataset" to start the process.

### Crawl Website

This feature uses the WebCrawler module to crawl websites and extract information.

Fields:
- Start URL: The starting URL for the crawl
- Chunk Size: Number of pages to crawl before saving results
- Total Chunks: Total number of chunks to crawl (optional, leave blank for unlimited)
- Deep Analysis: Check to perform deep analysis on every page

Click "Crawl Website" to start the crawl.

### Scrape Blogs

This feature uses the DynamicBlogScraper module to scrape content from blog posts.

Fields:
- URL Source: Source of URLs to scrape (e.g., CSV file path, database name)
- Export to Database: Check to export scraped data to a database

Click "Scrape Blogs" to start scraping.

## Notes

- The tool will display an alert message when each operation is completed.
- For long-running tasks, the interface may appear unresponsive. Be patient and wait for the alert.
- Ensure you have the necessary permissions and comply with website terms of service when crawling or scraping.
- When using the HuggingFace features, make sure you have a valid account and API token.

## Troubleshooting

- If you encounter any errors, check the terminal where you ran `data_tool.py` for error messages.
- Ensure all required modules (`data_set_gen.py`, `crawler.py`, `scraper.py`) are in the same directory as `data_tool.py`.
- Verify that all dependencies are correctly installed.

## Further Customization

This tool provides a basic interface for the DeerTick modules. For more advanced usage or customization, refer to the individual module documentation or modify the `data_tool.py` file.