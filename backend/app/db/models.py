import uuid
from sqlalchemy import (
    Column, String, Integer, Boolean, ForeignKey,
    DateTime, Text, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .session import Base


# ===============================
# XR Sessions
# ===============================

class XRSession(Base):
    __tablename__ = "xr_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phase = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    utterances = relationship("Utterance", back_populates="session")
    graph_versions = relationship("GraphVersion", back_populates="session")
    assets = relationship("Asset", back_populates="session")


# ===============================
# Utterances
# ===============================

class Utterance(Base):
    __tablename__ = "utterances"

    utterance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("xr_sessions.session_id"))
    user_id = Column(String)
    text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("XRSession", back_populates="utterances")


# ===============================
# Graph Versions
# ===============================

class GraphVersion(Base):
    __tablename__ = "graph_versions"

    graph_version_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("xr_sessions.session_id"))
    version = Column(Integer, nullable=False)
    confirmed_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("XRSession", back_populates="graph_versions")
    nodes = relationship("Node", back_populates="graph_version")
    edges = relationship("Edge", back_populates="graph_version")
    sub_graphs = relationship("SubGraph", back_populates="graph_version")
    snapshots = relationship("GraphSnapshot", back_populates="graph_version")

    __table_args__ = (
        UniqueConstraint("session_id", "version", name="uq_graph_version"),
    )


# ===============================
# Nodes
# ===============================

class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_version_id = Column(UUID(as_uuid=True), ForeignKey("graph_versions.graph_version_id"))

    label = Column(String)
    class_ = Column("class", Integer)

    is_anchor = Column(Boolean, default=False)
    anchor_type = Column(String)

    position = Column(JSONB)
    value = Column(JSONB)

    locked_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    graph_version = relationship("GraphVersion", back_populates="nodes")


# ===============================
# Edges
# ===============================

class Edge(Base):
    __tablename__ = "edges"

    edge_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_version_id = Column(UUID(as_uuid=True), ForeignKey("graph_versions.graph_version_id"))
    from_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id"))
    to_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id"))
    type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    graph_version = relationship("GraphVersion", back_populates="edges")


# ===============================
# SubGraphs
# ===============================

class SubGraph(Base):
    __tablename__ = "sub_graphs"

    sub_graph_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_version_id = Column(UUID(as_uuid=True), ForeignKey("graph_versions.graph_version_id"))
    root_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id"))
    anchor_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    graph_version = relationship("GraphVersion", back_populates="sub_graphs")

    __table_args__ = (
        UniqueConstraint("graph_version_id", "anchor_node_id", name="uq_sub_graph"),
    )


# ===============================
# SubGraph Nodes
# ===============================

class SubGraphNode(Base):
    __tablename__ = "sub_graph_nodes"

    sub_graph_id = Column(UUID(as_uuid=True), ForeignKey("sub_graphs.sub_graph_id"), primary_key=True)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id"), primary_key=True)


# ===============================
# SubGraph Edges
# ===============================

class SubGraphEdge(Base):
    __tablename__ = "sub_graph_edges"

    sub_graph_id = Column(UUID(as_uuid=True), ForeignKey("sub_graphs.sub_graph_id"), primary_key=True)
    edge_id = Column(UUID(as_uuid=True), ForeignKey("edges.edge_id"), primary_key=True)


# ===============================
# Graph Snapshots
# ===============================

class GraphSnapshot(Base):
    __tablename__ = "graph_snapshots"

    snapshot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_version_id = Column(UUID(as_uuid=True), ForeignKey("graph_versions.graph_version_id"))
    graph_state = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    graph_version = relationship("GraphVersion", back_populates="snapshots")


# ===============================
# SubGraph Snapshots
# ===============================

class SubGraphSnapshot(Base):
    __tablename__ = "sub_graph_snapshots"

    sub_graph_snapshot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sub_graph_id = Column(UUID(as_uuid=True), ForeignKey("sub_graphs.sub_graph_id"))
    snapshot_type = Column(String)
    snapshot_state = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ===============================
# Assets
# ===============================

class Asset(Base):
    __tablename__ = "assets"

    asset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("xr_sessions.session_id"))
    type = Column(String)
    url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("XRSession", back_populates="assets")