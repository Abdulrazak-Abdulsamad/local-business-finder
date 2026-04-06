# Local Business Finder - Project Structure & Presentation Script

---

# PART 1: PROJECT STRUCTURE

## 1. Project Overview

### Project Name
**Local Business Finder** - A Python-based web application for discovering, saving, and reviewing local businesses in Abuja, Nigeria.

### Purpose
To provide residents and visitors of Abuja with an easy-to-use platform to find local businesses, read reviews, and save their favorites - all in one place.

### Problem Solved
- Difficulty finding specific types of businesses in a large city
- No centralized platform for local business information
- Lack of user reviews and ratings for local businesses
- No way to save favorite businesses for quick access

---

## 2. File Organization

### Project Directory Structure

```
local-business-finder/
│
├── app.py                   # Main Streamlit application (web UI)
├── api.py                   # API integration layer
├── config.py                # Configuration and settings
├── models.py                # Data models (Business, Review, Bookmark)
├── storage.py              # Data persistence (JSON files)
├── utils.py                # Utility functions
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
│
├── data/                   # Data storage
│   ├── businesses.json     # Local business data
│   ├── bookmarks.json     # User bookmarks
│   ├── reviews.json       # User reviews
│   └── ...
│
└── logs/                   # Application logs
    └── app.log            # Log file
```

---

## 3. Component Descriptions

### 3.1 api.py - API Integration Layer

**Purpose**: Handles all external API calls and business data retrieval.

**Key Functions**:
- `search_businesses(query, category, min_rating, max_distance, limit, lat, lng)` - Main search function
- `get_business_by_id(business_id)` - Get detailed business info
- `load_businesses()` - Load business data from storage
- `calculate_distance(lat1, lng1, lat2, lng2)` - Haversine distance calculation

**API Integration**:
- Primary: Foursquare Places API
- Fallback: Google Places API
- Offline: Local mock data

**Code Example**:
```python
def search_businesses(
    query: str, 
    category: str = "All", 
    min_rating: float = 0.0, 
    max_distance: float = 50.0,
    limit: int = 20,
    lat: Optional[float] = None,
    lng: Optional[float] = None
) -> List[Business]:
    """Search for businesses near a given location."""
    # Uses Foursquare → Google → Mock data hierarchy
```

---

### 3.2 config.py - Configuration

**Purpose**: Centralized configuration constants for easy maintenance.

**Key Settings**:
- `APP_TITLE` - Application name
- `DEFAULT_LATITUDE/LONGITUDE` - Default location (Abuja coordinates)
- `BUSINESS_CATEGORIES` - List of business categories
- API keys and configuration
- Cache settings
- Error messages

**API Configuration**:
```python
FOURSQUARE_API_KEY = os.environ.get("FOURSQUARE_API_KEY", "")
USE_FOURSQUARE_API = os.environ.get("USE_FOURSQUARE_API", "false").lower() == "true"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
USE_GOOGLE_API = os.environ.get("USE_GOOGLE_API", "false").lower() == "true"
```

---

### 3.3 models.py - Data Models

**Purpose**: Defines data structures for the application.

**Key Classes**:

```python
@dataclass
class Business:
    id: str                    # Unique business ID
    name: str                  # Business name
    category: str              # Category (Restaurant, Hotel, etc.)
    address: str               # Street address
    city: str                  # City
    state: str                 # State
    zip_code: str              # Postal code
    phone: str                 # Phone number
    rating: float              # Rating (0.0-5.0)
    review_count: int          # Number of reviews
    price_level: str           # Price indicator (₦, ₦₦, ₦₦₦)
    latitude: float            # GPS latitude
    longitude: float           # GPS longitude
    description: str           # Business description
    is_open: bool              # Current open status
    distance: float = 0.0      # Distance from user
```

---

### 3.4 storage.py - Data Persistence

**Purpose**: Manages saving and loading data to/from JSON files.

**Key Functions**:
- `add_bookmark(business_id)` - Save a business to bookmarks
- `remove_bookmark(business_id)` - Remove a bookmark
- `is_bookmarked(business_id)` - Check if bookmarked
- `add_review(business_id, review)` - Save a review
- `get_reviews(business_id)` - Get all reviews for a business
- `get_bookmarks()` - Get all bookmarked businesses
- `get_recent_searches()` - Get recent search history

---

### 3.5 utils.py - Utility Functions

**Purpose**: Helper functions used throughout the application.

**Key Functions**:
- `validate_search_query(query)` - Validate search input
- `validate_review_text(text)` - Validate review content
- `validate_user_name(name)` - Validate user name
- `format_phone_number(phone)` - Format phone numbers
- `format_distance(distance)` - Format distance display

---

### 3.6 app.py - Main Application

**Purpose**: Streamlit web application - the user interface.

**Key Sections**:
- Page configuration
- Session state initialization
- Sidebar navigation
- Search page
- Dashboard page
- Bookmarks page
- Reviews page
- Business detail modal

---

## 4. Main Features & Functionality

