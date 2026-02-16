#!/usr/bin/env python3
"""Generate Resolve architecture diagram - clean white background."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(1, 1, figsize=(18, 11))
fig.patch.set_facecolor('#FFFFFF')
ax.set_facecolor('#FFFFFF')
ax.set_xlim(0, 18)
ax.set_ylim(0, 11)
ax.axis('off')

# ---------------------------------------------------------------------------
# Palette (white-friendly)
# ---------------------------------------------------------------------------
DARK = '#1A1A2E'
GRAY_700 = '#374151'
GRAY_500 = '#6B7280'
GRAY_300 = '#D1D5DB'
GRAY_100 = '#F3F4F6'

BLUE = '#2563EB'
BLUE_BG = '#EFF6FF'
TEAL = '#0D9488'
TEAL_BG = '#F0FDFA'
RED = '#DC2626'
RED_BG = '#FEF2F2'
PURPLE = '#7C3AED'
PURPLE_BG = '#F5F3FF'
GREEN = '#059669'
GREEN_BG = '#ECFDF5'
ORANGE = '#D97706'
ORANGE_BG = '#FFFBEB'
ELASTIC = '#005571'
ELASTIC_BG = '#E8F4F8'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def draw_box(x, y, w, h, facecolor, edgecolor, linewidth=1.5, radius=0.12):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={radius}",
        facecolor=facecolor, edgecolor=edgecolor,
        linewidth=linewidth, zorder=2
    )
    ax.add_patch(rect)

def draw_arrow(x1, y1, x2, y2, color=GRAY_500, lw=1.8, style='-|>', rad=0.08):
    ax.annotate(
        '', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle=style, color=color, lw=lw,
            connectionstyle=f'arc3,rad={rad}',
            shrinkA=4, shrinkB=4
        ), zorder=3
    )

def label(x, y, text, size=10, color=DARK, weight='normal', ha='center', va='center', family='sans-serif'):
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, fontfamily=family, zorder=5)

def mono(x, y, text, size=8.5, color=GRAY_700, ha='left', va='center'):
    ax.text(x, y, text, fontsize=size, color=color, fontfamily='monospace',
            ha=ha, va=va, zorder=5)

def bullet(x, y, text, color=GRAY_700, dot_color=None, size=8.5):
    if dot_color is None:
        dot_color = color
    ax.plot(x, y, 'o', color=dot_color, markersize=4, zorder=5)
    mono(x + 0.2, y, text, color=color, size=size)

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
label(9, 10.5, 'RESOLVE', size=30, weight='bold', color=DARK, family='sans-serif')
label(9, 10.0, 'Intelligent Incident Resolution Agent  |  Elastic Agent Builder', size=11, color=GRAY_500)

# ---------------------------------------------------------------------------
# 6-Step Protocol Bar (top)
# ---------------------------------------------------------------------------
steps = [
    ('1. ASSESS', BLUE, BLUE_BG),
    ('2. INVESTIGATE', PURPLE, PURPLE_BG),
    ('3. CORRELATE', ORANGE, ORANGE_BG),
    ('4. DIAGNOSE', TEAL, TEAL_BG),
    ('5. ACT', RED, RED_BG),
    ('6. VERIFY', GREEN, GREEN_BG),
]
bar_y = 8.95
bar_w = 2.35
bar_h = 0.6
bar_start = 1.0
for i, (step_name, col, bg) in enumerate(steps):
    sx = bar_start + i * 2.7
    draw_box(sx, bar_y, bar_w, bar_h, facecolor=bg, edgecolor=col, linewidth=2, radius=0.08)
    label(sx + bar_w / 2, bar_y + bar_h / 2, step_name, size=9.5, weight='bold', color=col, family='monospace')
    if i < len(steps) - 1:
        ax.annotate(
            '', xy=(sx + bar_w + 0.28, bar_y + bar_h / 2),
            xytext=(sx + bar_w + 0.07, bar_y + bar_h / 2),
            arrowprops=dict(arrowstyle='->', color=GRAY_300, lw=2)
        )

# ---------------------------------------------------------------------------
# Outer container: Elastic Cloud Serverless
# ---------------------------------------------------------------------------
draw_box(0.4, 0.4, 17.2, 8.2, facecolor='#FAFBFC', edgecolor=GRAY_300, linewidth=1.2, radius=0.15)
label(9, 8.35, 'Elastic Cloud Serverless', size=9, color=GRAY_500, weight='bold')

# ---------------------------------------------------------------------------
# KIBANA UI (top-right inside container)
# ---------------------------------------------------------------------------
kb_x, kb_y, kb_w, kb_h = 13.0, 6.3, 4.2, 1.8
draw_box(kb_x, kb_y, kb_w, kb_h, facecolor=BLUE_BG, edgecolor=BLUE, linewidth=1.8)
label(kb_x + kb_w / 2, kb_y + kb_h - 0.3, 'KIBANA UI', size=11, weight='bold', color=BLUE)
bullet(kb_x + 0.3, kb_y + kb_h - 0.7, 'Agent Builder Chat Interface', color=GRAY_700, dot_color=BLUE, size=8)
bullet(kb_x + 0.3, kb_y + kb_h - 1.1, 'Service Health Dashboard (5 panels)', color=GRAY_700, dot_color=BLUE, size=8)
bullet(kb_x + 0.3, kb_y + kb_h - 1.5, 'No custom frontend -- Kibana IS the UI', color=GRAY_500, dot_color=GRAY_300, size=7.5)

# ---------------------------------------------------------------------------
# RESOLVE AGENT (center)
# ---------------------------------------------------------------------------
ag_x, ag_y, ag_w, ag_h = 4.0, 3.6, 8.5, 4.2
draw_box(ag_x, ag_y, ag_w, ag_h, facecolor='#FFFFFF', edgecolor=DARK, linewidth=2.5, radius=0.15)
label(ag_x + ag_w / 2, ag_y + ag_h - 0.35, 'RESOLVE AGENT', size=14, weight='bold', color=DARK)
label(ag_x + ag_w / 2, ag_y + ag_h - 0.75, 'Powered by Claude Sonnet 4.5  |  6-Step Protocol', size=8.5, color=GRAY_500)

# Divider line inside agent
ax.plot([ag_x + 0.3, ag_x + ag_w - 0.3], [ag_y + ag_h - 1.05, ag_y + ag_h - 1.05],
        color=GRAY_300, linewidth=1, zorder=4)

# ES|QL Tools (left column)
esql_x = ag_x + 0.4
esql_top = ag_y + ag_h - 1.4
label(esql_x + 1.5, esql_top, 'ES|QL Tools (4)', size=9, weight='bold', color=BLUE, ha='center')
esql_tools = [
    ('search-error-logs', BLUE),
    ('analyze-error-trends', PURPLE),
    ('check-recent-deployments', ORANGE),
    ('get-service-health', GREEN),
]
for i, (name, col) in enumerate(esql_tools):
    ty = esql_top - 0.45 - i * 0.42
    draw_box(esql_x, ty - 0.15, 3.2, 0.35, facecolor=GRAY_100, edgecolor=col, linewidth=1.2, radius=0.06)
    mono(esql_x + 0.15, ty, name, color=col, size=8)

# Index Search (center column)
idx_x = ag_x + 3.85
idx_top = esql_top
label(idx_x + 1.0, idx_top, 'Index Search (1)', size=9, weight='bold', color=TEAL, ha='center')
draw_box(idx_x, idx_top - 0.6, 2.0, 0.35, facecolor=TEAL_BG, edgecolor=TEAL, linewidth=1.2, radius=0.06)
mono(idx_x + 0.15, idx_top - 0.42, 'search-runbooks', color=TEAL, size=8)
label(idx_x + 1.0, idx_top - 1.1, 'ELSER semantic', size=7.5, color=GRAY_500)
label(idx_x + 1.0, idx_top - 1.4, 'matching', size=7.5, color=GRAY_500)

# Workflow Tools (right column)
wf_x = ag_x + 6.1
wf_top = esql_top
label(wf_x + 1.15, wf_top, 'Workflows (3)', size=9, weight='bold', color=RED, ha='center')
wf_tools = [
    'create-incident',
    'notify-oncall',
    'execute-remediation',
]
for i, name in enumerate(wf_tools):
    ty = wf_top - 0.45 - i * 0.42
    draw_box(wf_x, ty - 0.15, 2.3, 0.35, facecolor=RED_BG, edgecolor=RED, linewidth=1.2, radius=0.06)
    mono(wf_x + 0.15, ty, name, color=RED, size=8)

# ---------------------------------------------------------------------------
# DATA LAYER (bottom-left)
# ---------------------------------------------------------------------------
dl_x, dl_y, dl_w, dl_h = 0.8, 0.7, 5.5, 2.6
draw_box(dl_x, dl_y, dl_w, dl_h, facecolor=TEAL_BG, edgecolor=TEAL, linewidth=1.8)
label(dl_x + dl_w / 2, dl_y + dl_h - 0.3, 'DATA LAYER', size=11, weight='bold', color=TEAL)
label(dl_x + dl_w / 2, dl_y + dl_h - 0.65, '6 Elasticsearch Indices  |  4,098 Documents', size=8, color=GRAY_500)

indices = [
    ('resolve-logs', '2,756', TEAL),
    ('resolve-metrics', '1,320', TEAL),
    ('resolve-deployments', '7', TEAL),
    ('resolve-runbooks', '10', TEAL),
    ('resolve-alerts', '5', TEAL),
    ('resolve-incidents', 'agent', TEAL),
]
for i, (idx_name, count, col) in enumerate(indices):
    row = i // 2
    column = i % 2
    ix = dl_x + 0.3 + column * 2.7
    iy = dl_y + dl_h - 1.05 - row * 0.45
    mono(ix, iy, f'{idx_name}', color=DARK, size=7.5)
    mono(ix + 2.1, iy, f'({count})', color=GRAY_500, size=7)

# ---------------------------------------------------------------------------
# ACTIONS & OUTPUT (bottom-right)
# ---------------------------------------------------------------------------
ac_x, ac_y, ac_w, ac_h = 11.7, 0.7, 5.5, 2.6
draw_box(ac_x, ac_y, ac_w, ac_h, facecolor=RED_BG, edgecolor=RED, linewidth=1.8)
label(ac_x + ac_w / 2, ac_y + ac_h - 0.3, 'ACTIONS & OUTPUT', size=11, weight='bold', color=RED)

actions = [
    'Incident Record Creation',
    'On-Call Webhook Notification',
    'Remediation Action Logging',
    'Root Cause Analysis Report',
    'Evidence Chain Timeline',
    'MTTR Calculation',
]
for i, action in enumerate(actions):
    row = i // 2
    column = i % 2
    bx = ac_x + 0.3 + column * 2.7
    by = ac_y + ac_h - 0.75 - row * 0.45
    bullet(bx, by, action, color=GRAY_700, dot_color=RED, size=7.5)

# ---------------------------------------------------------------------------
# Arrows
# ---------------------------------------------------------------------------
# Kibana -> Agent
draw_arrow(kb_x, kb_y + 0.3, ag_x + ag_w - 0.5, ag_y + ag_h, color=BLUE, lw=2, rad=0.15)
label(11.8, 7.95, 'user prompt', size=7.5, color=BLUE)

# Agent <-> Data Layer
draw_arrow(ag_x + 1.0, ag_y, dl_x + dl_w - 0.5, dl_y + dl_h, color=TEAL, lw=2, rad=0.12)
label(3.5, 3.25, 'ES|QL queries', size=7.5, color=TEAL)

draw_arrow(dl_x + dl_w - 0.5, dl_y + dl_h - 0.3, ag_x + 0.5, ag_y + 0.3, color=TEAL, lw=2, rad=-0.12)
label(3.5, 2.75, 'results', size=7.5, color=TEAL)

# Agent -> Actions
draw_arrow(ag_x + ag_w - 1.0, ag_y, ac_x + 0.5, ac_y + ac_h, color=RED, lw=2, rad=-0.12)
label(13.0, 3.25, 'workflow execution', size=7.5, color=RED)

# ---------------------------------------------------------------------------
# Legend bar at very bottom
# ---------------------------------------------------------------------------
ly = 0.15
legend_items = [
    ('ES|QL Tools (4)', BLUE),
    ('Index Search (1)', TEAL),
    ('Workflow Tools (3)', RED),
    ('8 Tools Total', GRAY_500),
]
lx = 4.5
for text, col in legend_items:
    ax.plot(lx, ly, 's', color=col, markersize=7, zorder=5)
    mono(lx + 0.2, ly, text, color=col, size=8)
    lx += 3.0

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
plt.tight_layout()
plt.savefig('docs/screenshots/01-architecture.png', dpi=200, bbox_inches='tight',
            facecolor='#FFFFFF', edgecolor='none')
plt.savefig('docs/resolve-architecture.png', dpi=200, bbox_inches='tight',
            facecolor='#FFFFFF', edgecolor='none')
print("Saved docs/screenshots/01-architecture.png")
print("Saved docs/resolve-architecture.png")
