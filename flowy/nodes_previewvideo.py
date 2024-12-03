import os
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)

class PreviewVideo:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "video": ("VIDEO",),
        }}

    CATEGORY = "Comflowy"
    DESCRIPTION = "Preview Video Node"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "load_video"

    def load_video(self, video):
        logger.info(f"PreviewVideo.load_video called with video: {video}")
        logger.info(f"Video type: {type(video)}")

        # 确保视频路径是有效的字符串
        if not video or not isinstance(video, str):
            logger.error(f'Invalid video path or type: {video}')
            return {"ui": {"video": ["error.mp4", "output"]}}

        # 检查文件是否存在
        if not os.path.exists(video):
            logger.error(f'Video file does not exist at path: {video}')
            return {"ui": {"video": ["error.mp4", "output"]}}

        # 获取完整的视频文件名和目录
        video_filename = os.path.basename(video)
        video_dir = os.path.dirname(video)
        
        logger.info(f'Video filename: {video_filename}')
        logger.info(f'Video directory: {video_dir}')
        logger.info(f'Full video path: {video}')
        logger.info(f'File exists: {os.path.exists(video)}')
        logger.info(f'File size: {os.path.getsize(video)} bytes')
        
        result = {"ui": {"video": [video, video_dir]}}
        logger.info(f'Returning result: {result}')
        
        return result