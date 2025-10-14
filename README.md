MIMIC-III EDA Summary

Branch: analysis/gloria_eda
This page summarizes exploratory data analysis (EDA) for DSC 180A Team 1’s MIMIC-III paper reproduction project.

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

Key Analyses for week 2
1. Patient Demographics (gloria_eda.ipynb)

Gender: 56.1% male, 43.9% female (gender_distribution.png)

Age by Gender: Adults (18–89); mean age 63.1 (F), 61.3 (M) (age_by_gender.png)

Age by Admission Type: Emergency, elective, urgent; newborns excluded (age_by_admission_type.png)

Ethnicity: Grouped into major categories (White, Black, Hispanic, Asian, Other) with mean ages shown (age_by_ethnicity.png)

2. Clinical Data

Admission Type Counts: Frequency of all admission types (admission_type_counts.png)

ICU Length of Stay: Distribution by ICU care unit, stays ≤ 60 days (los_by_icu_careunit.png)

Top Diagnoses: 15 most common ICD-9 codes (top_icd9_diagnoses.png)

Top Lab Tests: 20 most frequently ordered tests (top_lab_tests.png)

3. Clinical Notes

Note Categories: 10 most common note types (top_note_categories.png)

Note Lengths: Distribution of note character counts (note_length_distribution.png)

4. SOFA Score Analysis (illness_score.ipynb)

Systems: Respiratory, coagulation, liver, cardiovascular, CNS, renal

Criteria: ICU stay ≥ 24 hrs, age ≥ 16, elective vs non-elective admissions

Tables Used: patients, admissions, icustays

Outputs

All figures saved to assets/ with descriptive filenames.
Use these visualizations for demographic summaries and model input justification.
