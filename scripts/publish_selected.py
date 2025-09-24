#!/usr/bin/env python3
# scripts/publish_selected.py
# Llegeix publish.yaml i construeix només els elements amb publish:true.
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


# def run(cmd):
#     print("+", " ".join(cmd))
#     subprocess.run(cmd, check=True)


def pandoc_convert(src, out_md, media_dir):
    out_md.parent.mkdir(parents=True, exist_ok=True)

    # Treballem dins la carpeta del .md perquè els enllaços a imatges quedin RELATIUS (media/...)
    cwd = out_md.parent
    rel_media = "media"
    (cwd / rel_media).mkdir(parents=True, exist_ok=True)

    base = ["pandoc", str(src), "--to=gfm", "--wrap=none", f"-o={out_md.name}"]

    # 1r intent (Pandoc nou): --markdown-headings=atx
    try:
        run(base + [f"--extract-media={rel_media}", "--markdown-headings=atx"], cwd=cwd)
        return
    except subprocess.CalledProcessError:
        print("… Pandoc sense --markdown-headings=atx; provem amb --atx-headers")

    # 2n intent (Pandoc antic): --atx-headers
    run(base + [f"--extract-media={rel_media}", "--atx-headers"], cwd=cwd)


# def pandoc_convert(src, out_md, media_dir):
#     out_md.parent.mkdir(parents=True, exist_ok=True)
#     media_dir.mkdir(parents=True, exist_ok=True)
#     run([
#         "pandoc",
#         str(src),
#         "--to=gfm",
#         f"--extract-media={media_dir}",
#         "--wrap=none",
#         "--markdown-headings=atx",
#         f"-o={out_md}",
#     ])


# def pandoc_convert(src, out_md, media_dir):
#     out_md.parent.mkdir(parents=True, exist_ok=True)
#     media_dir.mkdir(parents=True, exist_ok=True)
#     run(["pandoc", str(src), "--to", "gfm", "--extract-media", str(media_dir),
#          "--wrap", "none", "--atx-headers", "-o", str(out_md)])

def copy_asset(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print("copy", src, "->", dest)

def main():
    if not MANIFEST.exists():
        print("No s'ha trobat publish.yaml", file=sys.stderr)
        sys.exit(1)
    with open(MANIFEST, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    items = data.get("items", [])
    published = [it for it in items if it.get("publish")]
    sections = defaultdict(list)

    for it in published:
        title = it["title"]
        source = ROOT / it["source"]
        output_rel = pathlib.Path(it["output"])
        out_md = DOCS / output_rel
        media_dir = out_md.parent / "media"

        if source.suffix.lower() == ".docx":
            pandoc_convert(source, out_md, media_dir)
        else:
            # Si no és DOCX, no el convertim a MD; només creem una pàgina en blanc amb enllaços.
            out_md.parent.mkdir(parents=True, exist_ok=True)
            if not out_md.exists():
                out_md.write_text(f"# {title}\n\n> (Aquest element no prové d'un DOCX, es mostra com a fitxer descarregable.)\n", encoding="utf-8")

        # Gestiona descàrregues
        dl_links = []
        for dl in it.get("downloads", []):
            dl_src = ROOT / dl
            rel_under_assets = pathlib.Path(dl).relative_to("source")
            dl_dest = DOCS / "assets" / rel_under_assets
            copy_asset(dl_src, dl_dest)
            dl_links.append(("assets/" + str(rel_under_assets)).replace("\\", "/"))

        sections[it.get("section","Altres")].append({
            "title": title,
            "page": str(output_rel).replace("\\", "/"),
            "downloads": dl_links
        })

    # (Re)genera docs/continguts.md
    lines = [
        "---",
        "title: Continguts publicats",
        "---",
        "",
        "> ⚠️ Aquesta pàgina es **(re)genera automàticament** a partir de `publish.yaml`.",
        "",
    ]
    for sec in sorted(sections.keys()):
        lines.append(f"## {sec}")
        for el in sections[sec]:
            lines.append(f"- [{el['title']}]({el['page']})")
            if el["downloads"]:
                for li in el["downloads"]:
                    lines.append(f"  - Descàrrega: [{os.path.basename(li)}]({li})")
        lines.append("")
    CONTINGUTS.write_text("\n".join(lines), encoding="utf-8")
    print("Regenerat:", CONTINGUTS)

if __name__ == "__main__":
    main()
