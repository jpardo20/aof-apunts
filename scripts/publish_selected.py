#!/usr/bin/env python3
# scripts/publish_selected.py
import os, sys, shutil, subprocess, yaml, pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SRC = ROOT / "source"
MANIFEST = ROOT / "publish.yaml"
CONTINGUTS = DOCS / "continguts.md"

def run(cmd, cwd=None):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd)

def pandoc_convert(src, out_md):
    out_md.parent.mkdir(parents=True, exist_ok=True)
    cwd = out_md.parent                      # generar enllaços RELATIUS
    base = ["pandoc", str(src), "--to", "gfm", "--wrap=none",
            "-o", out_md.name, "--extract-media", "."]  # → ./media/...

    # 1r intent (Pandoc nou)
    try:
        run(base + ["--markdown-headings=atx"], cwd=cwd)
    except subprocess.CalledProcessError:
        print("… Pandoc sense --markdown-headings=atx; provem amb --atx-headers")
        run(base + ["--atx-headers"], cwd=cwd)

    # Post-process: arregla media/media i enllaços si cal
    mm = cwd / "media" / "media"
    if mm.exists():
        for f in mm.iterdir():
            if f.is_file():
                f.rename(cwd / "media" / f.name)
        shutil.rmtree(mm, ignore_errors=True)
    p = out_md
    txt = p.read_text(encoding="utf-8")
    if "media/media/" in txt:
        p.write_text(txt.replace("media/media/", "media/"), encoding="utf-8")

def copy_asset(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print("copy", src, "->", dest)

def main():
    if not MANIFEST.exists():
        print("ERROR: no s'ha trobat publish.yaml", file=sys.stderr); sys.exit(1)
    with open(MANIFEST, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    items = [it for it in (data.get("items") or []) if it.get("publish")]

    sections = defaultdict(list)
    for it in items:
        title = it.get("title","(Sense títol)")
        source_rel = it.get("source"); output_rel = it.get("output")
        if not source_rel or not output_rel:
            print(f"WARNING: Element sense 'source' o 'output': {title}"); continue
        src_file = ROOT / source_rel
        out_md = DOCS / output_rel
        if not src_file.exists():
            print(f"WARNING: No trobo: {src_file}. Salto '{title}'."); continue

        if src_file.suffix.lower() == ".docx":
            pandoc_convert(src_file, out_md)
        else:
            out_md.parent.mkdir(parents=True, exist_ok=True)
            if not out_md.exists():
                out_md.write_text(f"# {title}\n\n> Contingut original com a descàrrega.\n", encoding="utf-8")

        dl_links = []
        for dl in it.get("downloads", []) or []:
            dl_src = ROOT / dl
            if not dl_src.exists():
                print(f"WARNING: Descàrrega no trobada: {dl_src}"); continue
            rel_under_assets = pathlib.Path(dl).relative_to("source")
            dl_dest = DOCS / "assets" / rel_under_assets
            copy_asset(dl_src, dl_dest)
            dl_links.append(("assets/" + str(rel_under_assets)).replace("\\", "/"))

        sections[it.get("section","Altres")].append({
            "title": title,
            "page": str(pathlib.Path(output_rel)).replace("\\", "/"),
            "downloads": dl_links
        })

    # Índex automàtic
    lines = ["---","title: Continguts publicats","---",""]
            #  "> ⚠️ Aquesta pàgina es (re)genera automàticament a partir de `publish.yaml`.",""]
            
    for sec in sorted(sections.keys()):
        lines.append(f"## {sec}")
        for el in sections[sec]:
            lines.append(f"- [{el['title']}]({el['page']})")
            for li in el["downloads"]:
                lines.append(f"  - Descàrrega: [{os.path.basename(li)}]({li})")
        lines.append("")
    CONTINGUTS.parent.mkdir(parents=True, exist_ok=True)
    CONTINGUTS.write_text("\n".join(lines), encoding="utf-8")
    print("Regenerat:", CONTINGUTS)

if __name__ == "__main__":
    main()
