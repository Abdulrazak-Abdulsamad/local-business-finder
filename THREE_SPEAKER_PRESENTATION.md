# Three-Speaker Presentation Script: Local Business Finder

**Total Duration**: 20-25 minutes

---

## SPEAKER 1: INTRODUCTION

### (5-6 minutes)

---

#### SLIDE 1: Opening

**[SAY]**

"Good morning/afternoon everyone! Thank you for joining us today. I'm Speaker 1, and I'll be introducing our Local Business Finder application.

Before we dive in, I'd like to ask: How many of you have struggled to find a specific type of business in a large city like Abuja?"

*(Pause for show of hands)*

"That's what inspired us to build this application."

---

#### SLIDE 2: Project Purpose

**[SAY]**

"The Local Business Finder is a web application designed to help people discover, save, and review local businesses in Abuja, Nigeria.

But why Abuja specifically? Abuja is Nigeria's capital - a rapidly growing city with thousands of businesses across various sectors. Yet, there was no centralized platform for residents and visitors to find and connect with these businesses."



---

#### SLIDE 3: Goals

**[SAY]**

"When we started this project, we had three main goals:

**Goal 1: Accessibility** - Make it easy for anyone to find businesses with just a few clicks.

**Goal 2: Reliability** - Ensure the app works even without internet connectivity through our mock data system.

**Goal 3: User Engagement** - Allow users to save favorites and share their experiences through reviews."



---

#### SLIDE 4: Target Audience

**[SAY]**

"Our application serves several user groups:

- **Residents** looking for nearby restaurants, shops, and services
- **Visitors and tourists** discovering local businesses
- **Business owners** hoping to be discovered by new customers
- **Researchers** studying local business ecosystems

The beauty of our design is its simplicity - no technical knowledge required. If you can use Google Maps, you can use our application."



---

#### SLIDE 5: Key Features Overview

**[SAY]**

"Let me walk you through our key features:

1. **Smart Search** - Users can search by keyword, category, or both
2. **Advanced Filtering** - Filter by rating, distance, and price level
3. **Location Services** - Choose from 12 Abuja areas or set custom location
4. **Bookmarks** - Save favorite businesses for quick access
5. **Reviews System** - Users can write ratings and text reviews
6. **Business Details** - Full contact info, hours, and descriptions

*(Speaker 2 will demonstrate these features shortly)*"



---

#### SLIDE 6: Technical Architecture Preview

**[SAY]**

"From a technical standpoint, we've built a robust system that prioritizes reliability.

We use a **multi-tier data approach** - first attempting to fetch live data from external APIs, and if that fails, seamlessly falling back to local mock data. This ensures users always have access to business information.

*(Speaker 3 will explain the technical details of our data layer)*"



---

#### SLIDE 7: Conclusion & Key Takeaways

**[SAY]**

"To summarize what we've built:

✅ A user-friendly web application for finding local businesses
✅ Smart search and filtering capabilities
✅ Bookmark and review features for user engagement
✅ Reliable fallback system ensuring 100% uptime
✅ Clean, maintainable Python codebase

**Future Improvements we're planning:**

- Interactive map integration
- User authentication system
- Mobile application version
- Multi-city expansion beyond Abuja

Now I'd like to hand over to Speaker 2, who will walk you through our user interface and user experience design."

---

## SPEAKER 2: USER INTERFACE & EXPERIENCE

### (8-10 minutes)

---

#### SLIDE 8: Hand-off from Speaker 1

**[SAY]**

"Thanks Speaker 1! Now I'll be walking you through the user interface and user experience design of our application.

Our goal was to create something intuitive - users should be able to find what they need in three clicks or less."



---

#### SLIDE 9: Layout Design

**[SAY]**

"Let's start with the overall layout. The interface is built using Streamlit, a Python-based web framework.

**The Layout Has Three Main Sections:**

1. **Sidebar (Left)** - Contains search controls, filters, and location settings
2. **Main Content Area (Center)** - Displays search results and business cards
3. **Header** - Application title and navigation

This three-column layout keeps controls accessible while maximizing the result display area."



---

#### SLIDE 10: Navigation Structure

**[SAY]**

"Our navigation is simple and intuitive. In the sidebar, users see four main sections:

1. **🔍 Search** - The main search functionality
2. **🏠 Dashboard** - Overview with recent searches and featured businesses
3. **💾 Bookmarks** - User's saved favorite businesses
4. **🔖 My Reviews** - User's submitted reviews

Each section is accessible with a single click, and the current section is highlighted."



---

#### SLIDE 11: Live Demo - Search Functionality

