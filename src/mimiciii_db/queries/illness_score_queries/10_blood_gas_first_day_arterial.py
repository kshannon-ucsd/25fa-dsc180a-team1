#script to create the table with the blood gas values for the first day of the ICU stay for arterial samples
import pandas as pd
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
DROP MATERIALIZED VIEW IF EXISTS mimiciii.blood_gas_first_day_arterial;

CREATE MATERIALIZED VIEW mimiciii.blood_gas_first_day_arterial AS
WITH stg_spo2 AS (
    SELECT
        ce.subject_id,
        ce.hadm_id,
        ce.icustay_id,
        ce.charttime,
        MAX(
            CASE
                WHEN ce.valuenum <= 0 OR ce.valuenum > 100 THEN NULL
                ELSE ce.valuenum
            END
        ) AS spo2
    FROM mimiciii.chartevents ce
    WHERE ce.itemid IN (
        646,      -- SpO2
        220277    -- O2 saturation pulseoxymetry
    )
    GROUP BY ce.subject_id, ce.hadm_id, ce.icustay_id, ce.charttime
),

stg_fio2 AS (
    SELECT
        ce.subject_id,
        ce.hadm_id,
        ce.icustay_id,
        ce.charttime,
        MAX(
            CASE
                WHEN ce.itemid = 223835 THEN
                    CASE
                        WHEN ce.valuenum > 0 AND ce.valuenum <= 1
                            THEN ce.valuenum * 100                    -- convert fraction -> %
                        WHEN ce.valuenum > 1 AND ce.valuenum < 21
                            THEN NULL                                 -- looks like flow in L/min, discard
                        WHEN ce.valuenum >= 21 AND ce.valuenum <= 100
                            THEN ce.valuenum                           -- already %
                        ELSE NULL
                    END
                WHEN ce.itemid IN (3420, 3422)
                    THEN ce.valuenum                                   -- already %
                WHEN ce.itemid = 190 AND ce.valuenum > 0.20 AND ce.valuenum < 1
                    THEN ce.valuenum * 100                             -- stored as fraction
                ELSE NULL
            END
        ) AS fio2_chartevents
    FROM mimiciii.chartevents ce
    WHERE ce.itemid IN (
        3420,      -- FiO2
        190,       -- FiO2 set
        223835,    -- Inspired O2 Fraction (FiO2)
        3422       -- FiO2 [measured]
    )
      AND (ce.error IS NULL OR ce.error = 0)
    GROUP BY ce.subject_id, ce.hadm_id, ce.icustay_id, ce.charttime
),

stg2 AS (
    SELECT
        bg.*,
        ROW_NUMBER() OVER (
            PARTITION BY bg.icustay_id, bg.charttime
            ORDER BY s1.charttime DESC
        ) AS lastRowSpO2,
        s1.spo2
    FROM mimiciii.blood_gas_first_day bg
    LEFT JOIN stg_spo2 s1
      ON bg.icustay_id = s1.icustay_id
     AND s1.charttime >= (bg.charttime - INTERVAL '2 hour')
     AND s1.charttime <= bg.charttime
    WHERE bg.po2 IS NOT NULL
),

stg3 AS (
    SELECT
        bg.*,
        ROW_NUMBER() OVER (
            PARTITION BY bg.icustay_id, bg.charttime
            ORDER BY s2.charttime DESC
        ) AS lastRowFiO2,
        s2.fio2_chartevents,

        /* logistic regression style arterial-specimen probability */
        1 / (
            1 + EXP(-(
                -0.02544
                +    0.04598 * bg.po2
                + COALESCE(-0.15356 * bg.spo2,
                           -0.15356 * 97.49420 + 0.13429)
                + COALESCE( 0.00621 * s2.fio2_chartevents,
                            0.00621 * 51.49550 + -0.24958)
                + COALESCE( 0.10559 * bg.hemoglobin,
                            0.10559 * 10.32307 + 0.05954)
                + COALESCE( 0.13251 * bg.so2,
                            0.13251 * 93.66539 + -0.23172)
                + COALESCE(-0.01511 * bg.pco2,
                           -0.01511 * 42.08866 + -0.01630)
                + COALESCE( 0.01480 * bg.fio2,
                            0.01480 * 63.97836 + -0.31142)
                + COALESCE(-0.00200 * bg.aado2,
                           -0.00200 * 442.21186 + -0.01328)
                + COALESCE(-0.03220 * bg.bicarbonate,
                           -0.03220 * 22.96894 + -0.06535)
                + COALESCE( 0.05384 * bg.totalco2,
                            0.05384 * 24.72632 + -0.01405)
                + COALESCE( 0.08202 * bg.lactate,
                            0.08202 * 3.06436  + 0.06038)
                + COALESCE( 0.10956 * bg.ph,
                            0.10956 * 7.36233  + -0.00617)
                + COALESCE( 0.00848 * bg.o2flow,
                            0.00848 * 7.59362  + -0.35803)
            ))
        ) AS specimen_prob
    FROM stg2 bg
    LEFT JOIN stg_fio2 s2
      ON bg.icustay_id = s2.icustay_id
     AND s2.charttime BETWEEN (bg.charttime - INTERVAL '4 hour') AND bg.charttime
    WHERE bg.lastRowSpO2 = 1
)

SELECT
    subject_id,
    hadm_id,
    icustay_id,
    charttime,

    specimen,

    CASE
        WHEN specimen IS NOT NULL THEN specimen
        WHEN specimen_prob > 0.75 THEN 'ART'
        ELSE NULL
    END AS specimen_pred,

    specimen_prob,

    -- oxygenation / vent parameters
    so2,
    spo2,
    po2,
    pco2,
    fio2_chartevents,
    fio2,
    aado2,

    -- A-a gradient we can recompute if needed
    CASE
        WHEN po2 IS NOT NULL
         AND pco2 IS NOT NULL
         AND COALESCE(fio2, fio2_chartevents) IS NOT NULL
        THEN
            (COALESCE(fio2, fio2_chartevents) / 100.0) * (760 - 47)
            - (pco2 / 0.8)
            - po2
        ELSE NULL
    END AS aado2_calc,

    CASE
        WHEN po2 IS NOT NULL
         AND COALESCE(fio2, fio2_chartevents) IS NOT NULL
        THEN
            100.0 * po2 / COALESCE(fio2, fio2_chartevents)
        ELSE NULL
    END AS pao2fio2,

    -- acid/base
    ph,
    baseexcess,
    bicarbonate,
    totalco2,

    -- blood counts
    hematocrit,
    hemoglobin,
    carboxyhemoglobin,
    methemoglobin,

    -- chemistry
    chloride,
    calcium,
    temperature,
    potassium,
    sodium,
    lactate,
    glucose,

    -- vent info
    intubated,
    tidalvolume,
    ventilationrate,
    ventilator,
    peep,
    o2flow,
    requiredo2

FROM stg3
WHERE lastRowFiO2 = 1
  AND (
        specimen = 'ART'
        OR specimen_prob > 0.75
      )
ORDER BY icustay_id, charttime;
"""

db.execute(query)

selection_query = f"""
SELECT * from mimiciii.blood_gas_first_day_arterial LIMIT 1;
"""
df = db.query_df(selection_query)

print(df)