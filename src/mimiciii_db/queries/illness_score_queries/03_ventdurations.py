import pandas as pd
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = """
DROP TABLE IF EXISTS mimiciii.ventilation_durations;

CREATE TABLE mimiciii.ventilation_durations AS
WITH vd0 AS (
    SELECT
        icustay_id,
        -- previous charttime of a mech vent event for this icustay_id
        CASE
            WHEN MechVent = 1 THEN
                LAG(charttime, 1) OVER (
                    PARTITION BY icustay_id, MechVent
                    ORDER BY charttime
                )
            ELSE NULL
        END AS charttime_lag,
        charttime,
        MechVent,
        OxygenTherapy,
        Extubated,
        SelfExtubated
    FROM mimiciii.ventilation_classification
),

vd1 AS (
    SELECT
        icustay_id,
        charttime_lag,
        charttime,
        MechVent,
        OxygenTherapy,
        Extubated,
        SelfExtubated,

        -- hours since last vent event, only for MechVent rows
        CASE
            WHEN MechVent = 1 AND charttime_lag IS NOT NULL THEN
                EXTRACT(EPOCH FROM (charttime - charttime_lag)) / 3600.0
            ELSE NULL
        END AS ventduration,

        LAG(Extubated, 1) OVER (
            PARTITION BY icustay_id,
                CASE WHEN MechVent = 1 OR Extubated = 1 THEN 1 ELSE 0 END
            ORDER BY charttime
        ) AS ExtubatedLag,

        -- mark whether this row starts a "new" vent run
        CASE
            -- if previous row was an extubation, new run starts now
            WHEN
                LAG(Extubated, 1) OVER (
                    PARTITION BY icustay_id,
                        CASE WHEN MechVent = 1 OR Extubated = 1 THEN 1 ELSE 0 END
                    ORDER BY charttime
                ) = 1
            THEN 1

            -- if not currently vented but got OxygenTherapy, count as new run
            WHEN MechVent = 0 AND OxygenTherapy = 1
            THEN 1

            -- if >8 hours gap since last vent event, that's a new run
            WHEN charttime_lag IS NOT NULL
                 AND charttime > charttime_lag + INTERVAL '8 hours'
            THEN 1

            ELSE 0
        END AS newvent
    FROM vd0
),

vd2 AS (
    SELECT
        vd1.*,
        -- cumulative "run number" per icustay_id
        CASE
            WHEN MechVent = 1 OR Extubated = 1 THEN
                SUM(newvent) OVER (
                    PARTITION BY icustay_id
                    ORDER BY charttime
                )
            ELSE NULL
        END AS ventnum
    FROM vd1
)

SELECT
    icustay_id,

    -- re-number runs sequentially within each icustay_id
    ROW_NUMBER() OVER (
        PARTITION BY icustay_id
        ORDER BY ventnum
    ) AS ventnum,

    MIN(charttime) AS starttime,
    MAX(charttime) AS endtime,

    -- duration in hours for this continuous run
    EXTRACT(EPOCH FROM (MAX(charttime) - MIN(charttime))) / 3600.0
        AS duration_hours

FROM vd2
GROUP BY icustay_id, ventnum
HAVING
    MIN(charttime) <> MAX(charttime)
    AND MAX(MechVent) = 1
ORDER BY icustay_id, ventnum;
"""

db.execute(query)

# sanity check
selection_query = """
SELECT * FROM mimiciii.ventilation_durations LIMIT 5;
"""
df = db.query_df(selection_query)
print(df)
