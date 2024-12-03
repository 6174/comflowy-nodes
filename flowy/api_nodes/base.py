from abc import ABC, abstractmethod
import time
import requests
import base64
import io
from PIL import Image
import torch
import numpy as np
import logging
import json
import os
from ..types import get_api_host
from ..api_key_manager import load_api_key
import soundfile as sf

import folder_paths

logger = logging.getLogger(__name__)

class FlowyApiNode(ABC):
    CATEGORY = "Comflowy"
    FUNCTION = "generate"
    RETURN_TYPES = []

    @classmethod
    @abstractmethod
    def INPUT_TYPES(cls):
        """Define input types for the node"""
        pass

    # 返回模型类型标识符
    @abstractmethod
    def get_model_type(self) -> str:
        """Return the model type identifier"""
        pass

    # 准备 API 请求的 payload
    @abstractmethod
    def prepare_payload(self, **kwargs) -> dict:
        """Prepare the API request payload"""
        pass

    # 返回请求需要的 API URL, 默认是 /api/open/v0/flowy, 如果是特殊模型, 则子类返回特殊模型的 API URL
    def get_api_host(self) -> str:
        API_HOST = get_api_host()
        API_URL = f"{API_HOST}/api/open/v0/flowy"
        return API_URL

    # 从 URL 下载图片并转换为 tensor
    def parse_image_output(self, output_url: str) -> torch.Tensor:
        """Convert image URL to tensor"""
        start_time = time.time()
        for attempt in range(3):
            try:
                img_response = requests.get(output_url, stream=True)
                img_response.raise_for_status()
                break
            except requests.RequestException as e:
                if attempt == 2:  # Last attempt
                    logger.error(f"Unable to access output URL after 3 attempts: {str(e)}")
                    raise Exception(f"Unable to access output URL: {str(e)}")
                logger.warning(f"Attempt {attempt + 1} failed, retrying in 1s...")
                time.sleep(1)

        logger.info(f"[Timing] Image download took {time.time() - start_time:.2f}s")
        download_start = time.time()

        logger.info(f"[Timing] Image download took {time.time() - download_start:.2f}s")
        process_start = time.time()

        # Convert image data to PIL Image
        img = Image.open(img_response.raw)

        # Convert to numpy array
        img_np = np.array(img)

        # Ensure image has 3 RGB channels
        if len(img_np.shape) == 2:  # Grayscale image
            img_np = np.stack([img_np] * 3, axis=-1)
        elif img_np.shape[-1] == 4:  # RGBA image
            img_np = img_np[:, :, :3]

        # Convert to float32 and normalize to 0-1 range
        img_np = img_np.astype(np.float32) / 255.0

        # Convert to torch tensor, ensure shape is [B,H,W,C]
        img_tensor = torch.from_numpy(img_np).unsqueeze(0)  # Add batch dimension

        logger.info(f"[Timing] Image processing took {time.time() - process_start:.2f}s")
        logger.info(f"[Timing] Total image parsing took {time.time() - start_time:.2f}s")

        return img_tensor

    # 从 URL 下载视频并返回本地路径
    def parse_video_output(self, output_url: str) -> str:
        """Download video from URL and return local path"""
        output_dir = folder_paths.get_output_directory()
        curr_time = time.time()
        vid_name = f"output_{curr_time}.mp4"
        output_video_path = os.path.join(output_dir, vid_name)

        response = requests.get(output_url)
        response.raise_for_status()

        with open(output_video_path, "wb") as f:
            f.write(response.content)

        return output_video_path
    
    def parse_audio_output(self, output_url: str) -> str:
        """Download audio from URL and return local path"""
        output_dir = folder_paths.get_output_directory()
        curr_time = time.time()
        audio_name = f"output_{curr_time}.wav"
        output_audio_path = os.path.join(output_dir, audio_name)

        response = requests.get(output_url)
        response.raise_for_status()

        with open(output_audio_path, "wb") as f:
            f.write(response.content)

        return output_audio_path

    # 处理输入图像
    def image_to_base64(self, image) -> str:
        """Process input image to base64 string"""
        if isinstance(image, torch.Tensor):
            if image.dim() == 4:
                image = image.squeeze(0)  # Remove batch dimension
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

        buffered = io.BytesIO()
        Image.fromarray(image).save(buffered, format="JPEG", quality=85)
        return (
            f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"
        )

    def audio_to_base64(self, audio):
        if isinstance(audio, dict) and "waveform" in audio and "sample_rate" in audio:
            waveform = audio["waveform"]
            sample_rate = audio["sample_rate"]
        else:
            waveform, sample_rate = audio

        # Ensure waveform is 2D
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)
        elif waveform.dim() > 2:
            waveform = waveform.squeeze()
            if waveform.dim() > 2:
                raise ValueError("Waveform must be 1D or 2D")

        buffer = io.BytesIO()
        sf.write(buffer, waveform.numpy().T, sample_rate, format="wav")
        buffer.seek(0)
        audio_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:audio/wav;base64,{audio_str}"

    # 发送 API 请求
    def make_api_request(self, payload: dict):
        """Make API request and return response"""
        api_key = load_api_key()
        if not api_key:
            raise ValueError(
                "API Key is not set. Please use the 'Comflowy Set API Key' node first."
            )

        API_URL = self.get_api_host()
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    # 主生成方法
    def generate(self, **kwargs):
        """Main generation method"""
        try:
            start_time = time.time()
            
            # Prepare payload with common fields
            payload = self.prepare_payload(**kwargs)
            payload["model_type"] = self.get_model_type()
            
            logger.info(f"[Timing] Payload preparation took {time.time() - start_time:.2f}s")
            api_start = time.time()

            # Make API request
            result = self.make_api_request(payload)
            
            logger.info(f"[Timing] API request took {time.time() - api_start:.2f}s")

            if not result.get("success"):
                raise Exception(
                    f"API request failed. Response: {json.dumps(result, indent=2)}"
                )

            output_urls = result.get("data", {}).get("output")
            if not output_urls or not isinstance(output_urls, list):
                raise Exception(
                    f"Invalid output URLs in response: {json.dumps(result, indent=2)}"
                )

            parse_start = time.time()
            
            # Handle different return types based on RETURN_TYPES
            if self.RETURN_TYPES[0] == "IMAGE":
                if len(output_urls) == 1:
                    # 单个图像，直接返回
                    result = (self.parse_image_output(output_urls[0]),)
                else:
                    # 多个图像，合并成一个批次
                    tensors = [self.parse_image_output(url) for url in output_urls]
                    result = (torch.cat(tensors, dim=0),)
            elif self.RETURN_TYPES[0] == "VIDEO":
                if len(output_urls) == 1:
                    result = (self.parse_video_output(output_urls[0]),)
                else:
                    result = tuple(self.parse_video_output(url) for url in output_urls)
            elif self.RETURN_TYPES[0] == "AUDIO":
                if len(output_urls) == 1:
                    result = (self.parse_audio_output(output_urls[0]),)
                else:
                    result = tuple(self.parse_audio_output(url) for url in output_urls)
            elif self.RETURN_TYPES[0] == "STERING":
                if len(output_urls) == 1:
                    result = (output_urls[0],)
                else:
                    result = tuple(output_urls)
            else:
                raise ValueError(f"Unsupported return type: {self.RETURN_TYPES[0]}")
            
            logger.info(f"[Timing] Output parsing took {time.time() - parse_start:.2f}s")
            logger.info(f"[Timing] Total generation took {time.time() - start_time:.2f}s")
            
            return result

        except Exception as e:
            logger.error(f"Error during generation: {str(e)}")
            logger.exception("Detailed error information:")

            if self.RETURN_TYPES[0] == "IMAGE":
                return (torch.zeros((1, 100, 400, 3), dtype=torch.float32),)
            elif self.RETURN_TYPES[0] == "VIDEO":
                return (os.path.join("output", "error.mp4"),)
            elif self.RETURN_TYPES[0] == "AUDIO":
                return (os.path.join("output", "error.wav"),)
            elif self.RETURN_TYPES[0] == "STERING":
                return (str(e),)
            else:
                raise ValueError(f"Unsupported return type: {self.RETURN_TYPES[0]}")
