import pandas as pd

from dotenv import load_dotenv
import os

from mimiciii_db import DB
from mimiciii_db.config import db_url

load_dotenv()

ELIXHAUSER_QUAN_PATH = os.getenv("ELIXHAUSER_QUAN_PATH")

db = DB.from_url(db_url())

db.run_sql_file(ELIXHAUSER_QUAN_PATH)

df = db.query_df("SELECT * FROM mimiciii.elixhauser_quan LIMIT 1;")

print(df)