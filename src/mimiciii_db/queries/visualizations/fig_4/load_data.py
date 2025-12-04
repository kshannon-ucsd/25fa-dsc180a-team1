"""
Data loading and merging functions for Figure 4 visualization.

This module handles:
- Loading patient data from database
- Loading LCA subgroup assignments
- Loading SOFA and OASIS scores
- Loading Angus sepsis criteria
- Merging all data sources
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

from mimiciii_db import DB
from mimiciii_db.config import db_url


def load_patients_data(db: DB) -> pd.DataFrame:
    """Load filtered patients with morbidity counts from database."""
    return db.table_df("filtered_patients_with_morbidity_counts", schema="mimiciii")


def load_lca_data(lca_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load LCA subgroup assignments.
    
    Args:
        lca_path: Path to LCA CSV file. If None, uses default path.
    
    Returns:
        DataFrame with hadm_id and subgroup_K6 columns
    """
    if lca_path is None:
        # Default path relative to project root
        project_root = Path(__file__).resolve().parents[5]
        lca_path = project_root / "data" / "lca_all_subgroups_relabeled.csv"
    
    return pd.read_csv(lca_path)


def load_sofa_oasis(sofa_path: Optional[str] = None, 
                    oasis_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load SOFA and OASIS scores from CSV files.
    
    Args:
        sofa_path: Path to SOFA CSV file. If None, uses default path.
        oasis_path: Path to OASIS CSV file. If None, uses default path.
    
    Returns:
        Tuple of (sofa_df, oasis_df)
    """
    if sofa_path is None:
        project_root = Path(__file__).resolve().parents[5]
        sofa_path = project_root / "csv" / "sofa.csv"
    
    if oasis_path is None:
        project_root = Path(__file__).resolve().parents[5]
        oasis_path = project_root / "csv" / "oasis.csv"
    
    sofa_df = pd.read_csv(sofa_path)
    oasis_df = pd.read_csv(oasis_path)
    
    return sofa_df, oasis_df


def load_angus_sepsis(db: DB) -> pd.DataFrame:
    """
    Load Angus sepsis criteria from database.
    
    Creates the angus table if it doesn't exist, then queries it.
    
    Args:
        db: Database connection
    
    Returns:
        DataFrame with angus sepsis criteria flags
    """
    query = """-- THIS SCRIPT IS AUTOMATICALLY GENERATED. DO NOT EDIT IT DIRECTLY.
DROP TABLE IF EXISTS angus; CREATE TABLE angus AS 
-- ICD-9 codes for Angus criteria of sepsis

-- Angus et al, 2001. Epidemiology of severe sepsis in the United States
-- http://www.ncbi.nlm.nih.gov/pubmed/11445675

-- Case selection and definitions
-- To identify cases with severe sepsis, we selected all acute care
-- hospitalizations with ICD-9-CM codes for both:
-- (a) a bacterial or fungal infectious process AND
-- (b) a diagnosis of acute organ dysfunction (Appendix 2).

-- ICD-9 codes for infection - as sourced from Appendix 1 of above paper
WITH infection_group AS
(
	SELECT subject_id, hadm_id,
	CASE
		WHEN SUBSTR(icd9_code,1,3) IN ('001','002','003','004','005','008',
			   '009','010','011','012','013','014','015','016','017','018',
			   '020','021','022','023','024','025','026','027','030','031',
			   '032','033','034','035','036','037','038','039','040','041',
			   '090','091','092','093','094','095','096','097','098','100',
			   '101','102','103','104','110','111','112','114','115','116',
			   '117','118','320','322','324','325','420','421','451','461',
			   '462','463','464','465','481','482','485','486','494','510',
			   '513','540','541','542','566','567','590','597','601','614',
			   '615','616','681','682','683','686','730') THEN 1
		WHEN SUBSTR(icd9_code,1,4) IN ('5695','5720','5721','5750','5990','7110',
				'7907','9966','9985','9993') THEN 1
		WHEN SUBSTR(icd9_code,1,5) IN ('49121','56201','56203','56211','56213',
				'56983') THEN 1
		ELSE 0 END AS infection
	from diagnoses_icd
),
-- ICD-9 codes for organ dysfunction - as sourced from Appendix 2 of above paper
organ_diag_group as
(
	SELECT subject_id, hadm_id,
		CASE
		-- Acute Organ Dysfunction Diagnosis Codes
		WHEN SUBSTR(icd9_code,1,3) IN ('458','293','570','584') THEN 1
		WHEN SUBSTR(icd9_code,1,4) IN ('7855','3483','3481',
				'2874','2875','2869','2866','5734')  THEN 1
		ELSE 0 END AS organ_dysfunction,
		-- Explicit diagnosis of severe sepsis or septic shock
		CASE
		WHEN SUBSTR(icd9_code,1,5) IN ('99592','78552')  THEN 1
		ELSE 0 END AS explicit_sepsis
	from diagnoses_icd
),
-- Mechanical ventilation
organ_proc_group as
(
	SELECT subject_id, hadm_id,
		CASE
		WHEN icd9_code IN ('9670', '9671', '9672') THEN 1
		ELSE 0 END AS mech_vent
	FROM procedures_icd
),
-- Aggregate above views together
aggregate as
(
	SELECT subject_id, hadm_id,
		CASE
			WHEN hadm_id in
					(SELECT DISTINCT hadm_id
					FROM infection_group
					WHERE infection = 1)
				THEN 1
			ELSE 0 END AS infection,
		CASE
			WHEN hadm_id in
					(SELECT DISTINCT hadm_id
					FROM organ_diag_group
					WHERE explicit_sepsis = 1)
				THEN 1
			ELSE 0 END AS explicit_sepsis,
		CASE
			WHEN hadm_id in
					(SELECT DISTINCT hadm_id
					FROM organ_diag_group
					WHERE organ_dysfunction = 1)
				THEN 1
			ELSE 0 END AS organ_dysfunction,
		CASE
		WHEN hadm_id in
				(SELECT DISTINCT hadm_id
				FROM organ_proc_group
				WHERE mech_vent = 1)
			THEN 1
		ELSE 0 END AS mech_vent
	FROM admissions
)
-- Output component flags (explicit sepsis, organ dysfunction) and final flag (angus)
SELECT subject_id, hadm_id, infection,
   explicit_sepsis, organ_dysfunction, mech_vent,
CASE
	WHEN explicit_sepsis = 1 THEN 1
	WHEN infection = 1 AND organ_dysfunction = 1 THEN 1
	WHEN infection = 1 AND mech_vent = 1 THEN 1
	ELSE 0 END
AS angus
FROM aggregate;"""
    
    # Execute the CREATE TABLE statement first (DDL)
    db.execute(query)
    
    # Then query the created table
    return db.query_df("SELECT * FROM angus")


def merge_all_data(patients: pd.DataFrame,
                   lca: pd.DataFrame,
                   sofa_df: pd.DataFrame,
                   oasis_df: pd.DataFrame,
                   angus: pd.DataFrame) -> pd.DataFrame:
    """
    Merge all data sources into a single DataFrame.
    
    Args:
        patients: Patient data with morbidity counts
        lca: LCA subgroup assignments
        sofa_df: SOFA scores
        oasis_df: OASIS scores
        angus: Angus sepsis criteria
    
    Returns:
        Merged DataFrame ready for analysis
    """
    # Ensure key dtypes match
    keys = ['subject_id', 'hadm_id']
    
    dataframes = {
        'patients': patients,
        'sofa': sofa_df,
        'oasis': oasis_df,
        'angus': angus
    }
    
    for df in dataframes.values():
        for k in keys:
            if k in df.columns:
                df[k] = pd.to_numeric(df[k], errors='coerce')
    
    # De-duplicate SOFA and OASIS
    sofa_df = sofa_df.drop_duplicates(subset=keys)
    oasis_df = oasis_df.drop_duplicates(subset=keys)
    angus = angus.drop_duplicates(subset=keys)
    
    # Merge SOFA and OASIS into patients
    merged = (
        patients
        .merge(sofa_df, on=keys, how='left', suffixes=('', '_sofa'))
        .merge(oasis_df, on=keys, how='left', suffixes=('', '_oasis'))
    )
    
    # Merge LCA subgroups
    merged = merged.merge(
        lca[['hadm_id', 'subgroup_K6']],
        on='hadm_id',
        how='left'
    )
    
    # Merge Angus sepsis data
    merged = merged.merge(angus, on=keys, how='left')
    
    # Clean up subgroup column
    merged['subgroup_K6'] = pd.to_numeric(
        merged['subgroup_K6'], 
        errors='coerce'
    ).astype('Int64')
    
    # Create standard column names if needed
    if 'sepsis' not in merged.columns and 'angus' in merged.columns:
        merged['sepsis'] = merged['angus']
    
    if 'mortality' not in merged.columns and 'hospital_expire_flag' in merged.columns:
        merged['mortality'] = merged['hospital_expire_flag']
    
    # Ensure binary flags are numeric
    for c in ['organ_dysfunction', 'sepsis', 'mortality']:
        if c in merged.columns:
            merged[c] = pd.to_numeric(merged[c], errors='coerce')
    
    return merged


def load_and_merge_all(sofa_path: Optional[str] = None,
                       oasis_path: Optional[str] = None,
                       lca_path: Optional[str] = None,
                       db: Optional[DB] = None) -> pd.DataFrame:
    """
    Convenience function to load and merge all data sources.
    
    Args:
        sofa_path: Path to SOFA CSV. If None, uses default.
        oasis_path: Path to OASIS CSV. If None, uses default.
        lca_path: Path to LCA CSV. If None, uses default.
        db: Database connection. If None, creates a new one.
    
    Returns:
        Fully merged DataFrame ready for analysis
    """
    if db is None:
        db = DB.from_url(db_url())
    
    # Load all data sources
    patients = load_patients_data(db)
    lca = load_lca_data(lca_path)
    sofa_df, oasis_df = load_sofa_oasis(sofa_path, oasis_path)
    angus = load_angus_sepsis(db)
    
    # Merge everything
    return merge_all_data(patients, lca, sofa_df, oasis_df, angus)

