import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()


class DBConnection:
    """Create PostgreSQL connections and write crawler outputs to staging tables."""

    def __init__(self):
        """Initialize the SQLAlchemy engine from environment variables."""
        self.engine = self._create_db_connection()

    def _create_db_connection(self):
        """Create a SQLAlchemy engine for the job database."""
        db_url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_JOB')}"
        try:
            return create_engine(db_url)
        except SQLAlchemyError as e:
            print(f"Database connection error: {e}")
            return None

    def insert_itviec_jobs(self, jobs):
        """Upsert ITViec job records into the staging table."""

        engine = self.engine
        if not jobs:
            print("No IT Viec jobs to insert")

        # Use ON CONFLICT to keep one staging record per source URL.
        query = text("""
            INSERT INTO staging.itviec_data_job (
                title, company, logo_url, url, job_category, working_location,
                work_model, tags, descriptions, requirements_and_experiences
            )
            VALUES (
                :title, :company, :logo, :url, :job_cat, :location, :mode,
                :tags, :descriptions, :requirements
            )
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                company = EXCLUDED.company,
                logo_url = EXCLUDED.logo_url,
                job_category = EXCLUDED.job_category,
                working_location = EXCLUDED.working_location,
                work_model = EXCLUDED.work_model,
                tags = EXCLUDED.tags,
                descriptions = EXCLUDED.descriptions,
                requirements_and_experiences = EXCLUDED.requirements_and_experiences
            """)

        try:
            with engine.connect() as conn:
                transactions = conn.begin()
                try:
                    conn.execute(query, jobs)
                    transactions.commit()
                except SQLAlchemyError as e:
                    transactions.rollback()
                    print(f"Error inserting IT Viec jobs: {e}")
        except SQLAlchemyError as e:
            print(f"Database error: {e}")

    def insert_topcv_jobs(self, jobs):
        """Upsert TopCV job records into the staging table."""

        engine = self.engine
        if not jobs:
            print("No TopCV jobs to insert")

        query = text("""
            INSERT INTO staging.topcv_data_job (
                title, company, logo_url, url, job_category, working_location,
                salary, descriptions, requirements, experiences,
                level_of_education, work_model
            )
            VALUES (
                :title, :company, :logo, :url, :job_cat, :location, :salary,
                :descriptions, :requirements, :experience, :education,
                :type_of_work
            )
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                company = EXCLUDED.company,
                logo_url = EXCLUDED.logo_url,
                job_category = EXCLUDED.job_category,
                working_location = EXCLUDED.working_location,
                salary = EXCLUDED.salary,
                descriptions = EXCLUDED.descriptions,
                requirements = EXCLUDED.requirements,
                experiences = EXCLUDED.experiences,
                level_of_education = EXCLUDED.level_of_education,
                work_model = EXCLUDED.work_model
            """)

        try:
            with engine.connect() as conn:
                transactions = conn.begin()
                try:
                    conn.execute(query, jobs)
                    transactions.commit()
                except SQLAlchemyError as e:
                    transactions.rollback()
                    print(f"Error inserting TopCV jobs: {e}")
        except SQLAlchemyError as e:
            print(f"Database error: {e}")

    def insert_company_logos(self, logos):
        """Insert new company logo URLs into the staging logo table."""

        engine = self.engine
        if not logos:
            print("No company logos to insert")

        query = text("""
            INSERT INTO staging.company_logos (logo_id, logo_url)
                    VALUES (MD5(:logo_url), :logo_url)
            ON CONFLICT (logo_id) DO NOTHING
            """)

        try:
            with engine.connect() as conn:
                transactions = conn.begin()
                try:
                    conn.execute(query, logos)
                    transactions.commit()
                except SQLAlchemyError as e:
                    transactions.rollback()
                    print(f"Error inserting company logos: {e}")
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
        return None

    def update_company_logos(self, logos: list[dict]):
        """Update downloaded company logo payloads in the staging logo table."""

        if not logos:
            print("No company logos to update")
            return

        engine = self.engine
        query = text("""
            UPDATE staging.company_logos
            SET logo_path = :logo_path,
                is_downloaded = TRUE,
                logo_id = MD5(:logo_url),
                updated_at = CURRENT_TIMESTAMP
            WHERE logo_url = :logo_url
            """)
        try:
            with engine.connect() as conn:
                transactions = conn.begin()
                try:
                    conn.execute(query, logos)
                    transactions.commit()
                except SQLAlchemyError as e:
                    transactions.rollback()
                    print(f"Error updating company logos: {e}")
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
