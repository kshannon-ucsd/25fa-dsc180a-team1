# MIMIC-III EDA Analysis Wiki

## Branch: `analysis/gloria_eda`

This wiki documents the exploratory data analysis (EDA) work conducted on the MIMIC-III database for DSC 180A Team 1's paper reproduction project.

## Project Structure

```
25fa-dsc180a-team1/
├── notebooks/01_eda/                    # EDA notebooks
│   ├── gloria_eda.ipynb             # Main EDA analysis
│   └── illness_score.ipynb          # SOFA score analysis
├── assets/                          # Generated visualizations
│   ├── age_by_admission_type.png
│   ├── age_by_ethnicity.png
│   ├── age_by_gender.png
│   ├── admission_type_counts.png
│   ├── gender_distribution.png
│   ├── los_by_icu_careunit.png
│   ├── note_length_distribution.png
│   ├── top_icd9_diagnoses.png
│   ├── top_lab_tests.png
│   └── top_note_categories.png
└── src/mimiciii_db/                 # Database connection package
```

## Analyses

### 1. Patient Demographics Analysis (`gloria_eda.ipynb`)

#### Gender Distribution
- **Visualization**: `assets/gender_distribution.png`
- **Findings**: 
  - Male patients: 26,121 (56.1%)
  - Female patients: 20,399 (43.9%)
- **Analysis**: Bar chart with percentage annotations

#### Age Analysis by Gender
- **Visualization**: `assets/age_by_gender.png`
- **Methodology**: 
  - Focus on adults (18-89 years old)
  - Stacked histogram by gender
  - Mean age annotations
- **Findings**:
  - Female mean age: 63.10 years
  - Male mean age: 61.27 years

#### Age Analysis by Admission Type
- **Visualization**: `assets/age_by_admission_type.png`
- **Methodology**:
  - Normalized admission types (e.g., "EW EMER." → "EMERGENCY")
  - Excluded NEWBORN admissions
  - Color-coded by admission frequency
- **Key Admission Types**:
  - Emergency admissions
  - Elective admissions
  - Urgent admissions

#### Ethnicity Analysis
- **Visualization**: `assets/age_by_ethnicity.png`
- **Methodology**:
  - Ethnicity normalization into broad categories
  - Categories: WHITE, BLACK, HISPANIC/LATINO, ASIAN, OTHER, etc.
  - Mean age annotations for each group

### 2. Clinical Data Analysis

#### Admission Type Distribution
- **Visualization**: `assets/admission_type_counts.png`
- **Analysis**: Horizontal bar chart showing frequency of different admission types

#### Length of Stay by ICU Care Unit
- **Visualization**: `assets/los_by_icu_careunit.png`
- **Methodology**:
  - Focus on stays 0-60 days
  - Stacked histogram by ICU care unit
  - Shows distribution of length of stay across different ICU types

#### Top ICD-9 Diagnoses
- **Visualization**: `assets/top_icd9_diagnoses.png`
- **Analysis**: Top 15 most common diagnoses in the database
- **Data Source**: `diagnoses_icd` and `d_icd_diagnoses` tables

#### Laboratory Tests Analysis
- **Visualization**: `assets/top_lab_tests.png`
- **Methodology**:
  - Top 20 most frequently ordered lab tests
  - Data from `labevents` and `d_labitems` tables
  - Excludes NULL values

### 3. Clinical Notes Analysis

#### Note Categories
- **Visualization**: `assets/top_note_categories.png`
- **Analysis**: Top 10 most common note categories
- **Data Source**: `noteevents` table

#### Note Length Distribution
- **Visualization**: `assets/note_length_distribution.png`
- **Analysis**: Histogram of note character lengths
- **Insights**: Understanding of clinical note complexity

### 4. SOFA Score Analysis (`illness_score.ipynb`)

This notebook focuses on Sequential Organ Failure Assessment (SOFA) score analysis:

#### SOFA Components
- **Respiratory System**: PaO2/FiO2 ratio
- **Coagulation**: Platelet count
- **Liver**: Bilirubin level
- **Cardiovascular**: Blood pressure
- **Central Nervous System**: Glasgow Coma Scale
- **Renal**: Creatinine/urine output

#### Analysis Criteria
- ICU stays ≥ 24 hours
- Age ≥ 16 years
- Elective vs non-elective admissions
- Focus on patients, admissions, and icustays tables

## File Organization

### Notebooks
- `gloria_eda.ipynb`: Comprehensive EDA covering demographics, admissions, clinical data
- `illness_score.ipynb`: SOFA score analysis and illness severity metrics

### Generated Assets
All plots are automatically saved to the `assets/` folder with descriptive filenames:
- Demographics plots: `gender_distribution.png`, `age_by_*.png`
- Clinical analysis: `admission_type_counts.png`, `los_by_icu_careunit.png`
- Data exploration: `top_*.png`, `note_length_distribution.png`
