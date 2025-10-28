import pandas as pd
from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
DROP TABLE IF EXISTS mimiciii.oasis;

CREATE TABLE mimiciii.oasis AS
WITH surgflag AS (
    SELECT
        ie.icustay_id,
        MAX(
            CASE
                WHEN lower(se.curr_service) LIKE '%surg%' THEN 1
                WHEN se.curr_service = 'ORTHO' THEN 1
                ELSE 0
            END
        ) AS surgical
    FROM mimiciii.icustays ie
    LEFT JOIN mimiciii.services se
      ON ie.hadm_id = se.hadm_id
     AND se.transfertime < (ie.intime + INTERVAL '1 day')
    GROUP BY ie.icustay_id
),

cohort AS (
    SELECT
        ie.subject_id,
        ie.hadm_id,
        ie.icustay_id,
        ie.intime,
        ie.outtime,
        adm.deathtime,

        -- pre-ICU length of stay in MINUTES
        EXTRACT(EPOCH FROM (ie.intime - adm.admittime)) / 60.0 AS preiculos,

        -- age in YEARS at ICU admit
        EXTRACT(YEAR FROM age(ie.intime, pat.dob)) AS age,

        gcs.mingcs,
        vital.heartrate_max,
        vital.heartrate_min,
        vital.meanbp_max,
        vital.meanbp_min,
        vital.resprate_max,
        vital.resprate_min,
        vital.tempc_max,
        vital.tempc_min,
        vent.vent AS mechvent,
        uo.urineoutput,

        CASE
            WHEN adm.admission_type = 'ELECTIVE'
             AND sf.surgical = 1
                THEN 1
            WHEN adm.admission_type IS NULL
             OR sf.surgical IS NULL
                THEN NULL
            ELSE 0
        END AS electivesurgery,

        -- ICU age group buckets
        CASE
            WHEN EXTRACT(YEAR FROM age(ie.intime, pat.dob)) <=  1 THEN 'neonate'
            WHEN EXTRACT(YEAR FROM age(ie.intime, pat.dob)) <= 15 THEN 'middle'
            ELSE 'adult'
        END AS icustay_age_group,

        -- ICU mortality flag
        CASE
            WHEN adm.deathtime BETWEEN ie.intime AND ie.outtime
                THEN 1
            WHEN adm.deathtime <= ie.intime   -- protect against typo death times
                THEN 1
            WHEN adm.dischtime <= ie.outtime
             AND adm.discharge_location = 'DEAD/EXPIRED'
                THEN 1
            ELSE 0
        END AS icustay_expire_flag,

        adm.hospital_expire_flag
    FROM mimiciii.icustays ie
    INNER JOIN mimiciii.admissions adm
      ON ie.hadm_id = adm.hadm_id
    INNER JOIN mimiciii.patients pat
      ON ie.subject_id = pat.subject_id
    LEFT JOIN surgflag sf
      ON ie.icustay_id = sf.icustay_id
    LEFT JOIN mimiciii.gcs_first_day gcs
      ON ie.icustay_id = gcs.icustay_id
    LEFT JOIN mimiciii.vitals_first_day vital
      ON ie.icustay_id = vital.icustay_id
    LEFT JOIN mimiciii.urine_output_first_day uo
      ON ie.icustay_id = uo.icustay_id
    LEFT JOIN mimiciii.ventilation_first_day vent
      ON ie.icustay_id = vent.icustay_id
),

