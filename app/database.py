import os
from pathlib import Path
from peewee import DatabaseProxy, Model, PostgresqlDatabase, SqliteDatabase

db = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = db


def init_db(app):
    """
    Initialize the database for the application.

    Supports dual-mode:
    1. SQLite (Default for zero-setup, local-first offline execution).
    2. PostgreSQL (Set DB_TYPE=postgres in .env for production/team environments).
    """
    db_type = os.environ.get("DB_TYPE", "sqlite").lower()

    if db_type == "postgres":
        try:
            database = PostgresqlDatabase(
                os.environ.get("DATABASE_NAME", "hackathon_db"),
                host=os.environ.get("DATABASE_HOST", "localhost"),
                port=int(os.environ.get("DATABASE_PORT", 5432)),
                user=os.environ.get("DATABASE_USER", "postgres"),
                password=os.environ.get("DATABASE_PASSWORD", "postgres"),
            )
            db.initialize(database)
            app.logger.info("Connected to PostgreSQL database.")
        except Exception as e:
            app.logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite.")
            db_type = "sqlite"

    if db_type == "sqlite":
        # Ensure data folder exists
        db_path = Path(os.environ.get("SQLITE_DB_PATH", "data/evaluator.db"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        database = SqliteDatabase(
            str(db_path),
            pragmas={
                "journal_mode": "wal",
                "cache_size": -1024 * 64,
                "foreign_keys": 1,
                "ignore_check_constraints": 0,
            },
        )
        db.initialize(database)
        app.logger.info(f"Initialized local SQLite database at {db_path}")

    @app.before_request
    def _db_connect():
        if db.is_closed():
            db.connect(reuse_if_open=True)

    @app.teardown_appcontext
    def _db_close(exc):
        if not db.is_closed():
            db.close()

    # Create tables automatically
    with app.app_context():
        try:
            if db.is_closed():
                db.connect(reuse_if_open=True)
            from app.models.evaluation import AgentModel, TestRunModel, ScenarioResultModel, ScorecardModel
            db.create_tables([AgentModel, TestRunModel, ScenarioResultModel, ScorecardModel], safe=True)
        except Exception as e:
            app.logger.warning(f"Could not auto-create DB tables: {e}")
        finally:
            if not db.is_closed():
                db.close()
