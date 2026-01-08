from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class Vec3(BaseModel):
    x: float
    y: float
    z: float

class GraphNode(BaseModel):
    node_id: UUID
    label: str
    class_: int = Field(alias="class")
    position: Vec3

class GraphEdge(BaseModel):
    from_node_id: UUID
    to_node_id: UUID
    type: str

class MainGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class SubGraph(BaseModel):
    sub_graph_id: UUID
    anchor_node: UUID
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class GraphState(BaseModel):
    graph_version_id: UUID
    root_node: UUID
    main_graph: MainGraph
    sub_graphs: List[SubGraph]