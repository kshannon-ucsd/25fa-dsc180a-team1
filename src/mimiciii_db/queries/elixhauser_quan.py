#script to generate the elixhauser_quan table in psql

import pandas as pd

from mimiciii_db import DB
from mimiciii_db.config import db_url

db = DB.from_url(db_url())

#find the filepath for the elixhauser_quan file
#for me, it was here - /Users/varunpabreja/Desktop/dsc180_capstone/mimic-code/mimic-iii/concepts_postgres/comorbidity/elixhauser_score_quan.sql

fp = "/Users/varunpabreja/Desktop/dsc180_capstone/mimic-code/mimic-iii/concepts_postgres/comorbidity/elixhauser_score_quan.sql"

query = f"""
\i {fp}
"""

df = db.query_df(query)

pd.display(df)

#this should be enough to create the elixhauser_quan comorbidity score
#prefix the file however you wish, so that the original db remains imutable ; for all the files i create, i prefix the table/view/mv with "varun_" ; 
#so, in addition to the command above, I would recommend running the command "ALTER TABLE {old_name} RENAME TO {varun_old_name};"