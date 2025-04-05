# scraper.py
import requests
from bs4 import BeautifulSoup
import html2text
import re
import logging

logger = logging.getLogger(__name__)

class WebScraper:
    """Class for scraping content from URLs"""
    
    def __init__(self, timeout=30):
        """
        Args:
            timeout (int): Request timeout in seconds
        """
        self.timeout = timeout
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.ignore_tables = False
        self.h2t.unicode_snob = True
        self.h2t.body_width = 0  # No wrapping

    def scrape(self, url):
        """Scrape content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Check and set encoding
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
                
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Scraping error [{url}]: {str(e)}")
            raise Exception(f"Scraping error: {str(e)}")

    def parse_content(self, html_content):
        """Parse HTML content to extract title, metadata, and main text"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.text.strip()
            
        # Meta description
        description = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            description = meta_desc['content'].strip()
            
        # OGP metadata
        og_data = {}
        for meta in soup.find_all('meta', property=re.compile('^og:')):
            property_name = meta.get('property', '').replace('og:', '')
            if property_name and meta.get('content'):
                og_data[property_name] = meta['content'].strip()
                
        # Extract main content (trying multiple methods)
        article_content = self._extract_article_content(soup)
                
        # Clean up the content
        article_content = self._clean_text(article_content)
            
        return {
            "title": title,
            "description": description,
            "og_data": og_data,
            "content": article_content
        }
    
    def _extract_article_content(self, soup):
        """Try multiple methods to extract the article content"""
        article_content = ""
        
        # Method 1: Look for common article containers
        article_containers = soup.select('article, .article, .post, .content, main, #main, #content')
        if article_containers:
            article_content = article_containers[0].get_text(separator='\n')
            return article_content
        
        # Method 2: Combine text from paragraph tags
        p_tags = soup.find_all('p')
        if p_tags and len(p_tags) > 3:  # If there are at least a few paragraphs
            article_content = '\n\n'.join([p.get_text().strip() for p in p_tags if len(p.get_text().strip()) > 40])
            if len(article_content) > 500:  # If there's a reasonable amount of content
                return article_content
        
        # Method 3: Find the largest text block (likely to be the main content)
        text_blocks = []
        for tag in soup.find_all(['div', 'section']):
            text = tag.get_text().strip()
            if len(text) > 200:  # Ignore blocks that are too short
                text_blocks.append((tag, text))
        
        if text_blocks:
            # Sort by text length
            text_blocks.sort(key=lambda x: len(x[1]), reverse=True)
            article_content = text_blocks[0][1]
            return article_content
        
        # Method 4: Use HTML2Text to convert HTML to Markdown
        markdown = self.h2t.handle(str(soup))
        
        # Remove unnecessary content
        markdown = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)  # Remove images
        markdown = re.sub(r'\n\s*\n+', '\n\n', markdown)     # Remove excessive line breaks
        
        return markdown
            
    def _clean_text(self, text):
        """Clean and normalize text"""
        # Remove excessive whitespace and line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        # Remove common website navigation and footer text
        common_patterns = [
            r'Menu', r'Search', r'Home', r'Contact', r'About', r'Privacy Policy',
            r'Terms of Service', r'© \d{4}', r'All Rights Reserved', r'Copyright'
        ]
        for pattern in common_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Trim text and fix indentation
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        return '\n\n'.join(cleaned_lines)