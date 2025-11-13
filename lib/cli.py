import argparse

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OpenGraph deception utility for manipulating nodes, edges, and graphs.")
    p.add_argument("--in", dest="in_path", help="Input OpenGraph JSON (not needed for register-icon)")
    p.add_argument("--out", dest="out_path", help="Output OpenGraph JSON (not needed for register-icon)")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    sub = p.add_subparsers(dest="cmd", required=True)

    # clone-node
    pn = sub.add_parser("clone-node", help="Clone a node; add --annotate for Deception fields + kind.")
    pn.add_argument("--id", dest="node_id", help="Match by id (CI) or by properties.node_id/objectid")
    pn.add_argument("--id-suffix", default="-DECEPTION", help="Suffix for cloned node id")
    pn.add_argument("--name", default=None, help="Explicit display name for the clone")
    pn.add_argument("--name-suffix", default="-DECEPTION", help="If no --name, append this to existing display name")
    pn.add_argument("--mirror-edges", action="store_true", help="Mirror edges touching the original")
    pn.add_argument("--no-mirror-edges", dest="mirror_edges", action="store_false")
    pn.set_defaults(mirror_edges=True)
    pn.add_argument("--skip-duplicates", action="store_true")
    pn.add_argument("--annotate", action="store_true", help="Add Description/Deception/CreationDate/SourceId and 'Deception' kind")
    pn.add_argument("--description", default="", help="Description when --annotate")
    pn.add_argument("--creation-date", dest="creation_date", default=None, help="Override CreationDate (ISO)")
    pn.add_argument("--deception-kind", default="Deception", help="Kind added when --annotate")

    # clone-edge
    pe = sub.add_parser("clone-edge", help="Clone an edge; add --annotate to decorate the clone.")
    pe.add_argument("--edge-kind", required=True)
    pe.add_argument("--start", required=True)
    pe.add_argument("--end", required=True)
    pe.add_argument("--skip-duplicates", action="store_true")
    pe.add_argument("--annotate", action="store_true")
    pe.add_argument("--description", default="")
    pe.add_argument("--creation-date", dest="creation_date", default=None)

    # decept-node (in-place)
    dn = sub.add_parser("decept-node", help="Mark an existing node as deception (no new nodes).")
    dn.add_argument("--id", dest="node_id", help="Match by id (CI) or properties.node_id/objectid")
    dn.add_argument("--name", default=None, help="Explicit display name; if omitted, appends -DECEPTION")
    dn.add_argument("--name-suffix", default="-DECEPTION")
    dn.add_argument("--description", default="")
    dn.add_argument("--creation-date", dest="creation_date", default=None)
    dn.add_argument("--deception-kind", default="Deception")

    # decept-edge (in-place)
    de = sub.add_parser("decept-edge", help="Mark an existing edge as deception (no new edges).")
    de.add_argument("--edge-kind", required=True)
    de.add_argument("--start", required=True)
    de.add_argument("--end", required=True)
    de.add_argument("--description", default="")
    de.add_argument("--creation-date", dest="creation_date", default=None)

    # attach-deception (new child + HasDeception)
    ad = sub.add_parser("attach-deception", help="Create a child deception node and connect via HasDeception.")
    ad.add_argument("--id", dest="node_id", help="Match parent by id (CI) or properties.node_id/objectid")
    ad.add_argument("--select-index", type=int, default=0)

    ad.add_argument("--name", required=True, help="Display name for the new deception child")
    ad.add_argument("--description", default="", help="Description for the new deception child")
    ad.add_argument("--id-suffix", default="-DECEPTION", help="Suffix to derive the child node id from the parent id")
    ad.add_argument("--deception-kind", default="Deception", help="Kind to add to child")
    ad.add_argument("--type", default="Deception", help="Set the type of newly created deception child, defaults to Deception")
    ad.add_argument('--kind', default="inherit", help="Set the kind (useful for pathfinding) of newly created child. Defaults to parent kind.")
    ad.add_argument("--creation-date", dest="creation_date", default=None, help="Override CreationDate (ISO)")

    # register-icon
    ri = sub.add_parser("register-icon", help="Register a custom icon type in BloodHound.")
    ri.add_argument("--url", required=True, help="BloodHound base URL, e.g., http://127.0.0.1:8080")
    ri.add_argument("--token", required=True, help="Bearer token")
    ri.add_argument("--type", default="Deception", help="Custom type name to register (should match the kind you add)")
    ri.add_argument("--icon", default="circle-radiation", help="Font Awesome icon name")
    ri.add_argument("--color", default="#FFD60A", help="Icon color")
    ri.add_argument("--insecure", action="store_true", help="Disable TLS verification")

    # Merge
    mg = sub.add_parser("merge-graphs", help="Merge two OpenGraph JSON graphs into a third.")
    mg.add_argument("--graph1", required=True, help="Path to first graph JSON")
    mg.add_argument("--graph2", required=True, help="Path to second graph JSON")
    mg.add_argument("--out", dest="merge_out", default="merged.json",
                    help="Output merged graph path (default: merged.json)")
    mg.add_argument(
        "--correlate",
        action="append",
        metavar="ID1,ID2",
        help="Add an 'Is' edge from ID1 to ID2 in the merged graph. Can be used multiple times."
    )
    mg.add_argument(
        "--correlate-file",
        help="CSV (no header) with lines 'ID1,ID2' to add 'Is' edges."
    )

    return p