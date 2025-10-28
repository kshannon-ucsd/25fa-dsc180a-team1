import pandas as pd
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
DROP TABLE IF EXISTS mimiciii.sofa;

CREATE TABLE mimiciii.sofa AS
WITH wt AS (
    SELECT
        ie.icustay_id,
        AVG(
            CASE
                WHEN c.itemid IN (762, 763, 3723, 3580, 226512)
                    THEN c.valuenum                            -- already kg
                WHEN c.itemid IN (3581)
                    THEN c.valuenum * 0.45359237               -- lb → kg
                WHEN c.itemid IN (3582)
                    THEN c.valuenum * 0.0283495231             -- oz → kg
                ELSE NULL
            END
        ) AS weight
    FROM mimiciii.icustays ie
    LEFT JOIN mimiciii.chartevents c
      ON ie.icustay_id = c.icustay_id
    WHERE c.valuenum IS NOT NULL
      AND c.itemid IN (
            762,763,3723,3580,        -- weight kg
            3581,                     -- lb
            3582,                     -- oz
            226512                    -- MetaVision admit wt kg
      )
      AND c.valuenum != 0
      AND c.charttime BETWEEN (ie.intime - INTERVAL '1 day')
                          AND (ie.intime + INTERVAL '1 day')
      AND (c.error IS NULL OR c.error = 0)
    GROUP BY ie.icustay_id
),

echo2 AS (
    -- backup weight from echo_data (which stored weight in lb)
    SELECT
        ie.icustay_id,
        AVG(echo.weight * 0.45359237) AS weight
    FROM mimiciii.icustays ie
    LEFT JOIN mimiciii.echo_data echo
      ON ie.hadm_id = echo.hadm_id
     AND echo.charttime > (ie.intime - INTERVAL '7 day')
     AND echo.charttime < (ie.intime + INTERVAL '1 day')
    GROUP BY ie.icustay_id
),

vaso_cv AS (
    SELECT
        ie.icustay_id,
        MAX(
            CASE
                WHEN cv.itemid = 30047
                    THEN cv.rate / COALESCE(wt.weight, ec.weight)  -- norepi, mcg/min → mcg/kg/min
                WHEN cv.itemid = 30120
                    THEN cv.rate                                   -- norepi already mcg/kg/min (ish)
                ELSE NULL
            END
        ) AS rate_norepinephrine,

        MAX(
            CASE
                WHEN cv.itemid = 30044
                    THEN cv.rate / COALESCE(wt.weight, ec.weight)  -- epi mcg/min → mcg/kg/min
                WHEN cv.itemid IN (30119,30309)
                    THEN cv.rate                                   -- epi mcg/kg/min
                ELSE NULL
            END
        ) AS rate_epinephrine,

        MAX(CASE WHEN cv.itemid IN (30043,30307) THEN cv.rate END) AS rate_dopamine,
        MAX(CASE WHEN cv.itemid IN (30042,30306) THEN cv.rate END) AS rate_dobutamine

    FROM mimiciii.icustays ie
    INNER JOIN mimiciii.inputevents_cv cv
      ON ie.icustay_id = cv.icustay_id
     AND cv.charttime BETWEEN ie.intime AND (ie.intime + INTERVAL '1 day')
    LEFT JOIN wt
      ON ie.icustay_id = wt.icustay_id
    LEFT JOIN echo2 ec
      ON ie.icustay_id = ec.icustay_id
    WHERE cv.itemid IN (
        30047,30120,        -- norepi
        30044,30119,30309,  -- epi
        30043,30307,        -- dopamine
        30042,30306         -- dobutamine
    )
      AND cv.rate IS NOT NULL
    GROUP BY ie.icustay_id
),

vaso_mv AS (
    SELECT
        ie.icustay_id,
        MAX(CASE WHEN mv.itemid = 221906 THEN mv.rate END) AS rate_norepinephrine,
        MAX(CASE WHEN mv.itemid = 221289 THEN mv.rate END) AS rate_epinephrine,
        MAX(CASE WHEN mv.itemid = 221662 THEN mv.rate END) AS rate_dopamine,
        MAX(CASE WHEN mv.itemid = 221653 THEN mv.rate END) AS rate_dobutamine
    FROM mimiciii.icustays ie
    INNER JOIN mimiciii.inputevents_mv mv
      ON ie.icustay_id = mv.icustay_id
     AND mv.starttime BETWEEN ie.intime AND (ie.intime + INTERVAL '1 day')
    WHERE mv.itemid IN (221906,221289,221662,221653)
      AND mv.statusdescription != 'Rewritten'
    GROUP BY ie.icustay_id
),

pafi1 AS (
    -- PaO2/FiO2 by time and vent status
    SELECT
        bg.icustay_id,
        bg.charttime,
        bg.pao2fio2,
        CASE WHEN vd.icustay_id IS NOT NULL THEN 1 ELSE 0 END AS isvent
    FROM mimiciii.blood_gas_first_day_arterial bg
    LEFT JOIN mimiciii.ventilation_durations vd
      ON bg.icustay_id = vd.icustay_id
     AND bg.charttime >= vd.starttime
     AND bg.charttime <= vd.endtime
    ORDER BY bg.icustay_id, bg.charttime
),

pafi2 AS (
    -- separate min PaO2/FiO2 when vented vs not vented
    SELECT
        icustay_id,
        MIN(CASE WHEN isvent = 0 THEN pao2fio2 ELSE NULL END) AS pao2fio2_novent_min,
        MIN(CASE WHEN isvent = 1 THEN pao2fio2 ELSE NULL END) AS pao2fio2_vent_min
    FROM pafi1
    GROUP BY icustay_id
),

