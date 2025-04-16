# modules/scraper.py
import requests
import time
import json
from urllib.parse import urljoin
import random
import string

class Scraper:
    def __init__(self, token, base_url=None, headers=None, proxies=None, stealth_mode=True, min_delay=1.0, max_delay=3.0):
        self.token = token
        self.base_url = base_url
        self.stealth_mode = stealth_mode
        
        # Default headers with authorization and disguised user agent
        if stealth_mode:
            # Use a common, innocuous user agent
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        else:
            user_agent = "Mozilla/5.0 (compatible; DataSync/1.0)"
        
        self.headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": user_agent,
            "Accept": "application/json"
        }
        
        # Add additional headers if provided
        if headers:
            self.headers.update(headers)
        
        self.proxies = proxies
        self.session = requests.Session()
        
        # Set random request delays to avoid detection
        self.min_delay = min_delay
        self.max_delay = max_delay
        
        # Track successful endpoints for reuse
        self.successful_endpoints = set()
    
    def _make_request(self, endpoint, method="GET", params=None, data=None, json_data=None):
        """Make HTTP request with stealth considerations"""
        url = endpoint if endpoint.startswith("http") else urljoin(self.base_url, endpoint)
        
        # Add jitter to avoid detection of automated requests
        if self.stealth_mode:
            time.sleep(random.uniform(self.min_delay, self.max_delay))
            
            # Occasionally add referrer from common sites
            if random.random() < 0.3:
                common_referrers = [
                    "https://www.google.com/",
                    "https://www.bing.com/",
                    "https://www.office.com/",
                    "https://outlook.office365.com/"
                ]
                self.headers["Referer"] = random.choice(common_referrers)
            else:
                if "Referer" in self.headers:
                    del self.headers["Referer"]
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    data=data,
                    json=json_data,
                    proxies=self.proxies,
                    timeout=10,
                    verify=True  # Always verify TLS certs in stealth mode
                )
                
                # Track successful endpoints
                if response.ok:
                    self.successful_endpoints.add(endpoint)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    time.sleep(retry_after + random.uniform(1, 3))  # Add jitter
                    continue
                
                response.raise_for_status()
                return response
            
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
                else:
                    raise
    
    def extract_cases(self, endpoints=None):
        """Extract cases from multiple endpoints"""
        if not endpoints:
            # First try previously successful endpoints
            if self.successful_endpoints:
                endpoints = list(self.successful_endpoints)
            elif self.base_url:
                # Default endpoints based on base_url
                endpoints = [
                    urljoin(self.base_url, "/api/cases"),
                    urljoin(self.base_url, "/api/v1/cases"),
                    urljoin(self.base_url, "/api/v2/cases")
                ]
            else:
                raise ValueError("No endpoints available")
        
        all_data = []
        
        for endpoint in endpoints:
            if "cases" not in endpoint:
                continue
            
            try:
                response = self._make_request(endpoint)
                
                if response.ok:
                    data = response.json()
                    
                    # Handle different response structures
                    if isinstance(data, list):
                        cases = data
                    elif isinstance(data, dict):
                        cases = data.get("cases", [])
                        if not cases:
                            cases = data.get("data", [])
                        if not cases:
                            cases = data.get("results", [])
                    else:
                        cases = []
                    
                    # Add source endpoint to each case
                    for case in cases:
                        case["_source"] = endpoint
                    
                    all_data.extend(cases)
            except Exception:
                # Silent failure in stealth mode
                pass
        
        return all_data
    
    def extract_pagination(self, endpoint, page_param="page", limit_param="limit", limit=100):
        """Extract data from paginated endpoint with stealth considerations"""
        all_data = []
        page = 1
        has_more = True
        
        while has_more:
            try:
                params = {
                    page_param: page,
                    limit_param: limit
                }
                
                response = self._make_request(endpoint, params=params)
                
                if response.ok:
                    data = response.json()
                    
                    # Handle different pagination formats
                    if isinstance(data, dict):
                        items = data.get("cases", [])
                        if not items:
                            items = data.get("data", [])
                        if not items:
                            items = data.get("results", [])
                            
                        # Check for pagination info
                        has_more = False
                        if "next_page" in data:
                            has_more = data["next_page"] is not None
                        elif "has_more" in data:
                            has_more = data["has_more"]
                        elif "next" in data:
                            has_more = data["next"] is not None
                        elif len(items) == limit:
                            # Assume there might be more if we got a full page
                            has_more = True
                    else:
                        items = data
                        has_more = len(items) == limit
                    
                    if not items:
                        has_more = False
                    
                    # Add metadata to each item
                    for item in items:
                        item["_source"] = endpoint
                        item["_page"] = page
                    
                    all_data.extend(items)
                    
                    # Move to next page
                    page += 1
                    
                    # Add longer delay between pages for stealth
                    if self.stealth_mode and has_more:
                        time.sleep(random.uniform(2.0, 5.0))
                else:
                    has_more = False
            
            except Exception:
                # Silent failure in stealth mode
                has_more = False
        
        return all_data

def extract_cases(token, base_url, endpoints, stealth_mode=True):
    scraper = Scraper(token, base_url, stealth_mode=stealth_mode)
    return scraper.extract_cases(endpoints)