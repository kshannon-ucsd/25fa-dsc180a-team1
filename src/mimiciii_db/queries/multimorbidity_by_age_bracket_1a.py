#script to create the table with the patients involved in the study

import pandas as pd

from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
CREATE MATERIALIZED VIEW mimiciii.multimorbidity_by_age_bracket_1a AS
 WITH base_table AS (
         SELECT (round(v.age))::integer AS age_rounded,
                CASE
                    WHEN ((round(v.age) >= (16)::numeric) AND (round(v.age) <= (24)::numeric)) THEN '16-24'::text
                    WHEN ((round(v.age) >= (25)::numeric) AND (round(v.age) <= (44)::numeric)) THEN '25-44'::text
                    WHEN ((round(v.age) >= (45)::numeric) AND (round(v.age) <= (64)::numeric)) THEN '45-64'::text
                    WHEN ((round(v.age) >= (65)::numeric) AND (round(v.age) <= (84)::numeric)) THEN '65-84'::text
                    ELSE '≥85'::text
                END AS age_bracket,
            ((v.morbidity_count >= 2))::integer AS is_multimorbid
           FROM mimiciii.filtered_patients_with_morbidity_count v
          WHERE (v.age IS NOT NULL)
        ), agg AS (
         SELECT base_table.age_bracket,
            (count(*))::integer AS n_in_bracket,
            (sum(base_table.is_multimorbid))::integer AS n_multimorbid,
            ((sum(base_table.is_multimorbid))::numeric / (NULLIF(count(*), 0))::numeric) AS p_hat
           FROM base_table
          GROUP BY base_table.age_bracket
        )
 SELECT age_bracket,
    n_in_bracket,
    n_multimorbid,
    (100.0 * p_hat) AS pct_multimorbid,
    (100.0 * sqrt(((p_hat * (1.0 - p_hat)) / (NULLIF(n_in_bracket, 0))::numeric))) AS se_pct,
    (100.0 * sqrt((p_hat * (1.0 - p_hat)))) AS sd_pct,
        CASE age_bracket
            WHEN '16-24'::text THEN 1
            WHEN '25-44'::text THEN 2
            WHEN '45-64'::text THEN 3
            WHEN '65-84'::text THEN 4
            WHEN '≥85'::text THEN 5
            ELSE NULL::integer
        END AS sort_key
   FROM agg
  ORDER BY
        CASE age_bracket
            WHEN '16-24'::text THEN 1
            WHEN '25-44'::text THEN 2
            WHEN '45-64'::text THEN 3
            WHEN '65-84'::text THEN 4
            WHEN '≥85'::text THEN 5
            ELSE NULL::integer
        END
"""

db.execute(query)

selection_query = f"""
SELECT * from multimorbidity_by_age_bracket_1a LIMIT 1;
"""
df = db.query_df(selection_query)

print(df)

#prefix the file however you wish, so that the original db remains imutable ; for all the files i create, i prefix the table/view/mv with "varun_" ; 
#so, in addition to the command above, I would recommend running the command "ALTER MATERIALIZED VIEW {old_mv} RENAME TO {varun_old_mv}"