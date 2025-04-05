# WebInsight API

A web API that scrapes content from URLs, analyzes it using Perplexity AI, and returns insights and summaries.

## Project Overview

WebInsight API is a Python-based web service that allows users to extract meaningful information from web articles. It combines web scraping with AI-powered analysis to provide summaries, key points, and in-depth analysis of content.

### Key Features

- **Web Scraping**: Extract content from any URL using Beautiful Soup
- **Content Analysis**: Analyze content using Perplexity API
- **Multiple Analysis Types**: Get basic summaries or detailed analysis
- **API Structure**: Simple RESTful JSON API endpoints
- **Rate Limiting**: Protection against API abuse
- **Error Handling**: Comprehensive error reporting

## Technical Stack

- **Backend**: Python + Flask
- **Hosting**: PythonAnywhere
- **Web Scraping**: Beautiful Soup, Requests
- **Text Processing**: html2text, regular expressions
- **AI Analysis**: Perplexity API

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Perplexity API key ([Get one here](https://www.perplexity.ai/api))

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/webinsight-api.git
   cd webinsight-api
   ```

2. Create a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your configuration:
   ```
   PERPLEXITY_API_KEY=your_perplexity_api_key_here
   FLASK_ENV=development
   MAX_CONTENT_LENGTH=200000
   SCRAPE_TIMEOUT=30
   ```

5. Run the application:
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5000/`.

### Deploying to PythonAnywhere

1. Sign up for a [PythonAnywhere](https://www.pythonanywhere.com/) account.

2. Create a new web app:
   - Choose Flask
   - Select the latest Python version

3. Upload your code through the PythonAnywhere Files interface or use Git:
   ```bash
   # In PythonAnywhere bash console
   git clone https://github.com/yourusername/webinsight-api.git
   ```

4. Set up a virtual environment and install dependencies:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.8 webinsight-venv
   workon webinsight-venv
   pip install -r webinsight-api/requirements.txt
   ```

5. Configure your web app:
   - Set WSGI configuration file to point to `wsgi.py`
   - Set source code directory and working directory to your project path

6. Add environment variables in the PythonAnywhere web app configuration or directly in the WSGI file.

7. Reload the web app.

## API Usage

### Endpoints

#### 1. Basic Information
```
GET /
```
Returns API documentation and available endpoints.

#### 2. Scrape URL
```
POST /api/scrape
```
**Body:**
```json
{
  "url": "https://example.com/article"
}
```
**Response:** Basic scraped content and summary.

#### 3. Analyze URL
```
POST /api/analyze
```
**Body:**
```json
{
  "url": "https://example.com/article",
  "query_type": "analysis"
}
```
**Optional Parameters:**
- `query_type`: Type of analysis to perform (options: "summary", "analysis")
- `custom_query`: Custom prompt for the Perplexity API

**Response:** Detailed analysis of the content.

#### 4. Health Check
```
GET /api/health
```
**Response:** API status information.

### Example Usage

Using cURL:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"url":"https://example.com/article"}' http://yourdomain.pythonanywhere.com/api/analyze
```

Using Python:
```python
import requests

url = "http://yourdomain.pythonanywhere.com/api/analyze"
payload = {
    "url": "https://example.com/article",
    "query_type": "analysis"
}
response = requests.post(url, json=payload)
data = response.json()
print(data["analysis"])
```

## Project Structure

```
WebInsight-API/
│
├── app.py              # Main application (Flask)
├── scraper.py          # Web scraping module
├── analyzer.py         # Perplexity API integration 
├── error_handler.py    # Error handling functionality
├── rate_limiter.py     # Rate limiting functionality
│
├── .env                # Environment variables (API keys, etc.)
├── requirements.txt    # Required packages
├── wsgi.py             # PythonAnywhere deployment file
└── README.md           # Project documentation
```

## Rate Limiting

To prevent abuse, the API implements rate limiting:
- Scraping endpoint: 10 requests per minute
- Analysis endpoint: 5 requests per minute

## Error Handling

The API provides descriptive error messages with appropriate HTTP status codes:
- 400: Bad Request (validation errors, scraping errors)
- 429: Too Many Requests (rate limit exceeded)
- 500: Internal Server Error
- 502: Bad Gateway (external API errors)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Perplexity AI](https://www.perplexity.ai/) for content analysis