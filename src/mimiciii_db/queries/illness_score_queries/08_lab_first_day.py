import pandas as pd
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
DROP TABLE IF EXISTS mimiciii.labs_first_day;

CREATE TABLE mimiciii.labs_first_day AS
-- This query pivots lab values taken in the first 24 hours of a patient's ICU stay.
-- We also allow labs drawn up to 6h *before* ICU intime (common clinically).

SELECT
    pvt.subject_id,
    pvt.hadm_id,
    pvt.icustay_id,

    MIN(CASE WHEN label = 'ANION GAP'    THEN valuenum END) AS aniongap_min,
    MAX(CASE WHEN label = 'ANION GAP'    THEN valuenum END) AS aniongap_max,

    MIN(CASE WHEN label = 'ALBUMIN'      THEN valuenum END) AS albumin_min,
    MAX(CASE WHEN label = 'ALBUMIN'      THEN valuenum END) AS albumin_max,

    MIN(CASE WHEN label = 'BANDS'        THEN valuenum END) AS bands_min,
    MAX(CASE WHEN label = 'BANDS'        THEN valuenum END) AS bands_max,

    MIN(CASE WHEN label = 'BICARBONATE'  THEN valuenum END) AS bicarbonate_min,
    MAX(CASE WHEN label = 'BICARBONATE'  THEN valuenum END) AS bicarbonate_max,

    MIN(CASE WHEN label = 'BILIRUBIN'    THEN valuenum END) AS bilirubin_min,
    MAX(CASE WHEN label = 'BILIRUBIN'    THEN valuenum END) AS bilirubin_max,

    MIN(CASE WHEN label = 'CREATININE'   THEN valuenum END) AS creatinine_min,
    MAX(CASE WHEN label = 'CREATININE'   THEN valuenum END) AS creatinine_max,

    MIN(CASE WHEN label = 'CHLORIDE'     THEN valuenum END) AS chloride_min,
    MAX(CASE WHEN label = 'CHLORIDE'     THEN valuenum END) AS chloride_max,

    MIN(CASE WHEN label = 'GLUCOSE'      THEN valuenum END) AS glucose_min,
    MAX(CASE WHEN label = 'GLUCOSE'      THEN valuenum END) AS glucose_max,

    MIN(CASE WHEN label = 'HEMATOCRIT'   THEN valuenum END) AS hematocrit_min,
    MAX(CASE WHEN label = 'HEMATOCRIT'   THEN valuenum END) AS hematocrit_max,

    MIN(CASE WHEN label = 'HEMOGLOBIN'   THEN valuenum END) AS hemoglobin_min,
    MAX(CASE WHEN label = 'HEMOGLOBIN'   THEN valuenum END) AS hemoglobin_max,

    MIN(CASE WHEN label = 'LACTATE'      THEN valuenum END) AS lactate_min,
    MAX(CASE WHEN label = 'LACTATE'      THEN valuenum END) AS lactate_max,

    MIN(CASE WHEN label = 'PLATELET'     THEN valuenum END) AS platelet_min,
    MAX(CASE WHEN label = 'PLATELET'     THEN valuenum END) AS platelet_max,

    MIN(CASE WHEN label = 'POTASSIUM'    THEN valuenum END) AS potassium_min,
    MAX(CASE WHEN label = 'POTASSIUM'    THEN valuenum END) AS potassium_max,

    MIN(CASE WHEN label = 'PTT'          THEN valuenum END) AS ptt_min,
    MAX(CASE WHEN label = 'PTT'          THEN valuenum END) AS ptt_max,

    MIN(CASE WHEN label = 'INR'          THEN valuenum END) AS inr_min,
    MAX(CASE WHEN label = 'INR'          THEN valuenum END) AS inr_max,

    MIN(CASE WHEN label = 'PT'           THEN valuenum END) AS pt_min,
    MAX(CASE WHEN label = 'PT'           THEN valuenum END) AS pt_max,

    MIN(CASE WHEN label = 'SODIUM'       THEN valuenum END) AS sodium_min,
    MAX(CASE WHEN label = 'SODIUM'       THEN valuenum END) AS sodium_max,

    MIN(CASE WHEN label = 'BUN'          THEN valuenum END) AS bun_min,
    MAX(CASE WHEN label = 'BUN'          THEN valuenum END) AS bun_max,

    MIN(CASE WHEN label = 'WBC'          THEN valuenum END) AS wbc_min,
    MAX(CASE WHEN label = 'WBC'          THEN valuenum END) AS wbc_max

