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

class FlowyUpscale:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "scale_factor": ("INT", {"default": 2, "min": 1, "max": 4, "step": 1}),
                "model": (["clarity-upscaler"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "upscale"
    CATEGORY = "Comflowy"
    DESCRIPTION = """
Nodes from https://comflowy.com: 
- Description: A service to upscale images using AI models.
- How to use: 
    - Provide an image to upscale.
    - Choose the scale factor and the upscaling model.
    - Make sure to set your API Key using the 'Comflowy Set API Key' node before using this node.
- Output: Returns the upscaled image.
"""

    def upscale(self, image, scale_factor, model):
        api_key = load_api_key()
        
        if not api_key:
            error_msg = "API Key is not set. Please use the 'Comflowy Set API Key' node to set a global API Key before using this node."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"开始处理图像放大请求。scale_factor: {scale_factor}, model: {model}")

        # 处理输入图像
        if isinstance(image, torch.Tensor):
            if image.dim() == 4:
                image = image.squeeze(0)  # 移除批次维度
            if image.shape[-1] == 3:
                image = (image.cpu().numpy() * 255).astype(np.uint8)
            elif image.shape[0] == 3:
                image = (image.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
            else:
                raise ValueError(f"Unsupported image shape: {image.shape}")
        elif isinstance(image, np.ndarray):
            if image.ndim == 2:
                image = np.stack([image] * 3, axis=-1)
            elif image.shape[-1] == 1:
                image = np.repeat(image, 3, axis=-1)
            elif image.shape[-1] != 3:
                raise ValueError(f"Unsupported number of channels: {image.shape[-1]}")
            image = (image * 255).astype(np.uint8)
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        # 将输入图像转换为 JPEG 格式并压缩
        buffered = io.BytesIO()
        Image.fromarray(image).save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        try:
            # 使用 API_HOST 构建 API 请求的 URL
            response = requests.post(
                f"{API_HOST}/api/open/v0/upscale",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "image": f"data:image/jpeg;base64,{img_str}",
                    "scale_factor": scale_factor,
                    "model": model
                }
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"API 请求完成。状态码: {response.status_code}")
            logger.debug(f"API 响应内容: {json.dumps(result, indent=2)}")

            if not result.get('success'):
                logger.error(f"API 请求失败。响应内容: {json.dumps(result, indent=2)}")
                raise Exception(f"API 请求失败。响应内容: {json.dumps(result, indent=2)}")

            output_url = result.get('data', {}).get('output', [None])[0]
            if not output_url:
                logger.error(f"完整的 API 响应: {json.dumps(result, indent=2)}")
                raise Exception(f"无法获取输出图像 URL。API 响应中没有预期的数据结构。完整响应: {json.dumps(result, indent=2)}")

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
            logger.info(f"API 请求完成。状态码: {response.status_code}")
            logger.debug(f"API 响应内容: {response.text}")

            return (img_tensor,)

        except Exception as e:
            error_msg = f"放大过程中出错: {str(e)}"
            logger.error(error_msg)
            logger.exception("详细错误信息:")
            # 返回一个错误标记图像，确保形状为 [B,H,W,C]
            error_image = torch.zeros((1, 100, 400, 3), dtype=torch.float32)
            return (error_image,)
