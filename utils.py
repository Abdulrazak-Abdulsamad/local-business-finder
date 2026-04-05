"""
========================================
LOCAL BUSINESS FINDER - HELPER FUNCTIONS
========================================

This file contains useful functions that help the app work.
Think of these as "tools" that other parts of the app can use.

For beginners: These are small, reusable functions that do specific jobs.
Instead of writing the same code over and over, we put it here
and call it whenever we need it.
"""

import re
from typing import List, Optional
from datetime import datetime

import config


# ============================================
# VALIDATION FUNCTIONS
# ============================================
# These check if user input is correct

def validate_search_query(query: str) -> tuple:
    """
    Check if a search query is valid.
    
    Args:
        query: What the user typed in the search box
    
    Returns:
        A tuple: (is_valid: bool, error_message: str)
        If valid, returns (True, "")
        If invalid, returns (False, "error message")
    """
    # Check if empty
    if not query or not query.strip():
        return False, config.ERROR_MESSAGES["empty_search"]
    
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
    # Check if empty
    if not text or not text.strip():
        return False, "Review cannot be empty."
    
    text_length = len(text.strip())
    
    # Check minimum length
    if text_length < config.MIN_REVIEW_LENGTH:
        return False, f"Review must be at least {config.MIN_REVIEW_LENGTH} characters."
    
    # Check maximum length
    if text_length > config.MAX_REVIEW_LENGTH:
        return False, f"Review cannot exceed {config.MAX_REVIEW_LENGTH} characters."
    
    return True, ""


def validate_user_name(name: str) -> tuple:
    """
    Check if a user name is valid.
    
    Args:
        name: The name the user entered
    
    Returns:
        A tuple: (is_valid: bool, error_message: str)
    """
    # Check if empty
    if not name or not name.strip():
        return False, "Name cannot be empty."
    
    name = name.strip()
    
    # Check minimum length
    if len(name) < 2:
        return False, "Name must be at least 2 characters."
    
    # Check maximum length
    if len(name) > 50:
        return False, "Name cannot exceed 50 characters."
    
    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        return False, "Name can only contain letters, spaces, hyphens, and apostrophes."
    
    return True, ""


# ============================================
# FORMATTING FUNCTIONS
# ============================================
# These make data look nice for display

def format_phone_number(phone: str) -> str:
    """
    Format a phone number nicely.
    
    Args:
        phone: Raw phone number (e.g., "08031234567")
    
    Returns:
        Formatted phone number (e.g., "0803 123 4567")
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Format as: 0803 123 4567
    if len(digits) == 11:
        return f"{digits[:4]} {digits[4:7]} {digits[7:]}"
    
    return phone


def format_distance(distance: float) -> str:
    """
    Format distance for display.
    
    Args:
        distance: Distance in kilometers
    
    Returns:
        Formatted string (e.g., "5.2 km")
    """
    if distance < 0.1:
        return "Less than 0.1 km"
    else:
        return f"{distance:.1f} km"


def format_rating(rating: float) -> str:
    """
    Format a rating with stars.
    
    Args:
        rating: Rating value (0-5)
    
    Returns:
        String with stars and number (e.g., "★★★★☆ (4.0)")
    """
    full_stars = int(rating)
    half_star = 1 if (rating - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    stars = "★" * full_stars + "½" * half_star + "☆" * empty_stars
    return f"{stars} ({rating:.1f})"


def format_price_level(price_level: str) -> str:
    """
    Format price level for display.
    
    Args:
        price_level: Price symbol (₦, ₦₦, ₦₦₦, ₦₦₦₦)
    
    Returns:
        Description of price level
    """
    price_map = {
        "₦": "Budget-Friendly",
        "₦₦": "Moderate",
        "₦₦₦": "Upscale",
        "₦₦₦₦": "Premium",
    }
    return price_map.get(price_level, price_level)


def format_timestamp(timestamp: str) -> str:
    """
    Format a timestamp for display.
    
    Args:
        timestamp: ISO format timestamp (e.g., "2026-03-31T14:30:00")
    
    Returns:
        Nice formatted date (e.g., "March 31, 2026 at 02:30 PM")
    """
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except (ValueError, TypeError):
        return timestamp


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Shorten text if it's too long.
    
    Args:
        text: Text to shorten
        max_length: Maximum length before adding "..."
    
    Returns:
        Shortened text with "..." if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def get_business_status_badge(is_open: bool) -> str:
    """
    Get a status badge for business open/closed.
    
    Args:
        is_open: Whether the business is open
    
    Returns:
        Status badge (e.g., "🟢 Open" or "🔴 Closed")
    """
    return "🟢 Open" if is_open else "🔴 Closed"


# ============================================
# FILTERING AND SORTING FUNCTIONS
# ============================================
# These help organize and filter business data

def filter_businesses(
    businesses: list,
    min_rating: float = 0.0,
    max_distance: float = 50.0,
    price_levels: Optional[List[str]] = None,
    open_only: bool = False,
) -> list:
    """
    Filter a list of businesses based on criteria.
    
    Args:
        businesses: List of Business objects
        min_rating: Minimum rating (0-5)
        max_distance: Maximum distance in km
        price_levels: List of acceptable price levels
        open_only: If True, only show open businesses
    
    Returns:
        Filtered list of businesses
    """
    filtered = businesses
    
    # Filter by rating
    if min_rating > 0:
        filtered = [b for b in filtered if b.rating >= min_rating]
    
    # Filter by distance
    if max_distance < 50:
        filtered = [b for b in filtered if b.distance <= max_distance]
    
    # Filter by price level
    if price_levels:
        filtered = [b for b in filtered if b.price_level in price_levels]
    
    # Filter by open status
    if open_only:
        filtered = [b for b in filtered if b.is_open]
    
    return filtered


def sort_businesses(
    businesses: list,
    sort_by: str = "rating",
    ascending: bool = False,
) -> list:
    """
    Sort businesses by a specific criteria.
    
    Args:
        businesses: List of Business objects
        sort_by: What to sort by ("rating", "distance", "name", "reviews")
        ascending: If True, sort low to high. If False, sort high to low.
    
    Returns:
        Sorted list of businesses
    """
    # Map sort options to business attributes
    sort_keys = {
        "rating": lambda b: b.rating,
        "distance": lambda b: b.distance,
        "name": lambda b: b.name.lower(),
        "reviews": lambda b: b.review_count,
    }
    
    # Get the sorting function
    key_func = sort_keys.get(sort_by, sort_keys["rating"])
    
    # Sort the businesses
    return sorted(businesses, key=key_func, reverse=not ascending)
