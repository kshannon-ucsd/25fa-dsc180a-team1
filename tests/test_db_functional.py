import pandas as pd
import pytest

from mimiciii_db import DB
from mimiciii_db.config import db_url


@pytest.fixture(scope="module")
def db():
    """Create DB connection using DATABASE_URL from environment."""
    url = db_url()
    db_instance = DB.from_url(url)
    yield db_instance
    db_instance.dispose()


def test_db_connection_works(db):
    """Verify DB object is created successfully."""
    assert db is not None
    assert db.engine is not None


def test_db_patients_table(db):
    """Test patients table and its columns."""
    result_table = db.table_df("patients", schema="mimiciii")
    assert isinstance(result_table, pd.DataFrame)
    assert len(result_table) == 100
    assert {
        "dob",
        "dod",
        "dod_hosp",
        "dod_ssn",
        "expire_flag",
        "gender",
        "row_id",
        "subject_id",
    } == set(result_table.columns)


def test_db_admissions_table(db):
    result_table = db.table_df("admissions", schema="mimiciii")
    assert isinstance(result_table, pd.DataFrame)
    assert len(result_table) == 100
    assert {
        "admission_location",
        "admission_type",
        "admittime",
        "deathtime",
        "diagnosis",
        "discharge_location",
        "dischtime",
        "edouttime",
        "edregtime",
        "ethnicity",
        "hadm_id",
        "has_chartevents_data",
        "hospital_expire_flag",
        "insurance",
        "language",
        "marital_status",
        "religion",
        "row_id",
        "subject_id",
    } == set(result_table.columns)


def test_db_diagnoses_icd_table(db):
    result_table = db.table_df("diagnoses_icd", schema="mimiciii")
    assert isinstance(result_table, pd.DataFrame)
    assert len(result_table) == 100
    assert {"hadm_id", "icd9_code", "row_id", "seq_num", "subject_id"} == set(
        result_table.columns
    )


def test_db_d_icd_diagnoses_table(db):
    result_table = db.table_df("d_icd_diagnoses", schema="mimiciii")
    assert isinstance(result_table, pd.DataFrame)
    assert len(result_table) == 100
    assert {
        "icd9_code",
        "long_title",
        "row_id",
        "short_title",
    } == set(result_table.columns)


# def test_query_df_returns_dataframe(db):
#     """Test basic query returns a pandas DataFrame."""
#     result = db.query_df("SELECT 1 as test_col")
#     assert isinstance(result, pd.DataFrame)
#     assert len(result) == 1
#     assert "test_col" in result.columns


# def test_count_tables_in_mimiciii_schema(db):
#     """Count tables in mimiciii schema."""
#     result = db.query_df(
#         "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = :schema",
#         {"schema": "mimiciii"},
#     )
#     assert len(result) > 0
#     assert result["table_count"].iloc[0] > 0


# def test_table_df_previews_patients(db):
#     """Test table_df can preview patients table."""
#     result = db.table_df("patients", schema="mimiciii", limit=10)
#     assert isinstance(result, pd.DataFrame)
#     assert len(result) <= 10