scorecomp AS (
    SELECT
        co.subject_id,
        co.hadm_id,
        co.icustay_id,
        co.icustay_age_group,
        co.icustay_expire_flag,
        co.hospital_expire_flag,

        -- component subscores
        CASE
            WHEN co.preiculos IS NULL        THEN NULL
            WHEN co.preiculos <   10.2       THEN 5
            WHEN co.preiculos <  297         THEN 3
            WHEN co.preiculos < 1440         THEN 0
            WHEN co.preiculos < 18708        THEN 1
            ELSE 2
        END AS preiculos_score,

        CASE
            WHEN co.age IS NULL              THEN NULL
            WHEN co.age < 24                 THEN 0
            WHEN co.age <= 53                THEN 3
            WHEN co.age <= 77                THEN 6
            WHEN co.age <= 89                THEN 9
            WHEN co.age >= 90                THEN 7
            ELSE 0
        END AS age_score,

        CASE
            WHEN co.mingcs IS NULL           THEN NULL
            WHEN co.mingcs <= 7              THEN 10
            WHEN co.mingcs < 14              THEN 4
            WHEN co.mingcs = 14              THEN 3
            ELSE 0
        END AS gcs_score,

        CASE
            WHEN co.heartrate_max IS NULL    THEN NULL
            WHEN co.heartrate_max > 125      THEN 6
            WHEN co.heartrate_min < 33       THEN 4
            WHEN co.heartrate_max BETWEEN 107 AND 125 THEN 3
            WHEN co.heartrate_max BETWEEN  89 AND 106 THEN 1
            ELSE 0
        END AS heartrate_score,

        CASE
            WHEN co.meanbp_min IS NULL       THEN NULL
            WHEN co.meanbp_min < 20.65       THEN 4
            WHEN co.meanbp_min < 51          THEN 3
            WHEN co.meanbp_max > 143.44      THEN 3
            WHEN co.meanbp_min >= 51 AND co.meanbp_min < 61.33 THEN 2
            ELSE 0
        END AS meanbp_score,

        CASE
            WHEN co.resprate_min IS NULL     THEN NULL
            WHEN co.resprate_min < 6         THEN 10
            WHEN co.resprate_max > 44        THEN 9
            WHEN co.resprate_max > 30        THEN 6
            WHEN co.resprate_max > 22        THEN 1
            WHEN co.resprate_min < 13        THEN 1
            ELSE 0
        END AS resprate_score,

        CASE
            WHEN co.tempc_max IS NULL        THEN NULL
            WHEN co.tempc_max > 39.88        THEN 6
            WHEN co.tempc_min >= 33.22 AND co.tempc_min <= 35.93 THEN 4
            WHEN co.tempc_max >= 33.22 AND co.tempc_max <= 35.93 THEN 4
            WHEN co.tempc_min < 33.22        THEN 3
            WHEN co.tempc_min > 35.93 AND co.tempc_min <= 36.39 THEN 2
            WHEN co.tempc_max >= 36.89 AND co.tempc_max <= 39.88 THEN 2
            ELSE 0
        END AS temp_score,

        CASE
            WHEN co.urineoutput IS NULL      THEN NULL
            WHEN co.urineoutput < 671.09     THEN 10
            WHEN co.urineoutput > 6896.80    THEN 8
            WHEN co.urineoutput >= 671.09  AND co.urineoutput <= 1426.99 THEN 5
            WHEN co.urineoutput >= 1427.00 AND co.urineoutput <= 2544.14 THEN 1
            ELSE 0
        END AS urineoutput_score,

        CASE
            WHEN co.mechvent IS NULL         THEN NULL
            WHEN co.mechvent = 1             THEN 9
            ELSE 0
        END AS mechvent_score,

        CASE
            WHEN co.electivesurgery IS NULL  THEN NULL
            WHEN co.electivesurgery = 1      THEN 0
            ELSE 6
        END AS electivesurgery_score,

        -- Also expose raw contributors (nice for debugging / downstream analysis)
        co.preiculos,
        co.age,
        co.mingcs AS gcs,

        CASE
            WHEN co.heartrate_max IS NULL THEN NULL
            WHEN co.heartrate_max > 125 THEN co.heartrate_max
            WHEN co.heartrate_min < 33  THEN co.heartrate_min
            WHEN co.heartrate_max BETWEEN 107 AND 125 THEN co.heartrate_max
            WHEN co.heartrate_max BETWEEN  89 AND 106 THEN co.heartrate_max
            ELSE (co.heartrate_min + co.heartrate_max) / 2.0
        END AS heartrate,

        CASE
            WHEN co.meanbp_min IS NULL THEN NULL
            WHEN co.meanbp_min < 20.65 THEN co.meanbp_min
            WHEN co.meanbp_min < 51    THEN co.meanbp_min
            WHEN co.meanbp_max > 143.44 THEN co.meanbp_max
            WHEN co.meanbp_min >= 51 AND co.meanbp_min < 61.33 THEN co.meanbp_min
            ELSE (co.meanbp_min + co.meanbp_max) / 2.0
        END AS meanbp,

        CASE
            WHEN co.resprate_min IS NULL THEN NULL
            WHEN co.resprate_min < 6    THEN co.resprate_min
            WHEN co.resprate_max > 44   THEN co.resprate_max
            WHEN co.resprate_max > 30   THEN co.resprate_max
            WHEN co.resprate_max > 22   THEN co.resprate_max
            WHEN co.resprate_min < 13   THEN co.resprate_min
            ELSE (co.resprate_min + co.resprate_max) / 2.0
        END AS resprate,

        CASE
            WHEN co.tempc_max IS NULL THEN NULL
            WHEN co.tempc_max > 39.88 THEN co.tempc_max
            WHEN co.tempc_min >= 33.22 AND co.tempc_min <= 35.93 THEN co.tempc_min
            WHEN co.tempc_max >= 33.22 AND co.tempc_max <= 35.93 THEN co.tempc_max
            WHEN co.tempc_min < 33.22 THEN co.tempc_min
            WHEN co.tempc_min > 35.93 AND co.tempc_min <= 36.39 THEN co.tempc_min
            WHEN co.tempc_max >= 36.89 AND co.tempc_max <= 39.88 THEN co.tempc_max
            ELSE (co.tempc_min + co.tempc_max) / 2.0
        END AS temp,

        co.urineoutput,
        co.mechvent,
        co.electivesurgery
    FROM cohort co
),

score AS (
    SELECT
        s.*,
        COALESCE(age_score,0)
      + COALESCE(preiculos_score,0)
      + COALESCE(gcs_score,0)
      + COALESCE(heartrate_score,0)
      + COALESCE(meanbp_score,0)
      + COALESCE(resprate_score,0)
      + COALESCE(temp_score,0)
      + COALESCE(urineoutput_score,0)
      + COALESCE(mechvent_score,0)
      + COALESCE(electivesurgery_score,0)
      AS oasis
    FROM scorecomp s
)

SELECT
    subject_id,
    hadm_id,
    icustay_id,
    icustay_age_group,
    hospital_expire_flag,
    icustay_expire_flag,
    oasis,

    -- mortality probability model from the paper
    1 / (1 + exp(-(-6.1746 + 0.1275 * oasis))) AS oasis_prob,

    age,             age_score,
    preiculos,       preiculos_score,
    gcs,             gcs_score,
    heartrate,       heartrate_score,
    meanbp,          meanbp_score,
    resprate,        resprate_score,
    temp,            temp_score,
    urineoutput,     urineoutput_score,
    mechvent,        mechvent_score,
    electivesurgery, electivesurgery_score

FROM score
ORDER BY icustay_id;
"""

db.execute(query)

selection_query = f"""
SELECT * from mimiciii.oasis LIMIT 1;
"""
df = db.query_df(selection_query)

print(df)