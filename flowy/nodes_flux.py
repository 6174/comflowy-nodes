import time
import requests
import base64
import io
from PIL import Image
import torch
import numpy as np
import logging
import json
from .types import STRING, INT, API_HOST
from .utils import logger, get_nested_value
from .api_key_manager import load_api_key

logger = logging.getLogger(__name__)

class ComflowyFlux:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "version": (["flux-1.1-pro", "flux-pro"],),
                "aspect_ratio": ([
                    "custom",
                    "1:1",
                    "16:9",
                    "2:3",
                    "3:2",
                    "4:5",
                    "5:4",
                    "9:16",
                    "3:4",
                    "4:3"
                ],),
                "height": ("INT", {"default": 256, "min": 256, "max": 1440}),
                "width": ("INT", {"default": 256, "min": 256, "max": 1440}),
                "prompt_upsampling": (["Off", "On"],),
                "safety_tolerance": ([
                    "1",
                    "2",
                    "3",
                    "4",
                    "5"
                ]),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2147483647}), 
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image_with_flux"
    CATEGORY = "Comflowy"
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to generate images using Flux AI.
- How to use: 
    - Provide a prompt to generate an image.
    - Choose version, aspect ratio, height, width, and seed.
    - Height and width are only used when aspect_ratio=custom. Must be a multiple of 32 (if it's not, it will be rounded to nearest multiple of 32). 
    - Prompt Upsampling: Automatically modify the prompt for more creative generation.
    - Safety tolerance, 1 is most strict and 5 is most permissive.
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
- Output: Returns the generated image.
"""

    def generate_image_with_flux(self, prompt, version, aspect_ratio, height, width, seed, prompt_upsampling, safety_tolerance):
        api_key = load_api_key()
        
        if not api_key:
            error_msg = "API Key is not set. Please use the 'Comflowy Set API Key' node to set a global API Key before using this node."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"开始处理 Flux 图像生成请求。prompt: {prompt}, version: {version}, aspect_ratio: {aspect_ratio}, height: {height}, width: {width}, seed: {seed}, prompt_upsampling: {prompt_upsampling}, safety_tolerance: {safety_tolerance}")

        try:
            response = requests.post(
                f"{API_HOST}/api/open/v0/flux",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "prompt": prompt,
                    "version": version, 
                    "aspect_ratio": aspect_ratio,
                    "height": height,
                    "width": width,
                    "prompt_upsampling": prompt_upsampling,
                    "safety_tolerance": safety_tolerance,
                    "seed": seed,
                }
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"API 请求完成。状态码: {response.status_code}")
            logger.debug(f"API 响应内容: {json.dumps(result, indent=2)}")

            if not result.get('success'):
                logger.error(f"API 请求失败。响应内容: {json.dumps(result, indent=2)}")
                raise Exception(f"API 请求失败。响应内容: {json.dumps(result, indent=2)}")

            output_url = result.get('data', {}).get('output')
            if not output_url or not isinstance(output_url, str):
                logger.error(f"完整的 API 响应: {json.dumps(result, indent=2)}")
                raise Exception(f"无法获取有效的输出图像 URL。API 响应中没有预期的数据结构。完整响应: {json.dumps(result, indent=2)}")

            logger.info(f"获取到的输出 URL: {output_url}")

            # 验证 URL 是否可访问
            try:
                url_check = requests.head(output_url)
                url_check.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"无法访问输出 URL: {str(e)}")
                raise Exception(f"无法访问输出 URL: {str(e)}")

            # 添加延迟,等待 Replicate 处理完成
            time.sleep(10)

            img_response = requests.get(output_url, stream=True)
            img_response.raise_for_status()

            # 将图像数据转换为 PIL Image
            img = Image.open(img_response.raw)

            # 转换为 numpy 数组
            img_np = np.array(img)

            # 确保图像是 3 通道 RGB
            if len(img_np.shape) == 2:  # 灰度图像
                img_np = np.stack([img_np] * 3, axis=-1)
            elif img_np.shape[-1] == 4:  # RGBA 图像
                img_np = img_np[:, :, :3]

            # 转换为 float32 并归一化到 0-1 范围
            img_np = img_np.astype(np.float32) / 255.0

            # 转换为 torch tensor，确保形状为 [B,H,W,C]
            img_tensor = torch.from_numpy(img_np).unsqueeze(0)  # 添加批次维度

            logger.info(f"图像处理完成。输出张量形状: {img_tensor.shape}")

            return (img_tensor,)

        except Exception as e:
            error_msg = f"图像生成过程中出错: {str(e)}"
            logger.error(error_msg)
            logger.exception("详细错误信息:")
            # 返回一个错误标记图像，确保形状为 [B,H,W,C]
            error_image = torch.zeros((1, 100, 400, 3), dtype=torch.float32)
            return (error_image,)
