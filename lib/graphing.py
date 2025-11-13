import copy, sys
from typing import Any, Dict, List, Optional
from utils import load_graph

def ensure_graph(obj: Dict[str, Any]) -> Dict[str, Any]:
    obj.setdefault("graph", {})
    obj["graph"].setdefault("nodes", [])
    obj["graph"].setdefault("edges", [])
    return obj

def resolve_single_node(nodes: List[Dict[str, Any]],
                        node_id: Optional[str],
                        kind: Optional[str],
                        prop_key: Optional[str],
                        prop_value: Optional[str]):
    match = find_nodes(nodes, node_id=node_id, kind=kind, prop_key=prop_key, prop_value=prop_value)
    if not matches:
        raise ValueError("No node matched the provided filters.")
    return match

def create_new_node_from(parent_like: Optional[Dict[str, Any]],
                         kinds: Optional[List[str]],
                         properties: Optional[Dict[str, Any]],
                         deception_kind: Optional[str],
                         description: str,
                         source_id: Optional[str],
                         creation_date: Optional[str],
                         id_base: str,
                         id_suffix: str,
                         graph: Dict[str, Any]) -> Dict[str, Any]:
    nodes = graph["graph"]["nodes"]
    existing_ids = {n["id"] for n in nodes}
    new_id = unique_node_id(existing_ids, id_base, id_suffix)

    if parent_like is not None:
        new_node = copy.deepcopy(parent_like)
        new_node["id"] = new_id
    else:
        new_node = {"id": new_id, "kinds": [], "properties": {}}

    if kinds:
        # Ensure unique kinds while preserving order
        kset = []
        for k in kinds:
            if k not in kset:
                kset.append(k)
        new_node["kinds"] = kset

    props = new_node.setdefault("properties", {})
    if properties:
        # Apply variable-expanded provided properties over inherited ones
        props.update(properties)

    # Deception annotation & kind
    if deception_kind:
        add_deception_kind(new_node, deception_kind=deception_kind, precedence="first" if "add_deception_kind" in globals() else "last")
    annotate_node_props(props, description=description, source_id=source_id or id_base, creation_date=creation_date)

    nodes.append(new_node)
    return new_node

def add_edge(graph: Dict[str, Any],
             kind: str,
             start_id: str,
             end_id: str,
             annotate: bool = False,
             description: str = "",
             creation_date: Optional[str] = None,
             source_id: Optional[str] = None) -> Dict[str, Any]:
    e = {
        "kind": kind,
        "start": {"value": start_id},
        "end": {"value": end_id},
        "properties": {}
    }
    if annotate:
        annotate_edge_props(e["properties"], description=description, source_id=source_id or f"{kind}:{start_id}->{end_id}", creation_date=creation_date)
    graph["graph"]["edges"].append(e)
    return e

# ---------------- Merging ------------------

