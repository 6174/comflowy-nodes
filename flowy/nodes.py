
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
}
