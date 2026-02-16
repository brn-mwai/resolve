#!/usr/bin/env python3
"""Generate Resolve architecture diagram for Devpost submission."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

fig, ax = plt.subplots(1, 1, figsize=(16, 10))
fig.patch.set_facecolor('#0D1117')
ax.set_facecolor('#0D1117')
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis('off')

# Colors
ELASTIC_TEAL = '#00BFB3'
ELASTIC_DARK = '#1B2A4A'
ACCENT_RED = '#FF4444'
ACCENT_BLUE = '#3B82F6'
ACCENT_PURPLE = '#8B5CF6'
ACCENT_GREEN = '#10B981'
ACCENT_ORANGE = '#F59E0B'
TEXT_WHITE = '#E6EDF3'
TEXT_GRAY = '#8B949E'
BG_CARD = '#161B22'
BORDER = '#30363D'

def draw_card(x, y, w, h, title, items=None, color=ELASTIC_TEAL, alpha=0.15):
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                          facecolor=color, alpha=alpha, edgecolor=color, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.25, title, ha='center', va='top',
            fontsize=11, fontweight='bold', color=color, fontfamily='monospace')
    if items:
        for i, item in enumerate(items):
            ax.text(x + 0.2, y + h - 0.65 - i*0.32, item, ha='left', va='top',
                    fontsize=8, color=TEXT_GRAY, fontfamily='monospace')

def draw_arrow(x1, y1, x2, y2, color=ELASTIC_TEAL, style='->', lw=1.5):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, connectionstyle='arc3,rad=0.1'))

# Title
ax.text(8, 9.6, 'RESOLVE', ha='center', va='center', fontsize=28, fontweight='bold',
        color=ACCENT_RED, fontfamily='monospace')
ax.text(8, 9.15, 'Intelligent Incident Resolution Agent', ha='center', va='center',
        fontsize=12, color=TEXT_GRAY, fontfamily='monospace')

# Protocol steps bar
steps = ['ASSESS', 'INVESTIGATE', 'CORRELATE', 'DIAGNOSE', 'ACT', 'VERIFY']
step_colors = [ACCENT_BLUE, ACCENT_PURPLE, ACCENT_ORANGE, ACCENT_GREEN, ACCENT_RED, ELASTIC_TEAL]
for i, (step, col) in enumerate(zip(steps, step_colors)):
    sx = 1.2 + i * 2.3
    rect = FancyBboxPatch((sx, 8.25), 2.0, 0.55, boxstyle="round,pad=0.08",
                          facecolor=col, alpha=0.25, edgecolor=col, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(sx + 1.0, 8.52, step, ha='center', va='center', fontsize=9,
            fontweight='bold', color=col, fontfamily='monospace')
    if i < len(steps) - 1:
        ax.annotate('', xy=(sx + 2.2, 8.52), xytext=(sx + 2.05, 8.52),
                    arrowprops=dict(arrowstyle='->', color=TEXT_GRAY, lw=1))

# Agent box (center)
agent_rect = FancyBboxPatch((5.5, 5.0), 5, 2.8, boxstyle="round,pad=0.15",
                            facecolor=ACCENT_RED, alpha=0.1, edgecolor=ACCENT_RED, linewidth=2)
ax.add_patch(agent_rect)
ax.text(8, 7.45, 'RESOLVE AGENT', ha='center', va='center', fontsize=14,
        fontweight='bold', color=ACCENT_RED, fontfamily='monospace')
ax.text(8, 7.05, 'Powered by Claude Opus 4.5', ha='center', va='center', fontsize=9,
        color=TEXT_GRAY, fontfamily='monospace')

# Tools inside agent
tools_left = [
    ('search-error-logs', 'ES|QL', ACCENT_BLUE),
    ('analyze-error-trends', 'ES|QL', ACCENT_PURPLE),
    ('check-deployments', 'ES|QL', ACCENT_ORANGE),
    ('get-service-health', 'ES|QL', ACCENT_GREEN),
]
tools_right = [
    ('search-runbooks', 'ELSER', ELASTIC_TEAL),
    ('create-incident', 'Workflow', ACCENT_RED),
    ('notify-oncall', 'Workflow', ACCENT_RED),
    ('execute-remediation', 'Workflow', ACCENT_RED),
]
for i, (name, ttype, col) in enumerate(tools_left):
    ty = 6.5 - i * 0.38
    ax.text(5.8, ty, f'{name}', ha='left', va='center', fontsize=7.5,
            color=col, fontfamily='monospace')

for i, (name, ttype, col) in enumerate(tools_right):
    ty = 6.5 - i * 0.38
    ax.text(8.5, ty, f'{name}', ha='left', va='center', fontsize=7.5,
            color=col, fontfamily='monospace')

# Data layer (bottom left)
draw_card(0.3, 0.5, 4.5, 4.0, 'DATA LAYER', [
    'resolve-logs        (2,756 docs)',
    'resolve-metrics     (1,320 docs)',
    'resolve-deployments (7 docs)',
    'resolve-runbooks    (10 docs)',
    'resolve-alerts      (5 docs)',
    'resolve-incidents   (agent writes)',
    '',
    'semantic_text + ELSER inference',
    'Elastic Cloud Serverless',
], ELASTIC_TEAL)

# Action layer (bottom right)
draw_card(11.2, 0.5, 4.5, 4.0, 'ACTIONS & OUTPUT', [
    'Incident Record Creation',
    'On-Call Webhook Notification',
    'Remediation Action Logging',
    '',
    'Formal Incident Report:',
    '  - Root Cause Analysis',
    '  - Evidence Chain Timeline',
    '  - MTTR Calculation',
    '  - Remediation Recommendation',
], ACCENT_RED)

# Kibana box (top right)
draw_card(12.5, 6.5, 3.2, 2.8, 'KIBANA UI', [
    'Agent Builder Chat',
    'Service Health Dashboard',
    '5 Visualization Panels',
    '',
    'No custom frontend',
    'Kibana IS the UI',
], ACCENT_BLUE)

# Arrows: Agent <-> Data
draw_arrow(5.5, 5.8, 4.8, 4.5, ELASTIC_TEAL)
draw_arrow(4.8, 3.5, 5.5, 5.2, ELASTIC_TEAL)

# Arrows: Agent -> Actions
draw_arrow(10.5, 5.8, 11.2, 4.5, ACCENT_RED)

# Arrows: Kibana -> Agent
draw_arrow(12.5, 7.2, 10.5, 6.8, ACCENT_BLUE)

# Legend
legend_y = 0.15
ax.text(5.5, legend_y, 'ES|QL', fontsize=8, color=ACCENT_BLUE, fontfamily='monospace', fontweight='bold')
ax.text(6.8, legend_y, 'Index Search', fontsize=8, color=ELASTIC_TEAL, fontfamily='monospace', fontweight='bold')
ax.text(8.6, legend_y, 'Workflows', fontsize=8, color=ACCENT_RED, fontfamily='monospace', fontweight='bold')
ax.text(10.2, legend_y, '8 Tools Total', fontsize=8, color=TEXT_GRAY, fontfamily='monospace')

plt.tight_layout()
plt.savefig('docs/resolve-architecture.png', dpi=200, bbox_inches='tight',
            facecolor='#0D1117', edgecolor='none')
print("Saved docs/resolve-architecture.png")
