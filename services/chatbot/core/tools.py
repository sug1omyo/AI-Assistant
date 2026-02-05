"""
Tool functions for chatbot
"""
import sys
import logging
import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Setup path
CHATBOT_DIR = Path(__file__).parent.parent.resolve()
if str(CHATBOT_DIR) not in sys.path:
    sys.path.insert(0, str(CHATBOT_DIR))

from core.config import GOOGLE_SEARCH_API_KEY_1, GOOGLE_SEARCH_API_KEY_2, GOOGLE_CSE_ID, GITHUB_TOKEN

logger = logging.getLogger(__name__)


def google_search_tool(query):
    """Google Custom Search API with improved error handling"""
    try:
        if not GOOGLE_SEARCH_API_KEY_1 or not GOOGLE_CSE_ID:
            return "❌ Google Search API chưa được cấu hình. Vui lòng thêm GOOGLE_SEARCH_API_KEY và GOOGLE_CSE_ID vào file .env"
        
        logger.info(f"[GOOGLE SEARCH] Query: {query}")
        
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Create session with retry strategy
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # Try with first API key
        params = {
            'key': GOOGLE_SEARCH_API_KEY_1,
            'cx': GOOGLE_CSE_ID,
            'q': query,
            'num': 5
        }
        
        response = session.get(url, params=params, timeout=30)
        
        logger.info(f"[GOOGLE SEARCH] Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            if 'items' in data:
                for item in data['items'][:5]:
                    title = item.get('title', 'No title')
                    link = item.get('link', '')
                    snippet = item.get('snippet', 'No description')
                    results.append(f"**{title}**\n{snippet}\n🔗 {link}")
                
                return "🔍 **Kết quả tìm kiếm:**\n\n" + "\n\n---\n\n".join(results)
            else:
                return "Không tìm thấy kết quả nào."
                
        elif response.status_code == 429:
            # Quota exceeded, try second key
            if GOOGLE_SEARCH_API_KEY_2:
                params['key'] = GOOGLE_SEARCH_API_KEY_2
                response = session.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    if 'items' in data:
                        for item in data['items'][:5]:
                            title = item.get('title', 'No title')
                            link = item.get('link', '')
                            snippet = item.get('snippet', 'No description')
                            results.append(f"**{title}**\n{snippet}\n🔗 {link}")
                        return "🔍 **Kết quả tìm kiếm:**\n\n" + "\n\n---\n\n".join(results)
            return "❌ Đã hết quota Google Search API. Vui lòng thử lại sau."
        else:
            return f"❌ Lỗi Google Search API: {response.status_code}"
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[GOOGLE SEARCH] Connection Error: {e}")
        return "❌ Lỗi kết nối đến Google Search API"
    except requests.exceptions.Timeout as e:
        logger.error(f"[GOOGLE SEARCH] Timeout Error: {e}")
        return "❌ Timeout khi kết nối đến Google Search API"
    except Exception as e:
        logger.error(f"[GOOGLE SEARCH] Unexpected Error: {e}")
        return f"❌ Lỗi: {str(e)}"


def github_search_tool(query):
    """GitHub Repository Search"""
    try:
        if not GITHUB_TOKEN:
            return "❌ GitHub Token chưa được cấu hình. Vui lòng thêm GITHUB_TOKEN vào file .env"
        
        url = "https://api.github.com/search/repositories"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': 5
        }
        
        cleaned_query = query.replace('\n', ' ').replace('\r', '')
        logger.info(f"[GITHUB SEARCH] Query: {cleaned_query}")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            if 'items' in data and len(data['items']) > 0:
                for repo in data['items']:
                    name = repo.get('full_name', 'Unknown')
                    desc = repo.get('description', 'No description')
                    stars = repo.get('stargazers_count', 0)
                    html_url = repo.get('html_url', '')
                    language = repo.get('language', 'N/A')
                    
                    results.append(f"**{name}** ⭐ {stars}\n{desc}\n💻 {language} | 🔗 {html_url}")
                
                return "🐙 **GitHub Repositories:**\n\n" + "\n\n---\n\n".join(results)
            else:
                return "Không tìm thấy repository nào."
        else:
            return f"❌ Lỗi GitHub API: {response.status_code}"
    
    except Exception as e:
        logger.error(f"[GITHUB SEARCH] Error: {e}")
        return f"❌ Lỗi: {str(e)}"
