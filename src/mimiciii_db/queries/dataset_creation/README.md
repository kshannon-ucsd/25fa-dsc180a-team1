# Dataset Creation Queries

This folder generates materialized views for a number of key operations during the paper replication process. The queries make use of materialized views of tables in the MIMIC-III database aimed at aggregating data for future use.

## Generated Tables

- **Elixhauser Quan** (`elixhauser_quan`) - Creating the Elixhauser Categorization table (using the script provided in the MIMIC-III Database).
- **Filtered Patients** (`filtered_patients`) - Creating the filtered dataset used for the visualizations within the paper.
- **Filtered Patients With Morbidity Counts** (`filtered_patients_with_morbidity_counts`) - Creating a dataset of the filtered patients with **counts of their Elixhauser Morbidities**.
- **Filtered Patients Agegrouped With Morbidities** (`filtered_patients_agegrouped_with_morbidities`) - Creating a dataset of the filtered patients with **boolean indicators** of whether they have each of the 30 Elixhauser Diseases.

## Usage

The scripts need to be created in the following order:
- elixhauser_quan.py
- filtered_patients.py
- filtered_patients_with_morbidity_counts.py
- filtered_patients_agegrouped_with_morbidities.py

Running the scripts is easy! All it requires is running a command along the lines of `python {script_name}`. For example, if I wanted to run the elixhauser_quan.py script, I would run the following commands:
- `cd src/mimiciii_db/queries/dataset_creation` (**note - this is assuming you are navigating in from the home directory**)
- `python filtered_patients.py`