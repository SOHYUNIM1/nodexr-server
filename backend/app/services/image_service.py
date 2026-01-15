import uuid
from typing import List

class ImageService:
    """
    NanoBanana + MinIO 연동 자리.
    지금은 더미 URL 3개를 생성.
    """
    def generate_images(self, prompt: str, n: int = 3) -> List[str]:
        return [f"https://dummy.local/{uuid.uuid4()}.png" for _ in range(n)]

image_service = ImageService()