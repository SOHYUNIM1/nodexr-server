import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    ForeignKey,
    TIMESTAMP,
    JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


# =================================================
# Rooms
# =================================================
class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    room_topic = Column(String, nullable=False)
    password = Column(String)
    phase = Column(String)
    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    # relationships (조회 편의용)
    users = relationship("User", back_populates="room")
    nodes = relationship("Node", back_populates="room")
    categories = relationship("Category", back_populates="room")
    graph_snapshots = relationship("GraphSnapshot", back_populates="room")


# =================================================
# Users
# =================================================
class User(Base):
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rooms.room_id", ondelete="CASCADE"),
        nullable=False
    )
    nickname = Column(String, nullable=False)
    leader = Column(Boolean, default=False)

    room = relationship("Room", back_populates="users")
    utterances = relationship("Utterance", back_populates="user")


# =================================================
# Utterances
# =================================================
class Utterance(Base):
    __tablename__ = "utterances"

    utterance_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    text = Column(Text, nullable=False)
    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    user = relationship("User", back_populates="utterances")


# =================================================
# Nodes
# =================================================
class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rooms.room_id", ondelete="CASCADE"),
        nullable=False
    )
    node_type = Column(String, nullable=False)

    room = relationship("Room", back_populates="nodes")

    outgoing_edges = relationship(
        "Edge",
        foreign_keys="Edge.from_node_id",
        back_populates="from_node"
    )
    incoming_edges = relationship(
        "Edge",
        foreign_keys="Edge.to_node_id",
        back_populates="to_node"
    )


# =================================================
# Edges
# =================================================
class Edge(Base):
    __tablename__ = "edges"

    edge_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    from_node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nodes.node_id", ondelete="CASCADE"),
        nullable=False
    )
    to_node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nodes.node_id", ondelete="CASCADE"),
        nullable=False
    )

    from_node = relationship(
        "Node",
        foreign_keys=[from_node_id],
        back_populates="outgoing_edges"
    )
    to_node = relationship(
        "Node",
        foreign_keys=[to_node_id],
        back_populates="incoming_edges"
    )


# =================================================
# Categories
# =================================================
class Category(Base):
    __tablename__ = "categories"

    category_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rooms.room_id", ondelete="CASCADE"),
        nullable=False
    )
    category_name = Column(String, nullable=False)
    phase = Column(String)

    room = relationship("Room", back_populates="categories")
    details = relationship("CategoryDetail", back_populates="category")


# =================================================
# Category Details
# =================================================
class CategoryDetail(Base):
    __tablename__ = "category_details"

    category_detail_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.category_id", ondelete="CASCADE"),
        nullable=False
    )
    node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nodes.node_id", ondelete="SET NULL")
    )
    detail_text = Column(Text)
    order = Column(Integer)

    category = relationship("Category", back_populates="details")
    node = relationship("Node")
    assets = relationship("Asset", back_populates="category_detail")


# =================================================
# Assets
# =================================================
class Asset(Base):
    __tablename__ = "assets"

    asset_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nodes.node_id", ondelete="SET NULL")
    )
    category_detail_id = Column(
        UUID(as_uuid=True),
        ForeignKey("category_details.category_detail_id", ondelete="CASCADE")
    )
    img_url = Column(Text, nullable=False)
    type = Column(String)

    node = relationship("Node")
    category_detail = relationship(
        "CategoryDetail",
        back_populates="assets"
    )


# =================================================
# Graph Snapshots
# =================================================
class GraphSnapshot(Base):
    __tablename__ = "graph_snapshots"

    graph_snapshot_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rooms.room_id", ondelete="CASCADE"),
        nullable=False
    )
    graph_state = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    room = relationship("Room", back_populates="graph_snapshots")