import pandas as pd
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = """
DROP TABLE IF EXISTS mimiciii.vitals_first_day;

CREATE TABLE mimiciii.vitals_first_day AS
-- first-24h vitals per ICU stay
SELECT
    pvt.subject_id,
    pvt.hadm_id,
    pvt.icustay_id,

    MIN(CASE WHEN vitalid = 1 THEN valuenum END) AS heartrate_min,
    MAX(CASE WHEN vitalid = 1 THEN valuenum END) AS heartrate_max,
    AVG(CASE WHEN vitalid = 1 THEN valuenum END) AS heartrate_mean,

    MIN(CASE WHEN vitalid = 2 THEN valuenum END) AS sysbp_min,
    MAX(CASE WHEN vitalid = 2 THEN valuenum END) AS sysbp_max,
    AVG(CASE WHEN vitalid = 2 THEN valuenum END) AS sysbp_mean,

    MIN(CASE WHEN vitalid = 3 THEN valuenum END) AS diasbp_min,
    MAX(CASE WHEN vitalid = 3 THEN valuenum END) AS diasbp_max,
    AVG(CASE WHEN vitalid = 3 THEN valuenum END) AS diasbp_mean,

    MIN(CASE WHEN vitalid = 4 THEN valuenum END) AS meanbp_min,
    MAX(CASE WHEN vitalid = 4 THEN valuenum END) AS meanbp_max,
    AVG(CASE WHEN vitalid = 4 THEN valuenum END) AS meanbp_mean,

    MIN(CASE WHEN vitalid = 5 THEN valuenum END) AS resprate_min,
    MAX(CASE WHEN vitalid = 5 THEN valuenum END) AS resprate_max,
    AVG(CASE WHEN vitalid = 5 THEN valuenum END) AS resprate_mean,

    MIN(CASE WHEN vitalid = 6 THEN valuenum END) AS tempc_min,
    MAX(CASE WHEN vitalid = 6 THEN valuenum END) AS tempc_max,
    AVG(CASE WHEN vitalid = 6 THEN valuenum END) AS tempc_mean,

    MIN(CASE WHEN vitalid = 7 THEN valuenum END) AS spo2_min,
    MAX(CASE WHEN vitalid = 7 THEN valuenum END) AS spo2_max,
    AVG(CASE WHEN vitalid = 7 THEN valuenum END) AS spo2_mean,

    MIN(CASE WHEN vitalid = 8 THEN valuenum END) AS glucose_min,
    MAX(CASE WHEN vitalid = 8 THEN valuenum END) AS glucose_max,
    AVG(CASE WHEN vitalid = 8 THEN valuenum END) AS glucose_mean

FROM (
    SELECT
        ie.subject_id,
        ie.hadm_id,
        ie.icustay_id,

        -- map itemids to "which vital sign is this?"
        CASE
            WHEN ce.itemid IN (211,220045)
                 AND ce.valuenum > 0 AND ce.valuenum < 300
            THEN 1  -- HeartRate

            WHEN ce.itemid IN (51,442,455,6701,220179,220050)
                 AND ce.valuenum > 0 AND ce.valuenum < 400
            THEN 2  -- SysBP

            WHEN ce.itemid IN (8368,8440,8441,8555,220180,220051)
                 AND ce.valuenum > 0 AND ce.valuenum < 300
            THEN 3  -- DiasBP

            WHEN ce.itemid IN (456,52,6702,443,220052,220181,225312)
                 AND ce.valuenum > 0 AND ce.valuenum < 300
            THEN 4  -- MeanBP

            WHEN ce.itemid IN (615,618,220210,224690)
                 AND ce.valuenum > 0 AND ce.valuenum < 70
            THEN 5  -- RespRate

            WHEN ce.itemid IN (223761,678)
                 AND ce.valuenum > 70 AND ce.valuenum < 120
            THEN 6  -- TempF (will convert below)

            WHEN ce.itemid IN (223762,676)
                 AND ce.valuenum > 10 AND ce.valuenum < 50
            THEN 6  -- TempC

            WHEN ce.itemid IN (646,220277)
                 AND ce.valuenum > 0 AND ce.valuenum <= 100
            THEN 7  -- SpO2

            WHEN ce.itemid IN (807,811,1529,3745,3744,225664,220621,226537)
                 AND ce.valuenum > 0
            THEN 8  -- Glucose

            ELSE NULL
        END AS vitalid,

        -- normalize temperature to Celsius
        CASE
            WHEN ce.itemid IN (223761,678) THEN (ce.valuenum - 32)/1.8
            ELSE ce.valuenum
        END AS valuenum

    FROM mimiciii.icustays ie
    LEFT JOIN mimiciii.chartevents ce
        ON ie.icustay_id = ce.icustay_id
        AND ce.charttime >= ie.intime
        AND ce.charttime <  ie.intime + INTERVAL '24 hours'
        -- exclude rows marked as error
        AND (ce.error IS NULL OR ce.error = 0)

    WHERE ce.itemid IN (
        -- HEART RATE
        211,        -- Heart Rate
        220045,     -- Heart Rate

        -- Systolic BP
        51,         -- Arterial BP [Systolic]
        442,        -- Manual BP [Systolic]
        455,        -- NBP [Systolic]
        6701,       -- Arterial BP #2 [Systolic]
        220179,     -- NIBP systolic
        220050,     -- Art BP systolic

        -- Diastolic BP
        8368,       -- Arterial BP [Diastolic]
        8440,       -- Manual BP [Diastolic]
        8441,       -- NBP [Diastolic]
        8555,       -- Arterial BP #2 [Diastolic]
        220180,     -- NIBP diastolic
        220051,     -- Art BP diastolic

        -- Mean BP
        456,        -- NBP Mean
        52,         -- Arterial BP Mean
        6702,       -- Arterial BP Mean #2
        443,        -- Manual BP Mean(calc)
        220052,     -- Art BP mean
        220181,     -- NIBP mean
        225312,     -- ART BP mean

        -- Respiratory Rate
        618,        -- Respiratory Rate
        615,        -- Resp Rate (Total)
        220210,     -- Respiratory Rate
        224690,     -- Respiratory Rate (Total)

        -- SpO2
        646,
        220277,

        -- Glucose
        807,        -- Fingerstick Glucose
        811,        -- Glucose (70-105)
        1529,       -- Glucose
        3745,       -- BloodGlucose
        3744,       -- Blood Glucose
        225664,     -- Glucose finger stick
        220621,     -- Glucose (serum)
        226537,     -- Glucose (whole blood)

        -- Temperature
        223762,     -- Temperature Celsius
        676,        -- Temperature C
        223761,     -- Temperature Fahrenheit
        678         -- Temperature F
    )
) pvt
GROUP BY pvt.subject_id, pvt.hadm_id, pvt.icustay_id
ORDER BY pvt.subject_id, pvt.hadm_id, pvt.icustay_id;
"""

db.execute(query)

selection_query = """
SELECT * FROM mimiciii.vitals_first_day LIMIT 1;
"""
df = db.query_df(selection_query)
print(df)
