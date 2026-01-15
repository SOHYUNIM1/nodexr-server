from typing import List, Optional, Literal
from uuid import UUID
from pydantic import BaseModel

NodeType = Literal["CATEGORY", "ASSET"]

class GraphNodeDTO(BaseModel):
    node_id: UUID
    node_type: NodeType
    label: Optional[str] = None      # CATEGORY
    order: Optional[int] = None      # CATEGORY
    img_url: Optional[str] = None    # ASSET
    parent_category_id: Optional[UUID] = None  # CATEGORY node_id

class GraphEdgeDTO(BaseModel):
    edge_id: UUID
    from_node_id: UUID
    to_node_id: UUID

class GraphStateDTO(BaseModel):
    graph_snapshot_id: Optional[UUID]
    nodes: List[GraphNodeDTO]
    edges: List[GraphEdgeDTO]

class GraphEventDTO(BaseModel):
    event: str
    core_img_url: Optional[str] = None
    graph_state: GraphStateDTO