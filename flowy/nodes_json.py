import json
from typing import Tuple

# You can use this node to save full size images through the websocket, the
# images will be sent in exactly the same format as the image previews: as
# binary images on the websocket with a 8 byte header indicating the type
# of binary message (first 4 bytes) and the image format (next 4 bytes).

# Note that no metadata will be put in the images saved with this node.
from .types import (
    STRING,
)
from .utils import get_nested_value, logger

class FlowyExtractJSON:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"json_value": ("JSON",)},
            "optional": {
                "json_path1": STRING,
                "json_path2": STRING,
                "json_path3": STRING,
                "json_path4": STRING,
                "json_path5": STRING,
            },
        }

    CATEGORY = "Comflowy"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("text1", "text2", "text3", "text4", "text5")
    OUTPUT_NODE = True
    FUNCTION = "extract_json"
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: Extract values from a JSON object.
- How to use: Provide a JSON object and the json_path to extract the value.
    - eg1. json_path: "a.b.c"
    - eg2. json_path: "outputs.0.text" if there is an array in the json object.
- Output: All output values are strings, according to the provided `json_path`, if the target json_path is not a string, will return the json dump value.
- Note: If the json_path is not found, it will return an error string.
"""

    def extract_json(
        self,
        json_value=None,
        json_path1=None,
        json_path2=None,
        json_path3=None,
        json_path4=None,
        json_path5=None,
    ):
        ret = ["", "", "", "", ""]
        paths = [json_path1, json_path2, json_path3, json_path4, json_path5]
        # return {"ui": {"text": [text]}, "result": (text,)}
        if json_value is not None:
            for i, path in enumerate(paths):
                if path:
                    try:
                        ret[i] = json.dumps(
                            get_nested_value(json_value, path), indent=4
                        )
                    except Exception as e:
                        ret[i] = f"Extract error: {e}"
                        logger.warn(e)

        logger.info(f"Extract json is running: {ret}")
        all_text = "\n".join(ret)
        return {"ui": {"text": [all_text]}, "result": tuple(ret)}


class FlowyPreviewJSON:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"json_value": ("JSON",)},
        }

    CATEGORY = "Comflowy"
    RETURN_TYPES = ("STRING",)
    OUTPUT_NODE = True
    FUNCTION = "preview_json"
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: Show a JSON in a human-readable format.
- Output: Return a JSON object as a string.
"""

    def preview_json(self, json_value=None):
        text = ""
        logger.info(f"preview json", json_value)
        # return {"ui": {"text": [text]}, "result": (text,)}
        if json_value is not None:
            if isinstance(json_value, dict):
                try:
                    text = json.dumps(json_value, indent=4)
                except Exception as e:
                    text = "The input is a dict, but could not be serialized.\n"
                    logger.warn(e)

            elif isinstance(json_value, list):
                try:
                    text = json.dumps(json_value, indent=4)
                except Exception as e:
                    text = "The input is a list, but could not be serialized.\n"
                    logger.warn(e)

            else:
                text = str(json_value)

        return {"ui": {"text": [text]}, "result": (text,)}


class ComflowyLoadJSON:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "json_str": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("JSON",)
    FUNCTION = "load_json"
    CATEGORY = "Comflowy"

    def load_json(self, json_str: str) -> Tuple[list[any]]:
        """Load canvas from file"""
        return (json.loads(json_str),)
