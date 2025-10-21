#script to create the table with the patients involved in the study

import pandas as pd

from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
CREATE MATERIALIZED VIEW mimiciii.filtered_patients AS
 WITH first_icu AS (
         SELECT DISTINCT ON (icustays.subject_id) icustays.subject_id,
            icustays.hadm_id,
            icustays.icustay_id,
            icustays.intime,
            icustays.outtime
           FROM mimiciii.icustays
          ORDER BY icustays.subject_id, icustays.intime
        )
 SELECT pat.subject_id,
    fi.hadm_id,
    fi.icustay_id,
    pat.gender,
    fi.intime AS icu_intime,
    fi.outtime AS icu_outtime,
    a.admittime,
    a.dischtime,
    a.deathtime,
    a.admission_type,
    round(((((fi.intime)::date - (pat.dob)::date))::numeric / 365.242), 2) AS age
   FROM ((first_icu fi
     JOIN mimiciii.patients pat USING (subject_id))
     JOIN mimiciii.admissions a USING (subject_id, hadm_id))
  WHERE ((round(((((fi.intime)::date - (pat.dob)::date))::numeric / 365.242), 2) >= (16)::numeric) AND (round(((((fi.intime)::date - (pat.dob)::date))::numeric / 365.242), 2) <= (89)::numeric))
"""

db.query_df(query)

selection_query = f"""
SELECT * from mimiciii.filtered_patients
"""
df = db.query_df(selection_query)

pd.display(df)

#prefix the file however you wish, so that the original db remains imutable ; for all the files i create, i prefix the table/view/mv with "varun_" ; 
#so, in addition to the command above, I would recommend running the command "ALTER MATERIALIZED VIEW {old_mv} RENAME TO {varun_old_mv}"