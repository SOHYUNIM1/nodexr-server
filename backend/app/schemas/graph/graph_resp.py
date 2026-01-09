from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class Vec3(BaseModel):
    x: float
    y: float
    z: float

class GraphNode(BaseModel):
    label: str
    class_: int = Field(alias="class")
    position: Vec3

class GraphEdge(BaseModel):
    from_node_id: str
    to_node_id: str

class MainGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class SubGraph(BaseModel):
    anchor_node: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class GraphResp(BaseModel):
    graph_version_id: UUID
    root_node: str
    main_graph: MainGraph
    sub_graphs: List[SubGraph]