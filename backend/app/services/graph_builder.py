from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.node import Node
from app.db.models.edge import Edge
from app.db.models.asset import Asset
from app.db.models.category_detail import CategoryDetail

def build_graph_state(db: Session, graph_snapshot_id: UUID | None, room_id: UUID) -> dict:
    # CATEGORY 노드: CategoryDetail에서 label/order 구성
    # ASSET 노드: Asset에서 img_url, parent_category_id 구성 (parent는 CategoryDetail.node_id)
    nodes_out = []
    edges_out = []

    # category node label mapping
    details = db.query(CategoryDetail).join(Node, Node.node_id == CategoryDetail.node_id)\
        .filter(Node.room_id == room_id).all()

    detail_by_node = {d.node_id: d for d in details}

    # nodes (CATEGORY + ASSET)
    nodes = db.query(Node).filter(Node.room_id == room_id).all()
    for n in nodes:
        if n.node_type == "CATEGORY":
            d = detail_by_node.get(n.node_id)
            nodes_out.append({
                "node_id": n.node_id,
                "node_type": "CATEGORY",
                "label": d.detail_text if d else "",
                "order": d.order if d else 0,
            })
        else:
            a = db.query(Asset).filter(Asset.node_id == n.node_id).first()
            parent_category_id = None
            if a:
                parent_detail = db.query(CategoryDetail).filter(CategoryDetail.category_detail_id == a.category_detail_id).first()
                parent_category_id = parent_detail.node_id if parent_detail else None
            nodes_out.append({
                "node_id": n.node_id,
                "node_type": "ASSET",
                "img_url": a.img_url if a else None,
                "parent_category_id": parent_category_id,
            })

    edges = db.query(Edge).all()
    for e in edges:
        edges_out.append({
            "edge_id": e.edge_id,
            "from_node_id": e.from_node_id,
            "to_node_id": e.to_node_id,
        })

    return {
        "graph_snapshot_id": graph_snapshot_id,
        "nodes": nodes_out,
        "edges": edges_out
    }