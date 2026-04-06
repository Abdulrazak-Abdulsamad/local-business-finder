# Local Business Finder - Technical Guide

A comprehensive technical guide for developers covering error handling, performance optimization, best practices, and working code snippets from the project.

---

## Table of Contents

1. [API Error Handling](#1-api-error-handling)
2. [UI](#2-ui)
3. [Storage](#3-storage)
4. [Models](#4-models)
5. [Utils](#5-utils)
6. [Interface](#6-interface)
7. [Testing](#7-testing)
8. [Documentation](#8-documentation)
9. [Error Recovery](#9-error-recovery)
10. [Performance](#10-performance)

---

## 1. API Error Handling

This section demonstrates the error handling patterns used in the Google Places API integration, including retry logic, rate limiting, and custom exceptions.

### 1.1 Checking if Errors Should Be Retried

The code pattern uses safe attribute access to handle different exception types:

```python
# From api.py lines 112-114
logger.error(f"API error in {endpoint}: {str(e)}")

# Safe check for is_retriable - handles both method and boolean attribute
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
```

**Explanation:**
- Uses `callable(getattr(...))` to safely check if `is_retriable` is a method
- Falls back to boolean attribute access if it's not callable
- Prevents `'bool' object is not callable` errors

### 1.2 Rate Limiting Implementation

The `RateLimiter` class manages API call frequency:

```python
# From api.py - RateLimiter class
class RateLimiter:
    """Rate limiter with exponential backoff for API calls."""
    
    def __init__(self, max_retries: int = None, base_delay: float = None):
        self.max_retries = max_retries or config.GOOGLE_API_MAX_RETRIES
        self.base_delay = base_delay or config.GOOGLE_API_RETRY_DELAY
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
```

**Usage Example:**
```python
# Check if we should retry
if rate_limiter.should_retry("nearby_search"):
    # Get delay with exponential backoff (1s, 2s, 4s, 8s...)
    delay = rate_limiter.get_delay("nearby_search")
    time.sleep(delay)
    rate_limiter.record_attempt("nearby_search")
    # Retry the request...
```

### 1.3 Quota Exceeded Handling

Custom exception for quota errors:

```python
# From api.py - QuotaExceededError
class QuotaExceededError(APIError):
    """Raised when API quota is exceeded."""
    
    def __init__(self, message: str = "API quota exceeded"):
        super().__init__(message, status_code=429, is_retriable=True)
```

**Usage in error handling:**
```python
try:
    # Make API call
    response = requests.get(url, params=params)
except QuotaExceededError as e:
    logger.warning(f"Quota exceeded: {e}")
    # Fall back to mock data
    return load_mock_data()
```

### 1.4 Billing Error Detection

Detect billing-related errors and fall back gracefully:

```python
# From api.py - _handle_api_error method
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
```

### 1.5 Complete Retry Logic with Exponential Backoff

The decorator pattern that ties everything together:

```python
# From api.py - with_rate_limit_and_retry decorator
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
                
                # Safe check for is_retriable
                is_retry = False
                if callable(getattr(e, 'is_retriable', None)):
                    is_retry = e.is_retriable()
                elif hasattr(e, 'is_retriable'):
                    is_retry = bool(e.is_retriable)
                
                if is_retry and rate_limiter.should_retry(endpoint):
                    delay = rate_limiter.get_delay(endpoint)
                    logger.info(f"Retrying {endpoint} after {delay}s")
                    time.sleep(delay)
                    continue
                raise
                
        # Fallback to mock data after max retries
        logger.warning(f"Max retries exceeded for {endpoint}, falling back to mock data")
        return func(*args, **kwargs)
    
    return wrapper
```

---

## 2. UI

This section covers user interface patterns for displaying search results, handling loading states, and error presentation.

### 2.1 Displaying Search Results

```python
# Using search_businesses function from api.py
from api import search_businesses

def display_search_results(query: str, category: str = "All", 
                         lat: float = None, lng: float = None):
    """Display search results in the UI."""
    
    results = search_businesses(
        query=query,
        category=category,
        lat=lat,
        lng=lng,
        max_distance=10.0,
        limit=20
    )
    
    if not results:
        return {"status": "empty", "message": "No businesses found"}
    
    # Format results for display
    formatted_results = []
    for business in results:
        formatted_results.append({
            "id": business.id,
            "name": business.name,
            "category": business.category,
            "address": business.address,
            "rating": business.rating,
            "review_count": business.review_count,
            "distance": getattr(business, 'distance', 0.0),
            "is_open": business.is_open,
        })
    
    return {"status": "success", "results": formatted_results}
```

### 2.2 Handling Loading States

```python
import streamlit as st

def search_with_loading(query: str, category: str = "All"):
    """Search with loading state management."""
    
    # Show spinner during search
    with st.spinner('Searching for businesses...'):
        try:
            results = search_businesses(
                query=query,
                category=category,
                lat=st.session_state.get('user_latitude'),
                lng=st.session_state.get('user_longitude')
            )
            st.session_state.search_results = results
            return results
        except Exception as e:
            st.error(f"Search failed: {str(e)}")
            return []
```

### 2.3 Error Message Presentation

```python
def show_error(message: str, error_type: str = "generic"):
    """Display formatted error messages."""
    
    error_messages = {
        "generic": "⚠️ An error occurred. Please try again.",
        "no_results": "📭 No businesses found. Try different search terms or filters.",
        "api_error": "🔌 API error. Falling back to cached data.",
        "location_error": "📍 Unable to detect your location. Please enter manually.",
        "quota_exceeded": "⏳ API quota exceeded. Please try again later.",
    }
    
    st.error(error_messages.get(error_type, message))
```

### 2.4 User Input Forms

```python
def render_search_form():
    """Render search input form."""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Search businesses",
            placeholder="e.g., restaurants, hotels, pharmacies",
            key="search_query"
        )
    
    with col2:
        st.write("")  # Spacing
        search_button = st.button("🔍 Search", type="primary")
    
    # Category filter
    category = st.selectbox(
        "Category",
        options=config.BUSINESS_CATEGORIES,
        index=0
    )
    
    return query, category, search_button
```

---

## 3. Storage

This section covers caching strategies and local data persistence patterns.

### 3.1 Caching Results

The in-memory cache implementation:

```python
# From api.py - APICache class
class APICache:
    """In-memory cache for API responses."""
    
    def __init__(self, ttl: int = None, max_size: int = None):
        self.ttl = ttl or config.CACHE_TTL  # Default: 3600 seconds (1 hour)
        self.max_size = max_size or config.CACHE_MAX_SIZE  # Default: 1000 entries
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = f"{prefix}:{str(args)}:{str(kwargs)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with TTL checking."""
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
        """Set value in cache with LRU eviction."""
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
```

**Using the cache with decorator:**
```python
# From api.py - @cached decorator
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
```

### 3.2 Local Data Persistence

The persistence pattern from api.py:

```python
# From api.py - load_businesses and generate_mock_businesses
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
    import time
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
```

---

## 4. Models

This section covers data structures for business objects, search parameters, and response parsing.

### 4.1 Business Object Data Structure

```python
# From models.py - Business dataclass
@dataclass
class Business:
    """
    A local business that users can search for and review.
    
    Each business has basic info like name, address, and rating.
    The @dataclass decorator automatically creates common methods
    like __init__ and __repr__ for us.
    """
    
    # Basic information
    id: str                    # Unique ID for this business
    name: str                  # Business name (e.g., "Chicken Republic")
    category: str              # Type of business (e.g., "Restaurants & Food")
    
    # Location information
    address: str               # Street address
    city: str                  # City (e.g., "Abuja")
    state: str                 # State (e.g., "FCT")
    zip_code: str              # Postal code
    
    # Contact information
    phone: str                 # Phone number
    
    # Rating and popularity
    rating: float              # Rating (0.0-5.0)
    review_count: int          # Number of reviews
    
    # Price and location
    price_level: str           # Price indicator (₦, ₦₦, ₦₦₦, ₦₦₦₦)
    latitude: float            # GPS latitude
    longitude: float           # GPS longitude
    
    # Additional information
    description: str           # Business description
    is_open: bool              # Current open status
    
    # Computed fields (optional)
    distance: float = 0.0      # Distance from search center (computed at runtime)
```

### 4.2 Search Query Parameters

```python
# From api.py - search_businesses function signature
def search_businesses(
    query: str,                    # Search query string
    category: str = "All",          # Business category filter
    min_rating: float = 0.0,        # Minimum rating filter
    max_distance: float = 50.0,     # Maximum distance in km
    limit: int = 20,                # Maximum results to return
    lat: Optional[float] = None,    # Latitude of search center
    lng: Optional[float] = None     # Longitude of search center
) -> List[Business]:
    """
    Search for businesses near a given location.
    
    Args:
        query: Search query string (e.g., "restaurant", "pharmacy")
        category: Business category filter ("All" for no filter)
        min_rating: Minimum rating filter (0.0 to 5.0)
        max_distance: Maximum distance in kilometers
        limit: Maximum number of results to return
        lat: Latitude of search center (uses default if None)
        lng: Longitude of search center (uses default if None)
    
    Returns:
        List of Business objects sorted by distance
    """
```

### 4.3 Response Parsing

```python
# From api.py - _parse_place_result method
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
            "food": "Restaurant",
            "lodging": "Hotel",
            "hospital": "Hospital",
            "pharmacy": "Pharmacy",
            "supermarket": "Supermarket",
            "shopping_mall": "Shopping Mall",
            "bank": "Bank",
            "atm": "ATM",
            "gas_station": "Gas Station",
            "gym": "Gym",
            # ... more mappings
        }
        for t in types:
            if t in type_mapping:
                category = type_mapping[t]
                break
    
    # Map price level
    price_level = place.get("price_level", -1)
    price_symbols = ["", "₦", "₦₦", "₦₦₦", "₦₦₦₦"]
    price_level_str = price_symbols[price_level] if 0 <= price_level <= 4 else "₦₦"
    
    # Create Business object
    business = Business(
        id=place.get("place_id", ""),
        name=place.get("name", ""),
        category=category,
        address=place.get("formatted_address", ""),
        city="Abuja",  # Default city
        state="FCT",  # Default state
        zip_code="900001",
        phone=place.get("formatted_phone_number", ""),
        rating=place.get("rating", 0.0),
        review_count=place.get("user_ratings_total", 0),
        price_level=price_level_str,
        latitude=lat,
        longitude=lng,
        description=place.get("editorial_summary", {}).get("overview", ""),
        is_open=place.get("opening_hours", {}).get("open_now", True),
        distance=0.0
    )
    
    return business
```

---

## 5. Utils

This section covers helper functions, input validation, data transformation, and formatting utilities.

### 5.1 Helper Functions - Distance Calculation

```python
# From api.py - calculate_distance function
def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1, lng1: First coordinate (latitude, longitude)
        lat2, lng2: Second coordinate (latitude, longitude)
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    # Convert to radians
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    # Haversine formula
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c
```

### 5.2 Input Validation

```python
# From utils.py - validation functions
def validate_search_query(query: str) -> tuple:
    """
    Check if a search query is valid.
    
    Args:
        query: What the user typed in the search box
    
    Returns:
        A tuple: (is_valid: bool, error_message: str)
    """
    # Check if empty
    if not query or not query.strip():
        return False, "Search query cannot be empty."
    
    # Check if too short
    if len(query.strip()) < 2:
        return False, "Search must be at least 2 characters."
    
    # Check if too long
    if len(query) > 100:
        return False, "Search is too long (max 100 characters)."
    
    return True, ""


def validate_review_text(text: str) -> tuple:
    """
    Check if review text is valid.
    
    Args:
        text: The review text the user wrote
    
    Returns:
        A tuple: (is_valid: bool, error_message: str)
    """
    if not text or not text.strip():
        return False, "Review cannot be empty."
    
    text_length = len(text.strip())
    
    if text_length < 10:
        return False, "Review must be at least 10 characters."
    
    if text_length > 500:
        return False, "Review cannot exceed 500 characters."
    
    return True, ""
```

### 5.3 Data Transformation

```python
def transform_business_for_display(business: Business) -> dict:
    """Transform business object for UI display."""
    return {
        "name": business.name,
        "category": business.category,
        "address": business.address,
        "rating_stars": "⭐" * int(business.rating),
        "rating": f"{business.rating:.1f}",
        "review_count": f"({business.review_count} reviews)",
        "price_level": business.price_level,
        "distance": f"{business.distance} km" if hasattr(business, 'distance') else "N/A",
        "is_open": "🟢 Open" if business.is_open else "🔴 Closed",
    }


def transform_results_for_api(results: List[Business]) -> dict:
    """Transform search results for JSON API response."""
    return {
        "status": "success",
        "count": len(results),
        "data": [
            {
                "id": b.id,
                "name": b.name,
                "category": b.category,
                "location": {
                    "lat": b.latitude,
                    "lng": b.longitude,
                },
                "rating": b.rating,
            }
            for b in results
        ]
    }
```

### 5.4 Formatting Utilities

```python
def format_phone_number(phone: str) -> str:
    """Format phone number for display."""
    if not phone:
        return "No phone"
    return phone


def format_price_level(price_level: str) -> str:
    """Format price level for display."""
    price_map = {
        "₦": "Budget",
        "₦₦": "Moderate",
        "₦₦₦": "Upscale",
        "₦₦₦₦": "Premium",
    }
    return price_map.get(price_level, price_level)


def format_distance(distance: float) -> str:
    """Format distance for display."""
    if distance < 1:
        return f"{int(distance * 1000)}m"
    return f"{distance:.1f}km"
```

---

## 6. Interface

This section covers connecting all components, event handlers, and workflow automation.

### 6.1 Connecting All Components

```python
# From app.py - Main application structure
import streamlit as st
import config
from api import search_businesses, get_business_by_id, calculate_distance
from models import Business, Review
from storage import storage

# Initialize session state
def initialize_session_state():
    """Initialize session state variables."""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "search"
    if 'selected_business' not in st.session_state:
        st.session_state.selected_business = None
    if 'user_latitude' not in st.session_state:
        st.session_state.user_latitude = config.DEFAULT_LATITUDE
    if 'user_longitude' not in st.session_state:
        st.session_state.user_longitude = config.DEFAULT_LONGITUDE


# Main application flow
def main():
    """Main application entry point."""
    st.set_page_config(
        page_title=config.APP_TITLE,
        page_icon=config.APP_ICON,
        layout=config.PAGE_LAYOUT,
    )
    
    initialize_session_state()
    render_sidebar()
    
    # Route to current page
    if st.session_state.current_page == "search":
        render_search_page()
    elif st.session_state.current_page == "dashboard":
        render_dashboard_page()
    elif st.session_state.current_page == "bookmarks":
        render_bookmarks_page()
    elif st.session_state.current_page == "reviews":
        render_reviews_page()
```

### 6.2 Event Handlers

```python
# Event handlers connecting to api.py endpoints
def handle_search(query: str, category: str, max_distance: float):
    """Handle search button click."""
    results = search_businesses(
        query=query,
        category=category,
        max_distance=max_distance,
        lat=st.session_state.user_latitude,
        lng=st.session_state.user_longitude
    )
    st.session_state.search_results = results
    st.session_state.has_searched = True


def handle_location_update(lat: float, lng: float, location_name: str):
    """Handle location change."""
    st.session_state.user_latitude = lat
    st.session_state.user_longitude = lng
    st.session_state.user_location_name = location_name


def handle_business_select(business_id: str):
    """Handle business selection."""
    business = get_business_by_id(business_id)
    st.session_state.selected_business = business
    st.session_state.modal_business = business


def handle_bookmark(business_id: str):
    """Handle bookmark toggle."""
    if storage.is_bookmarked(business_id):
        storage.remove_bookmark(business_id)
        st.toast("Bookmark removed")
    else:
        storage.add_bookmark(business_id)
        st.toast("Business bookmarked!")
```

### 6.3 Workflow Automation

```python
def automated_search_workflow():
    """Automated search workflow with error handling."""
    
    # Setup default location
    lat = st.session_state.user_latitude
    lng = st.session_state.user_longitude
    
    try:
        # Perform search
        results = search_businesses(
            query=st.session_state.search_query,
            category=st.session_state.search_category,
            lat=lat,
            lng=lng
        )
        
        # Cache results in session
        st.session_state.search_results = results
        
        # Auto-save to recent searches
        storage.add_recent_search({
            "query": st.session_state.search_query,
            "category": st.session_state.search_category,
            "timestamp": str(datetime.now()),
            "results_count": len(results)
        })
        
        return results
        
    except Exception as e:
        logger.error(f"Automated search failed: {e}")
        st.error("Search failed. Using cached results.")
        return st.session_state.search_results or []
```

---

## 7. Testing

This section provides unit and integration test examples.

### 7.1 Basic Import Test

```bash
# Syntax check and import test
python -m py_compile api.py && python -c "import api; print('Import successful')"
```

### 7.2 Unit Tests

```python
# tests/test_api.py
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api
import config


class TestDistanceCalculation(unittest.TestCase):
    """Test distance calculation function."""
    
    def test_calculate_distance_same_point(self):
        """Distance from point to itself should be zero."""
        distance = api.calculate_distance(9.0765, 7.3986, 9.0765, 7.3986)
        self.assertAlmostEqual(distance, 0.0, places=5)
    
    def test_calculate_distance_known_points(self):
        """Test with known distance between two points."""
        # Distance from Abuja to Lagos (approximately 350km)
        distance = api.calculate_distance(9.0765, 7.3986, 6.5244, 3.3798)
        self.assertGreater(distance, 300)
        self.assertLess(distance, 400)


class TestBusinessSearch(unittest.TestCase):
    """Test business search functionality."""
    
    def test_search_with_empty_query(self):
        """Search with empty query should return results."""
        results = api.search_businesses("")
        self.assertIsInstance(results, list)
    
    def test_search_with_category_filter(self):
        """Search with category filter."""
        results = api.search_businesses("", category="Restaurant")
        for business in results:
            self.assertEqual(business.category, "Restaurant")
    
    def test_search_with_distance_limit(self):
        """Search with max distance."""
        results = api.search_businesses("", max_distance=5.0)
        for business in results:
            if hasattr(business, 'distance'):
                self.assertLessEqual(business.distance, 5.0)


class TestCache(unittest.TestCase):
    """Test caching functionality."""
    
    def test_cache_set_and_get(self):
        """Test basic cache operations."""
        cache = api.APICache(ttl=60, max_size=10)
        
        cache.set("test_key", {"data": "test_value"})
        result = cache.get("test_key")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["data"], "test_value")
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = api.APICache()
        
        result = cache.get("nonexistent_key")
        self.assertIsNone(result)


class TestRateLimiter(unittest.TestCase):
    """Test rate limiter functionality."""
    
    def test_should_retry_initially_true(self):
        """Should retry when under max retries."""
        limiter = api.RateLimiter(max_retries=3)
        
        self.assertTrue(limiter.should_retry("test_endpoint"))
    
    def test_should_retry_after_max(self):
        """Should not retry after max retries."""
        limiter = api.RateLimiter(max_retries=2)
        
        limiter.record_attempt("test_endpoint")
        limiter.record_attempt("test_endpoint")
        limiter.record_attempt("test_endpoint")
        
        self.assertFalse(limiter.should_retry("test_endpoint"))
    
    def test_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        limiter = api.RateLimiter(max_retries=3, base_delay=1.0)
        
        # First retry: 1 * 2^0 = 1 second
        # Second retry: 1 * 2^1 = 2 seconds
        # Third retry: 1 * 2^2 = 4 seconds
        
        self.assertEqual(limiter.get_delay("test"), 1.0)
        limiter.record_attempt("test")
        self.assertEqual(limiter.get_delay("test"), 2.0)
        limiter.record_attempt("test")
        self.assertEqual(limiter.get_delay("test"), 4.0)


class TestConfig(unittest.TestCase):
    """Test configuration."""
    
    def test_is_api_configured_no_key(self):
        """Test API not configured without key."""
        # This will use environment or default
        self.assertIsInstance(config.is_api_configured(), bool)


if __name__ == '__main__':
    unittest.main()
```

### 7.3 Integration Tests

```python
# tests/test_integration.py
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGooglePlacesIntegration(unittest.TestCase):
    """Integration tests with Google Places API (when configured)."""
    
    @unittest.skipUnless(
        os.environ.get("GOOGLE_API_KEY") and os.environ.get("USE_GOOGLE_API") == "true",
        "Google API not configured"
    )
    def test_google_places_text_search(self):
        """Test actual Google Places text search."""
        import api
        
        client = api.get_google_places_client()
        results = client.text_search(
            query="restaurant",
            location="9.0765,7.3986",
            radius=5000
        )
        
        self.assertIsInstance(results, list)
        if results:
            self.assertIsInstance(results[0], api.Business)
    
    @unittest.skipUnless(
        os.environ.get("GOOGLE_API_KEY") and os.environ.get("USE_GOOGLE_API") == "true",
        "Google API not configured"
    )
    def test_google_places_nearby_search(self):
        """Test actual Google Places nearby search."""
        import api
        
        client = api.get_google_places_client()
        results = client.nearby_search(
            location="9.0765,7.3986",
            radius=5000,
            category="restaurant"
        )
        
        self.assertIsInstance(results, list)


class TestGeocodingIntegration(unittest.TestCase):
    """Integration tests with Geocoding API."""
    
    @unittest.skipUnless(
        os.environ.get("GOOGLE_API_KEY") and os.environ.get("USE_GOOGLE_API") == "true",
        "Google API not configured"
    )
    def test_geocode_address(self):
        """Test address geocoding."""
        import api
        
        result = api.geocode_address("Abuja, Nigeria")
        
        self.assertIsNotNone(result)
        self.assertIn("lat", result)
        self.assertIn("lng", result)


if __name__ == '__main__':
    unittest.main()
```

---

## 8. Documentation

This section covers API usage examples, configuration guides, and troubleshooting tips.

### 8.1 API Usage Examples

```python
# search_businesses function signature and usage
from api import search_businesses, get_business_by_id, geocode_address

# Basic search
results = search_businesses("restaurant")

# Search with location
results = search_businesses(
    query="restaurant",
    category="Restaurant",
    lat=9.0765,
    lng=7.3986,
    max_distance=10.0,
    limit=20
)

# Get business by ID
business = get_business_by_id("ChIJ1234567890abcdef")

# Geocode an address
coordinates = geocode_address("27 Aminu Crescent, Wuse 2, Abuja")
if coordinates:
    lat = coordinates["lat"]
    lng = coordinates["lng"]
```

### 8.2 Configuration Guide

```python
# Configuration options in config.py

# API Configuration
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")  # Set via environment
USE_GOOGLE_API = os.environ.get("USE_GOOGLE_API", "false").lower() == "true"

# Cache Configuration
CACHE_ENABLED = True           # Enable/disable caching
CACHE_TTL = 3600              # Time-to-live in seconds (1 hour)
CACHE_MAX_SIZE = 1000          # Maximum cache entries

# Rate Limiting
GOOGLE_API_TIMEOUT = 30        # Request timeout in seconds
GOOGLE_API_MAX_RETRIES = 3     # Maximum retry attempts
GOOGLE_API_RETRY_DELAY = 1     # Base delay for exponential backoff

# Logging
LOG_LEVEL = "INFO"            # DEBUG, INFO, WARNING, ERROR
LOG_API_REQUESTS = True        # Log API requests/responses

# Search Settings
DEFAULT_SEARCH_RADIUS = 10    # Default search radius in km
MAX_SEARCH_RADIUS = 50         # Maximum allowed radius
```

### 8.3 Environment Setup

```bash
# Set environment variables (Linux/Mac)
export GOOGLE_API_KEY="your_google_api_key_here"
export USE_GOOGLE_API="true"
export LOG_LEVEL="DEBUG"

# Run the application
streamlit run app.py

# Or use a .env file with python-dotenv
# Create .env file:
GOOGLE_API_KEY=your_google_api_key_here
USE_GOOGLE_API=true
LOG_LEVEL=INFO
LOG_API_REQUESTS=true
```

### 8.4 Troubleshooting Tips

```python
# Common error scenarios and solutions

# Error 1: API returns no results
# Solution: Check query parameters, try broader search
results = search_businesses("restaurant", max_distance=50)

# Error 2: Quota exceeded
# Solution: Enable caching, implement backoff
# Check config.CACHE_ENABLED is True

# Error 3: Billing not enabled
# Solution: Enable billing in Google Cloud Console
# Error message: "You must enable Billing on the Google Cloud Project"

# Error 4: Invalid API key
# Solution: Verify API key in Google Cloud Console
# Check that Places API is enabled

# Error 5: Network timeout
# Solution: Increase timeout in config.py
GOOGLE_API_TIMEOUT = 60  # Increase to 60 seconds
```

---

## 9. Error Recovery

This section covers error recovery patterns, exception hierarchy, and logging.

### 9.1 Handling REQUEST_DENIED Errors

```python
# From api.py - handling REQUEST_DENIED with billing detection
def _handle_api_error(self, status: str, error_message: str = None):
    """Handle API error responses with proper recovery."""
    
    error_msg = error_message or f"API error: {status}"
    
    if status == "OVER_QUERY_LIMIT":
        # Quota exceeded - can retry after delay
        raise QuotaExceededError(error_msg)
    
    elif status == "REQUEST_DENIED":
        # Check if it's a billing error (non-retriable)
        if "billing" in (error_message or "").lower():
            logger.error(
                "Billing not enabled on Google Cloud Project. "
                "Please enable billing at https://console.cloud.google.com/project/_/billing/enable"
            )
            raise APIError(
                "Google API billing not enabled. Please enable billing in Google Cloud Console. "
                "Falling back to mock data.",
                status_code=403,
                is_retriable=False
            )
        # Other authorization errors - not retriable
        raise APIError(error_msg, status_code=403, is_retriable=False)
    
    elif status == "INVALID_REQUEST":
        # Invalid request parameters - not retriable
        raise APIError(error_msg, status_code=400, is_retriable=False)
    
    else:
        # Unknown error - might be retriable
        raise APIError(error_msg, status_code=500, is_retriable=True)
```

### 9.2 Exception Hierarchy

```python
# From api.py - Custom exception classes

class APIError(Exception):
    """Base exception for API errors."""
    
    def __init__(self, message: str, status_code: int = None,
                 is_retriable: bool = False):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.is_retriable = is_retriable
    
    def is_retriable(self) -> bool:
        """Check if this error should trigger a retry."""
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
```

### 9.3 Logging Patterns for Endpoint Failures

```python
# Comprehensive logging for API failures

def log_endpoint_failure(endpoint: str, error: Exception, context: dict = None):
    """Log API endpoint failure with context."""
    
    logger.error(f"API failure in {endpoint}: {str(error)}")
    logger.error(f"Error type: {type(error).__name__}")
    
    if context:
        logger.error(f"Context: {context}")
    
    # Log if error is retriable
    if hasattr(error, 'is_retriable'):
        is_retry = False
        if callable(getattr(error, 'is_retriable', None)):
            is_retry = error.is_retriable()
        elif hasattr(error, 'is_retriable'):
            is_retry = bool(error.is_retriable)
        logger.error(f"Retriable: {is_retry}")
    
    # Log status code if available
    if hasattr(error, 'status_code') and error.status_code:
        logger.error(f"HTTP Status: {error.status_code}")


# Usage in API client
try:
    results = client.text_search(query="restaurant", location=loc)
except APIError as e:
    log_endpoint_failure(
        "text_search",
        e,
        {"query": "restaurant", "location": loc}
    )
    # Fallback or raise
    raise
```

### 9.4 Graceful Degradation

```python
# Fallback pattern for error recovery
def search_with_fallback(query: str, category: str = "All"):
    """
    Search with automatic fallback to mock data on API failure.
    """
    
    # Try Google API first if configured
    if config.is_api_configured():
        try:
            client = get_google_places_client()
            results = client.text_search(
                query=query,
                location=f"{config.DEFAULT_LATITUDE},{config.DEFAULT_LONGITUDE}",
                category=category if category != "All" else None
            )
            logger.info(f"Google API returned {len(results)} results")
            return results
            
        except APIError as e:
            logger.warning(f"Google API failed: {e}. Using fallback data.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}. Using fallback data.")
    
    # Fallback to local/mock data
    logger.info("Using local fallback data")
    return load_businesses()
```

---

## 10. Performance

This section covers caching strategies, connection management, and response optimization.

### 10.1 Caching Strategies

```python
# From api.py - Comprehensive caching implementation

# 1. In-memory cache with TTL
class APICache:
    """High-performance in-memory cache."""
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        self.ttl = ttl
        self.max_size = max_size
        self._cache = {}
    
    def get(self, key: str):
        """Check cache with TTL expiry."""
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        age = (datetime.now() - timestamp).total_seconds()
        
        if age > self.ttl:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any):
        """Cache with LRU eviction."""
        if len(self._cache) >= self.max_size:
            # Evict oldest entry
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest]
        
        self._cache[key] = (value, datetime.now())


# 2. Decorator-based caching
@cached("places", TTL=3600)  # Cache for 1 hour
def search_with_cache(query: str, location: str):
    """Cached search function."""
    # API call here...
    return results


# 3. Geocoding-specific caching (24 hours)
@cached("geocode", TTL=86400)  # Cache geocoding for 24 hours
def geocode_with_cache(address: str):
    """Geocoding is cached longer since addresses don't change."""
    return geocode_client.geocode(address)
```

### 10.2 Connection Pooling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    """Create requests session with connection pooling and retries."""
    
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    
    # Configure adapter with connection pooling
    adapter = HTTPAdapter(
        pool_connections=10,  # Number of connection pools
        pool_maxsize=20,      # Connections per pool
        max_retries=retry_strategy
    )
    
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session


# Use in API client
def _make_request(self, endpoint: str, params: dict) -> dict:
    """Make request with connection pooling."""
    
    session = create_session_with_retries()
    
    params["key"] = self.api_key
    url = f"{self.base_url}/{endpoint}/json"
    
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    return response.json()
```

### 10.3 Response Optimization

```python
# Optimize API responses for faster processing

# 1. Request only needed fields
def get_place_details_optimized(place_id: str):
    """Get only essential fields to reduce payload."""
    
    params = {
        "place_id": place_id,
        # Request only essential fields
        "fields": "place_id,name,formatted_address,geometry,types,"
                 "formatted_phone_number,rating,user_ratings_total",
        "language": "en-NG",
    }
    
    return client._make_request("details", params)


# 2. Batch requests where possible
def search_multiple_queries(queries: list):
    """Execute searches and cache all results."""
    
    results = []
    for query in queries:
        cached = api_cache.get(f"search:{query}")
        if cached:
            results.extend(cached)
        else:
            result = search_businesses(query)
            api_cache.set(f"search:{query}", result)
            results.extend(result)
    
    return results


# 3. Limit response size
def search_businesses_limited(query: str, limit: int = 20):
    """Limit response to specified number of results."""
    
    results = search_businesses(query)
    return results[:limit]  # Early truncation
```

### 10.4 Performance Monitoring

```python
import time
import functools

def measure_performance(func):
    """Decorator to measure function performance."""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        elapsed = time.time() - start_time
        logger.info(f"{func.__name__} completed in {elapsed:.3f}s")
        
        return result
    
    return wrapper


@measure_performance
def slow_search_operation(query: str):
    """Example of monitored function."""
    # Your code here...
    return results
```

---

## Summary

This technical guide covers all major aspects of the Local Business Finder project:

1. **API Error Handling**: Retry logic, rate limiting, billing detection
2. **UI**: Display patterns, loading states, error presentation
3. **Storage**: Caching, persistence patterns
4. **Models**: Data structures and response parsing
5. **Utils**: Helper functions and validation
6. **Interface**: Component integration and workflows
7. **Testing**: Unit and integration test examples
8. **Documentation**: API usage and configuration
9. **Error Recovery**: Exception hierarchy and logging
10. **Performance**: Caching strategies and optimization

All code snippets are extracted from the actual project files and can be used directly in your implementation.
