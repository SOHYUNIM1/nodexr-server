import io
import logging
import asyncio
from uuid import UUID
from typing import List
from io import BytesIO
from PIL import Image

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.db.models.node import Node
from app.db.models.asset import Asset
from app.storage.minio import upload_image_bytes, get_object_bytes

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
        logger.info(f"[IMAGE][START] BASIC image generation (n={n})")
        logger.info(f"[IMAGE][STEP 0] Prompt: {prompt}")

        tasks = [self._generate_single_image(prompt, idx=i) for i in range(n)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        urls: List[str] = []
        for idx, res in enumerate(results):
            if isinstance(res, str) and res:
                logger.info(f"[IMAGE][STEP 3] Image #{idx} generated successfully")
                urls.append(res)

                if db and node_id:
                    self._save_asset_to_db(db, node_id, res, "2D_ROOT_CANDIDATE")
            else:
                logger.error(f"[IMAGE][FAIL] Image #{idx} generation failed: {res}")

        if db:
            db.commit()
            logger.info("[IMAGE][DB] Assets committed")

        logger.info("[IMAGE][END] BASIC image generation finished")
        return urls

    async def _generate_single_image(self, prompt: str, idx: int = 0) -> str:
        try:
            logger.info(f"[IMAGE][STEP 1] Request Gemini image #{idx}")

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

            logger.info(f"[IMAGE][STEP 2] Gemini image #{idx} received")
            return self._save_image_to_minio(image, idx)

        except Exception as e:
            logger.error(f"[IMAGE][FAIL] SINGLE_GEN #{idx}: {e}")
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
        logger.info("[IMAGE][START] CATEGORY image generation")
        logger.info(f"[IMAGE][STEP 0] room_id={room_id}, n={n}")
        logger.info(f"[IMAGE][STEP 0] Prompt: {prompt}")

        core_image = self._load_core_image(db, room_id)
        if not core_image:
            logger.warning("[IMAGE][STOP] CORE image not found")
            return []

        tasks = [
            self._generate_single_category_image(prompt, core_image, idx=i)
            for i in range(n)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        urls: List[str] = []
        for idx, res in enumerate(results):
            if isinstance(res, str) and res:
                logger.info(f"[IMAGE][STEP 3] Category image #{idx} generated")
                urls.append(res)
            else:
                logger.error(f"[IMAGE][FAIL] Category image #{idx}: {res}")

        logger.info("[IMAGE][END] CATEGORY image generation finished")
        return urls

    async def _generate_single_category_image(
        self,
        prompt: str,
        core_image: Image.Image,
        idx: int = 0,
    ) -> str:
        try:
            logger.info(f"[IMAGE][STEP 1] Request Gemini category image #{idx}")

            buf = BytesIO()
            core_image.save(buf, format="PNG")
            buf.seek(0)

            image_part = types.Part.from_bytes(
                data=buf.read(),
                mime_type="image/png",
            )

            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(
                    candidate_count=1,
                    response_modalities=["IMAGE"],
                ),
            )

            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image = Image.open(BytesIO(part.inline_data.data))
                    logger.info(f"[IMAGE][STEP 2] Category image #{idx} received")
                    return self._save_image_to_minio(image, idx)

            return ""

        except Exception as e:
            logger.error(f"[IMAGE][FAIL] SINGLE_CATEGORY #{idx}: {e}")
            return ""

    # =========================================================
    # CORE IMAGE LOAD (MinIO → bytes → PIL)
    # =========================================================
    def _load_core_image(self, db: Session, room_id: UUID) -> Image.Image | None:
        logger.info("[IMAGE][CORE] Load core image from DB/MinIO")

        asset = (
            db.query(Asset)
            .join(Node, Asset.node_id == Node.node_id)
            .filter(Node.room_id == room_id)
            .filter(Asset.type == "CURR_2D_CORE")
            .first()
        )

        if not asset:
            logger.warning("[IMAGE][CORE] No core image asset found")
            return None

        try:
            data = get_object_bytes(asset.img_url)
            logger.info("[IMAGE][CORE] Core image loaded from MinIO")
            return Image.open(BytesIO(data))

        except Exception as e:
            logger.error(f"[IMAGE][CORE_FAIL] {e}")
            return None

    # =========================================================
    # MinIO + DB
    # =========================================================
    def _save_image_to_minio(self, image: Image.Image, idx: int = 0) -> str:
        logger.info(f"[IMAGE][STEP 2] Upload image #{idx} to MinIO")

        buf = BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)

        url = upload_image_bytes(buf)
        logger.info(f"[IMAGE][STEP 2] Uploaded image #{idx} → {url}")

        return url

    def _save_asset_to_db(
        self,
        db: Session,
        node_id: UUID,
        url: str,
        asset_type: str,
    ):
        logger.info(f"[IMAGE][DB] Save asset (type={asset_type})")
        db.add(
            Asset(
                node_id=node_id,
                img_url=url,
                type=asset_type,
            )
        )
image_service = ImageService()