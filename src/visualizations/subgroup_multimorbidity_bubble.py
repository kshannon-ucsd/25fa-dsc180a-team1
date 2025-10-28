"""
Creating bubble distribution visualization of multimorbidity counts across LCA subgroups.

This script generates bubble plots showing how patient counts are distributed across
different multimorbidity count bins within each LCA subgroup.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mimiciii_db import DB
from visualizations.config import *

DB_CONN = DB.from_url(DATABASE_URL)


def plot_subgroup_multimorbidity_bubble(
    df: pd.DataFrame,
    subgroup_col: str,
    morbidity_count_col: str,
    dest_path: str = "assets/subgroup_multimorbidity_bubble.png",
):
    """Generate bubble plot showing distribution of multimorbidity counts across subgroups.

    Args:
        df: DataFrame containing subgroup assignments and morbidity counts
        subgroup_col: Column name containing subgroup identifiers
        morbidity_count_col: Column name containing morbidity counts
        dest_path: Output file path for the visualization
    """
    # Bin morbidity counts into 0-7 and >8
    df = df.copy()
    df["morbidity_binned"] = df[morbidity_count_col].apply(lambda x: x if x <= 7 else 8)

    # Create cross-tabulation normalized by row (percentage within each subgroup)
    ct_binned = (
        pd.crosstab(df[subgroup_col], df["morbidity_binned"], normalize="index") * 100
    )

    # Create bubble plot
    plt.figure(figsize=(12, 8))

    # Create color palette for subgroups
    colors = plt.cm.Set3(np.linspace(0, 1, len(ct_binned.index)))

    # Plot bubbles
    for idx, i in enumerate(ct_binned.index):
        for j in ct_binned.columns:
            plt.scatter(i, j, s=ct_binned.loc[i, j] * 50, alpha=0.5, color=colors[idx])

    plt.ylabel("Number of Coexisting Conditions")
    plt.xlabel("Subgroup")
    plt.title("Distribution of Multimorbidity Counts Across Subgroups")

    # Add legend for bubble sizes
    sizes = [500, 2500]
    labels = ["10%", "50%"]
    legend_elements = [
        plt.scatter([], [], s=s, c="gray", alpha=0.5, label=l)
        for s, l in zip(sizes, labels)
    ]
    plt.legend(
        handles=legend_elements,
        title="Percentage of Patients in Subgroup",
        labelspacing=2,
        title_fontsize=10,
        loc="lower left",
    )

    plt.grid(True, alpha=0.3)
    plt.yticks(range(9), [str(i) if i < 8 else ">8" for i in range(9)])

    # Save the figure
    plt.tight_layout()
    plt.savefig(dest_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✓ Visualization saved to {dest_path}")


def load_subgroup_and_morbidity_data(csv_path: str, subgroup_col: str = "subgroup_K6"):
    """Load subgroup assignments from CSV and morbidity counts from database.

    Args:
        csv_path: Path to CSV file containing subgroup assignments
        subgroup_col: Column name containing subgroup assignments to extract

    Returns:
        DataFrame with merged subgroup and morbidity count data
    """
    # Load subgroup assignments
    subgroup_df = pd.read_csv(csv_path)[["hadm_id", subgroup_col]]

    # Query morbidity counts from database
    morbidity_df = DB_CONN.query_df(f"SELECT * FROM {MORBIDITY_COUNTS_TABLE}")

    # Merge the data
    merged_df = subgroup_df[["hadm_id", subgroup_col]].merge(
        morbidity_df[["hadm_id", "morbidity_count"]], on="hadm_id", how="inner"
    )

    return merged_df


def main():
    """Main function for standalone execution."""
    # Path to LCA subgroups CSV
    csv_path = "temp/lca_all_subgroups.csv"
    subgroup_col = "subgroup_K6"
    morbidity_count_col = "morbidity_count"

    df = load_subgroup_and_morbidity_data(csv_path, subgroup_col)
    plot_subgroup_multimorbidity_bubble(
        df,
        subgroup_col=subgroup_col,
        morbidity_count_col=morbidity_count_col,
        dest_path="assets/subgroup_multimorbidity_bubble.png",
    )


# Run main function
if __name__ == "__main__":
    main()
