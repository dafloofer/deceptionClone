from typing import Any, Dict, List, Optional
import json, requests, datetime, re

def load_graph(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_graph(g: Dict[str, Any], path: str, pretty: bool) -> None:
    with open(path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(g, f, indent=2, ensure_ascii=False)
        else:
            json.dump(g, f, separators=(",", ":"), ensure_ascii=False)


def norm(x: Any) -> str:
    return "" if x is None else str(x).casefold()

def now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"



def apply_display_name(props: Dict[str, Any], name: Optional[str], suffix: str) -> None:
    keys = ("name")
    for k in keys:
        if k in props:
            props[k] = name if name is not None else f"{props[k]}{suffix}"
            return

def unique_node_id(existing_ids: set, base_id: str, suffix: str) -> str:
    candidate = f"{base_id}{suffix}"
    i = 1
    while candidate in existing_ids:
        i += 1
        candidate = f"{base_id}{suffix}-{i}"
    return candidate

def warn_duplicate_node_ids(nodes: List[Dict[str, Any]]) -> None:
    seen, dups = set(), set()
    for n in nodes:
        nid = n.get("id")
        if nid in seen:
            dups.add(nid)
        seen.add(nid)
    if dups:
        sys.stderr.write(f"[!] Warning: duplicate node ids present: {sorted(dups)}\n")

def _sub_vars(text: str, vars_map: Dict[str, str]) -> str:
    if not isinstance(text, str):
        return text
    def repl(m):
        key = m.group(1)
        return vars_map.get(key, m.group(0))
    return re.sub(r"\$\{([A-Za-z0-9_]+)\}", repl, text)


def register_deception_icon(
    base_url: str,
    token: str,
    icon_type: str = "Deception",
    icon_name: str = "circle-radiation",
    icon_color: str = "#FFD60A",
    verify_ssl: bool = True,
) -> None:
    if requests is None:
        raise RuntimeError("The 'requests' package is required for register-icon (pip install requests).")
    url = f"{base_url.rstrip('/')}/api/v2/custom-nodes"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "custom_types": {
            icon_type: {
                "icon": {
                    "type": "font-awesome",
                    "name": icon_name,
                    "color": icon_color
                }
            }
        }
    }
    resp = requests.post(url, headers=headers, json=payload, verify=verify_ssl)
    print(f"Sent icon type: {icon_type}")
    print("Status:", resp.status_code)
    try:
        print("Response:", resp.json())
    except Exception:
        print("Response:", resp.text)