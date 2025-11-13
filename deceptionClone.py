import sys, re, csv
from typing import Any, Dict, List, Optional
from lib.graphing import *
from lib.cli import build_parser
from lib.utils import *

def main():
    args = build_parser().parse_args()

    if args.cmd == "register-icon":
        verify = not args.insecure
        register_deception_icon(
            base_url=args.url,
            token=args.token,
            icon_type=args.type,
            icon_name=args.icon,
            icon_color=args.color,
            verify_ssl=verify
        )
        return

    if args.cmd == "merge-graphs":
        # Parse correlate pairs from flags / file
        correlate = []

        # From repeated --correlate ID1,ID2
        if getattr(args, "correlate", None):
            for item in args.correlate:
                parts = [p.strip() for p in item.split(",")]
                if len(parts) == 2:
                    correlate.append((parts[0], parts[1]))
                else:
                    sys.stderr.write(f"[!] Ignoring malformed --correlate '{item}' (need ID1,ID2)\n")

        # From --correlate-file CSV
        if getattr(args, "correlate_file", None):
            
            with open(args.correlate_file, "r", encoding="utf-8") as f:
                for row in csv.reader(f):
                    if not row or len(row) < 2:
                        continue
                    correlate.append((row[0].strip(), row[1].strip()))

        merged = merge_graph_files(args.graph1, args.graph2, correlate=correlate)
        save_graph(merged, args.merge_out, pretty=args.pretty)
        sys.stderr.write(f"[+] Merged graphs into {args.merge_out} "
                         f"with source_kind='{merged.get('metadata', {}).get('source_kind')}', "
                         f"added {len(correlate)} 'Is' correlate edges.\n")
        return

    if not args.in_path or not args.out_path:
        sys.stderr.write("[!] --in and --out are required for graph operations.\n")
        sys.exit(1)

    g = ensure_graph(load_graph(args.in_path))
    nodes = g["graph"]["nodes"]
    edges = g["graph"]["edges"]

    warn_duplicate_node_ids(nodes)

    if args.cmd == "clone-node":
        match = find_nodes(nodes, node_id=getattr(args, "node_id", None))
        if not match:
            sys.stderr.write("[!] No node matched the provided node_id.\n")
            sys.exit(1)

        target = match
        new_node = clone_node(
            graph=g,
            target=target,
            id_suffix=args.id_suffix,
            name=args.name,
            name_suffix=args.name_suffix,
            mirror_edges=args.mirror_edges,
            skip_duplicates=args.skip_duplicates,
            annotate=args.annotate,
            description=args.description,
            deception_kind=args.deception_kind,
            creation_date=args.creation_date,
        )
        sys.stderr.write(f"[+] Cloned node {target['id']} -> {new_node['id']}\n")

    elif args.cmd == "clone-edge":
        src = find_edge(edges, args.edge_kind, args.start, args.end)
        if not src:
            sys.stderr.write("[!] Edge not found with provided kind/start/end.\n")
            sys.exit(1)
        new_e = clone_edge(
            graph=g,
            edge=src,
            skip_duplicates=args.skip_duplicates,
            annotate=args.annotate,
            description=args.description,
            creation_date=args.creation_date,
        )
        sys.stderr.write(f"[+] Cloned edge {src['kind']} {src['start']['value']} -> {src['end']['value']}\n")

    elif args.cmd == "decept-node":
        match = find_nodes(nodes, node_id=getattr(args, "node_id", None))
        if not match:
            sys.stderr.write("[!] No node matched the provided node_id.\n")
            sys.exit(1)

        target = match
        decept_node(
            node=target,
            name=args.name,
            name_suffix=args.name_suffix,
            description=args.description,
            creation_date=args.creation_date,
            deception_kind=args.deception_kind,
        )
        sys.stderr.write(f"[+] Marked node {target['id']} as deception (in place).\n")

    elif args.cmd == "decept-edge":
        src = find_edge(edges, args.edge_kind, args.start, args.end)
        if not src:
            sys.stderr.write("[!] Edge not found with provided kind/start/end.\n")
            sys.exit(1)
        decept_edge(
            edge=src,
            description=args.description,
            creation_date=args.creation_date,
        )
        sys.stderr.write(f"[+] Marked edge {src['kind']} {src['start']['value']} -> {src['end']['value']} as deception (in place).\n")

    elif args.cmd == "attach-deception":
        match = find_nodes(nodes, node_id=getattr(args, "node_id", None))
        if not match:
            sys.stderr.write("[!] No parent node matched the provided node_id.\n")
            sys.exit(1)

        parent = match
        child = attach_deception_child(
            graph=g,
            parent=parent,
            child_name=args.name,
            description=args.description,
            id_suffix=args.id_suffix,
            deception_kind=args.deception_kind,
            type=args.type,
            kind=args.kind,
            creation_date=args.creation_date,
        )
        sys.stderr.write(f"[+] Attached deception child {child['id']} to parent {parent['id']} via HasDeception.\n")
    

    save_graph(g, args.out_path, pretty=args.pretty)

if __name__ == "__main__":
    main()
