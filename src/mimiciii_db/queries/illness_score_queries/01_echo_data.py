#script to create the table with the patients involved in the study

import pandas as pd

from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

query = f"""
DROP TABLE IF EXISTS mimiciii.echo_data;

CREATE TABLE mimiciii.echo_data AS
SELECT
    ne.row_id,
    ne.subject_id,
    ne.hadm_id,
    ne.chartdate,

    -- Build charttime:
    -- take the date (YYYY-MM-DD) from chartdate
    -- plus the time like HH:MI from the note text ("Date/Time: ... at 14:32")
    -- and turn it into a real timestamp
    to_timestamp(
        to_char(ne.chartdate, 'YYYY-MM-DD') || ' ' ||
        substring(ne.text FROM 'Date/Time: .*? at ([0-9]+:[0-9]{2})'),
        'YYYY-MM-DD HH24:MI'
    ) AS charttime,

    -- Indication line
    substring(ne.text FROM 'Indication: (.*?)(\r|\n)') AS indication,

    -- Numeric fields
    CAST(substring(ne.text FROM 'Height: \\x28in\\x29 ([0-9]+)') AS numeric)                      AS height,
    CAST(substring(ne.text FROM 'Weight \\x28lb\\x29: ([0-9]+)(\r|\n)') AS numeric)               AS weight,
    CAST(substring(ne.text FROM 'BSA \\x28m2\\x29: ([0-9\\.]+) m2') AS numeric)                   AS bsa,

    -- Blood pressure info
    substring(ne.text FROM 'BP \\x28mm Hg\\x29: (.+)(\r|\n)')                                     AS bp,
    CAST(substring(ne.text FROM 'BP \\x28mm Hg\\x29: ([0-9]+)\/[0-9]+') AS numeric)               AS bpsys,
    CAST(substring(ne.text FROM 'BP \\x28mm Hg\\x29: [0-9]+\/([0-9]+)') AS numeric)               AS bpdias,

    -- Heart rate
    CAST(substring(ne.text FROM 'HR \\x28bpm\\x29: ([0-9]+)') AS numeric)                         AS hr,

    -- Other structured strings
    substring(ne.text FROM 'Status: (.*?)(\r|\n)')               AS status,
    substring(ne.text FROM 'Test: (.*?)(\r|\n)')                 AS test,
    substring(ne.text FROM 'Doppler: (.*?)(\r|\n)')              AS doppler,
    substring(ne.text FROM 'Contrast: (.*?)(\r|\n)')             AS contrast,
    substring(ne.text FROM 'Technical Quality: (.*?)(\r|\n)')    AS technicalquality

FROM mimiciii.noteevents ne
WHERE ne.category = 'Echo';
"""

db.execute(query)

selection_query = f"""
SELECT * from mimiciii.echo_data LIMIT 1;
"""
df = db.query_df(selection_query)

print(df)