def merge_graph_files(path1: str, path2: str, correlate: list) -> Dict[str, Any]:
    g1 = ensure_graph(load_graph(path1))
    g2 = ensure_graph(load_graph(path2))


    out_meta = copy.deepcopy(g1.get("metadata", {}))
    out_meta["source_kind"] = "GluedGraph"


    reserved_ids = {n.get("id") for n in g1["graph"]["nodes"] if "id" in n}

    def first_kind(n: Dict[str, Any]) -> str:
        ks = n.get("kinds", [])
        return (ks[0] if isinstance(ks, list) and ks else "UnknownKind")

    def unique_renamed_id(base_id: str, kind_name: str, already_used: set) -> str:
        base = f"{base_id}-{kind_name}"
        if base not in reserved_ids and base not in already_used:
            return base
        i = 2
        while True:
            cand = f"{base}-{i}"
            if cand not in reserved_ids and cand not in already_used:
                return cand
            i += 1

    id_remap_g2 = {}          
    used_renamed_ids = set()  

    for n in g2["graph"]["nodes"]:
        nid = n.get("id")
        if not nid:
            continue
        # deal with id collisions
        if nid in reserved_ids or nid in used_renamed_ids:
            new_id = unique_renamed_id(nid, first_kind(n), used_renamed_ids)
            id_remap_g2[nid] = new_id
            used_renamed_ids.add(new_id)
        else:
            used_renamed_ids.add(nid)

    # Apply renames to nodes and internal edges within graph2
    if id_remap_g2:
        for n in g2["graph"]["nodes"]:
            old = n.get("id")
            if old in id_remap_g2:
                new = id_remap_g2[old]
                n["id"] = new
                try:
                    if n.get("properties", {}).get("objectid") == old:
                        n["properties"]["objectid"] = new
                except Exception:
                    pass

        for e in g2["graph"]["edges"]:
            s = e.get("start", {}).get("value")
            t = e.get("end", {}).get("value")
            if s in id_remap_g2:
                e.setdefault("start", {})["value"] = id_remap_g2[s]
            if t in id_remap_g2:
                e.setdefault("end", {})["value"] = id_remap_g2[t]


    out = {"metadata": out_meta, "graph": {"nodes": [], "edges": []}}
    out_nodes = out["graph"]["nodes"]
    out_edges = out["graph"]["edges"]

    out_nodes.extend(copy.deepcopy(g1["graph"]["nodes"]))
    out_nodes.extend(copy.deepcopy(g2["graph"]["nodes"]))

    # deal with any kind arrays with more than 2 values
    trimmed_count = 0
    for n in out_nodes:
        kinds = n.get("kinds")
        if isinstance(kinds, list) and len(kinds) > 2:
            removed = kinds[2:]
            n["kinds"] = kinds[:2]
            trimmed_count += 1
            sys.stderr.write(
                f"[!] kinds trimmed for node '{n.get('id','<no-id>')}': "
                f"kept {n['kinds']}, removed {removed}\n"
            )
    if trimmed_count:
        sys.stderr.write(f"[!] Total nodes with kinds trimmed: {trimmed_count}\n")

    out_edges.extend(copy.deepcopy(g1["graph"]["edges"]))
    out_edges.extend(copy.deepcopy(g2["graph"]["edges"]))

    # add "Is" edges for each collision (bidirectional, since it is unclear how the two are related. may cause false positive traversals.)
    for old_id, new_id in id_remap_g2.items():
        out_edges.append({
            "kind": "Is",
            "start": {"value": old_id},
            "end": {"value": new_id},
            "properties": {"source": "auto-collision"}
        })
        out_edges.append({
            "kind": "Is",
            "start": {"value": new_id},
            "end": {"value": old_id},
            "properties": {"source": "auto-collision"}
        })


    for pair in correlate or []:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            sys.stderr.write(f"[!] Skipping invalid correlate entry (need 2-tuple): {pair}\n")
            continue
        id1, id2 = pair[0], pair[1]
        id1 = id_remap_g2.get(id1, id1)
        id2 = id_remap_g2.get(id2, id2)
        out_edges.append({
            "kind": "Is",
            "start": {"value": id1},
            "end": {"value": id2},
            "properties": {"source": "correlate"}
        })

    return out

