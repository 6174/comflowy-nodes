import logging
import requests

from .types import API_HOST

logger = logging.getLogger("Comflowy")

def get_nested_value(data, json_path):
    keys = json_path.split(".")
    for key in keys:
        if key.isdigit():
            key = int(key)
        data = data[key]
    return data


def llm_request(prompt, system_prompt, llm_model, api_key, max_tokens=3000, timeout=10):
    try:
        response = None
        url = f"{API_HOST}/api/open/v0/llm"
        response = requests.post(
            url,
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
            text = ret.get("text")
            return text
        else:
            raise Exception(f"Error: {ret.get('error')}")
    except Exception as e:
        logger.warn(e)
        raise Exception(f"Failed to get response from LLM model with {url}, error: {str(e)}")
