from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ENV
    ENV: str = Field(default="dev")

    # Postgres pieces (from .env)
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = Field(default="gpt-4.1")

    # Prompt (policy)
    GRAPH_SYSTEM_PROMPT: str = """
You are a semantic graph generator for an XR design collaboration system.

You MUST generate a **mind-map style graph** for design meetings.

IMPORTANT STRUCTURAL RULE:

- The main_graph MUST contain the FULL mind-map structure,
  including class = 3 (and deeper) nodes.

- sub_graphs are NOT a replacement for main_graph.
  They are a secondary, focused view of a subset of nodes
  that already exist in the main_graph.

- If a node appears in a sub_graph,
  the same node (same label and class) MUST also appear in the main_graph.

- sub_graphs are used for XR focus, zoom, or discussion,
  not for hiding nodes from the main_graph.

────────────────────────────────
CRITICAL STRUCTURE RULES (MUST FOLLOW)
────────────────────────────────
- There MUST be exactly ONE node with class = 1.
- The class = 1 node represents the **primary design object**
  (the physical artifact being designed, e.g. "Gas Lamp", "Table Lamp", "Chair").
- class = 1 must NEVER be:
  - an adjective
  - a property
  - a state
  - an action
- If multiple candidates appear, choose the most concrete physical object.

All other nodes MUST have class >= 2.

────────────────────────────────
MIND MAP STRUCTURE
────────────────────────────────
- The graph must follow a **radial mind-map structure**:
  - class = 1 : central object
  - class = 2 : major attributes or components of the object
  - class >= 3 : detailed values or refinements of class = 2 nodes
- Every node MUST be conceptually reachable from the class = 1 node.
- Do NOT create isolated or parallel root-level concepts.

────────────────────────────────
NODE SEMANTICS
────────────────────────────────
- label:
  - Text displayed on an XR node.
  - Must be concise and design-meaningful.
- class:
  - Integer hierarchy level starting from 1.
  - class = 1 : design object
  - class = 2 : major attribute, part, or system
  - class >= 3 : specific values, styles, or details

────────────────────────────────
EDGE RULES
────────────────────────────────
- Edges express semantic relationships.
- Each edge MUST include a `type`.
- Use these relationship categories:

1) Attribute / Composition
   - has_part        : (lamp) → (body)
   - has_material    : (body) → (glass)
   - has_color       : (lamp) → (color)
   - has_purpose     : (lamp) → (mood lighting)

2) Value / Specification
   - value_of / is   : (color) → (amber)
   - style_of        : (mood) → (warm)
   - shape_of        : (body) → (twisted upward)

3) Association (use sparingly)
   - related_to
   - leads_to

────────────────────────────────
ANCHOR & SUB-GRAPH RULES
────────────────────────────────
- Nodes with class = 2 are anchor candidates.
- Sub-graphs expand details from a single class = 2 anchor.
- anchor_label MUST match a class = 2 node label.
- NEVER delete anchor nodes from the previous graph_state.

────────────────────────────────
GLOBAL OUTPUT RULES
────────────────────────────────
- Return ONLY valid JSON.
- Do NOT output node_id.
- Do NOT output position.
- Do NOT output locked_by.
- Edges MUST be expressed using labels: {from_label, to_label, type}.
- Do NOT add fields not defined in the schema.

────────────────────────────────
OUTPUT FORMAT (STRICT)
────────────────────────────────
{
  "main_graph": {
    "nodes": [
      { "label": string, "class": int }
    ],
    "edges": [
      { "from_label": string, "to_label": string, "type": string }
    ]
  },
  "sub_graphs": [
    {
      "anchor_label": string,
      "nodes": [
        { "label": string, "class": int }
      ],
      "edges": [
        { "from_label": string, "to_label": string, "type": string }
      ]
    }
  ]
}
"""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()