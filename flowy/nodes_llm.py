import requests

# You can use this node to save full size images through the websocket, the
# images will be sent in exactly the same format as the image previews: as
# binary images on the websocket with a 8 byte header indicating the type
# of binary message (first 4 bytes) and the image format (next 4 bytes).

# Note that no metadata will be put in the images saved with this node.
from .types import (
    API_HOST,
    LLM_MODELS,
    STRING,
    STRING_ML,
)
from .utils import llm_request, logger

class FlowyLLM:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": STRING_ML,
                "system_prompt": STRING_ML,
                "llm_model": (LLM_MODELS,),
                "api_key": STRING,
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "llm_request"
    OUTPUT_NODE = True
    CATEGORY = "Comflowy"
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A free service to send a prompt to a LLM model, and get the response. 
- How to use: 
    - Provide a prompt and a system prompt to generate a response from the LLM model.
    - Choose the LLM model from the available options.
- Output: Return the generated text from the LLM model.
"""

    def llm_request(self, prompt, system_prompt, llm_model, api_key, seed, timeout=10):
        if seed > 0xFFFFFFFF:
            seed = seed & 0xFFFFFFFF
            logger.warning("Seed is too large. Truncating to 32-bit: %d", seed)
        try:
            generated_text = llm_request(
                prompt=prompt, 
                llm_model=llm_model, 
                system_prompt=system_prompt, 
                api_key=api_key, 
                max_tokens=4000, 
                timeout=10
            )
            return {"ui": {"text": [generated_text]}, "result": (generated_text,)}
        except Exception as e:
            return {"ui": {"text": [str(e)]}, "result": (str(e),)}