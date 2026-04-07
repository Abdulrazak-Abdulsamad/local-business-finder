
from dataclasses import dataclass, field, asdict
from datetime import datetime

@dataclass
class Business:
    """
    A local business that users can search for and review.
    
    Each business has basic info like name, address, and rating.
    The @dataclass decorator automatically creates common methods
    like __init__ and __repr__ for us.
    """
    
    # Basic information
    id: str                    
    name: str                  
    category: str             
    
    # Location information
    address: str               
    city: str                  
    state: str                 
    zip_code: str              
    
    # Contact information
    phone: str                 
    
    # Rating and popularity
    rating: float = 0.0        
    review_count: int = 0      
    
    # Additional details
    distance: float = 0.0      
    price_level: str = "$"     
    is_open: bool = True       
    image_url: str = ""        
    description: str = ""      
    
    # Map coordinates (for showing on a map)
    latitude: float = 0.0
    longitude: float = 0.0
    
    def to_dict(self):
        """
        Convert this business to a dictionary.
        Useful for saving to JSON files.
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Business from a dictionary.
        Useful for loading from JSON files.
        """
        return cls(**data)
    
    def get_full_address(self):
        """Get the complete address as one line."""
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}"
    
    def get_rating_stars(self):
        """
        Get star symbols for the rating.
        Example: 4.5 rating becomes "★★★★½"
        """
        full_stars = int(self.rating)           
        half_star = 1 if (self.rating - full_stars) >= 0.5 else 0  
        empty_stars = 5 - full_stars - half_star  
        return "★" * full_stars + "½" * half_star + "☆" * empty_stars



# REVIEW CLASS
# This represents a user's review of a business

@dataclass
class Review:
    """
    A review written by a user about a business.
    
    Reviews help other users decide which businesses to visit.
    """
    
    id: str                    
    business_id: str           
    business_name: str         
    user_name: str             
    rating: int                
    text: str                  
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        """Convert this review to a dictionary for saving."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        """Create a Review from a dictionary."""
        return cls(**data)
    
    def get_rating_stars(self):
        """Get star symbols for the rating."""
        return "★" * self.rating + "☆" * (5 - self.rating)
    
    def get_formatted_date(self):
        """
        Get a nice formatted date string.
        Example: "March 31, 2026 at 02:30 PM"
        """
        try:
            dt = datetime.fromisoformat(self.created_at)
            return dt.strftime("%B %d, %Y at %I:%M %p")
        except (ValueError, TypeError):
            return self.created_at



# BOOKMARK CLASS
# This represents a saved/bookmarked business

@dataclass
class Bookmark:
    """
    A business that a user has saved for quick access.
    
    Bookmarks let users quickly find businesses they like
    without searching again.
    """
    
    id: str                    
    business_id: str           
    business_name: str       
    business_category: str    
    business_address: str      
    business_rating: float     
    bookmarked_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        """Convert this bookmark to a dictionary for saving."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        """Create a Bookmark from a dictionary."""
        return cls(**data)
    
    def get_rating_stars(self):
        """Get star symbols for the rating."""
        full_stars = int(self.business_rating)
        half_star = 1 if (self.business_rating - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        return "★" * full_stars + "½" * half_star + "☆" * empty_stars
    
    def get_formatted_date(self):
        """Get a nice formatted date string."""
        try:
            dt = datetime.fromisoformat(self.bookmarked_at)
            return dt.strftime("%B %d, %Y at %I:%M %p")
        except (ValueError, TypeError):
            return self.bookmarked_at
