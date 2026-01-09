from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from app.db import models
from app.services.llm_service import LLMService
from app.services.graph_build import build_graph_state
from app.services.persist_service import get_latest_snapshot, persist_graph_snapshot

_llm = LLMService()

def save_utterance(db: Session, session_id: UUID, user_id, text, created_at):
    u = models.Utterance(
        session_id=session_id,
        user_id=user_id,
        text=text,
        created_at=created_at,
    )
    db.add(u)
    db.commit()

async def generate_graph_state(db: Session, session_id: UUID, utterance_text: str) -> dict:
    _, prev = get_latest_snapshot(db, session_id)
    skeleton = await _llm.generate_skeleton(utterance_text, prev)
    return build_graph_state(skeleton=skeleton, prev_graph_state=prev)

def persist_graph_state(db: Session, session_id: UUID, graph_state: dict):
    persist_graph_snapshot(db, session_id, graph_state)
    db.commit()

def project_to_unity(graph_state: dict) -> dict:
    # main nodes
    main_nodes = [
        {
            "label": n["label"],
            "class": n["class"],
            "position": n["position"],
        }
        for n in graph_state["main_graph"]["nodes"]
    ]

    main_edges = [
        {
            "from_node_id": e["from_node_id"],
            "to_node_id": e["to_node_id"],
        }
        for e in graph_state["main_graph"]["edges"]
    ]

    sub_graphs = []
    for sg in graph_state.get("sub_graphs", []):
        sg_nodes = [
            {
                "label": n["label"],
                "class": n["class"],
                "position": n["position"],
            }
            for n in sg["nodes"]
        ]
        sg_edges = [
            {
                "from_node_id": e["from_node_id"],
                "to_node_id": e["to_node_id"],
            }
            for e in sg["edges"]
        ]
        sub_graphs.append(
            {
                "anchor_node": sg["anchor_node"],
                "nodes": sg_nodes,
                "edges": sg_edges,
            }
        )

    return {
        "graph_version_id": graph_state["graph_version_id"],
        "root_node": graph_state["root_node"],
        "main_graph": {"nodes": main_nodes, "edges": main_edges},
        "sub_graphs": sub_graphs,
    }