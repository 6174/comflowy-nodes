import json
import requests

# You can use this node to save full size images through the websocket, the
# images will be sent in exactly the same format as the image previews: as
# binary images on the websocket with a 8 byte header indicating the type
# of binary message (first 4 bytes) and the image format (next 4 bytes).

# Note that no metadata will be put in the images saved with this node.
from .types import (
    HTTP_REQUEST_METHOD,
    STRING,
    STRING_ML,
)

class FlowyHttpRequest:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"url": STRING, "method": (HTTP_REQUEST_METHOD,)},
            "optional": {
                "headers_json": STRING_ML,
                "body_json": STRING_ML,
                # "json_path": STRING,
            },
        }

    RETURN_TYPES = ("JSON",)
    FUNCTION = "send_http_request"
    OUTPUT_NODE = True
    CATEGORY = "Comflowy"
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: Send an HTTP request to a URL.
- Output: Return a JSON result from the request.
"""

    def send_http_request(self, url, method, headers_json, body_json):
        try:
            timeout = 10
            try:
                headers = json.loads(headers_json) if headers_json else {}
                body = json.loads(body_json) if body_json else {}
            except Exception as e:
                raise ValueError(f"Invalid headers or body: {e}")
            print("http request with", url, headers, body)

            response = None
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(
                    url, headers=headers, json=body, timeout=timeout
                )
            elif method == "PUT":
                response = requests.put(
                    url, headers=headers, json=body, timeout=timeout
                )
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            elif method == "PATCH":
                response = requests.patch(
                    url, headers=headers, json=body, timeout=timeout
                )
            else:
                raise ValueError(f"Invalid method {method}")

            response.raise_for_status()  # Raise an HTTPError for bad responses

            ret = response.json()

            print("http request result", ret)
            # if json_path:
            #     print("json_path", json_path)
            #     ret = get_nested_value[json_path]

            return {"ui": {"text": [json.dumps(ret, indent=4)]}, "result": (ret,)}

        except requests.exceptions.RequestException as e:
            print("http request error", e)
            return {"ui": {"text": [str(e)]}, "result": (str(e),)}
