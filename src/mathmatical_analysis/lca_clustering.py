import numpy as np
import pandas as pd

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


def lac_ready_data(df_detailComorbidityData_PerPatient):
    """Prepare data for LCA clustering."""

    df = df_detailComorbidityData_PerPatient.copy()

    def admin_type_to_binary(admission_type):
        if admission_type.lower() == "elective":
            return 1
        else:
            return 0

    df["admission_type_binary"] = df["admission_type"].apply(admin_type_to_binary)

    # categorize age into bins
    age_bins = [16, 25, 45, 65, 85, 100]
    df["age_bin"] = pd.cut(
        df["age"], bins=age_bins, labels=["16-24", "25-44", "45-64", "65-84", "85+"]
    )

    # Convert categorical to string to avoid numpy array issues
    df["age_bin"] = df["age_bin"].astype(str)

    df.drop(columns=["age", "admission_type"], inplace=True)

    manifest = df.columns[1:].tolist()

    return df, manifest


def export_data_for_r(df, manifest, Kmax=8):
    """Export data and generate R script for LCA analysis in RStudio."""

    # Create temp directory if it doesn't exist
    import os

    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    # Save DataFrame to CSV for R to read
    df_subset = df[manifest].copy()
    csv_path = os.path.join(temp_dir, "lca_data.csv")
    df_subset.to_csv(csv_path, index=False)
    print(f"Data exported to: {csv_path}")

    # Build formula string
    mjoin = " + ".join(manifest)

    # Create R script
    r_script = f"""
# Load required libraries
library(poLCA)

# Read data
data <- read.csv("{csv_path}")

# Convert all columns to numeric (poLCA requires numeric data)
for(col in names(data)) {{
    data[[col]] <- as.numeric(as.factor(data[[col]]))
}}

# Build formula
formula <- as.formula("cbind({mjoin}) ~ 1")

# Fit LCA models
fits <- list()
print("Fitting LCA models with K=1 to {Kmax}...")

for(k in 1:{Kmax}) {{
    print(paste("  Fitting K=", k, "...", sep=""))
    tryCatch({{
        fit <- poLCA(formula, data, nclass=k, nrep=10, maxiter=5000, verbose=FALSE, na.rm=TRUE)
        fits[[k]] <- fit
        print(paste("    K=", k, ": BIC=", round(fit$bic, 1), ", AIC=", round(fit$aic, 1), sep=""))
    }}, error = function(e) {{
        print(paste("    K=", k, ": Failed -", e$message, sep=""))
    }})
}}

# Save results
saveRDS(fits, "{temp_dir}/lca_fits.rds")
print("LCA fitting completed!")

# Print summary of results
print("\\n=== LCA Model Summary ===")
for(k in 1:{Kmax}) {{
    if(!is.null(fits[[k]])) {{
        print(paste("K=", k, ": BIC=", round(fits[[k]]$bic, 1), ", AIC=", round(fits[[k]]$aic, 1), sep=""))
    }}
}}
"""

    # Write R script to file
    r_script_path = os.path.join(temp_dir, "lca_script.R")
    with open(r_script_path, "w") as f:
        f.write(r_script)

    print(f"R script generated at: {r_script_path}")
    print(f"Manifest variables: {manifest}")
    print(f"Data shape: {df_subset.shape}")

    return csv_path, r_script_path


if __name__ == "__main__":

    df_detailComorbidityData_PerPatient = get_detailComorbidityData_PerPatient()

    df_lac_ready_data, manifest = lac_ready_data(df_detailComorbidityData_PerPatient)

    # install_polca()

    csv_path, r_script_path = export_data_for_r(df_lac_ready_data, manifest)

    print(f"\n=== Export Complete ===")
    print(f"CSV data file: {csv_path}")
    print(f"R script file: {r_script_path}")
    print(f"\nNext steps:")
    print(f"1. Open RStudio")
    print(f"2. Copy and paste the contents of {r_script_path}")
    print(f"3. Run the script to perform LCA analysis")
