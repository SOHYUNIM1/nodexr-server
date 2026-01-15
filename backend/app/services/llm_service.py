import json
from pathlib import Path
from typing import List, Tuple
from openai import OpenAI
import os
from pathlib import Path
from app.core.config import settings

PROJECT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent  # nodexr-server 폴더 기준
PROMPT_DIR = PROJECT_DIR / "app/core/llm/prompts"  # 프롬프트 파일 경로


def load_prompt(filename: str) -> str:
    return (PROMPT_DIR / filename).read_text(encoding="utf-8")


class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

        self.basic_prompt_tpl = load_prompt("basic_discuss.txt")
        self.category_prompt_tpl = load_prompt("category_discuss.txt")

    def _call_openai(self, prompt: str) -> dict:
        print("_call_openai 호출")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": settings.GRAPH_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content

        try:
            print("openai 응답", content)
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"OpenAI 응답 JSON 파싱 실패:\n{content}")

    # =================================================
    # 1️⃣ BASIC_DISCUSS
    # =================================================
    def basic_discuss(
        self,
        room_topic: str,
        utterance: str
    ) -> Tuple[str, List[str], str]:

        prompt = self.basic_prompt_tpl \
            .replace("{{ROOM_TOPIC}}", room_topic) \
            .replace("{{UTTERANCE}}", utterance)

        result = self._call_openai(prompt)

        return (
            result["root_label"],
            result["categories"],
            result["sketch_prompt"],
        )

    # =================================================
    # 2️⃣ CATEGORY_DISCUSS
    # =================================================
    def category_discuss(
        self,
        category_name: str,
        utterance: str
    ) -> Tuple[str, str]:

        prompt = self.category_prompt_tpl \
            .replace("{{CATEGORY_NAME}}", category_name) \
            .replace("{{UTTERANCE}}", utterance)

        result = self._call_openai(prompt)

        return (
            result["keyword"],
            result["image_prompt"],
        )


llm_service = LLMService()