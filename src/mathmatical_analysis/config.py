import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

DATABASE_URL = os.getenv("DATABASE_URL")
ADMISSION_COMORBIDITY_TABLE = os.getenv("ADMISSION_COMORBIDITY_TABLE")
TARGET_PATIENT = os.getenv("TARGET_PATIENT")

# Validate required environment variables
missing_vars = []
if DATABASE_URL is None:
    missing_vars.append("DATABASE_URL")
if ADMISSION_COMORBIDITY_TABLE is None:
    missing_vars.append("ADMISSION_COMORBIDITY_TABLE")
if TARGET_PATIENT is None:
    missing_vars.append("TARGET_PATIENT")

if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}. "
        f"Please set these variables in your .env file or environment."
    )
