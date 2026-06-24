from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Every model in app/models/ inherits from this. SQLAlchemy collects
    every mapped table's metadata on Base.metadata — that's what Alembic
    reads from later to autogenerate migrations, and what lets all our
    model files "register themselves" just by being imported once.
    """
    pass