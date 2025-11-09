"""
Creating network visualization of comorbidity relationships for each LCA subgroup.

Each comorbidity is a node in the network, and the edges represent the relationships between the comorbidities.
The edges are weighted by the co-occurrence prevalence (number of disease pairs normalized to subgroup size).
Prevalence and co-occurrence are calculated within each subgroup only.
"""

import os
from itertools import combinations

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from mimiciii_db import DB
from visualizations.config import *

DB_CONN = DB.from_url(DATABASE_URL)
NODE_COLOR = {
    1: "white",
    3: "#90EE90",  # light green
    4: "#0000FF",  # blue
    6: "#FF00FF",  # magenta
}


def load_subgroup_comorbidity_data(
    subgroup_csv_path: str = "data/lca_all_subgroups_relabeled.csv",
):
    """Load subgroup assignments and merge with comorbidity data.

    Args:
        subgroup_csv_path: Path to the relabeled subgroup assignments CSV file.

    Returns:
        pandas.DataFrame: DataFrame with hadm_id, subgroup_K6, and all comorbidity columns.
    """
    # Load subgroup assignments
    subgroup_df = pd.read_csv(subgroup_csv_path)[["hadm_id", "subgroup_K6"]]

    # Load comorbidity data from database
    comorbidity_df = DB_CONN.query_df(f"SELECT * FROM {ADMISSION_COMORBIDITY_TABLE}")

    # Merge subgroup assignments with comorbidity data
    merged_df = subgroup_df.merge(comorbidity_df, on="hadm_id", how="inner")

    return merged_df


def calculate_prevalence_subgroup(df_subgroup, comorbidity_cols):
    """Calculate prevalence count and normalized prevalence for each comorbidity within a subgroup.

    Args:
        df_subgroup (pandas.DataFrame): DataFrame with detail comorbidity data per patient in the subgroup.
        comorbidity_cols (list): List of comorbidity columns.

    Returns:
        tuple: Two dictionaries containing:
            - prevalence_count: Dictionary with raw prevalence count for each comorbidity
            - prevalence_norm: Dictionary with normalized prevalence for each comorbidity (within subgroup)
    """
    subgroup_size = len(df_subgroup)
    prevalence_norm = {}

    for disease in comorbidity_cols:
        count = df_subgroup[disease].sum()
        prevalence_norm[disease] = count / subgroup_size

    return prevalence_norm


def calculate_cooccurrence_prevalence_subgroup(df_subgroup, comorbidity_cols):
    """
    Calculate co-occurrence prevalence for each comorbidity pair within a subgroup.

    Co-occurrence prevalence is the number of patients with both diseases normalized
    to the total number of patients in the subgroup.

    Args:
        df_subgroup (pandas.DataFrame): DataFrame with detail comorbidity data per patient in the subgroup.
        comorbidity_cols (list): List of comorbidity columns.

    Returns:
        dict: Dictionary with co-occurrence prevalence for each comorbidity pair.
        The keys are tuples of (comorbidity_a, comorbidity_b), and the values are dictionaries with:
        - cooccurrence_prevalence: Normalized co-occurrence (C_ab / N_subgroup)
    """
    N = len(df_subgroup)  # Subgroup size
    cooccurrence_data = {}

    for comorbidity_a, comorbidity_b in combinations(comorbidity_cols, 2):

        C_ab = (
            (df_subgroup[comorbidity_a] == 1) & (df_subgroup[comorbidity_b] == 1)
        ).sum()

        # Normalize to subgroup size
        cooccurrence_prevalence = C_ab / N if N > 0 else 0.0

        cooccurrence_data[(comorbidity_a, comorbidity_b)] = {
            "cooccurrence_prevalence": cooccurrence_prevalence,
        }

    return cooccurrence_data


def getting_grdient_edge_alpha(cooccurrence_values):
    """Getting gradient edge alpha based on normalized co-occurrence values that pass threshold.

    Top 10% of edges by co-occurrence get normalized alpha (0.1 to 0.8), others get light alpha (0.1).

    Args:
        cooccurrence_values: List of co-occurrence prevalence values for each edge.

    Returns:
        list: List of alpha values for each edge.
    """
    # Step 1: Calculate threshold for top X%
    cooccurrence_sorted = sorted(cooccurrence_values, reverse=True)
    top_percent_index = int(len(cooccurrence_sorted) * (10 / 100))
    threshold = (
        cooccurrence_sorted[top_percent_index]
        if top_percent_index > 0
        else cooccurrence_sorted[0]
    )

    # Step 2: Get co-occurrence values that pass the threshold
    above_threshold = [val for val in cooccurrence_values if val >= threshold]

    if not above_threshold:
        return [0.1] * len(cooccurrence_values)

    # Step 3: Calculate min and max for normalization
    min_val_above = min(above_threshold)
    max_val_above = max(above_threshold)

    # Step 4: Calculate alpha for each edge
    edge_alphas = []
    for val in cooccurrence_values:
        if val >= threshold:
            # Normalize within the threshold range (0.1 to 0.8)
            if max_val_above > min_val_above:
                normalized_val = (val - min_val_above) / (max_val_above - min_val_above)
            else:
                normalized_val = 0.5

            # Higher co-occurrence → higher alpha (more opaque)
            alpha = 0.1 + normalized_val * 0.7  # Range: 0.1 to 0.8
        else:
            # Below threshold: light alpha
            alpha = 0.1

        edge_alphas.append(alpha)

    return edge_alphas


