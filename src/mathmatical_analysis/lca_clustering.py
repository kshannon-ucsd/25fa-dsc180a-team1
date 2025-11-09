import os
import subprocess

import pandas as pd
from pandas.core.frame import DataFrame

from mathmatical_analysis.config import *
from mimiciii_db import DB

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

    return target_patients[["hadm_id", "age", "admission_type"]].merge(
        admission_comorbidity_details, on="hadm_id", how="left"
    )


def lca_ready_data(df_detailComorbidityData_PerPatient):
    """Prepare data for LCA clustering.
    All the categorical variables are converted to int starting with 1
    """
    df = df_detailComorbidityData_PerPatient.copy()
    df = df.dropna()

    # categorize age into bins
    # 1 -> 16-24, 2 -> 25-44, 3 -> 45-64, 4 -> 65-84, 5 -> 85+
    age_bins = [16, 25, 45, 65, 85, 100]
    df["age_bin"] = pd.cut(df["age"], bins=age_bins, labels=[1, 2, 3, 4, 5])

    # 1 -> elective, 2 -> non-elective
    df["admission_type_binary"] = df["admission_type"].apply(
        lambda x: 1 if x.lower() == "elective" else 2
    )

    df.drop(columns=["age", "admission_type"], inplace=True)

    for col in df.columns:
        df[col] = df[col].apply(lambda entry: 2 if entry == 0 else entry).astype(int)

    return df


def export_data_for_r(df):
    """Export data to CSV for R LCA analysis.

    Args:
        df: DataFrame with LCA-ready data

    Returns:
        str: Path to the exported CSV file
    """
    # Create temp directory if it doesn't exist
    temp_dir = "data"
    os.makedirs(temp_dir, exist_ok=True)

    # Save DataFrame to CSV for R to read
    csv_path = os.path.join(temp_dir, "lca_ready_data.csv")
    df.to_csv(csv_path, index=False)
    return csv_path


def lca_analysis():
    """
    Perform LCA analysis by exporting data and running R script.

    Args:
        data: DataFrame with LCA-ready data

    Returns:
        dict: Dictionary containing three DataFrames:
            - 'results_summary': Model comparison (K, BIC, AIC, MIN_SUBGROUP_SIZE)
            - 'subgroup_assignments': Patient subgroup assignments for all K
            - 'best_model_stats': Statistics for the best model

    Raises:
        FileNotFoundError: If R script or output files are missing
        subprocess.CalledProcessError: If R script execution fails
        Exception: Other errors during analysis
    """
    try:
        r_script_path = os.path.join(os.path.dirname(__file__), "lca_model_fitting.R")
        if not os.path.exists(r_script_path):
            raise FileNotFoundError(f"R script not found: {r_script_path}")

        # Run R script
        print(f"Running R script... This may take a few minutes...")
        subprocess.run(["Rscript", r_script_path], check=True, text=True)

        # Load results
        temp_dir = "data"
        results_summary_path = os.path.join(temp_dir, "lca_results_summary.csv")
        subgroup_assignments_path = os.path.join(temp_dir, "lca_all_subgroups.csv")
        best_model_stats_path = os.path.join(temp_dir, "lca_best_model_stats.csv")

        # Load CSV files into DataFrames
        results_summary = pd.read_csv(results_summary_path)
        subgroup_assignments = pd.read_csv(subgroup_assignments_path)
        best_model_stats = pd.read_csv(best_model_stats_path)

        return {
            "results_summary": results_summary,
            "subgroup_assignments": subgroup_assignments,
            "best_model_stats": best_model_stats,
        }

    except subprocess.CalledProcessError as e:
        print(f"❌ R script execution failed with return code {e.returncode}")
        print(f"Error output: {e.stderr}")
        raise
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        raise
    except Exception as e:
        print(f"❌ Error during LCA analysis: {e}")
        raise


