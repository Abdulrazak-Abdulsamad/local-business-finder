"""
API module for Local Business Finder
Handles external API calls and business data retrieval
Includes Google Places API integration, caching, rate limiting, and logging
"""

import json
import os
import random
import time
import logging
import hashlib
from math import radians, sin, cos, sqrt, atan2
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from functools import wraps

import config
from models import Business


# ============================================
# LOGGING CONFIGURATION
# ============================================

def setup_logging():
    """Configure application logging."""
    # Create logs directory if it doesn't exist
    log_dir = config.BASE_DIR / "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE_PATH),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ============================================
# RATE LIMITING WITH EXPONENTIAL BACKOFF
# ============================================

class RateLimiter:
    """Rate limiter with exponential backoff for API calls."""
    
    def __init__(self, max_retries: int = None, base_delay: float = None):
        self.max_retries = max_retries or config.API_MAX_RETRIES
        self.base_delay = base_delay or config.API_RETRY_DELAY
        self._retry_count = {}
        self._last_request_time = {}
    
    def should_retry(self, endpoint: str) -> bool:
        """Check if request should be retried."""
        count = self._retry_count.get(endpoint, 0)
        return count < self.max_retries
    
    def get_delay(self, endpoint: str) -> float:
        """Calculate exponential backoff delay."""
        count = self._retry_count.get(endpoint, 0)
        return self.base_delay * (2 ** count)
    
    def record_attempt(self, endpoint: str):
        """Record an API attempt."""
        self._retry_count[endpoint] = self._retry_count.get(endpoint, 0) + 1
        self._last_request_time[endpoint] = time.time()
    
    def record_success(self, endpoint: str):
        """Reset retry count after successful request."""
        self._retry_count[endpoint] = 0
    
    def wait_if_needed(self, endpoint: str):
        """Wait if rate limited."""
        if endpoint in self._last_request_time:
            delay = self.get_delay(endpoint)
            time.sleep(delay)


# Global rate limiter instance
rate_limiter = RateLimiter()


