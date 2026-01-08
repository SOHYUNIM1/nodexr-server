import uuid
from typing import Dict, Any, Optional, Tuple

DEFAULT_POS = {"x": 0.0, "y": 0.0, "z": 0.0}

def _key(label: str, class_: int) -> Tuple[str, int]:
    return (label.strip(), int(class_))

def build_graph_state(
    *,
    skeleton: Dict[str, Any],
    prev_graph_state: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    # 이전 노드 매핑: (label,class) -> node_id, node_id -> position
    prev_id_by_key: dict[Tuple[str,int], str] = {}
    prev_pos_by_id: dict[str, dict] = {}

    if prev_graph_state:
        for n in prev_graph_state.get("main_graph", {}).get("nodes", []):
            k = _key(n["label"], n["class"])
            prev_id_by_key[k] = str(n["node_id"])
            prev_pos_by_id[str(n["node_id"])] = n.get("position") or DEFAULT_POS

    # main nodes
    main_nodes = []
    key_to_id: dict[Tuple[str,int], str] = {}

    for n in skeleton["main_graph"]["nodes"]:
        label = n["label"]
        class_ = int(n["class"])
        k = _key(label, class_)

        node_id = prev_id_by_key.get(k) or str(uuid.uuid4())
        position = prev_pos_by_id.get(node_id, DEFAULT_POS)

        main_nodes.append({
            "node_id": node_id,
            "label": label,
            "class": class_,
            "position": position,
        })
        key_to_id[k] = node_id

    # edges: label -> node_id (label 중복이 있으면 깨질 수 있으니, MVP에서는 label 유일 가정)
    label_to_any_id = {n["label"].strip(): str(n["node_id"]) for n in main_nodes}

    main_edges = []
    for e in skeleton["main_graph"].get("edges", []):
        fl = e["from_label"].strip()
        tl = e["to_label"].strip()
        edge_type = e.get("type", "").strip()
        if fl in label_to_any_id and tl in label_to_any_id:
            main_edges.append({
                "from_node_id": label_to_any_id[fl],
                "to_node_id": label_to_any_id[tl],
                "type" : edge_type
            })

    # root_node: class==1 첫 노드
    root_node = None
    for n in main_nodes:
        if int(n["class"]) == 1:
            root_node = str(n["node_id"])
            break
    if root_node is None and main_nodes:
        root_node = str(main_nodes[0]["node_id"])
    if root_node is None:
        root_node = str(uuid.uuid4())

    # subgraphs: 서버가 sub_graph_id 생성 + anchor_label을 main anchor_node id로 변환
    sub_graphs_out = []
    for sg in skeleton.get("sub_graphs", []):
        anchor_label = (sg.get("anchor_label") or "").strip()
        if anchor_label not in label_to_any_id:
            continue
        anchor_node_id = label_to_any_id[anchor_label]
        sub_graph_id = str(uuid.uuid4())

        sg_nodes = []
        sg_label_to_id = {}
        for n in sg.get("nodes", []):
            nid = str(uuid.uuid4())
            sg_nodes.append({
                "node_id": nid,
                "label": n["label"],
                "class": int(n["class"]),
                "position": DEFAULT_POS,
            })
            sg_label_to_id[n["label"].strip()] = nid

        sg_edges = []
        for e in sg.get("edges", []):
            fl = e["from_label"].strip()
            tl = e["to_label"].strip()
            edge_type = e.get("type", "").strip()
            if fl in sg_label_to_id and tl in sg_label_to_id:
                sg_edges.append({
                    "from_node_id": sg_label_to_id[fl],
                    "to_node_id": sg_label_to_id[tl],
                    "type": edge_type
                })

        sub_graphs_out.append({
            "sub_graph_id": sub_graph_id,
            "anchor_node": anchor_node_id,
            "nodes": sg_nodes,
            "edges": sg_edges,
        })

    return {
        "graph_version_id": str(uuid.uuid4()),
        "root_node": root_node,
        "main_graph": {"nodes": main_nodes, "edges": main_edges},
        "sub_graphs": sub_graphs_out,
    }