import pandas as pd
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
DROP TABLE IF EXISTS mimiciii.blood_gas_first_day;

CREATE TABLE mimiciii.blood_gas_first_day AS
WITH pvt AS (
    SELECT
        ie.subject_id,
        ie.hadm_id,
        ie.icustay_id,
        le.charttime,
        /* Map ITEMID -> canonical label */
        CASE
            WHEN le.itemid = 50800 THEN 'SPECIMEN'
            WHEN le.itemid = 50801 THEN 'AADO2'
            WHEN le.itemid = 50802 THEN 'BASEEXCESS'
            WHEN le.itemid = 50803 THEN 'BICARBONATE'
            WHEN le.itemid = 50804 THEN 'TOTALCO2'
            WHEN le.itemid = 50805 THEN 'CARBOXYHEMOGLOBIN'
            WHEN le.itemid = 50806 THEN 'CHLORIDE'
            WHEN le.itemid = 50808 THEN 'CALCIUM'
            WHEN le.itemid = 50809 THEN 'GLUCOSE'
            WHEN le.itemid = 50810 THEN 'HEMATOCRIT'
            WHEN le.itemid = 50811 THEN 'HEMOGLOBIN'
            WHEN le.itemid = 50812 THEN 'INTUBATED'
            WHEN le.itemid = 50813 THEN 'LACTATE'
            WHEN le.itemid = 50814 THEN 'METHEMOGLOBIN'
            WHEN le.itemid = 50815 THEN 'O2FLOW'
            WHEN le.itemid = 50816 THEN 'FIO2'
            WHEN le.itemid = 50817 THEN 'SO2'
            WHEN le.itemid = 50818 THEN 'PCO2'
            WHEN le.itemid = 50819 THEN 'PEEP'
            WHEN le.itemid = 50820 THEN 'PH'
            WHEN le.itemid = 50821 THEN 'PO2'
            WHEN le.itemid = 50822 THEN 'POTASSIUM'
            WHEN le.itemid = 50823 THEN 'REQUIREDO2'
            WHEN le.itemid = 50824 THEN 'SODIUM'
            WHEN le.itemid = 50825 THEN 'TEMPERATURE'
            WHEN le.itemid = 50826 THEN 'TIDALVOLUME'
            WHEN le.itemid = 50827 THEN 'VENTILATIONRATE'
            WHEN le.itemid = 50828 THEN 'VENTILATOR'
            ELSE NULL
        END AS label,

        le.value,

        /* Clean numeric values and enforce plausible ranges */
        CASE
            WHEN le.valuenum <= 0 AND le.itemid <> 50802 THEN NULL
            WHEN le.itemid = 50810 AND le.valuenum > 100 THEN NULL       -- hematocrit
            WHEN le.itemid = 50816 AND le.valuenum < 20  THEN NULL       -- FiO2 sanity
            WHEN le.itemid = 50816 AND le.valuenum > 100 THEN NULL
            WHEN le.itemid = 50817 AND le.valuenum > 100 THEN NULL       -- O2 sat
            WHEN le.itemid = 50815 AND le.valuenum > 70  THEN NULL       -- O2 flow
            WHEN le.itemid = 50821 AND le.valuenum > 800 THEN NULL       -- PO2
            ELSE le.valuenum
        END AS valuenum

    FROM mimiciii.icustays ie
    LEFT JOIN mimiciii.labevents le
      ON le.subject_id = ie.subject_id
     AND le.hadm_id    = ie.hadm_id
     AND le.charttime BETWEEN (ie.intime - INTERVAL '6 hour')
                          AND (ie.intime + INTERVAL '1 day')
     AND le.itemid IN (
        50800,50801,50802,50803,50804,50805,50806,50807,50808,50809,
        50810,50811,50812,50813,50814,50815,50816,50817,50818,50819,
        50820,50821,50822,50823,50824,50825,50826,50827,50828,
        51545
     )
)
SELECT
    pvt.subject_id,
    pvt.hadm_id,
    pvt.icustay_id,
    pvt.charttime,

    MAX(CASE WHEN label = 'SPECIMEN'         THEN value     END) AS specimen,
    MAX(CASE WHEN label = 'AADO2'            THEN valuenum  END) AS aado2,
    MAX(CASE WHEN label = 'BASEEXCESS'       THEN valuenum  END) AS baseexcess,
    MAX(CASE WHEN label = 'BICARBONATE'      THEN valuenum  END) AS bicarbonate,
    MAX(CASE WHEN label = 'TOTALCO2'         THEN valuenum  END) AS totalco2,
    MAX(CASE WHEN label = 'CARBOXYHEMOGLOBIN'THEN valuenum  END) AS carboxyhemoglobin,
    MAX(CASE WHEN label = 'CHLORIDE'         THEN valuenum  END) AS chloride,
    MAX(CASE WHEN label = 'CALCIUM'          THEN valuenum  END) AS calcium,
    MAX(CASE WHEN label = 'GLUCOSE'          THEN valuenum  END) AS glucose,
    MAX(CASE WHEN label = 'HEMATOCRIT'       THEN valuenum  END) AS hematocrit,
    MAX(CASE WHEN label = 'HEMOGLOBIN'       THEN valuenum  END) AS hemoglobin,
    MAX(CASE WHEN label = 'INTUBATED'        THEN valuenum  END) AS intubated,
    MAX(CASE WHEN label = 'LACTATE'          THEN valuenum  END) AS lactate,
    MAX(CASE WHEN label = 'METHEMOGLOBIN'    THEN valuenum  END) AS methemoglobin,
    MAX(CASE WHEN label = 'O2FLOW'           THEN valuenum  END) AS o2flow,
    MAX(CASE WHEN label = 'FIO2'             THEN valuenum  END) AS fio2,
    MAX(CASE WHEN label = 'SO2'              THEN valuenum  END) AS so2,
    MAX(CASE WHEN label = 'PCO2'             THEN valuenum  END) AS pco2,
    MAX(CASE WHEN label = 'PEEP'             THEN valuenum  END) AS peep,
    MAX(CASE WHEN label = 'PH'               THEN valuenum  END) AS ph,
    MAX(CASE WHEN label = 'PO2'              THEN valuenum  END) AS po2,
    MAX(CASE WHEN label = 'POTASSIUM'        THEN valuenum  END) AS potassium,
    MAX(CASE WHEN label = 'REQUIREDO2'       THEN valuenum  END) AS requiredo2,
    MAX(CASE WHEN label = 'SODIUM'           THEN valuenum  END) AS sodium,
    MAX(CASE WHEN label = 'TEMPERATURE'      THEN valuenum  END) AS temperature,
    MAX(CASE WHEN label = 'TIDALVOLUME'      THEN valuenum  END) AS tidalvolume,
    MAX(CASE WHEN label = 'VENTILATIONRATE'  THEN valuenum  END) AS ventilationrate,
    MAX(CASE WHEN label = 'VENTILATOR'       THEN valuenum  END) AS ventilator

FROM pvt
GROUP BY
    pvt.subject_id,
    pvt.hadm_id,
    pvt.icustay_id,
    pvt.charttime

ORDER BY
    pvt.subject_id,
    pvt.hadm_id,
    pvt.icustay_id,
    pvt.charttime;
"""

db.execute(query)

selection_query = f"""
SELECT * from mimiciii.blood_gas_first_day LIMIT 1;
"""
df = db.query_df(selection_query)

print(df)