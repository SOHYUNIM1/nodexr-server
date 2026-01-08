import json
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings

def build_user_prompt(utterance: str, prev_graph_state: Optional[Dict[str, Any]]) -> str:
    if prev_graph_state is None:
        return f"Create a new graph from the utterance:\n{utterance}"
    return (
        "Update the graph based on the new utterance.\n\n"
        f"Previous graph_state:\n{json.dumps(prev_graph_state, ensure_ascii=False)}\n\n"
        f"New utterance:\n{utterance}"
    )

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def generate_skeleton(
        self,
        utterance: str,
        prev_graph_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": settings.GRAPH_SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(utterance, prev_graph_state)},
            ],
            temperature=0.2,
        )
        content = resp.choices[0].message.content or ""
        try:
            return json.loads(content)
        except Exception:
            raise RuntimeError(f"LLM returned invalid JSON:\n{content}")