#script to create the table with the patients involved in the study

import pandas as pd

from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
CREATE MATERIALIZED VIEW mimiciii.morbidity_counts AS
 SELECT fp.subject_id,
    fp.hadm_id,
    fp.icustay_id,
    fp.gender,
    fp.deathtime,
    fp.admission_type,
    fp.age,
    ((EXTRACT(epoch FROM ((fp.icu_outtime)::timestamp without time zone - (fp.icu_intime)::timestamp without time zone)) / (86400)::numeric))::numeric(10,2) AS los_days_icu,
    ((EXTRACT(epoch FROM ((fp.dischtime)::timestamp without time zone - (fp.admittime)::timestamp without time zone)) / (86400)::numeric))::numeric(10,2) AS los_days_hospital,
    (((((((((((((((((((((((((((((COALESCE(e.congestive_heart_failure, 0) + COALESCE(e.cardiac_arrhythmias, 0)) + COALESCE(e.valvular_disease, 0)) + COALESCE(e.pulmonary_circulation, 0)) + COALESCE(e.peripheral_vascular, 0)) + COALESCE(e.hypertension, 0)) + COALESCE(e.paralysis, 0)) + COALESCE(e.other_neurological, 0)) + COALESCE(e.chronic_pulmonary, 0)) + COALESCE(e.diabetes_uncomplicated, 0)) + COALESCE(e.diabetes_complicated, 0)) + COALESCE(e.hypothyroidism, 0)) + COALESCE(e.renal_failure, 0)) + COALESCE(e.liver_disease, 0)) + COALESCE(e.peptic_ulcer, 0)) + COALESCE(e.aids, 0)) + COALESCE(e.lymphoma, 0)) + COALESCE(e.metastatic_cancer, 0)) + COALESCE(e.solid_tumor, 0)) + COALESCE(e.rheumatoid_arthritis, 0)) + COALESCE(e.coagulopathy, 0)) + COALESCE(e.obesity, 0)) + COALESCE(e.weight_loss, 0)) + COALESCE(e.fluid_electrolyte, 0)) + COALESCE(e.blood_loss_anemia, 0)) + COALESCE(e.deficiency_anemias, 0)) + COALESCE(e.alcohol_abuse, 0)) + COALESCE(e.drug_abuse, 0)) + COALESCE(e.psychoses, 0)) + COALESCE(e.depression, 0)) AS morbidity_count
   FROM (mimiciii.filtered_patients fp
     JOIN mimiciii.elixhauser_quan e USING (hadm_id))
"""

db.query_df(query)

selection_query = f"""
SELECT * from mimiciii.morbidity_counts
"""
df = db.query_df(selection_query)

pd.display(df)

#prefix the file however you wish, so that the original db remains imutable ; for all the files i create, i prefix the table/view/mv with "varun_" ; 
#so, in addition to the command above, I would recommend running the command "ALTER MATERIALIZED VIEW {old_mv} RENAME TO {varun_old_mv}"