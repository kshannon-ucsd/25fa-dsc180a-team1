#!/usr/bin/env python3
"""
Main script to generate Figure 4.

This script orchestrates the creation of all panels:
- Panel A & B: SOFA and OASIS boxplots by subgroup
- Panel C: Prevalence of organ dysfunction & sepsis by subgroup
- Panel D: Conditional mortality by subgroup
"""
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(project_root / "src"))

from mimiciii_db.queries.visualizations.fig_4.load_data import load_and_merge_all
from mimiciii_db.queries.visualizations.fig_4.plot_fig_4_ab import plot_fig_4_ab
from mimiciii_db.queries.visualizations.fig_4.plot_fig_4_c import plot_fig_4_c
from mimiciii_db.queries.visualizations.fig_4.plot_fig_4_d import plot_fig_4_d


def main():
    """Generate all panels of Figure 4."""
    # Set up paths
    assets_dir = project_root / "assets" / "fig_4"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading and merging data...")
    df = load_and_merge_all()
    print(f"Loaded {len(df)} rows")
    
    print("\nGenerating Figure 4, Panels A & B...")
    plot_fig_4_ab(df, output_path=assets_dir / "fig_4_ab.png")
    print("✓ Saved fig_4_ab.png")
    
    print("\nGenerating Figure 4, Panel C...")
    plot_fig_4_c(df, output_path=assets_dir / "fig_4_c.png")
    print("✓ Saved fig_4_c.png")
    
    print("\nGenerating Figure 4, Panel D...")
    plot_fig_4_d(df, output_path=assets_dir / "fig_4_d.png")
    print("✓ Saved fig_4_d.png")
    
    print("\n✓ All panels generated successfully!")


if __name__ == "__main__":
    main()

