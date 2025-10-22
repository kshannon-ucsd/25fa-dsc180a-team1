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
import pandas as pd

from mimiciii_db import DB
from visualizations.config import *

DB_CONN = DB.from_url(DATABASE_URL)


# import sys
# from itertools import combinations
# from pathlib import Path

# import matplotlib.pyplot as plt
# import networkx as nx
# import numpy as np
# import pandas as pd
# from scipy.stats import chi2_contingency

# # Add parent directory to path for imports
# sys.path.insert(0, str(Path(__file__).parent.parent))
# from mimiciii_db import DB
# from mimiciii_db.config import db_url


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

    # Draw graph
    fig, ax = plt.subplots(figsize=(14, 14), facecolor="white")
    nx.draw_networkx_edges(
        G,
        node_pos,
        width=edge_widths,
        edge_color="black",
        alpha=0.3,
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
        node_pos,
        font_size=10,
        font_weight="bold",
        font_family="sans-serif",
        ax=ax,
    )

    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"✓ Visualization saved to {dest_path}")


# def calculate_edge_color(rr, factor=0.8):
#     """Map relative risk to grayscale color (darker = higher RR)."""
#     exp_factor = np.exp((rr - 1) * factor)
#     gray_val = max(0.01, min(0.99, 1 / exp_factor))
#     return str(gray_val)


# def format_label(node_name):
#     """Format node names for display (replace underscores with spaces)."""
#     return node_name.replace("_", " ")


# def calculate_relative_risk(df, disease_a, disease_b):
#     """Calculate relative risk and p-value for two diseases."""
#     # Contingency table
#     a_and_b = ((df[disease_a] == 1) & (df[disease_b] == 1)).sum()
#     a_not_b = ((df[disease_a] == 1) & (df[disease_b] == 0)).sum()
#     not_a_b = ((df[disease_a] == 0) & (df[disease_b] == 1)).sum()
#     not_a_not_b = ((df[disease_a] == 0) & (df[disease_b] == 0)).sum()

#     # Conditional probabilities
#     p_b_given_a = a_and_b / (a_and_b + a_not_b) if (a_and_b + a_not_b) > 0 else 0
#     p_b_given_not_a = (
#         not_a_b / (not_a_b + not_a_not_b) if (not_a_b + not_a_not_b) > 0 else 0
#     )

#     # Relative risk
#     rr = p_b_given_a / p_b_given_not_a if p_b_given_not_a > 0 else float("inf")

#     # Chi-square test
#     contingency_table = [[a_and_b, a_not_b], [not_a_b, not_a_not_b]]
#     _, p_value, _, _ = chi2_contingency(contingency_table)

#     return rr, p_value


# def query_comorbidity_data(db):
#     """Query comorbidity data from database."""
#     query = "SELECT * FROM filtered_patients_with_morbidity_counts"
#     return db.query_df(query)


# def build_network_graph(df, comorbidity_cols, prevalence):
#     """Build NetworkX graph with significant associations."""
#     G = nx.Graph()

#     # Add nodes
#     for disease in comorbidity_cols:
#         G.add_node(disease, prevalence=prevalence[disease])

#     # Calculate pairwise associations
#     edges_data = []
#     for disease_a, disease_b in combinations(comorbidity_cols, 2):
#         rr, p_value = calculate_relative_risk(df, disease_a, disease_b)

#         # Only include significant associations
#         if p_value < 0.05 and rr > 1.0:
#             edges_data.append(
#                 {"source": disease_a, "target": disease_b, "rr": rr, "p_value": p_value}
#             )

#     # Add edges
#     for edge in edges_data:
#         G.add_edge(
#             edge["source"], edge["target"], rr=edge["rr"], p_value=edge["p_value"]
#         )

#     return G


# def draw_network(
#     G,
#     prevalence,
#     output_path,
#     figsize=(12, 12),
#     node_size_mult=5000,
#     edge_width=4.0,
#     top_n=15,
# ):
#     """Draw and save network visualization."""
#     # Create figure
#     fig, ax = plt.subplots(figsize=figsize, facecolor="white")

