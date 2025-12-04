"""
Plotting functions for Figure 4, Panels A & B: SOFA and OASIS boxplots by subgroup.
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, List


# Subgroup colors matching paper's palette
# 1:white, 2:red, 3:green, 4:blue, 5:cyan, 6:magenta
SUBGROUP_COLORS = {
    1: 'white',
    2: '#E74C3C',
    3: '#27AE60',
    4: '#1F77B4',
    5: '#17BECF',
    6: '#E377C2'
}


def colored_boxplot(ax, data: pd.DataFrame, ycol: str, order: Optional[List[int]] = None):
    """
    Create a colored boxplot for a given column by subgroup.
    
    Args:
        ax: Matplotlib axis to plot on
        data: DataFrame with subgroup_K6 and the ycol column
        ycol: Column name to plot
        order: Order of subgroups to display
    """
    if order is None:
        order = [1, 2, 3, 4, 5, 6]
    plot_data = [data.loc[data['subgroup_K6'] == k, ycol].dropna() for k in order]
    colors_list = [SUBGROUP_COLORS.get(k, 'gray') for k in order]
    
    bp = ax.boxplot(plot_data, labels=order, showfliers=True, patch_artist=True)
    
    # Color the boxes
    for patch, c in zip(bp['boxes'], colors_list):
        patch.set_facecolor(c)
        patch.set_edgecolor('black')
    
    # Style whiskers and caps
    for w in bp['whiskers'] + bp['caps']:
        w.set_color('black')
    
    # Style medians
    for m in bp['medians']:
        m.set_color('black')
        m.set_linewidth(2)
    
    ax.set_xlabel('Subgroup')


def plot_fig_4_ab(data: pd.DataFrame, 
                  output_path: Optional[str] = None,
                  figsize: tuple = (10, 4)) -> plt.Figure:
    """
    Create Figure 4 Panels A & B: SOFA and OASIS boxplots by subgroup.
    
    Args:
        data: Merged DataFrame with subgroup_K6, sofa, and oasis columns
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure size tuple
    
    Returns:
        Matplotlib Figure object
    """
    # Filter to valid subgroups
    plot_data = data[data['subgroup_K6'].between(1, 6)].copy()
    
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # Panel A: SOFA scores
    colored_boxplot(axes[0], plot_data, 'sofa')
    axes[0].set_title('A')
    axes[0].set_ylabel('SOFA score')
    
    # Panel B: OASIS scores
    colored_boxplot(axes[1], plot_data, 'oasis')
    axes[1].set_title('B')
    axes[1].set_ylabel('OASIS score')
    
    plt.tight_layout()
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    return fig

