# 🏪 Local Business Finder

A beginner-friendly web app for finding, saving, and reviewing local businesses. Built with Python and Streamlit.

## What This App Does

This app lets you:
- **Search** for businesses (restaurants, shops, services, etc.)
- **Filter** results by category, rating, distance, and price
- **Bookmark** your favorite businesses to find them easily later
- **Write reviews** to share your experiences with others

## For Beginners

If you're new to Python or web development, this project is a great learning resource! The code is:
- ✅ Well-commented (explanations throughout)
- ✅ Simple and clean (no unnecessary complexity)
- ✅ Well-organized (each file has a clear purpose)
- ✅ Uses realistic data (Abuja businesses you might recognize)

## Project Structure

```
local_business_finder/
│
├── app.py          # Main app - creates the web interface
├── api.py          # Gets business data (Google API or mock data)
├── config.py       # Settings and constants
├── models.py       # Data blueprints (Business, Review, Bookmark)
├── storage.py      # Saves/loads data to JSON files
├── utils.py        # Helper functions
├── requirements.txt # Python packages needed
├── README.md       # This file
└── data/
    ├── bookmarks.json  # Your saved businesses
    └── reviews.json    # Your written reviews
```

## Quick Start

### 1. Install Python Packages

Open your terminal and run:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root or set environment variables:

```bash
# On Mac/Linux:
export GOOGLE_API_KEY="your_google_api_key"
export USE_GOOGLE_API="true"

# On Windows (Command Prompt):
set GOOGLE_API_KEY=your_google_api_key
set USE_GOOGLE_API=true
```

### 3. Run the App

```bash
streamlit run main.py
```

### 4. Open Your Browser

The app will open at `http://localhost:8501`

## Using Real Google Places API

By default, the app uses mock (fake) data for testing. To use real business data from Google:

### Step 1: Get a Google API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the following APIs for your project:
   - **Places API** - For searching and retrieving business details
   - **Geocoding API** - For address-to-coordinates conversion
4. Go to "Credentials" and create an API key
5. Copy your API key

### Step 2: Configure Environment Variables

**Option A: Environment Variables (Recommended)**
```bash
# On Mac/Linux:
export GOOGLE_API_KEY="your_api_key_here"
export USE_GOOGLE_API="true"

# On Windows:
set GOOGLE_API_KEY=your_api_key_here
set USE_GOOGLE_API=true
```

**Option B: Create a .env file (with python-dotenv)**
```bash
# Create .env file in project root
GOOGLE_API_KEY=your_api_key_here
USE_GOOGLE_API=true
LOG_LEVEL=INFO
```

### Step 3: Run the App

```bash
streamlit run main.py
```

The app will now fetch real business data from Google Places API!

### API Features

- **Google Places API**: Text search, nearby search, and place details
- **Google Geocoding API**: Convert addresses to coordinates
- **Rate Limiting**: Automatic retry with exponential backoff
- **Caching**: In-memory cache to reduce API calls
- **Logging**: Detailed API request/response logging

## How to Use

### Searching for Businesses
1. Type what you're looking for in the search box (e.g., "chicken", "hotel", "salon")
2. Use the filters in the sidebar to narrow your results
3. Click "Search" to find businesses

### Using Filters
- **Category**: Choose a business type (Restaurants, Supermarkets, etc.)
- **Minimum Rating**: Show only businesses with high ratings
- **Maximum Distance**: Limit how far to search
- **Price Level**: Filter by price range (₦ to ₦₦₦₦)
- **Open Now**: Show only currently open businesses
- **Sort By**: Order results by rating, distance, name, or reviews

### Saving Businesses
- Click the heart icon (🤍) on any business to bookmark it
- View your bookmarks by clicking "My Bookmarks" in the sidebar

### Writing Reviews
1. Click "Write Review" on any business
2. Enter your name
3. Select a star rating (1-5)
4. Write your review (10-1000 characters)
5. Click "Submit Review"

## Understanding the Code

### config.py - Settings
This file stores all the app's settings. If you want to change something (like the app title or default search distance), you can do it here.

