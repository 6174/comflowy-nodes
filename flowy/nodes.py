import os
import json
import logging
from .types import STRING
from .api_key_manager import save_api_key

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from .nodes_omost import (
    OmostLLMNode,
    OmostToConditioning,
    ComflowyOmostPreviewNode,
    ComflowyOmostLoadCanvasPythonCodeNode,
    ComflowyOmostLoadCanvasConditioningNode,
)

from .nodes_json import FlowyPreviewJSON, FlowyExtractJSON, ComflowyLoadJSON
from .nodes_http import FlowyHttpRequest
from .nodes_llm import FlowyLLM

API_KEY_FILE = os.path.join(os.path.dirname(__file__), "api_key.json")

class ComflowySetAPIKey:
    """
    A node for setting the global Comflowy API Key.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"api_key": STRING}}
    
    RETURN_TYPES = ()
    FUNCTION = "set_api_key"
    OUTPUT_NODE = True
    CATEGORY = "Comflowy"

    def set_api_key(self, api_key):
        """
        Set the global API key for Comflowy.
        
        Args:
            api_key (str): The API key to be set.
        
        Returns:
            tuple: An empty tuple as this node doesn't produce any output.
        
        Raises:
            ValueError: If the provided API key is empty.
        """
        if not api_key.strip():
            raise ValueError("API Key cannot be empty")
        save_api_key(api_key)
        print("Comflowy API Key has been set globally")
        return ()

NODE_CLASS_MAPPINGS = {
    "Comflowy_Http_Request": FlowyHttpRequest,
    "Comflowy_LLM": FlowyLLM,
    "Comflowy_Preview_JSON": FlowyPreviewJSON,
    "Comflowy_Extract_JSON": FlowyExtractJSON,
    "Comflowy_Load_JSON": ComflowyLoadJSON,
    "Comflowy_Omost_LLM": OmostLLMNode,
    "Comflowy_Omost_To_Conditioning": OmostToConditioning,
    "Comflowy_Omost_Preview": ComflowyOmostPreviewNode,
    "Comflowy_Omost_Load_Canvas_Python_Code": ComflowyOmostLoadCanvasPythonCodeNode,
    "Comflowy_Omost_Load_Canvas_Conditioning": ComflowyOmostLoadCanvasConditioningNode,
    "Comflowy_Set_API_Key": ComflowySetAPIKey
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Comflowy_Http_Request": "Comflowy Http Request",
    "Comflowy_LLM": "Comflowy LLM",
    "Comflowy_Preview_JSON": "Comflowy Preview JSON",
    "Comflowy_Extract_JSON": "Comflowy Extract JSON",
    "Comflowy_Load_JSON": "Comflowy Load JSON",
    "Comflowy_Omost_LLM": "Comflowy Omost LLM",
    "Comflowy_Omost_To_Conditioning": "Comflowy Omost To Conditioning",
    "Comflowy_Omost_Preview": "Comflowy Omost Preview",
    "Comflowy_Omost_Load_Canvas_Python_Code": "Comflowy Omost Load Canvas Python Code",
    "Comflowy_Omost_Load_Canvas_Conditioning": "Comflowy Omost Load Canvas Conditioning",
    "Comflowy_Set_API_Key": "Comflowy Set API Key"
}
