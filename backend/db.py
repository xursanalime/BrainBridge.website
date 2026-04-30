import os
from sqlalchemy import create_engine, inspect, text, Boolean, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/brainbridge"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    if isinstance(column.type, DateTime):
        return "CURRENT_TIMESTAMP"
    if isinstance(column.type, String) or isinstance(column.type, Text):
        return "''"
    return None
