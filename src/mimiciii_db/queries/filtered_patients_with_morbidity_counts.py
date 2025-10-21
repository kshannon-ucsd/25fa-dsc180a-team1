#script to create the table with the patients involved in the study

import pandas as pd

from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
CREATE MATERIALIZED VIEW mimiciii.filtered_patients_with_morbidity_counts AS
 SELECT fp.subject_id,
    fp.hadm_id,
    fp.icustay_id,
    fp.gender,
    fp.icu_intime,
    fp.icu_outtime,
    fp.admittime,
    fp.dischtime,
    fp.deathtime,
    fp.admission_type,
    fp.age,
    (((((((((((((((((((((((((((((e.congestive_heart_failure + e.cardiac_arrhythmias) + e.valvular_disease) + e.pulmonary_circulation) + e.peripheral_vascular) + e.hypertension) + e.paralysis) + e.other_neurological) + e.chronic_pulmonary) + e.diabetes_uncomplicated) + e.diabetes_complicated) + e.hypothyroidism) + e.renal_failure) + e.liver_disease) + e.peptic_ulcer) + e.aids) + e.lymphoma) + e.metastatic_cancer) + e.solid_tumor) + e.rheumatoid_arthritis) + e.coagulopathy) + e.obesity) + e.weight_loss) + e.fluid_electrolyte) + e.blood_loss_anemia) + e.deficiency_anemias) + e.alcohol_abuse) + e.drug_abuse) + e.psychoses) + e.depression) AS morbidity_count
   FROM (mimiciii.filtered_patients fp
     JOIN mimiciii.elixhauser_quan e USING (hadm_id))
"""

db.query_df(query)

selection_query = f"""
SELECT * from filtered_patients_with_morbidity_counts LIMIT 1;
"""
df = db.query_df(selection_query)

pd.display(df)

#prefix the file however you wish, so that the original db remains imutable ; for all the files i create, i prefix the table/view/mv with "varun_" ; 
#so, in addition to the command above, I would recommend running the command "ALTER MATERIALIZED VIEW {old_mv} RENAME TO {varun_old_mv}"