### 4.1 Business Search
- Search by keyword (name, category, description)
- Filter by category
- Filter by rating (1-5 stars)
- Filter by distance (1-50 km)
- Sort by distance, rating, or name

### 4.2 Location Services
- Default location: Abuja, Nigeria
- 12 preset location options
- Manual location entry
- Distance calculation using Haversine formula

### 4.3 Business Details
- Name, address, phone
- Rating and review count
- Price level indicator
- Operating hours
- Location on map
- Link to Google Maps

### 4.4 User Features
- **Bookmarking**: Save favorite businesses
- **Reviews**: Write and read reviews
- **Ratings**: View business ratings

### 4.5 Data Sources
- Foursquare Places API (primary)
- Google Places API (fallback)
- Local mock data (offline)

---

## 5. User Interface Flow

```
┌─────────────────────────────────────────────────────────┐
│                    MAIN APPLICATION                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────┐ │
│  │  Search  │   │Dashboard │   │Bookmarks │   │Reviews│ │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └──┬───┘ │
│       │              │              │             │      │
│       └──────────────┴──────────────┴─────────────┘      │
│                          │                               │
│                    ┌─────▼─────┐                         │
│                    │  Sidebar  │                         │
│                    │  - Search │                         │
│                    │  - Filter │                         │
│                    │  - Location│                        │
│                    └───────────┘                         │
│                          │                               │
│                    ┌─────▼─────┐                         │
│                    │  Results  │                         │
│                    │   List    │                         │
│                    └───────────┘                         │
│                          │                               │
│                    ┌─────▼─────┐                         │
│                    │  Business │                         │
│                    │  Detail   │                         │
│                    └───────────┘                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Data Handling & Storage

### 6.1 Data Storage

**File-based JSON Storage**:
- `data/businesses.json` - Business data
- `data/bookmarks.json` - User bookmarks
- `data/reviews.json` - User reviews

### 6.2 API Caching

```python
# In-memory cache with TTL
class APICache:
    def __init__(self, ttl=3600, max_size=1000):
        self.ttl = ttl      # 1-hour time-to-live
        self.max_size = max_size
```

### 6.3 Rate Limiting

```python
# Exponential backoff retry logic
class RateLimiter:
    def get_delay(self, endpoint):
        # First retry: 1s, Second: 2s, Third: 4s
        return self.base_delay * (2 ** attempt)
```

---

## 7. Error Handling Approach

### 7.1 Error Types

| Error | Handling |
|-------|----------|
| API Quota Exceeded | Wait and retry with backoff |
| API Rate Limited | Exponential backoff |
| Network Error | Fallback to mock data |
| Billing Not Enabled | Graceful fallback |
| Invalid Input | User-friendly error message |

### 7.2 Fallback Strategy

```
Try Foursquare API
    ↓ (if fails)
Try Google API
    ↓ (if fails)
Use Mock Data (always works)
```

### 7.3 Error Messages

```python
ERROR_MESSAGES = {
    "no_results": "No businesses found. Try different search terms or filters.",
    "api_error": "⚠️ Unable to search. Please try again.",
    "api_quota_exceeded": "⚠️ API quota exceeded. Please try again later.",
    "location_error": "⚠️ Unable to detect your location...",
}
```

---

## 8. Potential Future Enhancements

### 8.1 Short-term
- User authentication (login/register)
- Map integration (interactive map view)
- Business photos gallery
- Directions to business

### 8.2 Medium-term
- Mobile app (React Native/Flutter)
- Real-time notifications
- Social sharing
- Business owner accounts

### 8.3 Long-term
- Machine learning recommendations
- Business owner analytics
- Multi-city support
- Integration with delivery services
- Review moderation system

---

# PART 2: PRESENTATION SCRIPT

---

## PRESENTATION: LOCAL BUSINESS FINDER

**Duration**: 10-15 minutes

---

### SLIDE 1: Title Slide

**[SAY]**

"Welcome everyone! Today I'm going to present the **Local Business Finder** - a web application I built to help people discover businesses in Abuja, Nigeria."

---

### SLIDE 2: The Problem

**[SAY]**

"Let me start with the problem. Abuja is a large, growing city with thousands of businesses - restaurants, hotels, shops, and services. But finding specific types of businesses was difficult because..."

- "There was no centralized platform"
- "People relied on word of mouth or generic search engines"
- "No way to save favorite places or read local reviews"

---

### SLIDE 3: Our Solution

**[SAY]**

"I built the Local Business Finder to solve this problem. It's a Python-based web application that allows users to..."

- Search for any type of business
- Filter by category, rating, and distance
- Save favorites (bookmarks)
- Write and read reviews

---

### SLIDE 4: Demo - Main Interface

**[DEMO]**

"Let me show you the application. Here's the main interface..."

1. **Search Bar** - Type what you're looking for
2. **Category Filter** - Restaurant, Hotel, Shop, etc.
3. **Location** - Choose from 12 Abuja areas
4. **Results** - Business cards with ratings, distance, price

**[INTERACT]**
- Search for "restaurant"
- Show filtering by rating

---

### SLIDE 5: Technical Architecture

**[SAY]**

"From a technical standpoint, here's how the application works..."

```
User Request
    ↓
