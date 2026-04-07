import streamlit as st
import sys
import os

# Add the application directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main function from ui.py 
from ui import main as app_main

# Run the application when executed directly
if __name__ == "__main__":
    app_main()