def build_network_graph(
    edge_data,
    prevalence_norm,
    node_size_factor=1,
    edge_width_factor=1,
    node_color="white",
    dest_path="assets/comorbidity_network.png",
):
    """
    Build network graph.

    Args:
        edge_data (dict): Dictionary with co-occurrence prevalence for each comorbidity pair.
        prevalence_norm (dict): Dictionary with normalized prevalence for each comorbidity.
        node_size_factor (float): Factor to scale node size.
        edge_width_factor (float): Factor to scale edge width.
        node_color (str or list): Color for nodes. Can be a single color string (e.g., "white", "lightblue")
            or a list of colors for each node. Defaults to "white".
        dest_path (str): Path to save the visualization.

    Returns:
        None
    """
    G = nx.Graph()

    # Creating nodes
    created_nodes = set()
    for comorbidity_a, comorbidity_b in edge_data.keys():
        if comorbidity_a not in created_nodes:
            G.add_node(comorbidity_a, prevalence=prevalence_norm[comorbidity_a])
            created_nodes.add(comorbidity_a)
        if comorbidity_b not in created_nodes:
            G.add_node(comorbidity_b, prevalence=prevalence_norm[comorbidity_b])
            created_nodes.add(comorbidity_b)

    # Creating edges
    for (comorbidity_a, comorbidity_b), metrics in edge_data.items():
        G.add_edge(
            comorbidity_a,
            comorbidity_b,
            cooccurrence=metrics["cooccurrence_prevalence"],
        )

    # define graph info
    node_pos = nx.spring_layout(G, k=0.8, iterations=100, seed=42)
    node_sizes = [G.nodes[node]["prevalence"] * node_size_factor for node in G.nodes()]
    edge_widths = [G[u][v]["cooccurrence"] * edge_width_factor for u, v in G.edges()]
    edge_alphas = getting_grdient_edge_alpha(
        [G[u][v]["cooccurrence"] for u, v in G.edges()]
    )
    label_pos = {node: (x, y - 0.1) for node, (x, y) in node_pos.items()}

    # Draw graph
    fig, ax = plt.subplots(figsize=(14, 14), facecolor="white")
    nx.draw_networkx_edges(
        G,
        node_pos,
        width=edge_widths,
        edge_color="black",
        alpha=edge_alphas,
        ax=ax,
    )
    nx.draw_networkx_nodes(
        G,
        node_pos,
        node_size=node_sizes,
        node_color=node_color,
        edgecolors="black",
        linewidths=1.5,
        ax=ax,
    )

    nx.draw_networkx_labels(
        G,
        label_pos,
        font_size=13,
        font_weight="bold",
        font_family="sans-serif",
        ax=ax,
    )

    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"✓ Visualization saved to {dest_path}")


def main():
    """Main function to generate network visualizations for each subgroup."""
    # Load subgroup and comorbidity data
    df_all = load_subgroup_comorbidity_data()

    # Get comorbidity columns (exclude hadm_id and subgroup_K6)
    comorbidity_cols = [
        col for col in df_all.columns if col not in ["hadm_id", "subgroup_K6"]
    ]

    # Create output directory
    output_dir = "assets/fig_5"
    os.makedirs(output_dir, exist_ok=True)

    # Loop through subgroups 1-6
    for subgroup in [1, 3, 4, 6]:
        # Filter data to current subgroup
        df_subgroup = df_all[df_all["subgroup_K6"] == subgroup].copy()

        # Calculate prevalence within subgroup
        prevalence_norm = calculate_prevalence_subgroup(df_subgroup, comorbidity_cols)

        # Calculate co-occurrence prevalence within subgroup
        cooccurrence_data = calculate_cooccurrence_prevalence_subgroup(
            df_subgroup, comorbidity_cols
        )

        # Filter to edges with non-zero co-occurrence
        edge_data = {
            (comorbidity_a, comorbidity_b): metrics
            for (comorbidity_a, comorbidity_b), metrics in cooccurrence_data.items()
            if metrics["cooccurrence_prevalence"] > 0
        }

        # Build and save network graph
        output_path = os.path.join(output_dir, f"subgroup_network_group_{subgroup}.png")
        build_network_graph(
            edge_data, prevalence_norm, 5000, 7, NODE_COLOR[subgroup], output_path
        )

    print(f"\n✓ All subgroup network visualizations completed!")


# Run main function
if __name__ == "__main__":
    main()