api.py (Search Logic)
    ↓
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Foursquare  │ →   │  Google    │ →   │ Mock Data  │
│   API       │     │  Places    │     │  (Offline) │
└─────────────┘     └─────────────┘     └─────────────┘
    ↓                   ↓                    ↓
              Business Objects (List[Business])
    ↓
Response to User
```

**Key Point**: "We have a fallback hierarchy - if one API fails, we seamlessly switch to the next."

---

### SLIDE 6: API Integration (Code Highlight)

**[SAY]**

"Here's a look at the API integration code..."

```python
# Tries Foursquare first, then Google, then mock data
if config.FOURSQUARE_API_KEY and config.USE_FOURSQUARE_API:
    results = client.search(query, lat, lng, radius)
elif config.GOOGLE_API_KEY and config.USE_GOOGLE_API:
    results = client.text_search(query, location, radius)
else:
    results = load_businesses()  # Mock data fallback
```

**Key Point**: "The user experience is identical regardless of which data source we use."

---

### SLIDE 7: Error Handling

**[SAY]**

"Reliability is important. We have comprehensive error handling..."

- **Rate Limiting**: Exponential backoff prevents API quota exhaustion
- **Caching**: 1-hour cache reduces API calls by 70%
- **Graceful Fallbacks**: If both APIs fail, mock data keeps the app working
- **User-friendly Messages**: Clear error messages guide users

---

### SLIDE 8: Demo - Bookmarks & Reviews

**[DEMO]**

"Now let me show you the user features..."

1. **Bookmark a business** - Click the heart icon
2. **View bookmarks** - See all saved businesses
3. **Write a review** - Add rating and text
4. **Read reviews** - See what others said

**[SAY]**

"All data is persisted in local JSON files - no database setup required."

---

### SLIDE 9: Key Features Summary

**[SAY]**

"Let me summarize what we've built..."

| Feature | Description |
|---------|-------------|
| 🔍 Smart Search | Search by name, category, or keyword |
| 📍 Location Services | 12 Abuja areas + manual entry |
| ⭐ Ratings | View business ratings and reviews |
| 💾 Bookmarks | Save favorite businesses |
| ✍️ Reviews | Write and read user reviews |
| 🔄 API Fallbacks | Foursquare → Google → Mock data |
| 💾 Caching | Reduces API calls, faster response |
| 🛡️ Error Handling | Graceful degradation |

---

### SLIDE 10: Technology Stack

**[SAY]**

"The application is built with beginner-friendly technologies..."

- **Python** - Clean, readable code
- **Streamlit** - Rapid UI development
- **Requests** - HTTP API calls
- **JSON** - Simple data storage

**Key Point**: "Perfect for learning and expanding!"

---

### SLIDE 11: Challenges & Solutions

**[SAY]**

"During development, I faced a few challenges..."

1. **Challenge**: API rate limits and quotas
   - **Solution**: Implemented exponential backoff and caching

2. **Challenge**: API authentication failures
   - **Solution**: Multi-provider fallback system

3. **Challenge**: Need for offline capability
   - **Solution**: Mock data always available as fallback

---

### SLIDE 12: Future Enhancements

**[SAY]**

"What's next for this project? Here are some ideas..."

**Short-term**:
- Interactive map integration
- User authentication
- Business photos

**Medium-term**:
- Mobile app version
- Multi-city expansion

**Long-term**:
- AI recommendations
- Business analytics

---

### SLIDE 13: How to Run

**[SAY]**

"If you'd like to try it yourself..."

```bash
# Clone the repository
git clone <repository-url>

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export FOURSQUARE_API_KEY="your_key"
export USE_FOURSQUARE_API="true"

# Run the application
streamlit run app.py
```

**Open browser at**: http://localhost:8501

---

### SLIDE 14: Questions

**[SAY]**

"Thank you for your time! I'd be happy to answer any questions."

- Demo the application live
- Show code snippets
- Discuss technical details

---

### SLIDE 15: Thank You

**[SAY]**

"The Local Business Finder is available on GitHub. Feel free to explore the code, suggest improvements, or contribute!

**Contact**: [your email]
**GitHub**: [repository URL]

Happy business hunting! 🏪"

---

## PRESENTATION TIPS

### Delivering the Presentation

1. **Practice timing** - Aim for 10-15 minutes
2. **Live demos** - Always have backup screenshots
3. **Engage the audience** - Ask questions, invite interaction
4. **Be ready for questions** - Common ones:
   - "How does the API fallback work?"
   - "What's the data source?"
   - "How do you handle errors?"

### Visual Aids

- Use the application screenshots
- Show code snippets for technical audiences
- Keep slides simple - one idea per slide

### Handling Questions

- Repeat the question for everyone to hear
- "That's a great question" - buys thinking time
- Admit when you don't know something
- Offer to follow up offline

---

## END OF PRESENTATION SCRIPT
