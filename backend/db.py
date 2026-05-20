import os
import logging
from sqlalchemy import create_engine, inspect, text, Boolean, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("brainbridge.db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/brainbridge"
)

_is_sqlite = DATABASE_URL.startswith("sqlite")

_engine_kwargs: dict = {
    "pool_pre_ping": True,
}

if _is_sqlite:
    # SQLite: faqat bitta ulanish, thread-safe
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL: connection pool
    _engine_kwargs.update({
        "pool_size":    10,
        "max_overflow": 20,
        "pool_recycle": 1800,   # 30 daqiqada yangilan
        "pool_timeout": 30,
    })

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_engine():
    """Return the SQLAlchemy engine (for health checks etc.)."""
    return engine


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models import Base
    Base.metadata.create_all(bind=engine)
    _ensure_missing_columns()


def _ensure_missing_columns():
    from models import Base

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue

        existing_columns = {col["name"] for col in inspector.get_columns(table.name)}

        for column in table.columns:
            if column.name in existing_columns:
                continue

            column_type = column.type.compile(engine.dialect)
            sql = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type}'

            default_value = _get_column_default(column)
            if default_value is not None:
                sql += f" DEFAULT {default_value}"

            if not column.nullable:
                sql += " NOT NULL"

            with engine.begin() as conn:
                conn.execute(text(sql))
            print(f"Migrated missing column: {table.name}.{column.name}")


def _get_column_default(column):
    if column.server_default is not None and hasattr(column.server_default, "arg"):
        default_arg = column.server_default.arg
        if hasattr(default_arg, "text"):
            return default_arg.text
        default_value = str(default_arg)
        if default_value.startswith("nextval"):
            return None
        return default_value

    if isinstance(column.type, Boolean):
        return "false"
    if isinstance(column.type, Integer):
        return "0"
    if isinstance(column.type, Float):
        return "0.0"
    if isinstance(column.type, DateTime):
        return None if column.nullable else "'1970-01-01 00:00:00'"
    if isinstance(column.type, String) or isinstance(column.type, Text):
        return "''"
    return None
