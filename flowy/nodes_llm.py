import logging
from .api_key_manager import load_api_key
from .types import (
    API_HOST,
    LLM_MODELS,
    STRING,
    STRING_ML,
)
from .utils import llm_request

logger = logging.getLogger(__name__)

class FlowyLLM:
    """
    A node for making requests to the Comflowy LLM service.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": STRING_ML,
                "system_prompt": STRING_ML,
                "llm_model": (LLM_MODELS,),
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
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
- Output: Return the generated text from the LLM model.
"""

    def llm_request(self, prompt, system_prompt, llm_model, seed, timeout=10):
        """
        Make a request to the Comflowy LLM service.
        
        Args:
            prompt (str): The main prompt for the LLM.
            system_prompt (str): The system prompt for the LLM.
            llm_model (str): The LLM model to use.
            seed (int): The seed for random number generation.
            timeout (int, optional): Timeout for the request in seconds. Defaults to 10.
        
        Returns:
            dict: A dictionary containing the UI output and the result.
        """
        if seed > 0xFFFFFFFF:
            seed = seed & 0xFFFFFFFF
            logger.warning("Seed is too large. Truncating to 32-bit: %d", seed)
        
        api_key = load_api_key()
        
        if not api_key:
            error_msg = "API Key is not set. Please use the 'Comflowy Set API Key' node to set a global API Key before using this node."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
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
            logger.error(f"Error in LLM request: {str(e)}")
            return {"ui": {"text": [str(e)]}, "result": (str(e),)}