FROM (
    SELECT
        ie.subject_id,
        ie.hadm_id,
        ie.icustay_id,

        /* Map raw ITEMIDs to canonical lab labels */
        CASE
            WHEN le.itemid = 50868 THEN 'ANION GAP'
            WHEN le.itemid = 50862 THEN 'ALBUMIN'
            WHEN le.itemid = 51144 THEN 'BANDS'
            WHEN le.itemid = 50882 THEN 'BICARBONATE'
            WHEN le.itemid = 50885 THEN 'BILIRUBIN'
            WHEN le.itemid = 50912 THEN 'CREATININE'
            WHEN le.itemid = 50806 THEN 'CHLORIDE'
            WHEN le.itemid = 50902 THEN 'CHLORIDE'
            WHEN le.itemid = 50809 THEN 'GLUCOSE'
            WHEN le.itemid = 50931 THEN 'GLUCOSE'
            WHEN le.itemid = 50810 THEN 'HEMATOCRIT'
            WHEN le.itemid = 51221 THEN 'HEMATOCRIT'
            WHEN le.itemid = 50811 THEN 'HEMOGLOBIN'
            WHEN le.itemid = 51222 THEN 'HEMOGLOBIN'
            WHEN le.itemid = 50813 THEN 'LACTATE'
            WHEN le.itemid = 51265 THEN 'PLATELET'
            WHEN le.itemid = 50822 THEN 'POTASSIUM'
            WHEN le.itemid = 50971 THEN 'POTASSIUM'
            WHEN le.itemid = 51275 THEN 'PTT'
            WHEN le.itemid = 51237 THEN 'INR'
            WHEN le.itemid = 51274 THEN 'PT'
            WHEN le.itemid = 50824 THEN 'SODIUM'
            WHEN le.itemid = 50983 THEN 'SODIUM'
            WHEN le.itemid = 51006 THEN 'BUN'
            WHEN le.itemid = 51300 THEN 'WBC'
            WHEN le.itemid = 51301 THEN 'WBC'
            ELSE NULL
        END AS label,

        /* Range/sanity cleaning (upper bounds etc.) */
        CASE
            WHEN le.itemid = 50862 AND le.valuenum >    10 THEN NULL -- ALBUMIN g/dL
            WHEN le.itemid = 50868 AND le.valuenum > 10000 THEN NULL -- ANION GAP mEq/L
            WHEN le.itemid = 51144 AND le.valuenum <     0 THEN NULL -- BANDS %
            WHEN le.itemid = 51144 AND le.valuenum >   100 THEN NULL -- BANDS %
            WHEN le.itemid = 50882 AND le.valuenum > 10000 THEN NULL -- BICARBONATE
            WHEN le.itemid = 50885 AND le.valuenum >   150 THEN NULL -- BILIRUBIN mg/dL
            WHEN le.itemid = 50806 AND le.valuenum > 10000 THEN NULL -- CHLORIDE
            WHEN le.itemid = 50902 AND le.valuenum > 10000 THEN NULL -- CHLORIDE
            WHEN le.itemid = 50912 AND le.valuenum >   150 THEN NULL -- CREATININE mg/dL
            WHEN le.itemid = 50809 AND le.valuenum > 10000 THEN NULL -- GLUCOSE
            WHEN le.itemid = 50931 AND le.valuenum > 10000 THEN NULL -- GLUCOSE
            WHEN le.itemid = 50810 AND le.valuenum >   100 THEN NULL -- HCT %
            WHEN le.itemid = 51221 AND le.valuenum >   100 THEN NULL
            WHEN le.itemid = 50811 AND le.valuenum >    50 THEN NULL -- HGB g/dL
            WHEN le.itemid = 51222 AND le.valuenum >    50 THEN NULL
            WHEN le.itemid = 50813 AND le.valuenum >    50 THEN NULL -- LACTATE mmol/L
            WHEN le.itemid = 51265 AND le.valuenum > 10000 THEN NULL -- PLATELET K/uL
            WHEN le.itemid = 50822 AND le.valuenum >    30 THEN NULL -- K mEq/L
            WHEN le.itemid = 50971 AND le.valuenum >    30 THEN NULL
            WHEN le.itemid = 51275 AND le.valuenum >   150 THEN NULL -- PTT sec
            WHEN le.itemid = 51237 AND le.valuenum >    50 THEN NULL -- INR
            WHEN le.itemid = 51274 AND le.valuenum >   150 THEN NULL -- PT sec
            WHEN le.itemid = 50824 AND le.valuenum >   200 THEN NULL -- Na
            WHEN le.itemid = 50983 AND le.valuenum >   200 THEN NULL
            WHEN le.itemid = 51006 AND le.valuenum >   300 THEN NULL -- BUN
            WHEN le.itemid = 51300 AND le.valuenum >  1000 THEN NULL -- WBC
            WHEN le.itemid = 51301 AND le.valuenum >  1000 THEN NULL
            ELSE le.valuenum
        END AS valuenum

    FROM mimiciii.icustays ie
    LEFT JOIN mimiciii.labevents le
      ON le.subject_id = ie.subject_id
     AND le.hadm_id    = ie.hadm_id
     AND le.charttime BETWEEN (ie.intime - INTERVAL '6 hour')
                          AND (ie.intime + INTERVAL '1 day')
     AND le.itemid IN (
        50868, 50862, 51144, 50882, 50885,
        50912, 50902, 50806, 50931, 50809,
        51221, 50810, 51222, 50811, 50813,
        51265, 50971, 50822, 51275, 51237,
        51274, 50983, 50824, 51006, 51301,
        51300
     )
     AND le.valuenum IS NOT NULL
     AND le.valuenum > 0
) AS pvt
GROUP BY
    pvt.subject_id,
    pvt.hadm_id,
    pvt.icustay_id
ORDER BY
    pvt.subject_id,
    pvt.hadm_id,
    pvt.icustay_id;
"""

db.execute(query)

selection_query = f"""
SELECT * from mimiciii.labs_first_day LIMIT 1;
"""
df = db.query_df(selection_query)

print(df)