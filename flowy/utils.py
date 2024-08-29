import logging
import requests
from .types import API_HOST

logger = logging.getLogger(__name__)

def llm_request(prompt, system_prompt, llm_model, api_key, max_tokens=3000, timeout=10):
    """
    Send a request to the Comflowy LLM API.
    
    Args:
        prompt (str): The main prompt for the LLM.
        system_prompt (str): The system prompt for the LLM.
        llm_model (str): The LLM model to use.
        api_key (str): The API key for authentication.
        max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 3000.
        timeout (int, optional): Timeout for the request in seconds. Defaults to 10.
    
    Returns:
        str: The generated text from the LLM.
    
    Raises:
        Exception: If there's an error in the API request or response.
    """
    try:
        response = requests.post(
            f"{API_HOST}/api/open/v0/prompt",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "prompt": prompt,
                "system_prompt": system_prompt,
                "model": llm_model,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )

        response.raise_for_status()  # Raise an HTTPError for bad responses

        ret = response.json()
        if ret.get("success"):
            return ret.get("text")
        else:
            raise Exception(f"Error: {ret.get('error')}")
    except Exception as e:
        raise Exception(f"Failed to get response from LLM model with {API_HOST}/api/open/v0/prompt, error: {str(e)}")

def get_nested_value(obj, path, default=None):
    """
    Get a nested value from a dictionary using a dot-separated path.
    
    Args:
        obj (dict): The dictionary to search in.
        path (str): The dot-separated path to the desired value.
        default: The value to return if the path is not found.
    
    Returns:
        The value at the specified path, or the default value if not found.
    """
    keys = path.split('.')
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key, default)
        else:
            return default
    return obj

# Make sure to export the functions
__all__ = ['llm_request', 'get_nested_value']
