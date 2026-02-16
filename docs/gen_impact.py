#!/usr/bin/env python3
"""Generate impact comparison chart - clean white background."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(16, 8))
fig.patch.set_facecolor('#FFFFFF')
ax.set_facecolor('#FFFFFF')
ax.set_xlim(0, 16)
ax.set_ylim(0, 8)
ax.axis('off')

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
DARK = '#1A1A2E'
GRAY_700 = '#374151'
GRAY_500 = '#6B7280'
GRAY_300 = '#D1D5DB'
GRAY_100 = '#F3F4F6'
RED = '#DC2626'
RED_BG = '#FEF2F2'
GREEN = '#059669'
GREEN_BG = '#ECFDF5'
TEAL = '#0D9488'
BLUE = '#2563EB'

def draw_box(x, y, w, h, facecolor, edgecolor, lw=1.5, rad=0.1):
    rect = FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad={rad}",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, zorder=2
    )
    ax.add_patch(rect)

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
ax.text(8, 7.5, 'RESOLVE: MEASURABLE IMPACT', ha='center', va='center',
        fontsize=24, fontweight='bold', color=DARK, fontfamily='sans-serif')
ax.text(8, 7.05, 'Before vs After  --  Manual Incident Response vs Resolve Agent',
        ha='center', va='center', fontsize=10, color=GRAY_500, fontfamily='sans-serif')

# ---------------------------------------------------------------------------
# Column Headers
# ---------------------------------------------------------------------------
# Metric column
ax.text(4.2, 6.35, 'METRIC', ha='center', va='center',
        fontsize=10, fontweight='bold', color=GRAY_500, fontfamily='sans-serif')

# Before column
draw_box(6.5, 6.1, 3.5, 0.55, facecolor=RED_BG, edgecolor=RED, lw=1.5, rad=0.08)
ax.text(8.25, 6.37, 'BEFORE (Manual)', ha='center', va='center',
        fontsize=11, fontweight='bold', color=RED, fontfamily='sans-serif')

# After column
draw_box(10.3, 6.1, 3.5, 0.55, facecolor=GREEN_BG, edgecolor=GREEN, lw=1.5, rad=0.08)
ax.text(12.05, 6.37, 'AFTER (Resolve)', ha='center', va='center',
        fontsize=11, fontweight='bold', color=GREEN, fontfamily='sans-serif')

# Improvement column
ax.text(14.8, 6.35, 'GAIN', ha='center', va='center',
        fontsize=10, fontweight='bold', color=GRAY_500, fontfamily='sans-serif')

# ---------------------------------------------------------------------------
# Separator line under headers
# ---------------------------------------------------------------------------
ax.plot([1.2, 14.8], [5.95, 5.95], color=GRAY_300, linewidth=1.2, zorder=3)

# ---------------------------------------------------------------------------
# Metrics rows
# ---------------------------------------------------------------------------
metrics = [
    ('Mean Time To Resolution', '45 minutes', '< 5 minutes', '90% faster'),
    ('Steps to Diagnose', '8-12 manual steps', '6 automated steps', 'Autonomous'),
    ('Services Correlated', '1-2 (human limit)', 'All 5 simultaneously', '3x coverage'),
    ('Runbook Search Time', '5-10 minutes', '< 10 seconds', 'Semantic'),
    ('Data Sources Queried', '1-2 dashboards', '4 indices, 4,098 docs', 'Complete'),
    ('On-Call Notification', '5+ min (manual page)', 'Instant (workflow)', 'Automated'),
]

for i, (metric, before, after, gain) in enumerate(metrics):
    y = 5.45 - i * 0.82

    # Alternating row background
    if i % 2 == 0:
        draw_box(1.0, y - 0.32, 13.9, 0.72, facecolor=GRAY_100, edgecolor=GRAY_100, lw=0, rad=0.06)

    # Metric name
    ax.text(1.3, y, metric, ha='left', va='center',
            fontsize=10, fontweight='bold', color=DARK, fontfamily='sans-serif')

    # Before value
    ax.text(8.25, y, before, ha='center', va='center',
            fontsize=10.5, color=RED, fontfamily='monospace', fontweight='bold')

    # After value
    ax.text(12.05, y, after, ha='center', va='center',
            fontsize=10.5, color=GREEN, fontfamily='monospace', fontweight='bold')

    # Gain badge
    draw_box(14.0, y - 0.18, 1.6, 0.36, facecolor=GREEN_BG, edgecolor=GREEN, lw=1, rad=0.06)
    ax.text(14.8, y, gain, ha='center', va='center',
            fontsize=8.5, fontweight='bold', color=GREEN, fontfamily='sans-serif')

    # Row separator
    if i < len(metrics) - 1:
        ax.plot([1.2, 14.8], [y - 0.41, y - 0.41], color=GRAY_300, linewidth=0.5, zorder=3)

# ---------------------------------------------------------------------------
# Bottom tagline
# ---------------------------------------------------------------------------
ax.text(8, 0.45, 'Built with Elastic Agent Builder  |  ES|QL + ELSER + Workflows  |  8 Tools  |  6 Indices',
        ha='center', va='center', fontsize=9, color=GRAY_500, fontfamily='sans-serif')

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
plt.tight_layout()
plt.savefig('docs/screenshots/10-impact.png', dpi=200, bbox_inches='tight',
            facecolor='#FFFFFF', edgecolor='none')
print("Saved docs/screenshots/10-impact.png")
