#!/usr/bin/env python3
"""Generate Resolve agent reasoning trace flowchart - clean white background."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(1, 1, figsize=(12, 18))
fig.patch.set_facecolor('#FFFFFF')
ax.set_facecolor('#FFFFFF')
ax.set_xlim(0, 12)
ax.set_ylim(0, 18)
ax.axis('off')

# ---------------------------------------------------------------------------
# Palette
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
DARK_BG = '#1E293B'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def draw_box(x, y, w, h, facecolor, edgecolor, lw=1.5, rad=0.1):
    rect = FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad={rad}",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, zorder=2
    )
    ax.add_patch(rect)

def label(x, y, text, size=10, color=DARK, weight='normal', ha='center',
          va='center', family='sans-serif'):
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, fontfamily=family, zorder=5)

def mono(x, y, text, size=8, color=GRAY_700, ha='center', va='center'):
    ax.text(x, y, text, fontsize=size, color=color, fontfamily='monospace',
            ha=ha, va=va, zorder=5)

def draw_arrow(x1, y1, x2, y2, color=GRAY_300, lw=1.8):
    ax.annotate(
        '', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle='->', color=color, lw=lw,
            shrinkA=2, shrinkB=2
        ), zorder=3
    )

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
NODE_W = 6.0        # node width
NODE_H = 1.05       # node height
NODE_X = 2.0        # left edge of nodes (centered around x=5)
CX = NODE_X + NODE_W / 2   # center x of nodes = 5.0
ARROW_COLOR = GRAY_300
TIME_X = 9.2        # x for timing annotations
LABEL_X = 9.2       # x for arrow labels (right side)

# Y positions for each of the 10 nodes (top to bottom)
# Total space: ~17.0 top to ~2.0 bottom, 10 nodes
TOP_Y = 16.5
SPACING = 1.42
node_ys = [TOP_Y - i * SPACING for i in range(10)]

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
label(6.0, 17.75, 'RESOLVE: REASONING TRACE', size=22, weight='bold', color=DARK)
label(6.0, 17.35, 'Autonomous Investigation Flow  |  10 Tool Calls  |  113 Seconds', size=9, color=GRAY_500)

# ---------------------------------------------------------------------------
# Node definitions
# ---------------------------------------------------------------------------
nodes = [
    {
        'label': 'USER PROMPT',
        'detail': '"Critical alert on order-service..."',
        'bg': DARK_BG,
        'edge': DARK_BG,
        'text_color': '#FFFFFF',
        'detail_color': '#94A3B8',
        'time': '',
    },
    {
        'label': 'ASSESS',
        'detail': 'get-service-health + search-error-logs',
        'bg': BLUE_BG,
        'edge': BLUE,
        'text_color': BLUE,
        'detail_color': GRAY_700,
        'time': '+0s',
    },
    {
        'label': 'INVESTIGATE',
        'detail': 'analyze-error-trends (order-service)',
        'bg': BLUE_BG,
        'edge': BLUE,
        'text_color': BLUE,
        'detail_color': GRAY_700,
        'time': '+12s',
    },
    {
        'label': 'INVESTIGATE',
        'detail': 'analyze-error-trends (payment-service)',
        'bg': BLUE_BG,
        'edge': BLUE,
        'text_color': BLUE,
        'detail_color': GRAY_700,
        'time': '+28s',
    },
    {
        'label': 'CORRELATE',
        'detail': 'check-recent-deployments',
        'bg': BLUE_BG,
        'edge': BLUE,
        'text_color': BLUE,
        'detail_color': GRAY_700,
        'time': '+41s',
    },
    {
        'label': 'ASSESS (deep)',
        'detail': 'search-error-logs (2h window)',
        'bg': BLUE_BG,
        'edge': BLUE,
        'text_color': BLUE,
        'detail_color': GRAY_700,
        'time': '+55s',
    },
    {
        'label': 'DIAGNOSE',
        'detail': 'search-runbooks (ELSER)',
        'bg': TEAL_BG,
        'edge': TEAL,
        'text_color': TEAL,
        'detail_color': GRAY_700,
        'time': '+68s',
    },
    {
        'label': 'ACT',
        'detail': 'create-incident',
        'bg': RED_BG,
        'edge': RED,
        'text_color': RED,
        'detail_color': GRAY_700,
        'time': '+82s',
    },
    {
        'label': 'ACT',
        'detail': 'notify-oncall',
        'bg': RED_BG,
        'edge': RED,
        'text_color': RED,
        'detail_color': GRAY_700,
        'time': '+95s',
    },
    {
        'label': 'ACT',
        'detail': 'execute-remediation',
        'bg': RED_BG,
        'edge': RED,
        'text_color': RED,
        'detail_color': GRAY_700,
        'time': '+108s',
    },
]

# Arrow labels (between node i and node i+1)
arrow_labels = [
    '5 services checked, order-service errors found',
    'Error rate: 0.2% -> 44.3%',
    'Cascading: 0.1% -> 15.3%',
    'v2.4.1 by bob.kumar -- pool 50->5',
    '50 errors: DB_POOL_EXHAUSTED, CIRCUIT_OPEN',
    'Match: DB Connection Pool Exhaustion Runbook',
    'INC-JEsRaJwB created',
    'On-call team notified',
    'Rollback v2.4.1 -> v2.3.9 logged',
]

# ---------------------------------------------------------------------------
# Draw nodes
# ---------------------------------------------------------------------------
for i, node in enumerate(nodes):
    y = node_ys[i]
    # Box
    draw_box(NODE_X, y, NODE_W, NODE_H, facecolor=node['bg'],
             edgecolor=node['edge'], lw=2.0, rad=0.1)

    # Step number badge (small circle on left)
    if i > 0:
        badge_x = NODE_X + 0.35
        badge_y = y + NODE_H / 2
        circle = plt.Circle((badge_x, badge_y), 0.2, facecolor=node['edge'],
                             edgecolor='none', zorder=4)
        ax.add_patch(circle)
        label(badge_x, badge_y, str(i), size=8.5, weight='bold',
              color='#FFFFFF')

    # Label text
    lbl_offset = 0.35 if i > 0 else 0.0
    label(CX + lbl_offset, y + NODE_H * 0.65, node['label'],
          size=12, weight='bold', color=node['text_color'])
    mono(CX + lbl_offset, y + NODE_H * 0.28, node['detail'],
         size=7.5, color=node['detail_color'])

    # Timing annotation on the right
    if node['time']:
        label(TIME_X, y + NODE_H / 2, node['time'],
              size=9, color=GRAY_500, weight='bold', family='monospace')

# ---------------------------------------------------------------------------
# Draw arrows between nodes + arrow labels
# ---------------------------------------------------------------------------
for i in range(len(nodes) - 1):
    y_from = node_ys[i]
    y_to = node_ys[i + 1]

    # Vertical arrow from bottom of node i to top of node i+1
    draw_arrow(CX, y_from, CX, y_to + NODE_H, color=ARROW_COLOR, lw=1.5)

    # Arrow label to the right of the arrow, vertically centered in the gap
    mid_y = (y_from + y_to + NODE_H) / 2
    arrow_text = arrow_labels[i]

    # Draw a subtle label background
    txt_len = len(arrow_text) * 0.055 + 0.4
    # Position label to the left, next to the arrow
    label(CX - 0.1, mid_y, arrow_text,
          size=6.8, color=GRAY_500, ha='center', family='sans-serif',
          weight='normal')

# ---------------------------------------------------------------------------
# Summary bar at bottom
# ---------------------------------------------------------------------------
summary_y = 1.3
draw_box(0.8, summary_y, 10.4, 1.4, facecolor=GRAY_100, edgecolor=GRAY_300,
         lw=1.2, rad=0.12)

label(6.0, summary_y + 1.05, '13 LLM calls  |  10 tool calls  |  148K tokens  |  113 seconds',
      size=9.5, weight='bold', color=DARK, family='monospace')

label(6.0, summary_y + 0.6,
      'MTTR: 22 minutes  |  Root cause: DB pool misconfiguration',
      size=9, color=GRAY_700, family='sans-serif')

# Color legend in summary bar
legend_items = [
    ('ES|QL', BLUE),
    ('Index Search', TEAL),
    ('Workflow', RED),
    ('Reasoning', GRAY_500),
]
lx_start = 2.2
for txt, col in legend_items:
    ax.plot(lx_start, summary_y + 0.2, 's', color=col, markersize=6, zorder=5)
    mono(lx_start + 0.2, summary_y + 0.2, txt, size=7.5, color=col, ha='left')
    lx_start += 2.3

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
plt.tight_layout()
plt.savefig('docs/screenshots/11-reasoning-trace.png', dpi=200,
            bbox_inches='tight', facecolor='#FFFFFF', edgecolor='none')
plt.savefig('docs/resolve-reasoning-trace.png', dpi=200,
            bbox_inches='tight', facecolor='#FFFFFF', edgecolor='none')
print("Saved docs/screenshots/11-reasoning-trace.png")
print("Saved docs/resolve-reasoning-trace.png")
