"""
Plotting functions for Figure 4, Panel C: Prevalence of organ dysfunction & sepsis by subgroup.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Tuple


# Subgroup colors matching paper's palette
SUBGROUP_COLORS = {
    1: '#FFFFFF',
    2: '#E41A1C',
    3: '#4DAF4A',
    4: '#377EB8',
    5: '#4DD2D2',
    6: '#E377C2'
}


def wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """
    Calculate Wilson confidence interval for a proportion.
    
    Args:
        k: Number of successes
        n: Total number of trials
        z: Z-score for confidence level (default 1.96 for 95% CI)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n == 0:
        return np.nan, np.nan
    
    p = k / n
    den = 1 + z**2 / n
    cen = (p + z**2 / (2 * n)) / den
    half = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / den
    return cen - half, cen + half


def calculate_prevalence_stats(data: pd.DataFrame, flag_col: str) -> pd.DataFrame:
    """
    Calculate prevalence statistics with Wilson CIs by subgroup.
    
    Args:
        data: DataFrame with subgroup_K6 and the flag column
        flag_col: Column name of the binary flag to analyze
    
    Returns:
        DataFrame with subgroup, n, p, lo, hi, err_low, err_high
    """
    # Clean data
    df = data.copy()
    df = df.drop_duplicates(subset=['subject_id', 'hadm_id'])
    df['subgroup_K6'] = pd.to_numeric(df['subgroup_K6'], errors='coerce').astype('Int64')
    df = df[df['subgroup_K6'].between(1, 6)].copy()
    df[flag_col] = pd.to_numeric(df[flag_col], errors='coerce').fillna(0).astype(int)
    
    # Calculate statistics by subgroup
    groups = []
    for sg, sub in df.groupby('subgroup_K6'):
        n = len(sub)
        k = sub[flag_col].sum()
        p = k / n if n > 0 else np.nan
        lo, hi = wilson_ci(k, n)
        
        groups.append({
            'subgroup': int(sg),
            'n': n,
            'p': 100 * p,
            'lo': 100 * lo,
            'hi': 100 * hi,
            'err_low': 100 * (p - lo),
            'err_high': 100 * (hi - p)
        })
    
    stats = pd.DataFrame(groups).sort_values('subgroup')
    return stats


def plot_fig_4_c(data: pd.DataFrame,
                 output_path: Optional[str] = None,
                 figsize: tuple = (6, 4)) -> plt.Figure:
    """
    Create Figure 4 Panel C: Prevalence of organ dysfunction & sepsis by subgroup.
    
    Args:
        data: Merged DataFrame with subgroup_K6, organ_dysfunction, and sepsis columns
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure size tuple
    
    Returns:
        Matplotlib Figure object
    """
    # Calculate statistics
    organ_stats = calculate_prevalence_stats(data, 'organ_dysfunction')
    sepsis_stats = calculate_prevalence_stats(data, 'sepsis')
    
    # Prepare plotting
    x = organ_stats['subgroup'].to_numpy()
    w = 0.32  # bar width
    
    fig, ax = plt.subplots(figsize=figsize)
    
    for sg in x:
        col = SUBGROUP_COLORS.get(sg, 'gray')
        
        # Left bar: organ dysfunction
        organ_row = organ_stats.loc[organ_stats['subgroup'] == sg]
        if not organ_row.empty:
            ax.bar(
                sg - w / 2,
                organ_row['p'].values[0],
                width=w,
                yerr=np.vstack([
                    organ_row['err_low'].values,
                    organ_row['err_high'].values
                ]),
                capsize=3,
                edgecolor='black',
                linewidth=1.0,
                color=col
            )
        
        # Right bar: sepsis
        sepsis_row = sepsis_stats.loc[sepsis_stats['subgroup'] == sg]
        if not sepsis_row.empty:
            ax.bar(
                sg + w / 2,
                sepsis_row['p'].values[0],
                width=w,
                yerr=np.vstack([
                    sepsis_row['err_low'].values,
                    sepsis_row['err_high'].values
                ]),
                capsize=3,
                edgecolor='black',
                linewidth=1.0,
                color=col
            )
    
    ax.set_xlabel('Subgroup (K=6)')
    ax.set_ylabel('Percent prevalence')
    ax.set_xticks(x)
    ax.set_title('C')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle=':', linewidth=0.7, alpha=0.6)
    
    plt.tight_layout()
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    return fig

