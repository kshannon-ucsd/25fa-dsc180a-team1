# Illness Score Queries

This folder generates materialized views for a variety of severity of illness scores and supporting data tables. The queries make use of materialized views which aggregate data from the first day of a patient's ICU stay.

The scripts in this folder create materialized views that extract and calculate various clinical scores and measurements from the MIMIC-III database. These views are designed to support clinical research and analysis by providing pre-computed, standardized metrics.

## Generated Tables

### Severity of Illness Scores
- **SOFA** (`sofa`) - Sequential Organ Failure Assessment score
- **OASIS** (`oasis`) - Oxford Acute Severity of Illness Score  
- **SAPSII** (`sapsii`) - Simplified Acute Physiology Score II

### Data Tables
- **Echo Data** (`echo_data`) - Echocardiogram measurements
- **Ventilation Classification** (`ventilation_classification`) - Ventilation mode classification
- **Ventilation Durations** (`ventilation_durations`) - Duration of mechanical ventilation
- **Vitals First Day** (`vitals_first_day`) - Vital signs from first ICU day
- **Urine Output First Day** (`urine_output_first_day`) - Urine output measurements
- **Ventilation First Day** (`ventilation_first_day`) - Ventilation data from first day
- **GCS First Day** (`gcs_first_day`) - Glasgow Coma Scale scores
- **Labs First Day** (`labs_first_day`) - Laboratory values from first day
- **Blood Gas First Day** (`blood_gas_first_day`) - Blood gas measurements
- **Blood Gas First Day Arterial** (`blood_gas_first_day_arterial`) - Arterial blood gas values

## Usage

Each script can be run independently to generate its corresponding materialized view:


## Data Sources

The queries primarily utilize data from:
- Chart events
- Laboratory measurements
- Input/output events
- Procedure events
- Patient demographics and admission information

