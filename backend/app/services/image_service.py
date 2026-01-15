import io
import logging
import asyncio
import requests
from uuid import UUID
from typing import List
from io import BytesIO
from PIL import Image

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.db.models.node import Node
from app.db.models.asset import Asset
from app.storage.minio import upload_image_bytes

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self):
        self.client = genai.Client()

    # =========================================================
    # BASIC DISCUSS: prompt만으로 이미지 n개 생성
    # =========================================================
    async def generate_images(
        self,
        prompt: str,
        n: int = 3,
        db: Session | None = None,
        node_id: UUID | None = None,
    ) -> List[str]:
        logger.info(f"[IMAGE_GEN] BASIC {n}개 생성 시작")

        tasks = [self._generate_single_image(prompt) for _ in range(n)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        urls: List[str] = []
        for res in results:
            if isinstance(res, str) and res:
                urls.append(res)
                if db and node_id:
                    self._save_asset_to_db(db, node_id, res, "2D_ROOT_CANDIDATE")
            else:
                logger.error(f"[IMAGE_GEN_FAIL] {res}")

        if db:
            db.commit()

        return urls

    async def _generate_single_image(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    candidate_count=1,
                    response_modalities=["IMAGE"],
                ),
            )

            part = response.candidates[0].content.parts[0]
            image = Image.open(BytesIO(part.inline_data.data))
            return self._save_image_to_minio(image)

        except Exception as e:
            logger.error(f"[SINGLE_GEN_FAIL] {e}")
            return ""

    # =========================================================
    # CATEGORY DISCUSS: CORE 이미지 + prompt로 이미지 n개 생성
    # =========================================================
    async def generate_category_images(
        self,
        db: Session,
        prompt: str,
        n: int,
        room_id: UUID,
    ) -> List[str]:
        core_image = self._load_core_image(db, room_id)
        if not core_image:
            logger.warning("[CATEGORY_IMAGE] CORE 이미지 없음")
            return []

        logger.info(f"[CATEGORY_IMAGE] CORE 기반 {n}개 생성 시작")

        tasks = [
            self._generate_single_category_image(prompt, core_image)
            for _ in range(n)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        urls: List[str] = []
        for res in results:
            if isinstance(res, str) and res:
                urls.append(res)
            else:
                logger.error(f"[CATEGORY_SINGLE_FAIL] {res}")

        return urls

    async def _generate_single_category_image(
        self,
        prompt: str,
        core_image: Image.Image
    ) -> str:
        try:
            # ✅ PIL Image → bytes 변환
            buf = BytesIO()
            core_image.save(buf, format="PNG")
            buf.seek(0)

            image_part = types.Part.from_bytes(
                data=buf.read(),
                mime_type="image/png"
            )

            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[
                    prompt,
                    image_part
                ],
                config=types.GenerateContentConfig(
                    candidate_count=1,
                    response_modalities=["IMAGE"]
                )
            )

            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        image = Image.open(BytesIO(part.inline_data.data))
                        return self._save_image_to_minio(image)

            return ""

        except Exception as e:
            logger.error(f"[SINGLE_CATEGORY_FAIL] {e}")
            return ""


    # =========================================================
    # CORE IMAGE LOAD (MinIO → bytes → PIL)
    # =========================================================
    def _load_core_image(self, db: Session, room_id: UUID) -> Image.Image | None:
        asset = (
            db.query(Asset)
            .join(Node, Asset.node_id == Node.node_id)
            .filter(Node.room_id == room_id)
            .filter(Asset.type == "CURR_2D_CORE")
            .first()
        )

        if not asset:
            return None

        try:
            resp = requests.get(asset.img_url, timeout=10)
            resp.raise_for_status()
            return Image.open(BytesIO(resp.content))
        except Exception as e:
            logger.error(f"[CORE_IMAGE_LOAD_FAIL] {e}")
            return None

    # =========================================================
    # MinIO + DB
    # =========================================================
    def _save_image_to_minio(self, image: Image.Image) -> str:
        buf = BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        return upload_image_bytes(buf)

    def _save_asset_to_db(
        self,
        db: Session,
        node_id: UUID,
        url: str,
        asset_type: str,
    ):
        db.add(
            Asset(
                node_id=node_id,
                img_url=url,
                type=asset_type,
            )
        )


image_service = ImageService()