#     # Calculate layout
#     pos = nx.spring_layout(G, k=0.8, iterations=100, seed=42)

#     # Node sizes
#     node_sizes = [prevalence[node] * node_size_mult for node in G.nodes()]

#     # Determine top N edges for solid lines
#     all_rrs = [G[u][v]["rr"] for u, v in G.edges()]
#     sorted_rrs = sorted(all_rrs, reverse=True)
#     threshold = sorted_rrs[top_n - 1] if len(sorted_rrs) >= top_n else sorted_rrs[-1]

#     # Separate edges by style
#     dotted_edges, dotted_colors = [], []
#     solid_edges, solid_colors = [], []

#     for u, v in G.edges():
#         rr = G[u][v]["rr"]
#         color = calculate_edge_color(rr)

#         if rr >= threshold:
#             solid_edges.append((u, v))
#             solid_colors.append(color)
#         else:
#             dotted_edges.append((u, v))
#             dotted_colors.append(color)

#     # Draw dotted edges
#     if dotted_edges:
#         nx.draw_networkx_edges(
#             G,
#             pos,
#             edgelist=dotted_edges,
#             width=edge_width,
#             edge_color=dotted_colors,
#             alpha=1.0,
#             style="dotted",
#             ax=ax,
#         )

#     # Draw solid edges
#     if solid_edges:
#         nx.draw_networkx_edges(
#             G,
#             pos,
#             edgelist=solid_edges,
#             width=edge_width,
#             edge_color=solid_colors,
#             alpha=1.0,
#             style="solid",
#             ax=ax,
#         )

#     # Draw nodes
#     nx.draw_networkx_nodes(
#         G,
#         pos,
#         node_size=node_sizes,
#         node_color="white",
#         edgecolors="black",
#         linewidths=1.5,
#         ax=ax,
#     )

#     # Draw labels
#     labels = {node: format_label(node) for node in G.nodes()}
#     nx.draw_networkx_labels(
#         G,
#         pos,
#         labels=labels,
#         font_size=9,
#         font_weight="bold",
#         font_family="sans-serif",
#         ax=ax,
#     )

#     # Add legend
#     legend_elements = [
#         plt.scatter(
#             [],
#             [],
#             s=0.50 * node_size_mult,
#             c="white",
#             edgecolors="black",
#             linewidths=1.5,
#             label="50% prevalence",
#         ),
#         plt.scatter(
#             [],
#             [],
#             s=0.25 * node_size_mult,
#             c="white",
#             edgecolors="black",
#             linewidths=1.5,
#             label="25% prevalence",
#         ),
#     ]
#     ax.legend(handles=legend_elements, loc="lower right", frameon=True, fontsize=12)

#     # Styling
#     x_vals = [pos[n][0] for n in G.nodes()]
#     y_vals = [pos[n][1] for n in G.nodes()]
#     ax.set_xlim([min(x_vals) - 0.1, max(x_vals) + 0.1])
#     ax.set_ylim([min(y_vals) - 0.1, max(y_vals) + 0.1])
#     ax.axis("off")

#     # Title
#     ax.set_title(
#         "Comorbidity Network - Elixhauser Index\n"
#         "(Node size = Prevalence, Edge darkness = Relative Risk)",
#         fontsize=16,
#         fontweight="bold",
#         pad=20,
#     )

#     plt.tight_layout()
#     fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
#     print(f"✓ Visualization saved to {output_path}")
#     plt.close()


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

    build_network_graph(edge_data, prevalence_norm, 10000, 3)

    raise Exception("Stop here")

    # Build network
    print("4. Building network graph...")
    G = build_network_graph(df, comorbidity_cols, prevalence)
    print(f"   Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Create visualization
    print("5. Creating visualization...")
    output_path = (
        Path(__file__).parent.parent.parent / "assets" / "comorbidity_network.png"
    )
    draw_network(G, prevalence, str(output_path))

    print("\n" + "=" * 80)
    print("✓ Network visualization generation complete!")
    print("=" * 80)


# Run main function
if __name__ == "__main__":
    main()
