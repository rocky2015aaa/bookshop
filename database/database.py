from sqlmodel import SQLModel, Session, create_engine
import asyncio
from concurrent.futures import ThreadPoolExecutor

from exporter import DATABASE_URL, DATABASE_NAME

# SQLModel setup
engine = create_engine(DATABASE_URL+DATABASE_NAME, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


executor = ThreadPoolExecutor(max_workers=5)  # Adjust the number of workers as needed

# Function to get session asynchronously
async def get_session() -> Session:
    loop = asyncio.get_event_loop()
    session = await loop.run_in_executor(executor, Session, bind=engine)
    return session