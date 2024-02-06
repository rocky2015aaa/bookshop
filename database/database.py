from sqlmodel import SQLModel, Session, create_engine
from exporter import DATABASE_URL, DATABASE_NAME

# SQLModel setup
engine = create_engine(DATABASE_URL+DATABASE_NAME, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        yield session
