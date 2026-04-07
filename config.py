

import os
from pathlib import Path

APP_TITLE = "Abuja Business Finder"
APP_ICON = "/Users/samad/Documents/local-business-finder/local-business-finder-icon.png"
PAGE_LAYOUT = "wide"


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_FOLDER = DATA_DIR  
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"
REVIEWS_FILE = DATA_DIR / "reviews.json"
BUSINESSES_FILE = DATA_DIR / "businesses.json"



FOURSQUARE_API_KEY = os.environ.get("FOURSQUARE_API_KEY", "")

USE_FOURSQUARE_API = os.environ.get("USE_FOURSQUARE_API", "false").lower() == "true"


FOURSQUARE_PLACES_API_BASE_URL = "https://api.foursquare.com/places/v3"
FOURSQUARE_API_VERSION = "2024-03-01"


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

USE_GOOGLE_API = os.environ.get("USE_GOOGLE_API", "false").lower() == "true"

GOOGLE_PLACES_API_BASE_URL = "https://maps.googleapis.com/maps/api/place"
GOOGLE_GEOCODING_API_BASE_URL = "https://maps.googleapis.com/maps/api/geocode"



API_TIMEOUT = 30  # seconds
API_MAX_RETRIES = 3
API_RETRY_DELAY = 1  


CACHE_ENABLED = True
CACHE_TTL = 3600  # Time-to-live in seconds (1 hour)
CACHE_MAX_SIZE = 1000  # Maximum number of cached items

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_API_REQUESTS = os.environ.get("LOG_API_REQUESTS", "true").lower() == "true"
LOG_FILE_PATH = BASE_DIR / "logs" / "app.log"

# Search settings
DEFAULT_SEARCH_RADIUS = 10  
MAX_SEARCH_RADIUS = 50  # maximum search radius in km
MIN_SEARCH_RADIUS = 1  # minimum search radius in km
SEARCH_RADIUS_OPTIONS = [1, 2, 5, 10, 15, 20, 25, 30, 40, 50]


# Central Abuja coordinates as default
DEFAULT_LATITUDE = 9.0765
DEFAULT_LONGITUDE = 7.3986
DEFAULT_LOCATION_NAME = "Abuja, Nigeria"


LOCATION_PRESETS = [
    {"name": "Abuja (Central)", "lat": 9.0765, "lng": 7.3986},
    {"name": "Gwagwa", "lat": 9.1386, "lng": 7.3324},
    {"name": "Wuse", "lat": 9.0734, "lng": 7.4741},
    {"name": "Gwarinpa", "lat": 9.1068, "lng": 7.4474},
    {"name": " Maitama", "lat": 9.1156, "lng": 7.4824},
    {"name": "Asokoro", "lat": 9.0898, "lng": 7.5129},
    {"name": "Jabi", "lat": 9.0549, "lng": 7.4390},
    {"name": "Utako", "lat": 9.0774, "lng": 7.4204},
    {"name": "Karu", "lat": 9.0279, "lng": 7.7391},
    {"name": "Kubwa", "lat": 9.1704, "lng": 7.3204},
    {"name": "Zuba", "lat": 9.1536, "lng": 7.2101},
    {"name": "Airport (ABV)", "lat": 9.0062, "lng": 7.3196},
]


BUSINESS_CATEGORIES = [
    "All",
    "Restaurant",
    "Cafe",
    "Hotel",
    "Shopping Mall",
    "Supermarket",
    "Pharmacy",
    "Hospital",
    "Bank",
    "ATM",
    "Gas Station",
    "Park",
    "Gym",
    "Salon",
    "Laundry",
    "Electronics",
    "Furniture",
    "Clothing",
    "Books",
    "Jewelry",
]


DISTANCE_OPTIONS = [1, 2, 5, 10, 15, 20, 25, 30, 40, 50]
RATING_OPTIONS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
PRICE_LEVELS = ["₦", "₦₦", "₦₦₦", "₦₦₦₦"]


RESULTS_PER_PAGE = 20
MAX_RESULTS_DISPLAY = 50


SUCCESS_MESSAGES = {
    "bookmark_added": "✅ Business bookmarked successfully!",
    "bookmark_removed": "🗑️ Bookmark removed.",
    "review_added": "✅ Review submitted successfully!",
    "review_removed": "🗑️ Review deleted.",
    "location_updated": "📍 Location updated successfully!",
}

ERROR_MESSAGES = {
    "no_results": "No businesses found. Try different search terms or filters.",
    "api_error": "⚠️ Unable to search. Please try again.",
    "api_quota_exceeded": "⚠️ API quota exceeded. Please try again later.",
    "api_rate_limited": "⚠️ Too many requests. Please wait a moment.",
    "api_network_error": "⚠️ Network error. Please check your connection.",
    "file_error": "⚠️ Unable to access data. Please try again.",
    "location_error": "⚠️ Unable to detect your location. Please enter manually.",
    "invalid_location": "⚠️ Invalid location. Please enter valid coordinates.",
    "geolocation_denied": "Location access denied. Please enter your location manually.",
    "geolocation_unavailable": "Location service unavailable. Please enter your location manually.",
    "geocoding_failed": "⚠️ Unable to find location. Please try a different address.",
    "empty_search": "Please enter a search term.",
}

# Validation messages
VALIDATION_MESSAGES = {
    "search_empty": "Please enter a search term.",
    "search_too_short": "Search term must be at least 2 characters.",
    "name_empty": "Please enter your name.",
    "name_too_short": "Name must be at least 2 characters.",
    "review_empty": "Please write your review.",
    "review_too_short": "Review must be at least 10 characters.",
    "review_too_long": "Review must be less than 500 characters.",
}


def get_api_key() -> str:
    """Get API key from environment variable (checks Foursquare first, then Google)."""
    # Check Foursquare first (primary), then Google (fallback)
    return os.environ.get("FOURSQUARE_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")


def is_api_configured() -> bool:
    """Check if any API is properly configured (Foursquare or Google)."""
    # Check Foursquare first, then Google fallback
    return (bool(FOURSQUARE_API_KEY) and USE_FOURSQUARE_API) or (bool(GOOGLE_API_KEY) and USE_GOOGLE_API)


def get_active_api() -> str:
    """Get the name of the active API provider."""
    if FOURSQUARE_API_KEY and USE_FOURSQUARE_API:
        return "foursquare"
    elif GOOGLE_API_KEY and USE_GOOGLE_API:
        return "google"
    return "none"


def get_cache_config() -> dict:
    """Get cache configuration."""
    return {
        "enabled": CACHE_ENABLED,
        "ttl": CACHE_TTL,
        "max_size": CACHE_MAX_SIZE,
    }


def get_log_config() -> dict:
    """Get logging configuration."""
    return {
        "level": LOG_LEVEL,
        "log_api_requests": LOG_API_REQUESTS,
        "file_path": str(LOG_FILE_PATH),
    }
