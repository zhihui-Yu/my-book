import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"


def iter_markdown_files(base: Path):
    for dirpath, _, filenames in os.walk(base):
        dirpath = Path(dirpath)
        # skip hidden dirs
        parts = dirpath.relative_to(base).parts
        if any(p.startswith(".") for p in parts):
            continue
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            if not name.lower().endswith(".md"):
                continue
            path = dirpath / name
            yield path


def build_tree():
    tree = {}
    for path in iter_markdown_files(DOCS_DIR):
        rel = path.relative_to(DOCS_DIR)
        parts = rel.parts
        cur = tree
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur.setdefault("__files__", []).append(parts[-1])
    return tree


def sort_keys(d: dict):
    # keep chinese/other order as-is but ensure folders before readme/files
    keys = [k for k in d.keys() if k != "__files__"]
    def key_fn(k):
        # README 优先
        if k.lower() == "readme.md":
            return (0, k.lower())
        return (1, k.lower())
    return sorted(keys, key=key_fn)


def md_title_from_filename(name: str) -> str:
    if name.lower() == "readme.md":
        return "README"
    # strip extension
    stem = name[:-3] if name.lower().endswith(".md") else name
    return stem


def emit_md(tree: dict, base_prefix: str = "") -> str:
    lines = ["# Auto Generated Summary", ""]

    def walk(node: dict, prefix: str, level: int, path_parts: list):
        indent = "    " * level
        files = node.get("__files__", [])
        # files at this node
        for fname in sorted(files, key=str.lower):
            rel_path = "/".join(path_parts + [fname])
            title = md_title_from_filename(fname)
            lines.append(f"{indent}* [{title}]({rel_path})")
        # subdirs
        for k in sort_keys(node):
            child = node[k]
            title = k
            # if contains README.md use README as section link
            readme = None
            if isinstance(child, dict):
                files_child = child.get("__files__", [])
                for f in files_child:
                    if f.lower() == "readme.md":
                        readme = f
                        break
            if readme:
                rel_path = "/".join(path_parts + [k, readme])
                lines.append(f"{indent}* [{title}]({rel_path})")
            else:
                lines.append(f"{indent}* **{title}**")
            if isinstance(child, dict):
                walk(child, prefix, level + 1, path_parts + [k])

    walk(tree, base_prefix, 0, [])
    return "\n".join(lines) + "\n"


def main():
    tree = build_tree()
    content = emit_md(tree)
    out_path = DOCS_DIR / "SUMMARY.auto.md"
    out_path.write_text(content, encoding="utf-8")
    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()

