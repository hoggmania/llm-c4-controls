#!/usr/bin/env python3
"""Render an authentic completeness heatmap for the llm-c4-controls control set.
Data is hand-transcribed from CANDIDATE_APPS.md (the 41-row matrix). No invented numbers.
Two panels:
  (A) verdict-distribution bar (counts per verdict tier)
  (B) 41-cell grid, one row per control, colored by verdict tier, labeled by control id + layer
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

# control id, layer, verdict_tier
# tiers: 0 Full, 1 Repurpose, 2 Composite, 3 Arch, 4 Build
data = [
    ("an_dlp","Analyzer",0),("an_rbac","Analyzer",1),("an_inj","Analyzer",2),
    ("an_out","Analyzer",0),("tok_scrub","Tok/Diag",0),("tok_gate","Tok/Diag",1),
    ("tok_rl","Tok/Diag",1),("ss_enc","SemSearch",0),("ss_acl","SemSearch",0),
    ("ss_val","SemSearch",2),("rag_acl","RAG",2),("rag_scr","RAG",2),
    ("rag_red","RAG",0),("rag_out","RAG",2),("sc_inv","Supply",1),
    ("sc_sbom","Supply",2),("sc_train","Supply",4),("sc_cfg","Supply",1),
    ("sc_lic","Supply",1),("post_dlp","PostUse",2),("post_emb","PostUse",4),
    ("post_anom","PostUse",0),("post_drift","PostUse",0),("post_alert","PostUse",2),
    ("post_rt","PostUse",2),("agent","Agent",3),("proposal","Agent",2),
    ("registry","Agent",2),("identity","Agent",0),("param","Agent",2),
    ("pdp","Agent",0),("risk","Agent",2),("approval","Agent",2),
    ("credential","Agent",0),("txn","Agent",2),("proxy","Agent",2),
    ("result","Agent",2),("governor","Agent",2),("resilience","Agent",0),
    ("audit","Agent",2),("kill","Agent",2),
]

labels = [d[0] for d in data]
layers = [d[1] for d in data]
tiers  = np.array([d[2] for d in data], dtype=int)

tier_names = ["Full / near-Full","Partial (repurpose)","Partial (composite)","Architecture-only","Build / emerging"]
tier_colors = ["#2e7d32","#f9a825","#ef6c00","#6a1b9a","#c62828"]
counts = [int((tiers==i).sum()) for i in range(5)]

fig = plt.figure(figsize=(13, 7.2))
fig.suptitle("LLM Data-Exposure Controls — Implementation Completeness (41 components)",
             fontsize=15, fontweight="bold", y=0.97)

# ---- Panel A: distribution bar ----
axA = fig.add_axes([0.06, 0.10, 0.34, 0.78])
ypos = np.arange(len(tier_names))[::-1]
bars = axA.barh(ypos, counts, color=tier_colors, edgecolor="white")
axA.set_yticks(ypos)
axA.set_yticklabels(tier_names, fontsize=10)
axA.invert_yaxis()
axA.set_xlabel("Number of controls", fontsize=10)
axA.set_title("Verdict distribution", fontsize=12, fontweight="bold")
for b,c in zip(bars,counts):
    axA.text(b.get_width()+0.2, b.get_y()+b.get_height()/2, str(c),
             va="center", fontsize=11, fontweight="bold")
axA.set_xlim(0, max(counts)+3)
axA.spines[["top","right"]].set_visible(False)

# ---- Panel B: heatmap grid ----
axB = fig.add_axes([0.46, 0.10, 0.50, 0.78])
n = len(data)
# arrange in 5 columns x 9 rows (45 cells, 41 filled) for readability
ncols = 5
nrows = int(np.ceil(n/ncols))
grid = np.full((nrows, ncols), np.nan)
for i,(cid,_,t) in enumerate(data):
    r = i // ncols
    c = i % ncols
    grid[r, c] = t

from matplotlib.colors import ListedColormap, BoundaryNorm
cmap = ListedColormap(tier_colors)
norm = BoundaryNorm(np.arange(-0.5, 5.5, 1), cmap.N)
axB.imshow(grid, cmap=cmap, norm=norm, aspect="auto")
axB.set_xticks(range(ncols)); axB.set_xticklabels([f"col {i+1}" for i in range(ncols)])
axB.set_yticks(range(nrows)); axB.set_yticklabels([f"" for _ in range(nrows)])
axB.set_title("Per-control verdict (1–41, row-major)", fontsize=12, fontweight="bold")
axB.tick_params(length=0)

# label each cell with its control id
for i,(cid,_,t) in enumerate(data):
    r = i // ncols
    c = i % ncols
    axB.text(c, r, cid, ha="center", va="center", fontsize=7.4,
             color="white" if t in (0,2,3,4) else "black", fontweight="bold")

# legend
legend = [Patch(facecolor=tier_colors[i], label=f"{tier_names[i]} ({counts[i]})") for i in range(5)]
axB.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.08),
           ncol=3, fontsize=8.5, frameon=False)

fig.text(0.46, 0.02,
         "Full = turnkey  ·  Repurpose = wire generic infra (OPA/Vault/KMS)  ·  "
         "Composite = assemble 2–4 tools  ·  Architecture = design discipline  ·  Build = no off-the-shelf",
         fontsize=8, color="#444")

out = "completeness-heatmap.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
print("wrote", out)
