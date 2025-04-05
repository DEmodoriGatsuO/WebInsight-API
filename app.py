# app.py
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import logging
from scraper import WebScraper
from analyzer import PerplexityAnalyzer
from error_handler import register_error_handlers, ValidationError, ScrapingError, AnalysisError
from rate_limiter import RateLimiter, rate_limit
from security import setup_security, require_auth

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask application
app = Flask(__name__)

# Register error handlers
register_error_handlers(app)

# Apply security settings
app = setup_security(app)

# Environment variables
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 200000))
SCRAPE_TIMEOUT = int(os.getenv("SCRAPE_TIMEOUT", 30))

# Rate limiters
api_limiter = RateLimiter(limit=10, window=60)  # 10 requests per minute
analysis_limiter = RateLimiter(limit=5, window=60)  # 5 requests per minute (for more resource-intensive analysis)

@app.route('/', methods=['GET'])
def home():
    """Homepage (API documentation)"""
    return jsonify({
        "api": "WebInsight API",
        "version": "1.0.0",
        "endpoints": {
            "/api/scrape": "Scrape content from URL and provide a summary",
            "/api/analyze": "Scrape content from URL and provide detailed analysis",
            "/api/health": "API health check"
        },
        "usage": {
            "example": {
                "method": "POST",
                "url": "/api/analyze",
                "body": {
                    "url": "https://example.com/article",
                    "query_type": "analysis"
                }
            },
            "authentication": {
                "api_key": "Include X-API-Key header or api_key query parameter",
                "basic_auth": "Use HTTP Basic Authentication"
            }
        }
    })

@app.route('/api/scrape', methods=['POST'])
@rate_limit(api_limiter)
def scrape_url():
    """Scrape URL and provide basic summary"""
    try:
        # Validate request
        data = request.get_json()
        if not data:
            raise ValidationError("JSON data is required")
            
        url = data.get('url')
        if not url:
            raise ValidationError("URL is required")
            
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            raise ValidationError("Not a valid URL")
            
        logger.info(f"Scraping request: {url}")
        
        # Execute scraping
        scraper = WebScraper(timeout=SCRAPE_TIMEOUT)
        try:
            html_content = scraper.scrape(url)
            if len(html_content) > MAX_CONTENT_LENGTH:
                logger.warning(f"Content too large: {len(html_content)} bytes")
                html_content = html_content[:MAX_CONTENT_LENGTH]
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            raise ScrapingError(f"Failed to scrape URL: {str(e)}")
            
        # Parse content
        parsed_content = scraper.parse_content(html_content)
        
        # Prepare content for summary
        content_for_summary = parsed_content['content']
        if len(content_for_summary) > 10000:
            content_for_summary = content_for_summary[:10000] + "..."
        
        # Return basic information
        result = {
            "url": url,
            "title": parsed_content['title'],
            "description": parsed_content['description'],
            "og_data": parsed_content['og_data'],
            "content_length": len(parsed_content['content']),
            "content_preview": parsed_content['content'][:500] + "..." if len(parsed_content['content']) > 500 else parsed_content['content']
        }
        
        # Add summary if Perplexity API key is available
        if PERPLEXITY_API_KEY:
            try:
                analyzer = PerplexityAnalyzer(PERPLEXITY_API_KEY)
                result["summary"] = analyzer.analyze(content_for_summary, "summary")
            except Exception as e:
                logger.error(f"Summary error: {str(e)}")
                result["summary_error"] = f"Error occurred while summarizing content: {str(e)}"
        
        logger.info(f"Scraping completed: {url} (title: {parsed_content['title'][:30]}...)")
        return jsonify(result)
    
    except ValidationError as e:
        # ValidationError is already handled by error_handler
        raise
    except ScrapingError as e:
        # ScrapingError is already handled by error_handler
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise  # General exceptions are handled by error_handler

@app.route('/api/analyze', methods=['POST'])
@rate_limit(analysis_limiter)
def analyze_url():
    """Deep analysis of URL content with Perplexity API"""
    try:
        # Validate request
        data = request.get_json()
        if not data:
            raise ValidationError("JSON data is required")
            
        url = data.get('url')
        if not url:
            raise ValidationError("URL is required")
            
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            raise ValidationError("Not a valid URL")
            
        query_type = data.get('query_type', 'analysis')  # Analysis type (default is detailed analysis)
        custom_query = data.get('custom_query', '')      # Custom query
        
        logger.info(f"Analysis request: {url} (type: {query_type})")
        
        # Check Perplexity API key
        if not PERPLEXITY_API_KEY:
            raise AnalysisError("Perplexity API key is not configured")
            
        # Execute scraping
        scraper = WebScraper(timeout=SCRAPE_TIMEOUT)
        try:
            html_content = scraper.scrape(url)
            if len(html_content) > MAX_CONTENT_LENGTH:
                logger.warning(f"Content too large: {len(html_content)} bytes")
                html_content = html_content[:MAX_CONTENT_LENGTH]
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            raise ScrapingError(f"Failed to scrape URL: {str(e)}")
            
        # Parse content
        parsed_content = scraper.parse_content(html_content)
        
        # Prepare content for analysis
        content_for_analysis = parsed_content['content']
        if len(content_for_analysis) > 15000:
            content_for_analysis = content_for_analysis[:15000] + "..."
        
        # Execute analysis
        try:
            analyzer = PerplexityAnalyzer(PERPLEXITY_API_KEY)
            
            # Use custom query if provided
            if custom_query:
                analysis_content = f"{custom_query}\n\nURL: {url}\n\nContent:\n{content_for_analysis}"
                analysis_result = analyzer.analyze(analysis_content, "custom")
            else:
                analysis_result = analyzer.analyze(content_for_analysis, query_type)
                
            # Return results
            result = {
                "url": url,
                "title": parsed_content['title'],
                "description": parsed_content['description'],
                "analysis": analysis_result,
                "metadata": {
                    "query_type": query_type,
                    "custom_query": custom_query if custom_query else None,
                    "content_length": len(parsed_content['content'])
                }
            }
            
            logger.info(f"Analysis completed: {url}")
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            raise AnalysisError(f"Error occurred while analyzing content: {str(e)}")
    
    except ValidationError as e:
        raise
    except ScrapingError as e:
        raise
    except AnalysisError as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "OK", 
        "api_version": "1.0.0",
        "perplexity_api": "configured" if PERPLEXITY_API_KEY else "not configured"
    })

if __name__ == '__main__':
    # For local development
    app.run(debug=True)