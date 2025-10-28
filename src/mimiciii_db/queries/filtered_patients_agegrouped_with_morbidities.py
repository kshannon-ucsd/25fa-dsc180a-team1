#script to create the table with the patients involved in the study

import pandas as pd

from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
CREATE MATERIALIZED VIEW mimiciii.filtered_patients_agegrouped_with_morbidities AS
 SELECT c.subject_id,
    c.hadm_id,
    c.age,
        CASE
            WHEN ((round(c.age) >= (16)::numeric) AND (round(c.age) <= (24)::numeric)) THEN '16-24'::text
            WHEN ((round(c.age) >= (25)::numeric) AND (round(c.age) <= (44)::numeric)) THEN '25-44'::text
            WHEN ((round(c.age) >= (45)::numeric) AND (round(c.age) <= (64)::numeric)) THEN '45-64'::text
            WHEN ((round(c.age) >= (65)::numeric) AND (round(c.age) <= (84)::numeric)) THEN '65-84'::text
            ELSE '≥85'::text
        END AS age_bin,
    e.congestive_heart_failure,
    e.cardiac_arrhythmias,
    e.valvular_disease,
    e.pulmonary_circulation,
    e.peripheral_vascular,
    e.hypertension,
    e.paralysis,
    e.other_neurological,
    e.chronic_pulmonary,
    e.diabetes_uncomplicated,
    e.diabetes_complicated,
    e.hypothyroidism,
    e.renal_failure,
    e.liver_disease,
    e.peptic_ulcer,
    e.aids,
    e.lymphoma,
    e.metastatic_cancer,
    e.solid_tumor,
    e.rheumatoid_arthritis,
    e.coagulopathy,
    e.obesity,
    e.weight_loss,
    e.fluid_electrolyte,
    e.blood_loss_anemia,
    e.deficiency_anemias,
    e.alcohol_abuse,
    e.drug_abuse,
    e.psychoses,
    e.depression
   FROM (mimiciii.filtered_patients AS c
     LEFT JOIN mimiciii.elixhauser_quan AS e USING (hadm_id))
"""

db.execute(query)

selection_query = f"""
SELECT * from filtered_patients_agegrouped_with_morbidities LIMIT 1;
"""
df = db.query_df(selection_query)

print(df)

#prefix the file however you wish, so that the original db remains imutable ; for all the files i create, i prefix the table/view/mv with "varun_" ; 
#so, in addition to the command above, I would recommend running the command "ALTER MATERIALIZED VIEW {old_mv} RENAME TO {varun_old_mv}"