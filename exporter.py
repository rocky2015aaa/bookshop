from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")
FIXTURE_PATH_FOR_UNIT_TEST = os.getenv("FIXTURE_PATH_FOR_UNIT_TEST")
