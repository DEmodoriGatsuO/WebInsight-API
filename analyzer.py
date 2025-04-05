# analyzer.py
import requests
import json
import logging
import time

logger = logging.getLogger(__name__)

class PerplexityAnalyzer:
    """Class for analyzing content using the Perplexity API"""
    
    def __init__(self, api_key, max_retries=3, retry_delay=2):
        """
        Args:
            api_key (str): Perplexity API key
            max_retries (int): Maximum number of retries for API call failures
            retry_delay (int): Delay between retries in seconds
        """
        self.api_key = api_key
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
    def analyze(self, content, query_type="summary"):
        """Analyze content using the Perplexity API
        
        Args:
            content (str): Content to analyze
            query_type (str): Analysis type. One of "summary", "analysis", "custom"
            
        Returns:
            str: Analysis result
        """
        if not self.api_key:
            raise Exception("Perplexity API key is not configured")
            
        # Build prompt based on query type
        prompt = self._build_prompt(content, query_type)
        
        # Send API request with retries
        for attempt in range(self.max_retries):
            try:
                result = self._call_api(prompt)
                return result
            except Exception as e:
                logger.warning(f"API call failed (attempt {attempt+1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"API call failed (max retries reached): {str(e)}")
                    raise Exception(f"Perplexity API call error: {str(e)}")
    
    def _build_prompt(self, content, query_type):
        """Build prompt based on analysis type"""
        if query_type == "summary":
            return f"""Please provide a summary and key points for the following content.
            
Content:
{content}

Summary (approximately 300 characters):
Key points (up to 5):
"""
        elif query_type == "analysis":
            return f"""Please provide a detailed analysis of the following content. Include main information, reliability assessment, additional related information, and different perspectives.

Content:
{content}

Analysis:
1. Summary of main information
2. Assessment of information reliability
3. Supplementary information (from web search)
4. Different perspectives or considerations
5. Related data or statistics (if available)
"""
        elif query_type == "custom":
            # For custom queries, use the content as is
            return content
        else:
            # Default to basic summary
            return f"""Please summarize the following content:

{content}
"""
            
    def _call_api(self, prompt):
        """Call the Perplexity API"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": "sonar-deep-research",  # Use online model
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024
        }
        
        logger.debug("Calling Perplexity API")
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception("Invalid response from Perplexity API")
        except requests.exceptions.RequestException as e:
            logger.error(f"Perplexity API call error: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"API response: {e.response.text}")
            raise Exception(f"Perplexity API call error: {str(e)}")