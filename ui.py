"""
Local Business Finder - Main Streamlit Application
Features location detection with interactive map display
"""

import streamlit as st
from datetime import datetime
import random

import config
from models import Business, Review
from api import search_businesses, get_business_by_id, calculate_distance
from storage import storage
import utils


# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.PAGE_LAYOUT,
)


def initialize_session_state():
    """Initialize session state variables."""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "search"
    if 'selected_business' not in st.session_state:
        st.session_state.selected_business = None
    if 'modal_business' not in st.session_state:
        st.session_state.modal_business = None
    if 'has_searched' not in st.session_state:
        st.session_state.has_searched = False
    
    # Location state
    if 'user_latitude' not in st.session_state:
        st.session_state.user_latitude = config.DEFAULT_LATITUDE
    if 'user_longitude' not in st.session_state:
        st.session_state.user_longitude = config.DEFAULT_LONGITUDE
    if 'user_location_name' not in st.session_state:
        st.session_state.user_location_name = config.DEFAULT_LOCATION_NAME
    if 'search_radius' not in st.session_state:
        st.session_state.search_radius = config.DEFAULT_SEARCH_RADIUS


def render_sidebar():
    """Create the sidebar with logical navigation structure."""
    with st.sidebar:
        # ===== TITLE =====
        st.markdown("""
        <div style='text-align: center; padding: 10px;'>
            <h2 style='margin: 0; color: #FF4B4B;'>🏪 Abuja Business Finder</h2>
            <p style='margin: 0; color: #666; font-size: 0.9em;'>Find local businesses near you</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ===== LOCATION SETTINGS =====
        st.subheader("📍 Location Settings")
        render_location_settings()
        
        st.markdown("---")
        
        # ===== MAIN NAVIGATION =====
        st.subheader("🔍 Navigate")
        
        nav_options = [
            ("🔍", "Search", "search"),
            ("🏠", "Dashboard", "dashboard"),
            ("💾", "Bookmarks", "bookmarks"),
            ("🔖", "My Reviews", "reviews"),
        ]
        
        for icon, label, page in nav_options:
            btn_type = "primary" if st.session_state.current_page == page else "secondary"
            if st.button(f"{icon} {label}", use_container_width=True, type=btn_type):
                st.session_state.current_page = page
                st.session_state.modal_business = None
                st.rerun()
        
        st.markdown("---")
        
        # ===== FILTER SETTINGS (Search Page Only) =====
        if st.session_state.current_page == "search":
            render_search_filters()


def render_location_settings():
    """Render location settings with logical grouping."""
    # Current location display
    st.markdown(f"""
    <div style='background: #f0f2f6; padding: 10px; border-radius: 8px; margin-bottom: 10px;'>
        <p style='margin: 0; font-weight: bold;'>📍 {st.session_state.user_location_name}</p>
        <p style='margin: 0; color: #666; font-size: 0.85em;'>
            {st.session_state.user_latitude:.4f}, {st.session_state.user_longitude:.4f}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Location buttons
    manual_clicked = st.button("📝 Search your location", use_container_width=True, key="geo_manual")
    
    if manual_clicked:
        st.session_state.current_page = "location_input"
        st.rerun()
    
    # Search radius
    st.markdown("**🔄 Search Radius**")
    radius = st.select_slider(
        "Search within (km):",
        config.SEARCH_RADIUS_OPTIONS,
        value=st.session_state.search_radius,
        label_visibility="collapsed"
    )
    if radius != st.session_state.search_radius:
        st.session_state.search_radius = radius
        st.session_state.has_searched = False


def render_search_filters():
    """Render search filters in grouped section."""
    st.subheader("🎯 Filters")
    
    # Category filter
    st.session_state.category = st.selectbox(
        "Business Category",
        config.BUSINESS_CATEGORIES,
        index=0,
        label_visibility="collapsed"
    )
    
    # Rating filter
    st.session_state.min_rating = st.slider(
        "Minimum Rating",
        0.0, 5.0, 0.0, 0.5
    )
    
    # Price filter
    st.session_state.price_levels = st.multiselect(
        "Price Level",
        ["₦", "₦₦", "₦₦₦", "₦₦₦₦"],
        default=["₦", "₦₦", "₦₦₦", "₦₦₦₦"]
    )
    
    # Status filter
    st.session_state.open_only = st.checkbox("Open Now Only", value=False)
    
    # Sort option
    st.session_state.sort_by = st.selectbox(
        "Sort By",
        ["rating", "distance", "name", "reviews"],
        index=0
    )


def render_location_input_page():
    """Render manual location input page."""
    st.title("📍 Set Your Location")
    st.markdown("Enter coordinates or select a preset location in Abuja.")
    
    with st.form("location_form", clear_on_submit=True):
        st.subheader("📍 Quick Select")
        
        preset = st.selectbox(
            "Select Location",
            ["Custom..."] + [p["name"] for p in config.LOCATION_PRESETS],
            label_visibility="collapsed"
        )
        
        if preset != "Custom...":
            selected = next(p for p in config.LOCATION_PRESETS if p["name"] == preset)
            lat = st.number_input("Latitude", value=selected["lat"], format="%.4f")
            lng = st.number_input("Longitude", value=selected["lng"], format="%.4f")
            loc_name = st.text_input("Location Name", value=selected["name"])
        else:
            lat = st.number_input("Latitude", value=st.session_state.user_latitude, format="%.4f")
            lng = st.number_input("Longitude", value=st.session_state.user_longitude, format="%.4f")
            loc_name = st.text_input("Location Name", value="Custom Location")
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            save = st.form_submit_button("💾 Save Location", use_container_width=True, type="primary")
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if save:
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                st.session_state.user_latitude = lat
                st.session_state.user_longitude = lng
                st.session_state.user_location_name = loc_name
                st.session_state.has_searched = False
                st.success(config.SUCCESS_MESSAGES["location_updated"])
                st.session_state.current_page = "search"
                st.rerun()
            else:
                st.error(config.ERROR_MESSAGES["invalid_location"])
        
        if cancel:
            st.session_state.current_page = "search"
            st.rerun()


def render_search_page():
    """Render the main search interface."""
    st.title("🔍 Search Local Businesses")
    st.markdown(f"📍 Searching near **{st.session_state.user_location_name}** within **{st.session_state.search_radius}km**")
    st.markdown("---")
    
    # Search input
    col1, col2 = st.columns([4, 1])
    with col1:
        search_query = st.text_input(
            "Search", 
            placeholder="Enter business name, category, or keyword...", 
            label_visibility="collapsed", 
            key="search_input"
        )
    with col2:
        search_clicked = st.button("🔍 Search", use_container_width=True, type="primary")
    
    if search_clicked or (search_query and st.session_state.get('has_searched')):
        perform_search(search_query)
    
    if st.session_state.search_results:
        render_search_results()
    elif st.session_state.get('has_searched'):
        st.info(config.ERROR_MESSAGES["no_results"])


def perform_search(query: str):
    """Execute search and update results."""
    is_valid, error_msg = utils.validate_search_query(query)
    if not is_valid:
        st.error(error_msg)
        return
    
    with st.spinner("Searching for businesses..."):
        category = getattr(st.session_state, 'category', 'All')
        min_rating = getattr(st.session_state, 'min_rating', 0.0)
        
        results = search_businesses(
            query=query, 
            category=category, 
            min_rating=min_rating, 
            max_distance=st.session_state.search_radius,
            lat=st.session_state.user_latitude,
            lng=st.session_state.user_longitude
        )
        
        price_levels = getattr(st.session_state, 'price_levels', None)
        open_only = getattr(st.session_state, 'open_only', False)
        
        results = utils.filter_businesses(
            results, 
            min_rating=min_rating, 
            max_distance=st.session_state.search_radius, 
            price_levels=price_levels, 
            open_only=open_only
        )
        sort_by = getattr(st.session_state, 'sort_by', 'rating')
        results = utils.sort_businesses(results, sort_by=sort_by)
        
        st.session_state.search_results = results
        st.session_state.has_searched = True


def render_search_results():
    """Display search results."""
    st.markdown("---")
    st.subheader(f"📋 Results ({len(st.session_state.search_results)} businesses found)")
    st.markdown(f"📍 Distance from **{st.session_state.user_location_name}**")
    
    # Map toggle
    if st.session_state.search_results:
        show_map = st.checkbox("🗺️ Show on Map", value=False)
        if show_map:
            render_map_view()
    
    cols = st.columns(2)
    for idx, business in enumerate(st.session_state.search_results):
        with cols[idx % 2]:
            render_business_card(business)


def render_map_view():
    """Render map view of search results."""
    st.subheader("📍 Business Locations")
    for business in st.session_state.search_results:
        st.markdown(f"**{business.name}** ({business.category})")
        st.markdown(f"  📍 {business.latitude:.4f}, {business.longitude:.4f} | ⭐ {business.rating} | 📏 {business.distance}km")


def render_business_card(business: Business):
    """Render a single business card."""
    with st.container():
        # Header with name and bookmark
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {business.name}")
            st.caption(f"📍 {business.category}")
        with col2:
            is_bookmarked = storage.is_bookmarked(business.id)
            heart = "❤️" if is_bookmarked else "🤍"
            if st.button(heart, key=f"bm_{business.id}"):
                toggle_bookmark(business)
                st.rerun()
        
        # Details row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**{utils.format_rating(business.rating)}**")
        with col2:
            st.markdown(f"**{business.price_level}**")
        with col3:
            status = utils.get_business_status_badge(business.is_open)
            st.markdown(f"**{status}**")
        
        # Contact info
        st.markdown(f"📍 {business.get_full_address()}")
        st.markdown(f"📞 {utils.format_phone_number(business.phone)}")
        st.markdown(f"📏 {utils.format_distance(business.distance)} away")
        
        if business.description:
            st.markdown(f"_{utils.truncate_text(business.description, 100)}_")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Write Review", key=f"rev_{business.id}", use_container_width=True):
                st.session_state.selected_business = business
                st.session_state.current_page = "write_review"
                st.rerun()
        with col2:
            if st.button("👁️ View Details", key=f"det_{business.id}", use_container_width=True):
                show_business_details(business)


def show_business_details(business: Business):
    """Show detailed business information."""
    seed = abs(sum(ord(c) for c in business.id[:8])) % 100000
    hours = generate_mock_opening_hours(seed)
    rating, count, reviews = generate_mock_reviews(seed)
    
    data = {
        'business': business,
        'distance': business.distance,
        'hours': hours,
        'rating': rating,
        'count': count,
        'reviews': reviews,
        'is_open': business.is_open
    }
    st.session_state.modal_business = data
    st.session_state.current_page = "business_details"
    st.rerun()


def render_business_details_page():
    """Render detailed business information page."""
    data = st.session_state.modal_business
    
    if not data:
        st.error("No business selected.")
        if st.button("← Back to Search"):
            st.session_state.current_page = "search"
            st.rerun()
        return
    
    business = data['business']
    
    if st.button("← Back to Results"):
        st.session_state.current_page = "search"
        st.session_state.modal_business = None
        st.rerun()
    
    st.title(business.name)
    st.markdown(f"📍 {business.category}")
    st.markdown("---")
    
    # Map link
    st.markdown("### 🗺️ Location")
    st.markdown(f"📍 {business.latitude}, {business.longitude}")
    st.markdown(f"[View on Google Maps](https://www.google.com/maps/search/?api=1&query={business.latitude},{business.longitude})")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rating", f"{business.rating} ★")
    with col2:
        st.metric("Reviews", business.review_count)
    with col3:
        st.metric("Distance", f"{business.distance} km")
    
    st.markdown("---")
    
    # Contact
    st.subheader("📞 Contact Information")
    st.markdown(f"**Address:** {business.get_full_address()}")
    st.markdown(f"**Phone:** {utils.format_phone_number(business.phone)}")
    st.markdown(f"**Status:** {utils.get_business_status_badge(business.is_open)}")
    st.markdown(f"**Price Level:** {utils.format_price_level(business.price_level)}")
    
    if business.description:
        st.subheader("📖 About")
        st.markdown(business.description)
    
    st.markdown("---")
    
    # Actions
    col1, col2 = st.columns(2)
    with col1:
        is_bookmarked = storage.is_bookmarked(business.id)
        bk_txt = "❤️ Bookmarked" if is_bookmarked else "🤍 Bookmark"
        if st.button(bk_txt, use_container_width=True, type="primary"):
            toggle_bookmark(business)
            st.rerun()
    with col2:
        if st.button("📝 Write Review", use_container_width=True):
            st.session_state.current_page = "write_review"
            st.session_state.selected_business = business
            st.rerun()


def toggle_bookmark(business: Business):
    """Toggle bookmark status."""
    if storage.is_bookmarked(business.id):
        if storage.remove_bookmark(business.id):
            st.success(config.SUCCESS_MESSAGES["bookmark_removed"])
    else:
        if storage.add_bookmark(business):
            st.success(config.SUCCESS_MESSAGES["bookmark_added"])


# ===== HELPER FUNCTIONS =====
def generate_mock_opening_hours(seed: int) -> dict:
    random.seed(seed)
    opens = ["06:00", "07:00", "08:00", "09:00", "10:00"]
    closes = ["18:00", "19:00", "20:00", "21:00", "22:00", "23:00"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = {}
    for day in days:
        if random.random() < 0.1:
            hours[day] = "Closed"
        else:
            open_t, close_t = random.choice(opens), random.choice(closes)
            if random.random() < 0.25:
                hours[day] = f"{open_t} AM - 1:00 PM, 2:00 PM - {close_t} PM"
            else:
                hours[day] = f"{open_t} AM - {close_t} PM"
    return hours


def generate_mock_reviews(seed: int) -> tuple:
    random.seed(seed + 1000)
    rating = random.randint(1, 5)
    count = random.randint(10, 500)
    
    positive = ["Excellent! Highly recommended.", "Great service!", "Amazing experience!", "Best in Abuja!"]
    neutral = ["Okay service.", "Average.", "Nothing special.", "Decent."]
    mixed = ["Good but expensive.", "Great food.", "Nice location.", "Hard parking."]
    
    sentiments = {"positive": positive, "neutral": neutral, "mixed": mixed}
    reviews = []
    for i in range(random.randint(3, 5)):
        sent = random.choice(["positive", "neutral", "mixed"])
        reviews.append({
            'author': random.choice(["John D.", "Sarah M.", "Mike T.", "Emma R.", "David K."]),
            'rating': random.randint(2, 5),
            'text': random.choice(sentiments[sent]),
            'sentiment': sent
        })
    return rating, count, reviews


def calculate_proximity(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))


# ===== DASHBOARD =====
def render_dashboard():
    """Render dashboard with grid view."""
    st.title("🏠 Abuja Business Dashboard")
    st.markdown(f"📍 Near **{st.session_state.user_location_name}** within **{st.session_state.search_radius}km**")
    st.markdown(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
    st.markdown("---")
    
    with st.spinner("Loading businesses..."):
        businesses = search_businesses(
            "", 
            "All", 
            0.0, 
            st.session_state.search_radius,
            lat=st.session_state.user_latitude,
            lng=st.session_state.user_longitude,
            limit=50
        )
    
    if not businesses:
        st.info("No businesses found within your search radius.")
        return
    
    # Process business data
    user_lat = st.session_state.user_latitude
    user_lng = st.session_state.user_longitude
    
    business_data = []
    for business in businesses:
        dist = calculate_proximity(user_lat, user_lng, business.latitude, business.longitude)
        seed = abs(sum(ord(c) for c in business.id[:8])) % 100000
        hours = generate_mock_opening_hours(seed)
        rating, count, reviews = generate_mock_reviews(seed)
        
        day = datetime.now().strftime("%A")
        is_open = hours.get(day, "Closed") != "Closed"
        
        business_data.append({
            'business': business,
            'distance': dist,
            'hours': hours,
            'rating': rating,
            'count': count,
            'reviews': reviews,
            'is_open': is_open
        })
    
    business_data.sort(key=lambda x: x['distance'])
    
    st.subheader(f"📍 {len(business_data)} Businesses Within {st.session_state.search_radius}km")
    if st.button("🔄 Refresh"):
        st.rerun()
    
    # Map toggle
    show_map = st.checkbox("🗺️ Show on Map", value=False)
    if show_map:
        render_dashboard_map(business_data)
    
    st.markdown("---")
    
    # Grid display
    cols = st.columns(3)
    for idx, data in enumerate(business_data):
        business = data['business']
        
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"### {business.name}")
                st.caption(f"📍 {business.category}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if data['is_open']:
                        st.success("🟢 Open")
                    else:
                        st.error("🔴 Closed")
                with col_b:
                    st.info(f"📏 {data['distance']:.1f} km")
                
                st.markdown(f"**{'★' * data['rating']}☆** ({data['rating']}.0) • {data['count']} reviews")
                st.markdown(f"**{business.price_level}**")
                st.caption(business.address[:45] + "..." if len(business.address) > 45 else business.address)
                
                if st.button(f"👁️ View Details", key=f"dash_view_{business.id}"):
                    show_business_details(business)
                
                st.markdown("---")


def render_dashboard_map(business_data):
    """Render map view in dashboard."""
    st.subheader("🗺️ Business Map")
    
    for data in business_data:
        business = data['business']
        st.markdown(f"**{business.name}** ({business.category})")
        st.markdown(f"  📍 {business.latitude:.4f}, {business.longitude:.4f}")
        st.markdown(f"  📏 {data['distance']:.1f}km | ⭐ {data['rating']} | {'🟢 Open' if data['is_open'] else '🔴 Closed'}")
        st.markdown("")


# ===== BOOKMARKS PAGE =====
def render_bookmarks_page():
    """Render the bookmarks view."""
    st.title("📚 My Bookmarks")
    st.markdown("Your saved businesses for quick access.")
    
    bookmarks = storage.get_all_bookmarks()
    
    if not bookmarks:
        st.info("You haven't bookmarked any businesses yet. Start searching to save your favorites!")
        return
    
    st.markdown(f"**{len(bookmarks)} bookmarked businesses**")
    st.markdown("---")
    
    for bookmark in bookmarks:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"### {bookmark.business_name}")
            st.caption(f"📍 {bookmark.business_category}")
            st.markdown(f"📍 {bookmark.business_address}")
            st.markdown(f"**{utils.format_rating(bookmark.business_rating)}**")
            st.caption(f"Bookmarked on {bookmark.get_formatted_date()}")
        with col2:
            if st.button("👁️ View", key=f"view_bm_{bookmark.id}", use_container_width=True):
                business = get_business_by_id(bookmark.business_id)
                if business:
                    show_business_details(business)
        with col3:
            if st.button("🗑️ Remove", key=f"remove_bm_{bookmark.id}", use_container_width=True):
                if storage.remove_bookmark(bookmark.business_id):
                    st.success(config.SUCCESS_MESSAGES["bookmark_removed"])
                    st.rerun()
        st.markdown("---")


# ===== REVIEWS PAGE =====
def render_reviews_page():
    """Render the user reviews view."""
    st.title("✍️ My Reviews")
    st.markdown("Reviews you've submitted for local businesses.")
    
    reviews = storage.get_all_reviews()
    
    if not reviews:
        st.info("You haven't written any reviews yet. Search for businesses and share your experiences!")
        return
    
    st.markdown(f"**{len(reviews)} reviews written**")
    st.markdown("---")
    
    for review in reviews:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {review.business_name}")
            st.markdown(f"**{review.get_rating_stars()}**")
            st.markdown(f"_{review.text}_")
            st.caption(f"By {review.user_name} on {review.get_formatted_date()}")
        with col2:
            if st.button("🗑️ Delete", key=f"del_r_{review.id}", use_container_width=True):
                if storage.remove_review(review.id):
                    st.success(config.SUCCESS_MESSAGES["review_removed"])
                    st.rerun()
        st.markdown("---")


# ===== WRITE REVIEW PAGE =====
def render_write_review_page():
    """Render write review form."""
    business = st.session_state.selected_business
    
    if not business:
        st.error("No business selected. Please select a business to review.")
        if st.button("← Back to Search"):
            st.session_state.current_page = "search"
            st.rerun()
        return
    
    st.title("📝 Write a Review")
    st.markdown(f"### {business.name}")
    st.markdown(f"📍 {business.get_full_address()}")
    st.markdown("---")
    
    with st.form("review_form", clear_on_submit=True):
        user_name = st.text_input("Your Name", placeholder="Enter your name")
        rating = st.slider("Rating", 1, 5, 5)
        review_text = st.text_area("Your Review", placeholder="Share your experience...", height=150)
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("📤 Submit Review", use_container_width=True, type="primary")
        with col2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submitted:
            name_valid, name_error = utils.validate_user_name(user_name)
            if not name_valid:
                st.error(name_error)
                return
            
            text_valid, text_error = utils.validate_review_text(review_text)
            if not text_valid:
                st.error(text_error)
                return
            
            review = Review(
                id=f"review_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                business_id=business.id,
                business_name=business.name,
                user_name=user_name.strip(),
                rating=rating,
                text=utils.sanitize_input(review_text),
            )
            
            if storage.add_review(review):
                st.success(config.SUCCESS_MESSAGES["review_added"])
                st.balloons()
                st.session_state.current_page = "reviews"
                st.rerun()
        
        if cancelled:
            st.session_state.current_page = "search"
            st.rerun()

def main():
    """Main entry point for the Streamlit application."""
    initialize_session_state()
    render_sidebar()
    
    current_page = st.session_state.current_page
    
    if current_page == "search":
        render_search_page()
    elif current_page == "location_input":
        render_location_input_page()
    elif current_page == "dashboard":
        render_dashboard()
    elif current_page == "bookmarks":
        render_bookmarks_page()
    elif current_page == "reviews":
        render_reviews_page()
    elif current_page == "write_review":
        render_write_review_page()
    elif current_page == "business_details":
        render_business_details_page()
    else:
        render_search_page()


if __name__ == "__main__":
    main()

