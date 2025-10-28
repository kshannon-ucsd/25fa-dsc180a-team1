import pandas as pd
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = """
DROP TABLE IF EXISTS mimiciii.urine_output_first_day;

CREATE TABLE mimiciii.urine_output_first_day AS
-- ------------------------------------------------------------------
-- Purpose: total urine output for each ICU stay in first 24h
-- ------------------------------------------------------------------

SELECT
    ie.subject_id,
    ie.hadm_id,
    ie.icustay_id,

    SUM(
        CASE
            -- GU irrigant going in should count as negative (it's not patient urine)
            WHEN oe.itemid = 227488 AND oe.value > 0
                THEN -1 * oe.value
            ELSE oe.value
        END
    ) AS urineoutput

FROM mimiciii.icustays ie
LEFT JOIN mimiciii.outputevents oe
    ON ie.subject_id = oe.subject_id
    AND ie.hadm_id = oe.hadm_id
    AND ie.icustay_id = oe.icustay_id
    -- first ICU day only
    AND oe.charttime >= ie.intime
    AND oe.charttime <  ie.intime + INTERVAL '24 hours'

WHERE oe.itemid IN (
    -- CareVue urine outputs
    40055,  -- Urine Out Foley
    43175,  -- Urine .
    40069,  -- Urine Out Void
    40094,  -- Urine Out Condom Cath
    40715,  -- Urine Out Suprapubic
    40473,  -- Urine Out IleoConduit
    40085,  -- Urine Out Incontinent
    40057,  -- Urine Out Rt Nephrostomy
    40056,  -- Urine Out Lt Nephrostomy
    40405,  -- Urine Out Other
    40428,  -- Urine Out Straight Cath
    40086,  -- Urine Out Incontinent
    40096,  -- Urine Out Ureteral Stent #1
    40651,  -- Urine Out Ureteral Stent #2

    -- MetaVision urine outputs
    226559, -- Foley
    226560, -- Void
    226561, -- Condom Cath
    226584, -- Ileoconduit
    226563, -- Suprapubic
    226564, -- R Nephrostomy
    226565, -- L Nephrostomy
    226567, -- Straight Cath
    226557, -- R Ureteral Stent
    226558, -- L Ureteral Stent
    227488, -- GU Irrigant Volume In
    227489  -- GU Irrigant/Urine Volume Out
)

GROUP BY ie.subject_id, ie.hadm_id, ie.icustay_id
ORDER BY ie.subject_id, ie.hadm_id, ie.icustay_id;
"""

db.execute(query)

selection_query = """
SELECT * FROM mimiciii.urine_output_first_day LIMIT 1;
"""
df = db.query_df(selection_query)
print(df)