**[SAY]**

"Let me show you how our search works...

*(DEMO - Type "restaurant" in search box)*

As you can see:
- The search bar accepts any text input
- Results update automatically when you click Search
- Results appear as cards showing name, category, rating, and distance

*(DEMO - Search for "pharmacy")*

Here's another example searching for pharmacies - you can see all nearby options with their ratings."



---

#### SLIDE 12: Filter System

**[SAY]**

"Our filtering system is comprehensive but easy to use.

**Available Filters:**

- **Category** - Dropdown with 20+ business types (Restaurant, Cafe, Hotel, etc.)
- **Minimum Rating** - 0.0 to 5.0 stars
- **Maximum Distance** - 1km to 50km radius
- **Price Level** - ₦ (Budget) to ₦₦₦₦ (Premium)

*(DEMO - Apply a 4-star minimum filter)*

Users can combine multiple filters for precise results. The filters appear in the sidebar and update results instantly."



---

#### SLIDE 13: Results Display

**[SAY]**

"Search results are displayed as clean, informative cards. Each card shows:

- **Business Name** - Prominently displayed
- **Category Icon** - Visual category identification
- **Rating** - Star rating with review count (e.g., "⭐ 4.5 (128 reviews)")
- **Price Level** - ₦ symbols indicating affordability
- **Distance** - Distance from user's location
- **Status** - Open/Closed indicator
- **Address** - Full street address

*(DEMO - Show a result card)*

Clicking on any card opens detailed information about that business."



---

#### SLIDE 14: Business Detail View

**[SAY]**

"When a user clicks on a business, they see a comprehensive detail view with:

- **Full business name and description**
- **Contact information** - Phone number (clickable), address
- **Location** - Coordinates and link to Google Maps
- **Hours of operation** - Open/closed status
- **User reviews** - All reviews from other users
- **Action buttons** - Bookmark and Write Review

This gives users everything they need to make a decision or visit the business."



---

#### SLIDE 15: Responsive Design

**[SAY]**

"We've designed the application to work across devices:

- **Desktop** - Full sidebar + wide content area
- **Tablet** - Collapsible sidebar + medium content
- **Mobile** - Stacked layout with slide-out menu

The interface adapts automatically using Streamlit's responsive components. Users can access all features from any device."



---

#### SLIDE 16: User Experience Highlights

**[SAY]**

"Let me highlight some UX elements we incorporated:

**Loading States** - Spinner displays during search to indicate activity

**Empty States** - Friendly messages when no results found (e.g., "No businesses found. Try different search terms or filters.")

**Error Handling** - Clear error messages guide users when issues occur

**Feedback** - Toast notifications confirm actions like "Bookmark added" or "Review submitted"

**Consistency** - Same visual patterns across all pages

*(DEMO - Add a bookmark to show the toast notification)*

Now I'll hand over to Speaker 3 to explain our data management approach."

---

## SPEAKER 3: APPLICATION STORAGE & DATA

### (7-9 minutes)

---

#### SLIDE 17: Hand-off from Speaker 2

**[SAY]**

"Thank you Speaker 2! Now I'll explain how we store and manage data in the Local Business Finder.

Our approach balances simplicity with reliability - using local file storage rather than requiring database setup."



---

#### SLIDE 18: Database Structure Overview

**[SAY]**

"We use a file-based JSON storage system. Here's our data structure:

```
data/
├── businesses.json    # Business data (names, addresses, ratings)
├── bookmarks.json    # User's saved businesses
├── reviews.json     # User-submitted reviews
└── (generated at runtime)
```

Each file is a simple JSON structure that's human-readable and easy to debug."



---

#### SLIDE 19: Data Models - Business

**[SAY]**

"Our primary data model is the Business object. Here's how it's defined in code:

```python
@dataclass
class Business:
    id: str                    # Unique identifier
    name: str                  # Business name
    category: str              # Category (Restaurant, Hotel, etc.)
    address: str               # Street address
    city: str                  # City
    state: str                 # State
    zip_code: str              # Postal code
    phone: str                 # Phone number
    rating: float              # Rating (0.0-5.0)
    review_count: int          # Number of reviews
    price_level: str           # Price indicator (₦ - ₦₦₦₦)
    latitude: float            # GPS latitude
    longitude: float           # GPS longitude
    description: str           # Business description
    is_open: bool              # Current open status
    distance: float = 0.0      # Distance from user (computed)
```

Each field serves a specific purpose in displaying business information to users."



---

#### SLIDE 20: Data Models - Reviews

**[SAY]**

"Our review system stores user feedback:

