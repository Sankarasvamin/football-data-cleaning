import pandas as pd
import os
import glob
import re
from graphviz import Digraph

DATA_DIR = "/Users/apple/Desktop/surviveFdu/数据库与企业数据管理/maindata"  # 改成你的 CSV 目录
OUTPUT   = "er_diagram"

# ── 1. 读取表结构（只采样，不全量加载）──────────────────────────────────────
def load_schemas(data_dir, sample_rows=300):
    tables = {}
    for fp in sorted(glob.glob(os.path.join(data_dir, "*.csv"))):
        raw_name = os.path.splitext(os.path.basename(fp))[0]
        name = re.sub(r"[\s\(\)]", "_", raw_name).strip("_")
        try:
            df = pd.read_csv(fp, nrows=sample_rows, low_memory=False)
            tables[name] = {"df": df, "cols": list(df.columns), "dtypes": df.dtypes}
            print(f"  ✓ {name:35s} {len(df.columns)} cols")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
    return tables

# ── 2. 外键推断 ──────────────────────────────────────────────────────────────
def detect_fks(tables):
    fks = []
    names = list(tables.keys())

    for src, info in tables.items():
        for col in info["cols"]:
            cl = col.lower()
            if not cl.endswith("_id") or cl == "id":
                continue
            base = cl[:-3]  # e.g. "team_id" → "team"

            for tgt in names:
                if tgt == src:
                    continue
                # 去掉性别前缀再比较
                tgt_base = re.sub(r"^(male|female)_", "", tgt.lower())
                if base in (tgt_base, tgt_base.rstrip("s"), tgt_base + "s", tgt.lower()):
                    tgt_cols_lower = [c.lower() for c in tables[tgt]["cols"]]
                    if "id" in tgt_cols_lower:
                        fks.append((src, col, tgt, "id"))
                        break
    return fks

# ── 3. dtype → 简短标签 ──────────────────────────────────────────────────────
def dtype_tag(dt):
    s = str(dt)
    if "int"      in s: return "INT"
    if "float"    in s: return "FLOAT"
    if "bool"     in s: return "BOOL"
    if "datetime" in s: return "DATE"
    return "TEXT"

# ── 4. 绘图 ──────────────────────────────────────────────────────────────────
PALETTE = {
    "female": {"hdr": "#C2185B", "bg": "#2a1020", "border": "#E91E8C"},
    "male":   {"hdr": "#1565C0", "bg": "#0d1a2a", "border": "#1E90FF"},
}
DEFAULT_PAL = {"hdr": "#2E7D32", "bg": "#0d1f0d", "border": "#4CAF50"}

def table_label(name, info, fk_cols):
    p = PALETTE.get("female" if "female" in name else ("male" if "male" in name else "x"), DEFAULT_PAL)
    rows = ""
    for col in info["cols"]:
        cl = col.lower()
        tag  = dtype_tag(info["dtypes"][col])
        flag = "[PK]" if cl == "id" else ("[FK]" if col in fk_cols else "")
        bold_open  = "<B>" if cl == "id" else ""
        bold_close = "</B>" if cl == "id" else ""
        flag_color = "#FFD700" if flag else "#888888"
        rows += (
            f'<TR>'
            f'<TD ALIGN="LEFT" PORT="{col}" BGCOLOR="{p["bg"]}">'
            f'<FONT COLOR="white" FACE="Helvetica" POINT-SIZE="10">'
            f'{bold_open}{col}{bold_close}</FONT></TD>'
            f'<TD ALIGN="CENTER" BGCOLOR="{p["bg"]}">'
            f'<FONT COLOR="#aaaaaa" FACE="Helvetica" POINT-SIZE="9">{tag}</FONT></TD>'
            f'<TD ALIGN="CENTER" BGCOLOR="{p["bg"]}">'
            f'<FONT COLOR="{flag_color}" FACE="Helvetica-Bold" POINT-SIZE="9">{flag}</FONT></TD>'
            f'</TR>'
        )
    display = name.replace("_legacy_", "\n(legacy)\n")
    return (
        f'<<TABLE BORDER="2" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5" '
        f'COLOR="{p["border"]}" BGCOLOR="{p["bg"]}">'
        f'<TR><TD COLSPAN="3" BGCOLOR="{p["hdr"]}" ALIGN="CENTER">'
        f'<FONT COLOR="white" FACE="Helvetica-Bold" POINT-SIZE="12"><B>{display}</B></FONT>'
        f'</TD></TR>'
        f'{rows}'
        f'</TABLE>>'
    )

def draw(tables, fks, output=OUTPUT):
    dot = Digraph("ER", format="png")
    dot.attr(
        rankdir="LR", splines="polyline",
        nodesep="0.6", ranksep="2.0",
        bgcolor="#12121f", fontname="Helvetica", pad="0.8",
        dpi="180"
    )

    # 收集每张表的 FK 列名
    fk_map = {t: set() for t in tables}
    for src, sc, tgt, tc in fks:
        fk_map[src].add(sc)

    # 节点
    for name, info in tables.items():
        dot.node(name, label=table_label(name, info, fk_map[name]),
                 shape="none", margin="0")

    # 子图分组
    for gender, color in [("female", "#E91E8C"), ("male", "#1E90FF")]:
        with dot.subgraph(name=f"cluster_{gender}") as sg:
            sg.attr(label=gender.capitalize(), style="rounded,dashed",
                    color=color, fontcolor=color, fontsize="14", penwidth="1.5")
            for t in tables:
                if gender in t:
                    sg.node(t)

    # 边
    seen = set()
    for src, sc, tgt, tc in fks:
        key = (src, sc, tgt)
        if key in seen:
            continue
        seen.add(key)
        dot.edge(
            f"{src}:{sc}", f"{tgt}:{tc}",
            color="#FFD700", penwidth="1.8",
            arrowhead="crow", arrowtail="odot", dir="both",
            style="dashed", constraint="true"
        )

    dot.render(output, cleanup=True, view=True)
    print(f"\n  → Saved: {output}.png")

# ── main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading schemas...")
    tables = load_schemas(DATA_DIR)

    print("\nDetecting foreign keys...")
    fks = detect_fks(tables)
    for src, sc, tgt, tc in fks:
        print(f"  {src}.{sc}  →  {tgt}.{tc}")

    print("\nRendering E-R diagram...")
    draw(tables, fks)