def find_nodes(
    nodes: List[Dict[str, Any]],
    node_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    want_id = norm(node_id)

    out = []
    for n in nodes:
        if node_id is not None:
            nid_ci = norm(n.get("id"))
            if not (nid_ci == want_id):
                continue
        out.append(n)
    return out[0]

def find_edge(edges: List[Dict[str, Any]], kind: str, start: str, end: str) -> Optional[Dict[str, Any]]:
    want_kind, want_start, want_end = norm(kind), norm(start), norm(end)
    for e in edges:
        if norm(e.get("kind")) != want_kind:                continue
        if norm(e.get("start", {}).get("value")) != want_start: continue
        if norm(e.get("end", {}).get("value")) != want_end:     continue
        return e
    return None

def clone_node(
    graph: Dict[str, Any],
    target: Dict[str, Any],
    id_suffix: str,
    name: Optional[str],
    name_suffix: str,
    mirror_edges: bool,
    skip_duplicates: bool,
    annotate: bool,
    description: str,
    deception_kind: str,
    creation_date: Optional[str],
) -> Dict[str, Any]:
    nodes = graph["graph"]["nodes"]
    edges = graph["graph"]["edges"]
    existing_ids = {n["id"] for n in nodes}

    orig_id = target["id"]
    new_id  = unique_node_id(existing_ids, orig_id, id_suffix)

    new_node = copy.deepcopy(target)
    new_node["id"] = new_id

    props = new_node.setdefault("properties", {})
    apply_display_name(props, name=name, suffix=name_suffix)

    if annotate:
        annotate_node_props(props, description=description, source_id=orig_id, creation_date=creation_date)
        add_deception_kind(new_node, deception_kind=deception_kind)

    nodes.append(new_node)

    if mirror_edges:
        for e in list(edges):
            s = e.get("start", {}).get("value")
            t = e.get("end", {}).get("value")

            if s == orig_id:
                new_e = copy.deepcopy(e)
                new_e["start"]["value"] = new_id
                if not (skip_duplicates and any(
                    x.get("kind")==new_e["kind"] and
                    x.get("start", {}).get("value")==new_e["start"]["value"] and
                    x.get("end", {}).get("value")==new_e["end"]["value"] and
                    x.get("properties", {})==new_e.get("properties", {})
                    for x in edges
                )):
                    edges.append(new_e)

            if t == orig_id:
                new_e = copy.deepcopy(e)
                new_e["end"]["value"] = new_id
                if not (skip_duplicates and any(
                    x.get("kind")==new_e["kind"] and
                    x.get("start", {}).get("value")==new_e["start"]["value"] and
                    x.get("end", {}).get("value")==new_e["end"]["value"] and
                    x.get("properties", {})==new_e.get("properties", {})
                    for x in edges
                )):
                    edges.append(new_e)

    return new_node

def clone_edge(
    graph: Dict[str, Any],
    edge: Dict[str, Any],
    skip_duplicates: bool,
    annotate: bool,
    description: str,
    creation_date: Optional[str],
) -> Dict[str, Any]:
    edges = graph["graph"]["edges"]
    new_e = copy.deepcopy(edge)

    if annotate:
        props = new_e.setdefault("properties", {})
        src = f"{edge.get('kind')}:{edge.get('start',{}).get('value')}->{edge.get('end',{}).get('value')}"
        annotate_edge_props(props, description=description, source_id=src, creation_date=creation_date)

    if not (skip_duplicates and any(
        x.get("kind")==new_e["kind"] and
        x.get("start", {}).get("value")==new_e["start"]["value"] and
        x.get("end", {}).get("value")==new_e["end"]["value"] and
        x.get("properties", {})==new_e.get("properties", {})
        for x in edges
    )):
        edges.append(new_e)
    return new_e

def add_deception_kind(node: Dict[str, Any], kind: str, deception_kind: str = "Deception") -> None:
    kinds = list(node.get("kinds", []))
    # must insert deception kind to be at the top of the list, otherwise icon won't show
    if kind == 'inherit': 
        if deception_kind not in kinds:
            kinds.insert(0, deception_kind)
            print(kinds)
        # TODO: Check Metadata for kind and if it exists in array, remove it to make room. Temp fix just remove last kind from array
        if len(kinds) >= 3:
            del kinds[-1]
        print(kinds)
        node["kinds"] = kinds
    else:
        node["kinds"] = [deception_kind, kind]


def decept_node(
    node: Dict[str, Any],
    name: Optional[str],
    name_suffix: str,
    description: str,
    creation_date: Optional[str],
    deception_kind: str,
) -> None:
    props = node.setdefault("properties", {})
    apply_display_name(props, name=name, suffix=name_suffix)
    annotate_node_props(props, description=description, source_id=node.get("id"), creation_date=creation_date)
    add_deception_kind(node, deception_kind=deception_kind)

def decept_edge(
    edge: Dict[str, Any],
    description: str,
    creation_date: Optional[str],
) -> None:
    props = edge.setdefault("properties", {})
    src = f"{edge.get('kind')}:{edge.get('start',{}).get('value')}->{edge.get('end',{}).get('value')}"
    annotate_edge_props(props, description=description, source_id=src, creation_date=creation_date)


def attach_deception_child(
    graph: Dict[str, Any],
    parent: Dict[str, Any],
    child_name: str,
    description: str,
    id_suffix: str,
    deception_kind: str,
    type: str,
    kind: Optional[str],
    creation_date: Optional[str],
) -> Dict[str, Any]:
    nodes = graph["graph"]["nodes"]
    edges = graph["graph"]["edges"]

    existing_ids = {n["id"] for n in nodes}
    parent_id = parent["id"]
    child_id  = unique_node_id(existing_ids, parent_id, id_suffix)


    child = copy.deepcopy(parent)
    child["id"] = child_id
    naming_keys = ("name")
    props = child.setdefault("properties", {})

    for k in naming_keys:
        if k in props:
            props[k] = child_name
            break

    annotate_node_props(props, description=description, creation_date=creation_date)
    add_deception_kind(child, kind, deception_kind=deception_kind)


    child["properties"]["objectid"] = child_id
    child["properties"]["displayname"] = child_name
    if type != "parent":
        child["properties"]["type"] = type
    print(child)
    nodes.append(child)

    # Connect with HasDeception
    # TODO: modify to allow a custom edge kind 
    edge = {
        "kind": "HasDeception",
        "start": {"value": parent_id, "match_by": "id"},
        "end": {"value": child_id, "match_by": "id"}
    }
    edges.append(edge)

    return child

## property helpers
def annotate_node_props(props: Dict[str, Any], description: str, 
                        creation_date: Optional[str]) -> None:
    props["Description"] = description
    props["Deception"] = True
    props["CreationDate"] = creation_date or now_iso()

def annotate_edge_props(props: Dict[str, Any], description: str, source_id: str,
                        creation_date: Optional[str]) -> None:
    props["Description"] = description
    props["Deception"] = True
    props["CreationDate"] = creation_date or now_iso()
    props["SourceId"] = source_id