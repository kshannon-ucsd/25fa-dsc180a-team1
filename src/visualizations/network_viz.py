#!/usr/bin/env python3
"""
Creating network visualization of comorbidity relationships based on the Elixhauser Index.

Each comorbidity is a node in the network, and the edges represent the relationships between the comorbidities.
the edges are weighted by the relative risk of the comorbidities.
"""
from itertools import combinations
from math import exp

import matplotlib.pyplot as plt
import networkx as nx

from mimiciii_db import DB
from visualizations.config import *

DB_CONN = DB.from_url(DATABASE_URL)


def get_detailComorbidityData_PerPatient():
    """Get detail comorbidity data per patient.

    Returns:
        pandas.DataFrame: DataFrame with detail comorbidity data per patient.
    """
    admission_comorbidity_details = DB_CONN.query_df(
        f"SELECT * FROM {ADMISSION_COMORBIDITY_TABLE}"
    )
    target_patients = DB_CONN.query_df(f"SELECT * FROM {TARGET_PATIENT}")

    return target_patients[["hadm_id"]].merge(
        admission_comorbidity_details, on="hadm_id", how="left"
    )


def calculate_prevalence(df, comorbidity_cols):
    """Calculate prevalence count and normalized prevalence for each comorbidity.

    Args:
        df (pandas.DataFrame): DataFrame with detail comorbidity data per patient.
        comorbidity_cols (list): List of comorbidity columns.

    Returns:
        tuple: Two dictionaries containing:
            - prevalence_count: Dictionary with raw prevalence count for each comorbidity
            - prevalence_norm: Dictionary with normalized prevalence for each comorbidity
    """
    total_patients = len(df)
    prevalence_count = {}
    prevalence_norm = {}

    for disease in comorbidity_cols:
        count = df[disease].sum()
        prevalence_count[disease] = count
        prevalence_norm[disease] = count / total_patients

    return prevalence_count, prevalence_norm


def calculate_relative_risk(df, comorbidity_cols, prevalence):
    N = len(df)
    relative_risks = {}

    for comorbidity_a, comorbidity_b in combinations(comorbidity_cols, 2):

        C_ab = ((df[comorbidity_a] == 1) & (df[comorbidity_b] == 1)).sum()
        P_a = prevalence[comorbidity_a]
        P_b = prevalence[comorbidity_b]

        if C_ab == 0 or P_a == 0 or P_b == 0:
            relative_risks[(comorbidity_a, comorbidity_b)] = {
                "rr": float("nan"),
                "rr_ci_lower": float("nan"),
                "rr_ci_upper": float("nan"),
                "significant": False,
            }
            continue

        rr = C_ab * N / (P_a * P_b)

        sigma_ab = 1 / C_ab + 1 / (P_a * P_b) - 1 / N - 1 / (N**2)

        # 95% confidence interval
        rr_ci_lower = rr * exp(-1.96 * sigma_ab)
        rr_ci_upper = rr * exp(1.96 * sigma_ab)

        if rr_ci_lower <= 1 <= rr_ci_upper:
            significant = False
        else:
            significant = True

        relative_risks[(comorbidity_a, comorbidity_b)] = {
            "rr": rr,
            "rr_ci_lower": rr_ci_lower,
            "rr_ci_upper": rr_ci_upper,
            "significant": significant,
        }

    return relative_risks


def getting_grdient_edge_alpha(rr_values):
    """Getting gradient edge alpha based on normalized RR values that pass threshold.

    Top 5% of edges by RR get normalized alpha (0.1 to 0.8), others get light alpha (0.1).

    Args:
        rr_values: List of RR values for each edge.

    Returns:
        list: List of alpha values for each edge.
    """
    # Step 1: Calculate threshold for top X%
    rr_values_sorted = sorted(rr_values, reverse=True)
    top_percent_index = int(len(rr_values_sorted) * (10 / 100))
    threshold = (
        rr_values_sorted[top_percent_index]
        if top_percent_index > 0
        else rr_values_sorted[0]
    )

    # Step 2: Get RR values that pass the threshold
    above_threshold_rr = [rr for rr in rr_values if rr >= threshold]

    if not above_threshold_rr:
        return [0.1] * len(rr_values)

    # Step 3: Calculate min and max for normalization
    min_rr_above = min(above_threshold_rr)
    max_rr_above = max(above_threshold_rr)

    # Step 4: Calculate alpha for each edge
    edge_alphas = []
    for rr in rr_values:
        if rr >= threshold:
            # Normalize RR within the threshold range (0.1 to 0.8)
            if max_rr_above > min_rr_above:
                normalized_rr = (rr - min_rr_above) / (max_rr_above - min_rr_above)
            else:
                normalized_rr = 0.5

            # Higher RR → higher alpha (more opaque)
            alpha = 0.1 + normalized_rr * 0.7  # Range: 0.1 to 0.8
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
    dest_path="assets/comorbidity_network.png",
):
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
        G.add_edge(comorbidity_a, comorbidity_b, rr=metrics["rr"])

    # define graph info
    node_pos = nx.spring_layout(G, k=0.8, iterations=100, seed=42)
    node_sizes = [G.nodes[node]["prevalence"] * node_size_factor for node in G.nodes()]
    edge_widths = [G[u][v]["rr"] * edge_width_factor for u, v in G.edges()]
    edge_alphas = getting_grdient_edge_alpha([G[u][v]["rr"] for u, v in G.edges()])
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
        node_color="white",
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
    # Getting data
    df_tpatients_comorbidity_details = get_detailComorbidityData_PerPatient()

    # Calculating prevalence
    comorbidity_cols = df_tpatients_comorbidity_details.columns[1:].tolist()
    prevalence_count, prevalence_norm = calculate_prevalence(
        df_tpatients_comorbidity_details, comorbidity_cols
    )

    # Calculating relative risk
    relative_risk = calculate_relative_risk(
        df_tpatients_comorbidity_details, comorbidity_cols, prevalence_count
    )

    # Building network graph
    edge_data = {
        (comorbidity_a, comorbidity_b): metrics
        for (comorbidity_a, comorbidity_b), metrics in relative_risk.items()
        if metrics["significant"]
    }

    build_network_graph(edge_data, prevalence_norm, 25000, 1.25)


# Run main function
if __name__ == "__main__":
    main()
