#script to create the table to identify the presence of a mechanical ventilation on the first day of the ICU stay
import pandas as pd
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = """
DROP MATERIALIZED VIEW IF EXISTS mimiciii.ventilation_first_day;

CREATE MATERIALIZED VIEW mimiciii.ventilation_first_day AS
-- Determines if a patient is ventilated on the first day of their ICU stay.
-- Requires the ventilation_durations table already built in mimiciii.

SELECT
    ie.subject_id,
    ie.hadm_id,
    ie.icustay_id,

    -- vent = 1 if any ventilation event overlaps the first 24h window
    MAX(
        CASE
            WHEN vd.icustay_id IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS vent

FROM mimiciii.icustays ie
LEFT JOIN mimiciii.ventilation_durations vd
    ON ie.icustay_id = vd.icustay_id
    AND (
        -- Case 1: They were already vented on ICU admit
        (vd.starttime <= ie.intime AND vd.endtime >= ie.intime)
        OR
        -- Case 2: Vent started sometime in first 24h of ICU stay
        (vd.starttime >= ie.intime AND vd.starttime <= ie.intime + INTERVAL '1 day')
    )

GROUP BY ie.subject_id, ie.hadm_id, ie.icustay_id
ORDER BY ie.subject_id, ie.hadm_id, ie.icustay_id;
"""

db.execute(query)

selection_query = """
SELECT * FROM mimiciii.ventilation_first_day LIMIT 5;
"""
df = db.query_df(selection_query)
print(df)
