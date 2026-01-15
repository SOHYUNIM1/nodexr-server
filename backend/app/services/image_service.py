import io
import logging
import asyncio
from uuid import UUID
from PIL import Image
from io import BytesIO
from typing import List

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

# 프로젝트 내부 모듈 (경로에 맞춰 수정 필요)
from app.db.models.node import Node
from app.db.models.asset import Asset
from app.storage.minio import upload_image_bytes

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        # API Key는 환경변수에 설정되어 있어야 합니다.
        self.client = genai.Client()

    async def generate_images(self, prompt: str, n: int = 3, db: Session = None, node_id: UUID = None) -> List[str]:
        """
        prompt를 첫 번째 인자로 배치하여 기존 호출부와의 호환성을 높인 버전
        """
        logger.info(f"[NANO_BANANA] {n}개 이미지 생성 프로세스 시작")

        tasks = [self._generate_single_image(prompt) for _ in range(n)]
        image_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_urls = []
        for res in image_results:
            if isinstance(res, str) and (res.startswith("http")or "minio" in res):
                valid_urls.append(res)
                # db와 node_id가 모두 있을 때만 저장 수행
                if db and node_id:
                    self._save_asset_to_db(db, node_id, res)
            else:
                logger.error(f"[IMAGE_GEN_ERROR] 단일 생성 실패: {res}")

        if db and node_id:
            db.commit() 
            
        return valid_urls
    
    async def _generate_single_image(self, prompt: str) -> str:
        """API를 호출하여 1장의 이미지를 생성하고 MinIO URL을 반환"""
        try:
            # 런타임 루프를 방해하지 않기 위해 run_in_executor 등으로 감쌀 수 있으나
            # SDK가 내부적으로 비동기를 지원하지 않을 경우를 대비해 직접 호출
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=prompt,
                config=types.GenerateContentConfig(
                    candidate_count=1, # 모델 제약상 1 고정
                    response_modalities=["IMAGE"]
                ),
            )

            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                if part.inline_data:
                    # 이미지 바이트 추출 및 PIL 변환
                    image = Image.open(io.BytesIO(part.inline_data.data))
                    # MinIO 업로드
                    return self._save_image_to_minio(image)
            
            return ""
        except Exception as e:
            logger.error(f"[SINGLE_GEN_FAIL] {e}")
            return str(e)

    async def generate_category_images(self, db: Session, prompt: str, n: int, room_id: UUID, node_id: UUID) -> List[str]:
        """
        기존 Core Image를 참조하여 카테고리 이미지를 n장 비동기로 생성
        """
        # 1. 기준 이미지 URL 가져오기
        core_image_url = self._get_core_image_url(db, room_id)
        if not core_image_url:
            logger.warning("[CATEGORY_IMAGE] 기준 이미지가 없어 생성을 중단합니다.")
            return []

        logger.info(f"[CATEGORY_IMAGE] 기준 이미지 참조하여 {n}개 생성 시작")

        # 2. 비동기 태스크 생성 (n번 호출)
        tasks = [self._generate_single_category_image(prompt, core_image_url) for _ in range(n)]
        
        # 3. 병렬 실행 및 결과 취합
        image_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_urls = []
        for res in image_results:
            if isinstance(res, str) and res.startswith("http"):
                valid_urls.append(res)
                # 4. DB 저장
                self._save_asset_to_db(db, node_id, res, asset_type="CATEGORY_CANDIDATE")
            else:
                logger.error(f"[CATEGORY_GEN_ERROR] 단일 생성 실패: {res}")

        db.commit() # 전체 성공/실패 여부 관계없이 유효한 것들 커밋
        return valid_urls

    async def _generate_single_category_image(self, prompt: str, core_image_url: str) -> str:
        """기존 이미지를 참조하여 1장의 이미지를 생성하고 MinIO URL 반환"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[
                    prompt,
                    types.Part.from_uri(file_uri=core_image_url, mime_type="image/png")
                ],
                config=types.GenerateContentConfig(
                    candidate_count=1,
                    response_modalities=["IMAGE"]
                ),
            )

            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                if part.inline_data:
                    image = Image.open(io.BytesIO(part.inline_data.data))
                    return self._save_image_to_minio(image)
            
            return ""
        except Exception as e:
            logger.error(f"[SINGLE_CATEGORY_FAIL] {e}")
            return str(e)

    def _get_core_image_url(self, db: Session, room_id: UUID) -> str:
        asset = (
            db.query(Asset)
            .join(Node, Asset.node_id == Node.node_id)
            .filter(Node.room_id == room_id)
            .filter(Asset.type == "CURR_2D_CORE")
            .first()
        )
        return asset.img_url if asset else ""

    def _save_image_to_minio(self, image: Image) -> str:
        img_byte_array = BytesIO()
        image.save(img_byte_array, format='PNG')
        img_byte_array.seek(0)
        return upload_image_bytes(img_byte_array)

    def _save_asset_to_db(self, db: Session, node_id: UUID, url: str, asset_type: str = "CANDIDATE"):
        new_asset = Asset(
            node_id=node_id,
            img_url=url,
            type=asset_type
        )
        db.add(new_asset)

image_service = ImageService()