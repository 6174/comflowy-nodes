import json
import sys
import os

API_HOST = "https://app.comflowy.com" 
# API_HOST = "http://127.0.0.1:3000" 
PPT_TOKEN = ""
RUN_ID = ""
ENV = "pro"
# ENV = "preview"

def _read_config():
    try:
        # 首先尝试从线程上下文获取
        thread_context_module = sys.modules.get("flowy_execute_thread_context")
        if thread_context_module and hasattr(thread_context_module, "get_run_context"):
            options = thread_context_module.get_run_context("options")
            if options:
                print("get_run_context", options.get("custom_node_api_config", {}))
                return options.get("custom_node_api_config", {})
    except Exception as e:
        print(f"Error getting context from thread: {e}")

    # 回退到文件读取
    try:
        config_path = "/comfyui/custom_node_api_config.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                ret = json.load(f)
                print("read_config", ret)
                return ret
    except Exception as e:
        print(f"Error reading custom node api config file: {e}")

    # 如果都失败了，返回空字典
    return {}


def get_api_host():
    config = _read_config()
    return config.get("domain", API_HOST)

def get_modal_cloud_web_url():
    config = _read_config()
    env = config.get("env", ENV)
    if env == "dev":
        return "https://comflowy--cloud-web-dev.modal.run"
    else:
        return "https://comflowy--comflowyspacecloud-web-main.modal.run"

def get_ppt_token():
    config = _read_config()
    return config.get("ppt_token", PPT_TOKEN)

def get_run_id():
    config = _read_config()
    return config.get("run_id", RUN_ID)

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

SAFETY_TOLERANCE = ["1", "2", "3", "4", "5", "6"]

NUM_IMAGES = ["1", "2", "3", "4"]

OUTPUT_FORMAT = ["jpeg", "png"]

class AnyType(str):
    """A special class that is always equal in not equal comparisons. Credit to pythongosssss"""

    def __eq__(self, _) -> bool:
        return True

    def __ne__(self, __value: object) -> bool:
        return False

any = AnyType("*")