scorecomp AS (
    SELECT
        ie.icustay_id,

        v.meanbp_min,
        COALESCE(cv.rate_norepinephrine, mv.rate_norepinephrine) AS rate_norepinephrine,
        COALESCE(cv.rate_epinephrine,    mv.rate_epinephrine)    AS rate_epinephrine,
        COALESCE(cv.rate_dopamine,       mv.rate_dopamine)       AS rate_dopamine,
        COALESCE(cv.rate_dobutamine,     mv.rate_dobutamine)     AS rate_dobutamine,

        l.creatinine_max,
        l.bilirubin_max,
        l.platelet_min,

        pf.pao2fio2_novent_min,
        pf.pao2fio2_vent_min,

        uo.urineoutput,

        gcs.mingcs
    FROM mimiciii.icustays ie
    LEFT JOIN vaso_cv cv
      ON ie.icustay_id = cv.icustay_id
    LEFT JOIN vaso_mv mv
      ON ie.icustay_id = mv.icustay_id
    LEFT JOIN pafi2 pf
      ON ie.icustay_id = pf.icustay_id
    LEFT JOIN mimiciii.vitals_first_day v
      ON ie.icustay_id = v.icustay_id
    LEFT JOIN mimiciii.labs_first_day l
      ON ie.icustay_id = l.icustay_id
    LEFT JOIN mimiciii.urine_output_first_day uo
      ON ie.icustay_id = uo.icustay_id
    LEFT JOIN mimiciii.gcs_first_day gcs
      ON ie.icustay_id = gcs.icustay_id
),

scorecalc AS (
    SELECT
        icustay_id,

        -- Respiration
        CASE
            WHEN pao2fio2_vent_min   < 100 THEN 4
            WHEN pao2fio2_vent_min   < 200 THEN 3
            WHEN pao2fio2_novent_min < 300 THEN 2
            WHEN pao2fio2_novent_min < 400 THEN 1
            WHEN COALESCE(pao2fio2_vent_min, pao2fio2_novent_min) IS NULL THEN NULL
            ELSE 0
        END AS respiration,

        -- Coagulation
        CASE
            WHEN platelet_min < 20  THEN 4
            WHEN platelet_min < 50  THEN 3
            WHEN platelet_min < 100 THEN 2
            WHEN platelet_min < 150 THEN 1
            WHEN platelet_min IS NULL THEN NULL
            ELSE 0
        END AS coagulation,

        -- Liver (bilirubin mg/dL)
        CASE
            WHEN bilirubin_max >= 12.0 THEN 4
            WHEN bilirubin_max >=  6.0 THEN 3
            WHEN bilirubin_max >=  2.0 THEN 2
            WHEN bilirubin_max >=  1.2 THEN 1
            WHEN bilirubin_max IS NULL THEN NULL
            ELSE 0
        END AS liver,

        -- Cardiovascular
        CASE
            WHEN rate_dopamine > 15
              OR rate_epinephrine > 0.1
              OR rate_norepinephrine > 0.1
                THEN 4
            WHEN rate_dopamine > 5
              OR rate_epinephrine <= 0.1
              OR rate_norepinephrine <= 0.1
                THEN 3
            WHEN rate_dopamine > 0
              OR rate_dobutamine > 0
                THEN 2
            WHEN meanbp_min < 70
                THEN 1
            WHEN COALESCE(
                    meanbp_min,
                    rate_dopamine,
                    rate_dobutamine,
                    rate_epinephrine,
                    rate_norepinephrine
                 ) IS NULL
                THEN NULL
            ELSE 0
        END AS cardiovascular,

        -- CNS (GCS)
        CASE
            WHEN mingcs BETWEEN 13 AND 14 THEN 1
            WHEN mingcs BETWEEN 10 AND 12 THEN 2
            WHEN mingcs BETWEEN  6 AND  9 THEN 3
            WHEN mingcs < 6            THEN 4
            WHEN mingcs IS NULL        THEN NULL
            ELSE 0
        END AS cns,

        -- Renal (creatinine or urine output)
        CASE
            WHEN creatinine_max >= 5.0 THEN 4
            WHEN urineoutput < 200     THEN 4
            WHEN creatinine_max >= 3.5 AND creatinine_max < 5.0 THEN 3
            WHEN urineoutput < 500     THEN 3
            WHEN creatinine_max >= 2.0 AND creatinine_max < 3.5 THEN 2
            WHEN creatinine_max >= 1.2 AND creatinine_max < 2.0 THEN 1
            WHEN COALESCE(urineoutput, creatinine_max) IS NULL THEN NULL
            ELSE 0
        END AS renal
    FROM scorecomp
)

SELECT
    ie.subject_id,
    ie.hadm_id,
    ie.icustay_id,
    COALESCE(respiration,0)
  + COALESCE(coagulation,0)
  + COALESCE(liver,0)
  + COALESCE(cardiovascular,0)
  + COALESCE(cns,0)
  + COALESCE(renal,0) AS sofa,
    respiration,
    coagulation,
    liver,
    cardiovascular,
    cns,
    renal
FROM mimiciii.icustays ie
LEFT JOIN scorecalc s
  ON ie.icustay_id = s.icustay_id
ORDER BY ie.icustay_id;
"""

db.execute(query)

selection_query = f"""
SELECT * from mimiciii.sofa LIMIT 1;
"""
df = db.query_df(selection_query)

print(df)