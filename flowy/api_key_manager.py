import os
import json
import logging

logger = logging.getLogger(__name__)

API_KEY_FILE = os.path.join(os.path.dirname(__file__), "api_key.json")

def save_api_key(api_key):
    """
    Save the API key to a JSON file.
    
    Args:
        api_key (str): The API key to be saved.
    """
    try:
        with open(API_KEY_FILE, "w") as f:
            json.dump({"api_key": api_key}, f)
        logger.debug(f"API Key saved to {API_KEY_FILE}")
    except Exception as e:
        logger.error(f"Failed to save API Key: {str(e)}")

def load_api_key():
    """
    Load the API key from the JSON file.
    
    Returns:
        str or None: The loaded API key, or None if not found or an error occurred.
    """
    try:
        if os.path.exists(API_KEY_FILE):
            with open(API_KEY_FILE, "r") as f:
                data = json.load(f)
                return data.get("api_key")
    except Exception as e:
        logger.error(f"Failed to load API Key: {str(e)}")
    return None
