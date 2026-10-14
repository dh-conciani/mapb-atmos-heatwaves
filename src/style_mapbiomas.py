from pathlib import Path
import matplotlib as mpl

COLORS = {
    'green': '#0B6E4F',
    'teal': '#56B6C7',
    'orange': '#F2A23A',
    'purple': '#8E2CA2',
    'v1': '#7FAFC1',
    'v2': '#8E2CA2',
    'station': '#222222',
    'text': '#26332C',
    'mid': '#5B675F',
    'light': '#EFF4EF',
    'pale': '#F6F7F3',
    'warm': '#FFF6E8',
}

MONTHS_PT = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']


def apply_style():
    mpl.rcParams.update({
        'font.family': 'DejaVu Sans',
        'font.size': 10,
        'axes.titlesize': 13,
        'axes.titleweight': 'bold',
        'axes.labelsize': 10,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.edgecolor': '#C9D2CC',
        'axes.labelcolor': COLORS['text'],
        'xtick.color': COLORS['mid'],
        'ytick.color': COLORS['mid'],
        'text.color': COLORS['text'],
        'grid.color': '#DDE5E0',
        'grid.alpha': 0.55,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'savefig.facecolor': 'white',
    })


def ensure_dirs(*paths):
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)