def with_rate_limit_and_retry(func):
    """Decorator for rate limiting and retry logic."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        endpoint = func.__name__
        
        # Check if API is configured
        if not config.is_api_configured():
            logger.warning(f"API not configured, falling back to mock data")
            return func(*args, **kwargs)
        
        # Retry loop
        while rate_limiter.should_retry(endpoint):
            try:
                rate_limiter.wait_if_needed(endpoint)
                rate_limiter.record_attempt(endpoint)
                
                result = func(*args, **kwargs)
                rate_limiter.record_success(endpoint)
                return result
                
            except APIError as e:
                logger.error(f"API error in {endpoint}: {str(e)}")
                
                # Check if error is retriable (handles both method and boolean attribute)
                is_retry = False
                if callable(getattr(e, 'is_retriable', None)):
                    is_retry = e.is_retriable()
                elif hasattr(e, 'is_retriable'):
                    is_retry = bool(e.is_retriable)
                
                if is_retry and rate_limiter.should_retry(endpoint):
                    delay = rate_limiter.get_delay(endpoint)
                    logger.info(f"Retrying {endpoint} after {delay}s (attempt {rate_limiter._retry_count.get(endpoint, 1)})")
                    time.sleep(delay)
                    continue
                raise
                
        # Fallback to mock data after max retries
        logger.warning(f"Max retries exceeded for {endpoint}, falling back to mock data")
        return func(*args, **kwargs)
    
    return wrapper


# ============================================
# IN-MEMORY CACHING LAYER
# ============================================

class APICache:
    """In-memory cache for API responses."""
    
    def __init__(self, ttl: int = None, max_size: int = None):
        self.ttl = ttl or config.CACHE_TTL
        self.max_size = max_size or config.CACHE_MAX_SIZE
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = f"{prefix}:{str(args)}:{str(kwargs)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        age = (datetime.now() - timestamp).total_seconds()
        
        if age > self.ttl:
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit: {key[:8]}...")
        return value
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        # Clear old entries if at capacity
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), 
                          key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
            logger.debug(f"Cache full, evicted oldest entry")
        
        self._cache[key] = (value, datetime.now())
        logger.debug(f"Cache set: {key[:8]}...")
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")


# Global cache instance
api_cache = APICache()


def cached(prefix: str, TTL: int = None):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not config.CACHE_ENABLED:
                return func(*args, **kwargs)
            
            cache_key = f"{prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            cached_value = api_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            api_cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator


# ============================================
# CUSTOM EXCEPTIONS
# ============================================

class APIError(Exception):
    """Base exception for API errors."""
    
    def __init__(self, message: str, status_code: int = None, 
                 is_retriable: bool = False):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.is_retriable = is_retriable
    
    def is_retriable(self) -> bool:
        return self.is_retriable


class QuotaExceededError(APIError):
    """Raised when API quota is exceeded."""
    
    def __init__(self, message: str = "API quota exceeded"):
        super().__init__(message, status_code=429, is_retriable=True)


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429, is_retriable=True)


class NetworkError(APIError):
    """Raised when network error occurs."""
    
    def __init__(self, message: str = "Network error"):
        super().__init__(message, is_retriable=True)


class GeocodingError(APIError):
    """Raised when geocoding fails."""
    
    def __init__(self, message: str = "Geocoding failed"):
        super().__init__(message, is_retriable=False)


# ============================================
# GOOGlE PLACES API CLIENT
# ============================================

# ============================================
# FOURSQUARE PLACES API CLIENT
# ============================================

class FoursquarePlacesClient:
    """Client for Foursquare Places API v3.
    
    Foursquare API Documentation: https://location.foursquare.com/developer-guide/places-api/
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.FOURSQUARE_API_KEY
        self.base_url = config.FOURSQUARE_PLACES_API_BASE_URL
        self.api_version = config.FOURSQUARE_API_VERSION
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP request to Foursquare API."""
        import requests
        
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "apiversion": self.api_version,
        }
        
        if config.LOG_API_REQUESTS:
            logger.info(f"Foursquare API Request: {endpoint} - params: {list((params or {}).keys())}")
        
        try:
            response = requests.get(
                url,
                params=params or {},
                headers=headers,
                timeout=config.API_TIMEOUT
            )
            
            if config.LOG_API_REQUESTS:
                logger.info(f"Foursquare API Response: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            # Check for Foursquare API errors
            if "error" in data:
                self._handle_api_error(data.get("error", {}))
            
            return data
            
        except requests.exceptions.Timeout:
            raise NetworkError("Foursquare request timeout")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Foursquare connection error")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise QuotaExceededError("Foursquare API quota exceeded")
            elif e.response.status_code == 401:
                raise APIError("Foursquare API authentication failed. Check API key.", 
                            status_code=401, is_retriable=False)
            raise NetworkError(str(e))
    
    def _handle_api_error(self, error: Dict):
        """Handle Foursquare API error responses."""
        error_type = error.get("errorType", "")
        error_detail = error.get("message", "Unknown error")
        
        if error_type == "RATE_LIMIT_EXCEEDED":
            raise RateLimitError(error_detail)
        elif error_type == "QUOTA_EXCEEDED":
            raise QuotaExceededError(error_detail)
        else:
            raise APIError(f"Foursquare API error: {error_detail}", is_retriable=True)
    
    @with_rate_limit_and_retry
    def search(self, query: str = None, lat: float = None, lng: float = None,
               radius: int = None, category: str = None, limit: int = 20) -> List[Business]:
        """
        Search for businesses using Foursquare Places API.
        
        Args:
            query: Search query (e.g., "restaurant", "cafe")
            lat: Latitude
            lng: Longitude
            radius: Search radius in meters
            category: Foursquare category ID
            limit: Maximum results (max 50)
        
        Returns:
            List of Business objects
        """
        # Build query parameters
        params = {
            "ll": f"{lat},{lng}" if lat and lng else None,
            "query": query,
            "radius": radius,
            "categories": category,
            "limit": min(limit, 50),  # Foursquare max is 50
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        # Foursquare v3 uses /search endpoint under /places
        data = self._make_request("search", params)
        
        results = []
        for place in data.get("results", []):
            business = self._parse_foursquare_result(place)
            results.append(business)
        
        if config.LOG_API_REQUESTS:
            logger.info(f"Foursquare search returned {len(results)} results")
        
        return results
    
    @with_rate_limit_and_retry
    def get_place_details(self, fsq_id: str) -> Optional[Business]:
        """
        Get detailed information about a Foursquare place.
        
        Args:
            fsq_id: Foursquare place ID
        
        Returns:
            Business object or None
        """
        # Foursquare v3 uses different endpoint for details
        # Using the search endpoint with query for now as v3 changed approach
        data = self._make_request(f"{fsq_id}", {"fields": "name,location,categories,rating,price,hours,telephone,photos"})
        
        if not data:
            return None
        
        return self._parse_foursquare_result(data)
    
    def _parse_foursquare_result(self, place: Dict) -> Business:
        """Parse Foursquare API result to Business object."""
        
        # Extract location
        location = place.get("location", {})
        lat = location.get("lat", 0.0)
        lng = location.get("long", 0.0)
        
        # Extract address
        address_parts = []
        if location.get("address"):
            address_parts.append(location["address"])
        if location.get("crosstreet"):
            address_parts.append(location["crosstreet"])
        if location.get("locality"):
            address_parts.append(location["locality"])
        address = ", ".join(address_parts) if address_parts else location.get("formatted_address", "")
        
        # Extract category
        categories = place.get("categories", [])
        category = "Other"
        if categories:
            # Map Foursquare categories to our categories
            category_mapping = {
                13032: "Restaurant",
                13032: "Restaurant",
                13035: "Cafe",
                13036: "Bar",
                13037: "Bar",
                13065: "Hotel",
                17000: "Hospital",
                17014: "Pharmacy",
                17021: "Supermarket",
                17000: "Shopping Mall",
                17002: "Bank",
                17003: "ATM",
                17005: "Gas Station",
                16000: "Park",
                16028: "Gym",
                15000: "Salon",
                15010: "Laundry",
                17009: "Electronics",
                17010: "Furniture",
                17011: "Clothing",
                17120: "Books",
                17127: "Jewelry",
            }
            for cat in categories:
                cat_id = cat.get("id")
                if cat_id in category_mapping:
                    category = category_mapping[cat_id]
                    break
            # Use first category name as fallback
            if category == "Other" and categories:
                category = categories[0].get("name", "Other")
        
        # Map price level
        price_tier = place.get("price", 1)
        price_symbols = ["", "₦", "₦₦", "₦₦₦", "₦₦₦₦"]
        price_level_str = price_symbols[price_tier] if 1 <= price_tier <= 4 else "₦₦"
        
        # Extract hours
        hours = place.get("hours", {})
        is_open = True
        if hours.get("regular"):
            is_open = hours["regular"].get("is_local_lapsed", False)
        
        # Get rating and review count
        rating = place.get("rating", 0.0) / 2 if place.get("rating") else 0.0  # Foursquare uses 0-10, convert to 0-5
        
        # Get phone
        telephone = place.get("telephone", "") or location.get("phone", "")
        
        # Get place ID
        fsq_id = place.get("fsq_id", "") or place.get("place_id", "")
        
        business = Business(
            id=fsq_id,
            name=place.get("name", ""),
            category=category,
            address=address,
            city=location.get("locality", "Abuja"),
            state=location.get("region", "FCT"),
            zip_code=location.get("postcode", "900001"),
            phone=telephone,
            rating=rating,
            review_count=place.get("rating", 0) or 0,  # Foursquare uses rating score
            price_level=price_level_str,
            latitude=lat,
            longitude=lng,
            description=place.get("description", ""),
            is_open=is_open,
            distance=0.0
        )
        
        return business


# Global Foursquare client
foursquare_client = None


def get_foursquare_client() -> FoursquarePlacesClient:
    """Get or create Foursquare Places client."""
    global foursquare_client
    if foursquare_client is None:
        foursquare_client = FoursquarePlacesClient()
    return foursquare_client


# ============================================


class GooglePlacesClient:
    """Client for Google Places API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.GOOGLE_API_KEY
        self.base_url = config.GOOGLE_PLACES_API_BASE_URL
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make HTTP request to Google API."""
        import requests
        
        params["key"] = self.api_key
        url = f"{self.base_url}/{endpoint}/json"
        
        if config.LOG_API_REQUESTS:
            logger.info(f"API Request: {endpoint} - params: {list(params.keys())}")
        
        try:
            response = requests.get(
                url, 
                params=params,
                timeout=config.API_TIMEOUT
            )
            
            if config.LOG_API_REQUESTS:
                logger.info(f"API Response: {response.status_code}")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API-level errors
            if data.get("status") != "OK":
                self._handle_api_error(data.get("status"), data.get("error_message"))
            
            return data
            
        except requests.exceptions.Timeout:
            raise NetworkError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection error")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise QuotaExceededError()
            raise NetworkError(str(e))
    
    def _handle_api_error(self, status: str, error_message: str = None):
        """Handle API error responses."""
        error_msg = error_message or f"API error: {status}"
        
        if status == "OVER_QUERY_LIMIT":
            raise QuotaExceededError(error_msg)
        elif status == "REQUEST_DENIED":
            # Check if it's a billing error
            if "billing" in (error_message or "").lower():
                raise APIError(
                    "Google API billing not enabled. Please enable billing in Google Cloud Console. "
                    "Falling back to mock data.",
                    status_code=403,
                    is_retriable=False
                )
            raise APIError(error_msg, status_code=403, is_retriable=False)
        elif status == "INVALID_REQUEST":
            raise APIError(error_msg, status_code=400, is_retriable=False)
        else:
            raise APIError(error_msg, status_code=500, is_retriable=True)
    
    @with_rate_limit_and_retry
    def text_search(self, query: str, location: str = None, 
                   radius: int = None, category: str = None) -> List[Business]:
        """
        Search for businesses using text query.
        
        Args:
            query: Search query
            location: Location in format "lat,lng"
            radius: Search radius in meters
            category: Business category (optional, uses types if provided)
        
        Returns:
            List of Business objects
        """
        params = {
            "query": query,
            "language": "en-NG",
        }
        
        if location:
            params["location"] = location
        if radius:
            params["radius"] = radius
        if category:
            params["type"] = category.lower()
        
        data = self._make_request("textsearch", params)
        
        results = []
        for place in data.get("results", []):
            business = self._parse_place_result(place)
            results.append(business)
        
        if config.LOG_API_REQUESTS:
            logger.info(f"Text search returned {len(results)} results")
        
        return results
    
    @with_rate_limit_and_retry
    def nearby_search(self, location: str, radius: int = None,
                      category: str = None) -> List[Business]:
        """
        Search for nearby businesses.
        
        Args:
            location: Location in format "lat,lng"
            radius: Search radius in meters
            category: Business category
        
        Returns:
            List of Business objects
        """
        params = {
            "location": location,
            "language": "en-NG",
        }
        
        if radius:
            params["radius"] = radius
        if category:
            params["type"] = category.lower()
        
        data = self._make_request("nearbysearch", params)
        
        results = []
        for place in data.get("results", []):
            business = self._parse_place_result(place)
            results.append(business)
        
        if config.LOG_API_REQUESTS:
            logger.info(f"Nearby search returned {len(results)} results")
        
        return results
    
    @with_rate_limit_and_retry
    def get_place_details(self, place_id: str) -> Optional[Business]:
        """
        Get detailed information about a place.
        
        Args:
            place_id: Google Places ID
        
        Returns:
            Business object or None
        """
        params = {
            "place_id": place_id,
            "fields": "place_id,name,formatted_address,geometry,types,"
                     "formatted_phone_number,rating,user_ratings_total,"
                     "price_level,opening_hours,editorial_summary",
            "language": "en-NG",
        }
        
        data = self._make_request("details", params)
        
        place = data.get("result")
        if not place:
            return None
        
        return self._parse_place_result(place)
    
    def _parse_place_result(self, place: Dict) -> Business:
        """Parse Google Places API result to Business object."""
        # Extract location
        lat = place.get("geometry", {}).get("location", {}).get("lat", 0.0)
        lng = place.get("geometry", {}).get("location", {}).get("lng", 0.0)
        
        # Extract category from types
        types = place.get("types", [])
        category = "Other"
        if types:
            # Map Google types to our categories
            type_mapping = {
                "restaurant": "Restaurant",
                "cafe": "Cafe",
                "bar": "Restaurant",
                "food": "Restaurant",
                " lodging": "Hotel",
                "hospital": "Hospital",
                "pharmacy": "Pharmacy",
                "supermarket": "Supermarket",
                "shopping_mall": "Shopping Mall",
                "bank": "Bank",
                "atm": "ATM",
                "gas_station": "Gas Station",
                "park": "Park",
                "gym": "Gym",
                "hair_care": "Salon",
                "laundry": "Laundry",
                "electronics_store": "Electronics",
                "furniture_store": "Furniture",
                "clothing_store": "Clothing",
                "book_store": "Books",
                "jewelry_store": "Jewelry",
            }
            for t in types:
                if t in type_mapping:
                    category = type_mapping[t]
                    break
        
        # Map price level
        price_level = place.get("price_level", -1)
        price_symbols = ["", "₦", "₦₦", "₦₦₦", "₦₦₦₦"]
        price_level_str = price_symbols[price_level] if 0 <= price_level <= 4 else "₦₦"
        
        # Get address components
        address = place.get("formatted_address", "")
        
        # Extract city and state
        city = "Abuja"
        state = "FCT"
        address_components = address.split(", ")
        if len(address_components) > 1:
            city = address_components[-2] if address_components[-2] else city
        if address_components:
            state = address_components[-1] if address_components[-1] else state
        
        # Check if open now
        hours = place.get("opening_hours", {})
        is_open = hours.get("open_now", True)
        
        business = Business(
            id=place.get("place_id", ""),
            name=place.get("name", ""),
            category=category,
            address=address,
            city=city,
            state=state,
            zip_code="900001",
            phone=place.get("formatted_phone_number", ""),
            rating=place.get("rating", 0.0),
            review_count=place.get("user_ratings_total", 0),
            price_level=price_level_str,
            latitude=lat,
            longitude=lng,
            description=place.get("editorial_summary", {}).get("overview", ""),
            is_open=is_open,
            distance=0.0
        )
        
        return business


# Global Google Places client
google_places_client = None


def get_google_places_client() -> GooglePlacesClient:
    """Get or create Google Places client."""
    global google_places_client
    if google_places_client is None:
        google_places_client = GooglePlacesClient()
    return google_places_client


# ============================================
# GOOGLE GEOCODING API CLIENT
# ============================================

class GoogleGeocodingClient:
    """Client for Google Geocoding API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.get_api_key()
        self.base_url = config.GOOGLE_GEOCODING_API_BASE_URL
    
    def _make_request(self, params: Dict) -> Dict:
        """Make HTTP request to Geocoding API."""
        import requests
        
        params["key"] = self.api_key
        url = f"{self.base_url}/json"
        
        if config.LOG_API_REQUESTS:
            logger.info(f"Geocoding Request: {list(params.keys())}")
        
        try:
            response = requests.get(
                url,
                params=params,
                timeout=config.GOOGLE_API_TIMEOUT
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                self._handle_api_error(data.get("status"), data.get("error_message"))
            
            return data
            
        except requests.exceptions.Timeout:
            raise NetworkError("Geocoding timeout")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Geocoding connection error")
        except requests.HTTPError as e:
            raise NetworkError(str(e))
    
    def _handle_api_error(self, status: str, error_message: str = None):
        """Handle API error responses."""
        error_msg = error_message or f"Geocoding error: {status}"
        
        if status == "OVER_QUERY_LIMIT":
            raise QuotaExceededError(error_msg)
        elif status == "ZERO_RESULTS":
            raise GeocodingError("No results found for address")
        else:
            raise GeocodingError(error_msg)
    
    @with_rate_limit_and_retry
    @cached("geocode", TTL=86400)  # Cache geocoding for 24 hours
    def geocode(self, address: str) -> Optional[Dict[str, float]]:
        """
        Convert address to coordinates.
        
        Args:
            address: Street address
        
        Returns:
            Dict with 'lat' and 'lng' keys, or None if not found
        """
        params = {
            "address": address,
            "language": "en",
            "region": "ng",  # Nigeria
        }
        
        try:
            data = self._make_request(params)
            
            result = data.get("results", [])
            if not result:
                return None
            
            # Get first result
            location = result[0].get("geometry", {}).get("location", {})
            
            return {
                "lat": location.get("lat", 0.0),
                "lng": location.get("lng", 0.0),
            }
            
        except APIError as e:
            logger.error(f"Geocoding failed for '{address}': {str(e)}")
            return None
    
    @with_rate_limit_and_retry
    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Convert coordinates to address.
        
        Args:
            lat: Latitude
            lng: Longitude
        
        Returns:
            Address string or None
        """
        params = {
            "latlng": f"{lat},{lng}",
            "language": "en",
        }
        
        try:
            data = self._make_request(params)
            
            result = data.get("results", [])
            if not result:
                return None
            
            return result[0].get("formatted_address", "")
            
        except APIError as e:
            logger.error(f"Reverse geocoding failed: {str(e)}")
            return None


# Global Geocoding client
geocoding_client = None


def get_geocoding_client() -> GoogleGeocodingClient:
    """Get or create Geocoding client."""
    global geocoding_client
    if geocoding_client is None:
        geocoding_client = GoogleGeocodingClient()
    return geocoding_client


def geocode_address(address: str) -> Optional[Dict[str, float]]:
    """Convert address to coordinates."""
    client = get_geocoding_client()
    return client.geocode(address)


def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """Convert coordinates to address."""
    client = get_geocoding_client()
    return client.reverse_geocode(lat, lng)


# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula."""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


# ============================================
# MOCK BUSINESS DATA
# ============================================

ABUJA_BUSINESSES = [
    {
        "name": "Mama's Kitchen",
        "category": "Restaurant",
        "address": "27 Aminu Crescent, Wuse 2",
        "city": "Abuja",
        "state": "FCT",
        "phone": "+234 803 123 4567",
        "rating": 4.5,
        "review_count": 128,
        "price_level": "₦₦",
        "latitude": 9.0734,
        "longitude": 7.4741,
        "description": "Traditional Nigerian cuisine in a cozy atmosphere."
    },
    {
        "name": "Capital Grill",
        "category": "Restaurant",
        "address": "45 Adetokunbo Ademola, Maitama",
        "city": "Abuja",
        "state": "FCT",
        "phone": "+234 803 234 5678",
        "rating": 4.8,
        "review_count": 256,
        "price_level": "₦₦₦",
        "latitude": 9.1156,
        "longitude": 7.4824,
        "description": "Premium steakhouse with Abuja's best steaks."
    },
    {
        "name": "Jabi Lake Mall",
        "category": "Shopping Mall",
        "address": "Jabi Road, Jabi",
        "city": "Abuja",
        "state": "FCT",
        "phone": "+234 809 345 6789",
        "rating": 4.2,
        "review_count": 312,
        "price_level": "₦₦",
        "latitude": 9.0549,
        "longitude": 7.4390,
        "description": "Modern shopping mall with cinema and restaurants."
    },
    {
        "name": "Centenary Supermarket",
        "category": "Supermarket",
        "address": "140 Ahmadu Bello Way, Garki",
        "city": "Abuja",
        "state": "FCT",
        "phone": "+234 803 456 7890",
        "rating": 4.0,
        "review_count": 89,
        "price_level": "₦₦",
        "latitude": 9.0898,
        "longitude": 7.5129,
        "description": "Quality groceries and household items."
    },
    {
        "name": "MediCare Pharmacy",
        "category": "Pharmacy",
        "address": "22 Banana Island, Gwarinpa",
        "city": "Abuja",
        "state": "FCT",
        "phone": "+234 803 567 8901",
        "rating": 4.6,
        "review_count": 167,
        "price_level": "₦₦",
        "latitude": 9.1068,
        "longitude": 7.4474,
        "description": "24-hour pharmacy with delivery service."
    },
    {
        "name": "Abuja National Mosque",
        "category": "Park",
        "address": "Maitama Expressway, Maitama",
        "city": "Abuja",
        "state": "FCT",
        "phone": "+234 803 678 9012",
        "rating": 4.9,
        "review_count": 512,
        "price_level": "₦",
        "latitude": 9.1156,
        "longitude": 7.4824,
        "description": "Iconic religious and cultural landmark."
    },
    {
        "name": "Zenith Fitness Club",
        "category": "Gym",
        "address": "3 River Road, Gwarinpa",
        "city": "Abuja",
        "state": "FCT",
        "phone": "+234 803 789 0123",
        "rating": 4.3,
        "review_count": 98,
        "price_level": "₦₦₦",
        "latitude": 9.1068,
        "longitude": 7.4474,
        "description": "Full-service gym with personal trainers."
    },
    {
        "name": "Golden Tulip Hotel",
        "category": "Hotel",
        "address": "1 Aziz Abdulfattah, Asokoro",
        "city": "Abuja",
        "state": "FCT",
        "phone": "+234 803 890 1234",
        "rating": 4.7,
        "review_count": 342,
        "price_level": "₦₦₦₦",
        "latitude": 9.0898,
        "longitude": 7.5129,
        "description": "Luxury hotel in the diplomatic district."
    },
    {
        "name": "First Bank of Nigeria",
        "category": "Bank",
        "address": "82 Ahmadu Bello Avenue, Central Business District",
        "city": "Abuja",
        "state": "FCT",
        "phone": "+234 803 901 2345",
        "rating": 3.8,
        "review_count": 234,
        "price_level": "₦",
        "latitude": 9.0765,
        "longitude": 7.3986,
        "description": "Major commercial bank branch."
    },
    {
        "name": "Eco Cafe",
        "category": "Cafe",
        "address": "15 Libre Avenue, Wuse 2",
        "city": "Abuja",
        "state": "FCT",
        "phone": "+234 803 012 3456",
        "rating": 4.4,
        "review_count": 156,
        "price_level": "₦₦",
        "latitude": 9.0734,
        "longitude": 7.4741,
        "description": "Cozy cafe with specialty coffee."
    },
]


# ============================================
# BUSINESS DATA FUNCTIONS
# ============================================

def load_businesses() -> List[Business]:
    """Load businesses from the JSON file, generating mock data if needed."""
    if not os.path.exists(config.BUSINESSES_FILE):
        generate_mock_businesses()
    
    try:
        with open(config.BUSINESSES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            businesses_list = data.get("businesses", [])
            if not businesses_list:
                generate_mock_businesses()
                with open(config.BUSINESSES_FILE, 'r', encoding='utf-8') as f2:
                    data = json.load(f2)
                    businesses_list = data.get("businesses", [])
            return [Business(**item) for item in businesses_list]
    except Exception as e:
        logger.error(f"Error loading businesses: {e}")
        generate_mock_businesses()
        with open(config.BUSINESSES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [Business(**item) for item in data.get("businesses", [])]


def generate_mock_businesses() -> None:
    """Generate mock business data for the application."""
    businesses = []
    
    for idx, biz_data in enumerate(ABUJA_BUSINESSES):
        unique_string = f"{biz_data['name']}_{biz_data['address']}_{idx}"
        place_id = f"place_{abs(hash(unique_string)) % 1000000000}"
        
        business = {
            "id": place_id,
            "name": biz_data["name"],
            "category": biz_data["category"],
            "address": biz_data["address"],
            "city": biz_data.get("city", "Abuja"),
            "state": biz_data.get("state", "FCT"),
            "zip_code": biz_data.get("zip_code", "900001"),
            "phone": biz_data.get("phone", ""),
            "rating": biz_data["rating"],
            "review_count": biz_data["review_count"],
            "price_level": biz_data["price_level"],
            "latitude": biz_data["latitude"],
            "longitude": biz_data["longitude"],
            "description": biz_data.get("description", ""),
            "is_open": True
        }
        businesses.append(business)
    
    data = {
        "businesses": businesses,
        "last_updated": str(time.time())
    }
    
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.BUSINESSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Generated {len(businesses)} mock businesses")


def search_businesses(
    query: str, 
    category: str = "All", 
    min_rating: float = 0.0, 
    max_distance: float = 50.0,
    limit: int = 20,
    lat: Optional[float] = None,
    lng: Optional[float] = None
) -> List[Business]:
    """
    Search for businesses near a given location.
    
    Args:
        query: Search query string
        category: Business category filter
        min_rating: Minimum rating filter
        max_distance: Maximum distance in km
        limit: Maximum results to return
        lat: Latitude of search center
        lng: Longitude of search center
    
    Returns:
        List of Business objects sorted by distance
    """
    # Use default location if not provided
    if lat is None:
        lat = config.DEFAULT_LATITUDE
    if lng is None:
        lng = config.DEFAULT_LONGITUDE
    
    # Try Foursquare API first (primary), then Google (fallback), then mock data
    # Check which API is configured and try in order
    
    # Try Foursquare API if configured
    if config.FOURSQUARE_API_KEY and config.USE_FOURSQUARE_API:
        try:
            client = get_foursquare_client()
            
            # Foursquare uses lat,lng directly
            radius_meters = int(max_distance * 1000)
            
            results = client.search(
                query=query if query else None,
                lat=lat,
                lng=lng,
                radius=radius_meters,
                category=category if category != "All" else None,
                limit=limit
            )
            
            # Foursquare already returns distance-sorted results
            # Filter by additional criteria
            filtered_results = []
            for business in results:
                try:
                    # Recalculate distance for verification
                    distance = calculate_distance(lat, lng, business.latitude, business.longitude)
                    business.distance = round(distance, 1)
                    
                    if distance <= max_distance:
                        if business.rating >= min_rating:
                            filtered_results.append(business)
                except Exception as e:
                    logger.error(f"Error calculating distance: {e}")
            
            filtered_results.sort(key=lambda b: b.distance)
            logger.info(f"Foursquare API search returned {len(filtered_results)} results")
            return filtered_results[:limit]
            
        except APIError as e:
            logger.warning(f"Foursquare API error, trying Google: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Foursquare search: {str(e)}")
    
    # Try Google API if configured (fallback)
    if config.GOOGLE_API_KEY and config.USE_GOOGLE_API:
        try:
            client = get_google_places_client()
            location_str = f"{lat},{lng}"
            
            if query:
                results = client.text_search(
                    query=query,
                    location=location_str,
                    radius=int(max_distance * 1000),
                    category=category if category != "All" else None
                )
            else:
                results = client.nearby_search(
                    location=location_str,
                    radius=int(max_distance * 1000),
                    category=category if category != "All" else None
                )
            
            # Filter and sort by distance
            filtered_results = []
            for business in results:
                try:
                    distance = calculate_distance(lat, lng, business.latitude, business.longitude)
                    business.distance = round(distance, 1)
                    
                    if distance <= max_distance:
                        if business.rating >= min_rating:
                            filtered_results.append(business)
                except Exception as e:
                    logger.error(f"Error calculating distance: {e}")
            
            filtered_results.sort(key=lambda b: b.distance)
            logger.info(f"Google API search returned {len(filtered_results)} results")
            return filtered_results[:limit]
            
        except APIError as e:
            logger.warning(f"Google API error, falling back to local data: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in API search: {str(e)}")
    
    # Fallback to local/mock data
    businesses = load_businesses()
    
    # Filter by category
    if category and category != "All":
        businesses = [b for b in businesses if b.category == category]
    
    # Filter by rating
    if min_rating > 0:
        businesses = [b for b in businesses if b.rating >= min_rating]
    
    # Calculate distance for each business
    results = []
    for business in businesses:
        try:
            distance = calculate_distance(lat, lng, business.latitude, business.longitude)
            business.distance = round(distance, 1)
            
            # Filter by distance
            if distance <= max_distance:
                results.append(business)
        except Exception:
            pass
    
    # Filter by query
    if query and query.strip():
        query_lower = query.lower().strip()
        filtered = []
        for business in results:
            if (query_lower in business.name.lower() or 
                query_lower in business.category.lower() or
                query_lower in business.address.lower() or
                (business.description and query_lower in business.description.lower())):
                filtered.append(business)
        results = filtered
    
    # Sort by distance
    results.sort(key=lambda b: b.distance)
    
    # Apply limit
    return results[:limit]


def get_business_by_id(business_id: str) -> Optional[Business]:
    """Get a business by its ID."""
    # Try Foursquare first (primary API)
    if config.FOURSQUARE_API_KEY and config.USE_FOURSQUARE_API:
        # Foursquare place IDs are alphanumeric
        try:
            client = get_foursquare_client()
            return client.get_place_details(business_id)
        except APIError as e:
            logger.warning(f"Foursquare API error fetching business: {str(e)}")
        except Exception as e:
            logger.error(f"Foursquare error: {str(e)}")
    
    # Try Google as fallback
    if config.GOOGLE_API_KEY and config.USE_GOOGLE_API and business_id.startswith("ChIJ"):
        try:
            client = get_google_places_client()
            return client.get_place_details(business_id)
        except APIError as e:
            logger.warning(f"Google API error fetching business: {str(e)}")
        except Exception as e:
            logger.error(f"Google error: {str(e)}")
    
    # Fallback to local data
    businesses = load_businesses()
    
    for business in businesses:
        if business.id == business_id:
            return business
    
    return None


def get_categories() -> List[str]:
    """Get list of available categories."""
    return config.BUSINESS_CATEGORIES


def get_businesses_by_category(category: str) -> List[Business]:
    """Get all businesses in a specific category."""
    return search_businesses("", category=category, min_rating=0.0, max_distance=50.0)


def get_nearby_businesses(lat: float, lng: float, radius: float = 10.0) -> List[Business]:
    """Get all businesses within a radius of a given location."""
    return search_businesses("", max_distance=radius, lat=lat, lng=lng)
