"""
Plotting functions for Figure 4, Panel D: Conditional mortality by subgroup.
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


def calculate_conditional_mortality(data: pd.DataFrame, flag_col: str) -> pd.DataFrame:
    """
    Calculate conditional mortality (mortality only among those with flag==1) by subgroup.
    
    Args:
        data: DataFrame with subgroup_K6, the flag column, and mortality
        flag_col: Column name of the binary flag (e.g., 'organ_dysfunction' or 'sepsis')
    
    Returns:
        DataFrame with subgroup, n, p, err_low, err_high
    """
    # Clean data
    df = data.copy()
    df = df.drop_duplicates(subset=['subject_id', 'hadm_id'])
    df['subgroup_K6'] = pd.to_numeric(df['subgroup_K6'], errors='coerce').astype('Int64')
    df = df[df['subgroup_K6'].between(1, 6)].copy()
    
    # Ensure binary flags are numeric
    for c in ['organ_dysfunction', 'sepsis', 'mortality', flag_col]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
    
    # Calculate conditional mortality by subgroup
    groups = []
    for sg, sub in df.groupby('subgroup_K6'):
        # Filter to only those with flag == 1
        sub_filtered = sub[sub[flag_col] == 1]
        n = len(sub_filtered)
        k = sub_filtered['mortality'].sum()
        
        lo, hi = wilson_ci(k, n)
        
        groups.append({
            'subgroup': int(sg),
            'n': n,
            'p': 100 * (k / n) if n > 0 else np.nan,
            'err_low': 100 * ((k / n) - lo) if n > 0 else np.nan,
            'err_high': 100 * (hi - (k / n)) if n > 0 else np.nan
        })
    
    stats = pd.DataFrame(groups).sort_values('subgroup')
    return stats


def plot_fig_4_d(data: pd.DataFrame,
                 output_path: Optional[str] = None,
                 figsize: tuple = (6, 4)) -> plt.Figure:
    """
    Create Figure 4 Panel D: Conditional mortality by subgroup.
    
    Shows mortality among those with organ dysfunction vs. those with sepsis.
    
    Args:
        data: Merged DataFrame with subgroup_K6, organ_dysfunction, sepsis, and mortality columns
        output_path: Path to save the figure. If None, figure is not saved.
        figsize: Figure size tuple
    
    Returns:
        Matplotlib Figure object
    """
    # Calculate conditional mortality statistics
    mort_od = calculate_conditional_mortality(data, 'organ_dysfunction')
    mort_sep = calculate_conditional_mortality(data, 'sepsis')
    
    # Prepare plotting
    x = mort_od['subgroup'].to_numpy()
    w = 0.32  # bar width
    
    fig, ax = plt.subplots(figsize=figsize)
    
    for sg in x:
        col = SUBGROUP_COLORS.get(sg, 'gray')
        
        # Left bar: organ dysfunction mortality
        od_row = mort_od.loc[mort_od['subgroup'] == sg]
        if not od_row.empty and not pd.isna(od_row['p'].values[0]):
            ax.bar(
                sg - w / 2,
                od_row['p'].values[0],
                width=w,
                yerr=np.vstack([
                    od_row['err_low'].values,
                    od_row['err_high'].values
                ]).astype(float),
                capsize=3,
                edgecolor='black',
                linewidth=1.0,
                color=col
            )
        
        # Right bar: sepsis mortality
        sep_row = mort_sep.loc[mort_sep['subgroup'] == sg]
        if not sep_row.empty and not pd.isna(sep_row['p'].values[0]):
            ax.bar(
                sg + w / 2,
                sep_row['p'].values[0],
                width=w,
                yerr=np.vstack([
                    sep_row['err_low'].values,
                    sep_row['err_high'].values
                ]).astype(float),
                capsize=3,
                edgecolor='black',
                linewidth=1.0,
                color=col
            )
    
    ax.set_xlabel('Subgroup (K=6)')
    ax.set_ylabel('Percent mortality')
    ax.set_xticks(x)
    ax.set_title('D')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle=':', linewidth=0.7, alpha=0.6)
    
    plt.tight_layout()
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    return fig

