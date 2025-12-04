"""
Figure 4 visualization modules.

This package provides modules for generating Figure 4:
- Panels A & B: SOFA and OASIS boxplots by subgroup
- Panel C: Prevalence of organ dysfunction & sepsis by subgroup
- Panel D: Conditional mortality by subgroup
"""
from .load_data import (
    load_and_merge_all,
    load_patients_data,
    load_lca_data,
    load_sofa_oasis,
    load_angus_sepsis,
    merge_all_data
)
from .plot_fig_4_ab import plot_fig_4_ab
from .plot_fig_4_c import plot_fig_4_c
from .plot_fig_4_d import plot_fig_4_d

__all__ = [
    'load_and_merge_all',
    'load_patients_data',
    'load_lca_data',
    'load_sofa_oasis',
    'load_angus_sepsis',
    'merge_all_data',
    'plot_fig_4_ab',
    'plot_fig_4_c',
    'plot_fig_4_d',
]

