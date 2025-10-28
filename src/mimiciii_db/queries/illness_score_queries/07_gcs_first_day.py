import pandas as pd
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = """
DROP TABLE IF EXISTS mimiciii.gcs_first_day;

CREATE TABLE mimiciii.gcs_first_day AS
WITH base AS (
    SELECT
        pvt.icustay_id,
        pvt.charttime,
        MAX(CASE WHEN pvt.itemid = 454 THEN pvt.valuenum END) AS gcsmotor,
        MAX(CASE WHEN pvt.itemid = 723 THEN pvt.valuenum END) AS gcsverbal,
        MAX(CASE WHEN pvt.itemid = 184 THEN pvt.valuenum END) AS gcseyes,
        CASE
            WHEN MAX(CASE WHEN pvt.itemid = 723 THEN pvt.valuenum END) = 0
            THEN 1 ELSE 0
        END AS endotrachflag,
        ROW_NUMBER() OVER (
            PARTITION BY pvt.icustay_id
            ORDER BY pvt.charttime ASC
        ) AS rn
    FROM (
        SELECT
            l.icustay_id,
            CASE
                WHEN l.itemid IN (723,223900)   THEN 723
                WHEN l.itemid IN (454,223901)   THEN 454
                WHEN l.itemid IN (184,220739)   THEN 184
                ELSE l.itemid
            END AS itemid,
            CASE
                WHEN l.itemid = 723
                     AND l.value = '1.0 ET/Trach' THEN 0
                WHEN l.itemid = 223900
                     AND l.value = 'No Response-ETT' THEN 0
                ELSE l.valuenum
            END AS valuenum,
            l.charttime
        FROM mimiciii.chartevents l
        INNER JOIN mimiciii.icustays b
            ON l.icustay_id = b.icustay_id
        WHERE l.itemid IN (
            184,454,723,
            223900,223901,220739
        )
        AND l.charttime BETWEEN b.intime AND (b.intime + INTERVAL '1 day')
        AND (l.error IS NULL OR l.error = 0)
    ) pvt
    GROUP BY pvt.icustay_id, pvt.charttime
),
gcs AS (
    SELECT
        b.*,
        b2.gcsverbal  AS gcsverbalprev,
        b2.gcsmotor   AS gcsmotorprev,
        b2.gcseyes    AS gcseyesprev,
        CASE
            WHEN b.gcsverbal = 0 THEN 15
            WHEN b.gcsverbal IS NULL AND b2.gcsverbal = 0 THEN 15
            WHEN b2.gcsverbal = 0 THEN
                COALESCE(b.gcsmotor,6)
              + COALESCE(b.gcsverbal,5)
              + COALESCE(b.gcseyes,4)
            ELSE
                COALESCE(b.gcsmotor,  COALESCE(b2.gcsmotor,6))
              + COALESCE(b.gcsverbal, COALESCE(b2.gcsverbal,5))
              + COALESCE(b.gcseyes,   COALESCE(b2.gcseyes,4))
        END AS gcs
    FROM base b
    LEFT JOIN base b2
        ON  b.icustay_id = b2.icustay_id
        AND b.rn = b2.rn + 1
        AND b2.charttime > (b.charttime - INTERVAL '6 hour')
),
gcs_final AS (
    SELECT
        gcs.*,
        ROW_NUMBER() OVER (
            PARTITION BY gcs.icustay_id
            ORDER BY gcs.gcs
        ) AS ismingcs
    FROM gcs
)
SELECT
    ie.subject_id,
    ie.hadm_id,
    ie.icustay_id,
    gf.gcs AS mingcs,
    COALESCE(gf.gcsmotor,  gf.gcsmotorprev)  AS gcsmotor,
    COALESCE(gf.gcsverbal, gf.gcsverbalprev) AS gcsverbal,
    COALESCE(gf.gcseyes,   gf.gcseyesprev)   AS gcseyes,
    gf.endotrachflag      AS endotrachflag
FROM mimiciii.icustays ie
LEFT JOIN gcs_final gf
    ON ie.icustay_id = gf.icustay_id
   AND gf.ismingcs = 1
ORDER BY ie.icustay_id;
"""

db.execute(query)

df = db.query_df("SELECT * FROM mimiciii.gcs_first_day LIMIT 5;")
print(df)
