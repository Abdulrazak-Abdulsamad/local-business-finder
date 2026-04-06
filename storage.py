import json
import fcntl
import os
import hashlib
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

import config
from models import Business, Review, Bookmark


class BusinessStorage:
    """
    Robust storage for business data with location metadata.
    
    Provides methods for:
    - Loading/saving businesses to JSON
    - Adding/updating business records
    - Finding businesses by place_id or name+location
    - Validating business data
    - File locking for thread safety
    """
    
    def __init__(self, file_path: Optional[Path] = None):
        """
        Initialize the business storage.
        
        Args:
            file_path: Path to businesses JSON file. Uses config.BUSINESSES_FILE if not provided.
        """
        self.file_path = file_path or config.BUSINESSES_FILE
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Create the data folder and JSON file if they don't exist."""
        try:
            from pathlib import Path
            path = Path(self.file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                self._write_json({"businesses": [], "last_updated": datetime.now().isoformat()})
        except OSError as error:
            print(f"Error creating data file: {error}")
    
    def _read_json(self) -> Dict[str, Any]:
        """
        Read and parse the JSON file.
        Uses file locking for safe concurrent access.
        
        Returns:
            Dictionary containing businesses data
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                # Acquire shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {"businesses": [], "last_updated": datetime.now().isoformat()}
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error reading JSON: {error}")
            return {"businesses": [], "last_updated": datetime.now().isoformat()}
    
    def _write_json(self, data: Dict[str, Any]) -> bool:
        """
        Write data to the JSON file.
        Uses file locking for safe concurrent access.
        
        Args:
            data: Dictionary to write to JSON
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                # Acquire exclusive lock for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    return True
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except IOError as error:
            print(f"Error writing JSON: {error}")
            return False
    
    def load_businesses(self) -> List[Dict[str, Any]]:
        """
        Load all businesses from the JSON file.
        
        Returns:
            List of business dictionaries
        """
        data = self._read_json()
        return data.get("businesses", [])
    
    def save_businesses(self, businesses: List[Dict[str, Any]]) -> bool:
        """
        Save all businesses to the JSON file.
        
        Args:
            businesses: List of business dictionaries
        
        Returns:
            True if successful, False otherwise
        """
        data = {
            "businesses": businesses,
            "last_updated": datetime.now().isoformat()
        }
        return self._write_json(data)
    
    def validate_business_data(self, business: Dict[str, Any]) -> tuple:
        """
        Validate business data before saving.
        Checks for required fields and data integrity.
        
        Args:
            business: Business dictionary to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required top-level fields
        for field in config.REQUIRED_BUSINESS_FIELDS:
            if field not in business or not business[field]:
                return False, f"Missing required field: {field}"
        
        # Validate location
        location = business.get("location", {})
        if not isinstance(location, dict):
            return False, "Location must be a dictionary"
        
        for field in config.REQUIRED_LOCATION_FIELDS:
            if field not in location or not location[field]:
                return False, f"Missing required location field: {field}"
        
        # Validate coordinates
        coordinates = location.get("coordinates", {})
        if not isinstance(coordinates, dict):
            return False, "Coordinates must be a dictionary"
        
        for field in config.REQUIRED_COORDINATE_FIELDS:
            if field not in coordinates:
                return False, f"Missing required coordinate field: {field}"
        
        return True, ""
    
    def find_business_by_place_id(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a business by its Google Places ID.
        
        Args:
            place_id: Google Places ID
        
        Returns:
            Business dictionary if found, None otherwise
        """
        businesses = self.load_businesses()
        for business in businesses:
            if business.get("place_id") == place_id:
                return business
        return None
    
    def find_business_by_name_and_location(
        self,
        name: str,
        area: str,
        street: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a business by name and location.
        
        Args:
            name: Business name (case-insensitive)
            area: Area/location name
            street: Optional street name
        
        Returns:
            Business dictionary if found, None otherwise
        """
        businesses = self.load_businesses()
        name_lower = name.lower().strip()
        area_lower = area.lower().strip()
        
        for business in businesses:
            business_name = business.get("name", "").lower().strip()
            location = business.get("location", {})
            business_area = location.get("area", "").lower().strip()
            
            # Match by name and area
            if business_name == name_lower and business_area == area_lower:
                # If street provided, also check street
                if street:
                    business_street = location.get("street", "").lower().strip()
                    if business_street == street.lower().strip():
                        return business
                else:
                    return business
        
        return None
    
    def add_business(self, business: Dict[str, Any]) -> tuple:
        """
        Add a new business to storage.
        Prevents duplicates based on place_id or name+location.
        
        Args:
            business: Business dictionary to add
        
        Returns:
            Tuple of (success, message)
        """
        # Validate business data
        is_valid, error_msg = self.validate_business_data(business)
        if not is_valid:
            return False, error_msg
        
        # Check for duplicate by place_id
        place_id = business.get("place_id")
        if place_id:
            existing = self.find_business_by_place_id(place_id)
            if existing:
                return False, "Business with this place_id already exists"
        
        # Check for duplicate by name + location
        location = business.get("location", {})
        existing = self.find_business_by_name_and_location(
            business.get("name", ""),
            location.get("area", ""),
            location.get("street")
        )
        if existing:
            return False, config.ERROR_MESSAGES.get("duplicate_business", 
                "A business with this name and location already exists.")
        
        # Add timestamp
        business["last_updated"] = datetime.now().isoformat()
        
        # Save to file
        businesses = self.load_businesses()
        businesses.append(business)
        
        if self.save_businesses(businesses):
            return True, "Business added successfully"
        else:
            return False, config.ERROR_MESSAGES["storage_error"]
    
    def update_business(self, place_id: str, updates: Dict[str, Any]) -> tuple:
        """
        Update an existing business record.
        
        Args:
            place_id: Google Places ID of the business to update
            updates: Dictionary of fields to update
        
        Returns:
            Tuple of (success, message)
        """
        businesses = self.load_businesses()
        
        # Find the business
        found_index = None
        for i, business in enumerate(business):
            if business.get("place_id") == place_id:
                found_index = i
                break
        
        if found_index is None:
            return False, config.ERROR_MESSAGES.get("business_not_found", "Business not found")
        
        # Validate updates if they include location
        if "location" in updates:
            test_business = businesses[found_index].copy()
            test_business.update(updates)
            is_valid, error_msg = self.validate_business_data(test_business)
            if not is_valid:
                return False, error_msg
        
        # Apply updates
        businesses[found_index].update(updates)
        businesses[found_index]["last_updated"] = datetime.now().isoformat()
        
        if self.save_businesses(businesses):
            return True, "Business updated successfully"
        else:
            return False, config.ERROR_MESSAGES["storage_error"]
    
    def delete_business(self, place_id: str) -> tuple:
        """
        Delete a business from storage.
        
        Args:
            place_id: Google Places ID of the business to delete
        
        Returns:
            Tuple of (success, message)
        """
        businesses = self.load_businesses()
        
        # Find and remove the business
        original_count = len(businesses)
        businesses = [b for b in businesses if b.get("place_id") != place_id]
        
        if len(businesses) == original_count:
            return False, config.ERROR_MESSAGES.get("business_not_found", "Business not found")
        
        if self.save_businesses(businesses):
            return True, "Business deleted successfully"
        else:
            return False, config.ERROR_MESSAGES["storage_error"]
    
    def search_businesses(
        self,
        query: str = "",
        category: str = "All",
        area: Optional[str] = None,
        min_rating: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search businesses with optional filters.
        
        Args:
            query: Search query (matches name or description)
            category: Business category filter
            area: Area/location filter
            min_rating: Minimum rating filter
        
        Returns:
            List of matching business dictionaries
        """
        businesses = self.load_businesses()
        results = []
        
        query_lower = query.lower().strip() if query else ""
        area_lower = area.lower().strip() if area else ""
        
        for business in businesses:
            # Filter by category
            if category != "All" and business.get("category") != category:
                continue
            
            # Filter by area
            if area_lower:
                business_area = business.get("location", {}).get("area", "").lower()
                if area_lower not in business_area:
                    continue
            
            # Filter by rating
            if min_rating > 0:
                rating = business.get("rating", 0)
                if rating < min_rating:
                    continue
            
            # Filter by query
            if query_lower:
                name = business.get("name", "").lower()
                description = business.get("description", "").lower()
                category_text = business.get("category", "").lower()
                
                if (query_lower not in name and 
                    query_lower not in description and 
                    query_lower not in category_text):
                    continue
            
            results.append(business)
        
        return results
    
    def get_all_areas(self) -> List[str]:
        """
        Get list of all unique areas.
        
        Returns:
            List of area names
        """
        businesses = self.load_businesses()
        areas = set()
        
        for business in businesses:
            area = business.get("location", {}).get("area", "")
            if area:
                areas.add(area)
        
        return sorted(list(areas))
    
    def get_business_count(self) -> int:
        """
        Get total number of businesses.
        
        Returns:
            Count of businesses
        """
        return len(self.load_businesses())


# ============================================
# ORIGINAL BOOKMARKS/REVIEWS STORAGE
# ============================================
# Keep the existing bookmark and review storage functionality

class Storage:
    """Legacy storage class for bookmarks and reviews."""
    
    def __init__(self):
        """Set up storage and make sure data folder exists."""
        self._make_data_folder()
    
    def _make_data_folder(self):
        """Create the data folder if it doesn't exist."""
        try:
            config.DATA_FOLDER.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            print(f"Couldn't create data folder: {error}")
    
    def _read_json_file(self, file_path: Path) -> list:
        """Read a JSON file."""
        try:
            if not file_path.exists():
                return []
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, IOError) as error:
            print(f"Error reading JSON from {file_path}: {error}")
            return []
    
    def _write_json_file(self, file_path: Path, data: list) -> bool:
        """Write data to a JSON file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            return True
        except IOError as error:
            print(f"Error writing to file {file_path}: {error}")
            return False
    
    # Bookmark methods
    def get_all_bookmarks(self) -> List[Bookmark]:
        """Get all bookmarked businesses."""
        data = self._read_json_file(config.BOOKMARKS_FILE)
        return [Bookmark.from_dict(item) for item in data]
    
    def get_bookmark_by_business_id(self, business_id: str) -> Optional[Bookmark]:
        """Find a bookmark by business ID."""
        for bookmark in self.get_all_bookmarks():
            if bookmark.business_id == business_id:
                return bookmark
        return None
    
    def add_bookmark(self, business: Business) -> bool:
        """Save a business to bookmarks."""
        if self.get_bookmark_by_business_id(business.id):
            return False
        bookmark = Bookmark(
            id=f"bookmark_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            business_id=business.id,
            business_name=business.name,
            business_category=business.category,
            business_address=business.get_full_address(),
            business_rating=business.rating,
        )
        bookmarks = self.get_all_bookmarks()
        bookmarks.append(bookmark)
        return self._write_json_file(config.BOOKMARKS_FILE, [b.to_dict() for b in bookmarks])
    
    def remove_bookmark(self, business_id: str) -> bool:
        """Remove a business from bookmarks."""
        bookmarks = self.get_all_bookmarks()
        original_count = len(bookmarks)
        bookmarks = [b for b in bookmarks if b.business_id != business_id]
        if len(bookmarks) == original_count:
            return False
        return self._write_json_file(config.BOOKMARKS_FILE, [b.to_dict() for b in bookmarks])
    
    def is_bookmarked(self, business_id: str) -> bool:
        """Check if a business is bookmarked."""
        return self.get_bookmark_by_business_id(business_id) is not None
    
    # Review methods
    def get_all_reviews(self) -> List[Review]:
        """Get all reviews."""
        data = self._read_json_file(config.REVIEWS_FILE)
        return [Review.from_dict(item) for item in data]
    
    def get_reviews_by_business_id(self, business_id: str) -> List[Review]:
        """Get all reviews for a specific business."""
        return [r for r in self.get_all_reviews() if r.business_id == business_id]
    
    def add_review(self, review: Review) -> bool:
        """Add a new review."""
        reviews = self.get_all_reviews()
        reviews.append(review)
        return self._write_json_file(config.REVIEWS_FILE, [r.to_dict() for r in reviews])
    
    def remove_review(self, review_id: str) -> bool:
        """Delete a review."""
        reviews = self.get_all_reviews()
        original_count = len(reviews)
        reviews = [r for r in reviews if r.id != review_id]
        if len(reviews) == original_count:
            return False
        return self._write_json_file(config.REVIEWS_FILE, [r.to_dict() for r in reviews])


# ============================================
# GLOBAL INSTANCES
# ============================================

# Business data storage with full location support
business_storage = BusinessStorage()

# Legacy storage for bookmarks and reviews
storage = Storage()
