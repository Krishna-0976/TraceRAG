import json
from typing import Generator
from sqlalchemy import create_engine, TypeDecorator, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import event, text
from app.core.config import settings

# Engine configuration
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class VectorType(TypeDecorator):
    """
    Cross-dialect Vector column:
    - On PostgreSQL: utilizes native pgvector Vector(dim)
    - On SQLite/Others: utilizes JSON serialized float arrays with transparent conversion
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 1536, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dim))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        # SQLite / other: serialize to JSON string
        if isinstance(value, (list, tuple)):
            return json.dumps(list(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            if hasattr(value, "tolist"):
                return value.tolist()
            return list(value)
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return []
        return list(value)


def init_db():
    """Ensure database tables and extensions are created."""
    if engine.url.drivername.startswith("postgresql"):
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