```python
@dataclass
class Review:
    id: str                    # Unique review ID
    business_id: str           # Reference to business
    user_name: str              # Reviewer's name
    rating: float               # Rating given (1-5)
    text: str                   # Review text
    timestamp: str              # When review was written
```

Reviews are linked to businesses via the `business_id` field, allowing us to display all reviews for any business."



---

#### SLIDE 21: Data Storage & Retrieval

**[SAY]**

"How data flows through our system:

**Storing Data:**
```python
# In storage.py
def add_bookmark(business_id: str):
    # Read existing bookmarks
    # Add new bookmark
    # Write back to file
```

**Retrieving Data:**
```python
# In storage.py
def get_bookmarks():
    # Read bookmarks.json
    # Return list of bookmarked business IDs
```

The storage layer handles all read/write operations, abstracting the file management from the rest of the application."



---

#### SLIDE 22: API Integrations

**[SAY]**

"We integrate with two external APIs for live data:

**Primary: Foursquare Places API**
- Endpoint: `https://api.foursquare.com/places/v3/search`
- Authentication: Bearer token
- Returns: Names, addresses, ratings, photos, hours

**Fallback: Google Places API**
- Endpoint: `https://maps.googleapis.com/maps/api/place/`
- Authentication: API key
- Similar data structure to Foursquare

**The API call chain:**
```python
try Foursquare API
    except: try Google API
        except: use local mock data
```

This ensures users always get results, even if both external services fail."



---

#### SLIDE 23: Data Management Approaches

**[SAY]**

"We've implemented several data management best practices:

**1. Caching System:**
```python
class APICache:
    # 1-hour time-to-live
    # Max 1000 entries
    # LRU eviction when full
```
Reduces API calls by ~70% and speeds up repeated searches.

**2. Rate Limiting:**
```python
class RateLimiter:
    # Exponential backoff (1s, 2s, 4s)
    # Max 3 retries per request
```
Prevents quota exhaustion from rapid searches.

**3. Mock Data Fallback:**
- Pre-loaded with 20 Abuja businesses
- Always available when APIs fail
- Fully functional - users don't notice the difference

---

#### SLIDE 24: Sample Data

**[SAY]**

"Let me show you a sample of our mock data structure:

*(Show JSON from data/businesses.json)*

As you can see, each business has all the fields needed for display - name, category, address, rating, coordinates, and more.

We also include realistic Abuja businesses like Jabi Lake Mall, Mama's Kitchen restaurant, and Centenary Supermarket."



---

#### SLIDE 25: Summary & Closing

**[SAY]**

"To summarize our data layer:

✅ **File-based JSON storage** - Simple, no database required
✅ **Two external APIs** - Foursquare (primary) + Google (fallback)
✅ **Smart caching** - 1-hour TTL reduces API calls significantly
✅ **Rate limiting** - Exponential backoff prevents quota issues
✅ **Mock data** - Always-on reliability with pre-loaded business data

This approach gives us the best of both worlds - live data when available, with bulletproof reliability.

*(Turn to audience)*

That concludes our presentation! We're happy to answer any questions you might have about the Local Business Finder application."



---

## POST-PRESENTATION: Q&A SUGGESTIONS

### Common Questions & Answers

**Q: Why use JSON files instead of a database?**
A: For a project of this scope, JSON provides simplicity and zero setup. It makes the application easy to run anywhere without database configuration.

**Q: How do you handle API failures gracefully?**
A: We have a tiered fallback system - try Foursquare first, then Google, then mock data. The user experience remains identical.

**Q: Can this scale to more cities?**
A: Yes! The data model supports any location. We'd simply add more business data for new cities.

**Q: How do users add new businesses?**
A: Currently, businesses come from our data sources. We're planning a business owner submission feature for future versions.

---

## PRESENTATION NOTES

### Timing Guide
| Speaker | Section | Duration |
|---------|---------|----------|
| Speaker 1 | Introduction | 5-6 min |
| Speaker 2 | UI/UX | 8-10 min |
| Speaker 3 | Storage/Data | 7-9 min |
| **Total** | | **20-25 min** |

### Transition Phrases
- Speaker 1 → 2: "Now I'd like to hand over to Speaker 2, who will walk you through our user interface..."
- Speaker 2 → 3: "Thank you Speaker 2! Now I'll explain how we store and manage data..."
- Speaker 3 → Q&A: "That concludes our presentation! We're happy to answer any questions..."

### Technical Terms to Define
- **API**: Application Programming Interface
- **Fallback**: Backup data source
- **Cache**: Temporary data storage for faster access
- **Rate Limiting**: Controlling request frequency