### models.py - Data Blueprints
These are like templates that tell the app what information each piece of data should have. For example, a Business has a name, address, rating, etc.

### api.py - Business Data
This file can use either:
- **Google Places API**: Real business data from Google Maps
- **Mock API**: Fake data for testing (no API key needed)

### storage.py - Saving Data
This handles saving your bookmarks and reviews to JSON files. When you close the app and open it again, your data is still there!

### utils.py - Helper Tools
These are small functions that help the app work. For example, validating user input, formatting phone numbers, and sorting businesses.

### app.py - The Web Interface
This is the main file that creates what you see in the browser. It uses Streamlit to build the user interface.

## Sample Businesses (Mock Data)

When using mock data, the app includes realistic businesses like:
- **Restaurants**: Chicken Republic, Mr. Biggs, Kilimanjaro, Tantalizers
- **Supermarkets**: Shoprite, Spar, Park 'n' Shop
- **Salons**: Tasala Hair Salon, Beauty Bar Maitama
- **Logistics**: GIG Logistics, DHL, Kwik Delivery
- **Hotels**: Transcorp Hilton, Sheraton Abuja
- **And many more!**

## Abuja Locations Included

The app uses real Abuja areas:
- Wuse, Garki, Maitama, Asokoro
- Jabi, Utako, Gwarinpa, Kubwa
- Lugbe, Kuje, Central Area, Gwagwalada

## Customizing the App

### Change App Title
Edit `config.py`:
```python
APP_TITLE = "🏪 My Custom Title"
```

### Add New Business Categories
Edit `config.py`:
```python
BUSINESS_CATEGORIES = [
    "All",
    "Your New Category",
    # ... other categories
]
```

### Change Default Search Settings
Edit `config.py`:
```python
DEFAULT_SEARCH_RADIUS = 20  # Change from 10 to 20 km
DEFAULT_MIN_RATING = 3.0    # Show only 3+ star businesses
```

## API Configuration Options

In `config.py`, you can adjust:

```python
# Use mock data (True) or real Google API (False)
USE_MOCK_API = True

# Your Google API key
GOOGLE_API_KEY = ""  # Set this to use real data

# Abuja coordinates (center of the city)
ABUJA_LATITUDE = 9.0579
ABUJA_LONGITUDE = 7.4951

# How far to search (in kilometers)
DEFAULT_SEARCH_RADIUS = 10

# Maximum results to show
DEFAULT_MAX_RESULTS = 50
```

## Learning Resources

If you want to learn more about the technologies used:
- **Python**: [python.org](https://python.org)
- **Streamlit**: [streamlit.io](https://streamlit.io)
- **Google Places API**: [developers.google.com/maps](https://developers.google.com/maps/documentation/places/web-service)
- **JSON**: [json.org](https://json.org)

## Troubleshooting

### App won't start
- Make sure Python is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Try running: `streamlit run main.py`

### Data not saving
- Check that the `data/` folder exists
- Make sure you have write permissions

### Search returns no results
- Try different search terms
- Adjust your filters (increase distance, lower rating)
- Check if you have any filters set too strictly

### Google API not working
- Make sure your API key is correct
- Check that Places API is enabled in Google Cloud Console
- Verify your API key has proper permissions
- Check the console for error messages

### API quota exceeded
- Google Places API has daily limits
- Wait 24 hours or upgrade your Google Cloud plan
- Switch to mock data temporarily: `USE_MOCK_API = True`

## For Developers

### Code Style
- PEP 8 compliant
- Well-commented
- Type hints used throughout
- Clear variable names

### Adding Real API Integration
The app already supports Google Places API! Just:
1. Get a Google API key
2. Set `GOOGLE_API_KEY` environment variable
3. Set `USE_MOCK_API = False` in `config.py`

### Extending the App
You can easily add:
- More business categories
- Additional filters
- Map integration
- User authentication
- Database storage

## License

This project is open source and free to use for learning and development.

## Support

If you have questions or need help, feel free to ask! This project is designed to be beginner-friendly and educational.

---

**Happy business hunting! 🏪**
