\set ON_ERROR_STOP on

\getenv db_job DB_JOB
\getenv db_trino DB_TRINO

SELECT format('CREATE DATABASE %I', :'db_job')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'db_job')\gexec

SELECT format('CREATE DATABASE %I', :'db_trino')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'db_trino')\gexec
