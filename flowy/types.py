import sys

API_HOST = "https://app.comflowy.com" 
# API_HOST = "http://127.0.0.1:3000" 
FLOAT = (
    "FLOAT",
    {"default": 1, "min": -sys.float_info.max, "max": sys.float_info.max, "step": 0.01},
)

BOOLEAN = ("BOOLEAN", {"default": True})
BOOLEAN_FALSE = ("BOOLEAN", {"default": False})

INT = ("INT", {"default": 1, "min": -sys.maxsize, "max": sys.maxsize, "step": 1})

STRING = ("STRING", {"default": ""})

STRING_ML = ("STRING", {"multiline": True, "default": ""})

STRING_WIDGET = ("STRING", {"forceInput": True})

JSON_WIDGET = ("JSON", {"forceInput": True})

METADATA_RAW = ("METADATA_RAW", {"forceInput": True})

HTTP_REQUEST_METHOD = ["GET", "POST", "PUT", "DELETE", "PATCH"]

HTTP_REQUEST_TYPE = ["application/json", "application/x-www-form-urlencoded", "multipart/form-data"]

HTTP_REQUEST_RETURN_TYPE = ["TEXT", "JSON"]

LLM_MODELS = [
  "Qwen/Qwen2-7B-Instruct",
  "Qwen/Qwen2-1.5B-Instruct",
  "THUDM/glm-4-9b-chat",
  "THUDM/chatglm3-6b",
  "01-ai/Yi-1.5-9B-Chat-16K",
  "01-ai/Yi-1.5-6B-Chat",
  "internlm/internlm2_5-7b-chat"
]

SAFETY_TOLERANCE = ["1", "2", "3", "4", "5"]

class AnyType(str):
    """A special class that is always equal in not equal comparisons. Credit to pythongosssss"""

    def __eq__(self, _) -> bool:
        return True

    def __ne__(self, __value: object) -> bool:
        return False

any = AnyType("*")