def relabel_subgroups(
    ori_subgroup_path: pd.DataFrame,
    new_subgroup_path: str = "data/lca_all_subgroups_relabeled.csv",
):
    """
    Relabel subgroups based on the main paper subgroup status

    Group 1: highest pulmonary diabetes
    Group 2: lowest prevelance of all comorbidities
    Group 3: highest alcohol abuse
    Group 4: highest diabetes and hypertension and renal failture
    Group 5: highest diabetes and hypertension
    Group 6: highest cardiopulmonary disease

    Args:
        ori_subgroup_path: Path to the original subgroup assignments.
        new_subgroup_path: Path to the new subgroup assignments.

    Returns:
        None
    """
    ori_6k_df = ori_subgroup_path.copy()[["hadm_id", "subgroup_K6"]]
    morbidity_counts_df = DB_CONN.query_df(
        f"SELECT * FROM {ADMISSION_COMORBIDITY_TABLE}"
    )

    ori_6k_df = ori_6k_df.merge(morbidity_counts_df, on="hadm_id", how="left")

    ori_6k_df["group1_cond"] = ori_6k_df["chronic_pulmonary"] == 1
    ori_6k_df["group3_cond"] = (ori_6k_df["alcohol_abuse"] == 1) & (
        ori_6k_df["liver_disease"] == 1
    )
    ori_6k_df["group4_cond"] = ori_6k_df["renal_failure"] == 1
    ori_6k_df["group4_5_cond"] = (
        (ori_6k_df["diabetes_uncomplicated"] == 1)
        | (ori_6k_df["diabetes_complicated"] == 1)
    ) & (ori_6k_df["hypertension"] == 1)
    ori_6k_df["group6_cond"] = ori_6k_df["cardiac_arrhythmias"] == 1

    group_stats = (
        ori_6k_df.groupby("subgroup_K6")
        .agg(
            {
                "group1_cond": "mean",
                "group3_cond": "mean",
                "group4_cond": "mean",
                "group4_5_cond": "mean",
                "group6_cond": "mean",
            }
        )
        .reset_index()
    )

    mapping = dict()

    g1 = int(group_stats.loc[group_stats["group1_cond"].idxmax(), "subgroup_K6"])
    mapping[g1] = 1
    group_stats = group_stats[group_stats["subgroup_K6"] != g1]

    g3 = int(group_stats.loc[group_stats["group3_cond"].idxmax(), "subgroup_K6"])
    mapping[g3] = 3
    group_stats = group_stats[group_stats["subgroup_K6"] != g3]

    g6 = int(group_stats.loc[group_stats["group6_cond"].idxmax(), "subgroup_K6"])
    mapping[g6] = 6
    group_stats = group_stats[group_stats["subgroup_K6"] != g6]

    g4_5_niche = group_stats.sort_values(by=["group4_5_cond"], ascending=False)[
        :2
    ].sort_values(by=["group4_cond"], ascending=False)

    g4 = int(g4_5_niche.iloc[0]["subgroup_K6"])
    mapping[g4] = 4
    group_stats = group_stats[group_stats["subgroup_K6"] != g4]

    g5 = int(g4_5_niche.iloc[1]["subgroup_K6"])
    mapping[g5] = 5
    group_stats = group_stats[group_stats["subgroup_K6"] != g5]

    g2 = int(group_stats["subgroup_K6"].unique()[0])
    mapping[g2] = 2

    ori_6k_df["subgroup_K6"] = ori_6k_df["subgroup_K6"].map(mapping)

    output = ori_6k_df[["hadm_id", "subgroup_K6"]]

    output.to_csv(new_subgroup_path, index=False)


if __name__ == "__main__":

    df_detailComorbidityData_PerPatient = get_detailComorbidityData_PerPatient()

    df_lca_ready_data = lca_ready_data(df_detailComorbidityData_PerPatient)
    export_data_for_r(df_lca_ready_data)

    results = lca_analysis()
    print("Done running LCA clustering")

    relabel_subgroups(
        results["subgroup_assignments"], "data/lca_all_subgroups_relabeled.csv"
    )

    print("Relabeled subgroups saved to data/lca_all_subgroups_relabeled.csv")
