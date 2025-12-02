import pandas as pd

from dotenv import load_dotenv
import os

from mimiciii_db import DB
from mimiciii_db.config import db_url

load_dotenv()

ANGUS_PATH = os.getenv("ANGUS_PATH")

db = DB.from_url(db_url())

db.run_sql_file(ANGUS_PATH)

df = db.query_df("SELECT * FROM mimiciii.angus LIMIT 1;")

print(df)