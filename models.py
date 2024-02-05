from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field, UniqueConstraint, Column, Integer
from sqlalchemy import ForeignKey

from errors import ValidityError


# Define database models using SQLModel
class Author(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("name", "birth_date",
                                       name="unique_name_birth_date"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    birth_date: str

    def check_request_validity(self):
        """
        Checks the validity of the author"s request.
        Raises:
            ValueError: If the birth date is not in the format
            "YYYY-MM-DD" or if it"s before January 1, 1900.
            TypeError: If the birth date is not provided as a string.
        """
        try:
            # Check if the birth date is provided as a string
            if not isinstance(self.birth_date, str):
                raise TypeError("Birth date must be provided as a string")
            # Parse the birth date string to a datetime object
            birth_date = datetime.strptime(self.birth_date, "%Y-%m-%d")
            # Check if the birth date is before January 1, 1900
            if birth_date < datetime(1900, 1, 1):
                raise ValueError("Birth date must be on or after January 1, 1900")
        except ValueError as ve:
            raise ValidityError(f"Invalid date: {str(ve)}. Date must be in YYYY-MM-DD format and on or after January 1, 1900")
        except TypeError as te:
            raise ValidityError(f"Invalid input type: {str(te)}. Birth date must be provided as a string")
        except Exception as e:
            raise ValidityError(f"Error occurred during request validation: {str(e)}")


class Book(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("title", "publish_year",
                                       name="unique_title_publish_year"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    publish_year: int
    author: int = Field(sa_column=Column("author_id", Integer, ForeignKey("author.id")))
    barcode: str = Field(unique=True)

    def check_request_validity(self):
        if self.publish_year <= 1900:
            raise ValidityError("publish_year must be greater than 1900")


class Inventory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id")
    quantity: int
    date: str

    def check_request_validity(self):
        if self.quantity <= 0:
            raise ValidityError("quantity must be greater than 0")
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValidityError("Invalid date format. Date must be in YYYY-MM-DD format")


class InventoryRequest(SQLModel):
    barcode: str
    quantity: int

    def check_request_validity(self):
        if self.quantity <= 0:
            raise ValidityError("quantity must be greater than 0")


class InventoryHistoryRequest(SQLModel):
    start: str
    end: str
    book: Optional[str]

    def check_request_validity(self):
        try:
            start_date = datetime.strptime(self.start, "%Y-%m-%d")
            end_date = datetime.strptime(self.end, "%Y-%m-%d")
            if end_date < start_date:
                raise ValidityError("end must be later than start")
        except ValueError:
            raise ValidityError("Invalid date format. Date must be in YYYY-MM-DD format")
