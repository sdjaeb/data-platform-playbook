#!/bin/bash
set -e

# This script is executed by the PostgreSQL Docker image's entrypoint
# during the initial setup of the database.
# It creates the necessary users and databases for Airflow, Superset, and dbt.

# Read secrets for the PostgreSQL superuser (initial user created by Docker image)
# These secrets are mounted into the container at /run/secrets/
POSTGRES_USER=$(cat /run/secrets/postgres_user)
POSTGRES_PASSWORD=$(cat /run/secrets/postgres_pass)

# Read secrets for Superset and dbt database users
SUPERSET_DB_USER=$(cat /run/secrets/superset_db_user)
SUPERSET_DB_PASS=$(cat /run/secrets/superset_db_pass)
DBT_DB_USER=$(cat /run/secrets/dbt_db_user)
DBT_DB_PASS=$(cat /run/secrets/dbt_db_pass)

# Wait for PostgreSQL to be ready to accept connections
# (The Docker entrypoint does some waiting, but this ensures it's fully up for psql commands)
until pg_isready -h localhost -p 5432 -U "$POSTGRES_USER"; do
  echo "Postgres init script: Waiting for PostgreSQL to be ready..."
  sleep 1
done

echo "Postgres init script: Initializing PostgreSQL users and databases..."

# Create Airflow user and database (matching hardcoded values in Airflow config)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE airflow;
    CREATE USER airflow WITH PASSWORD 'airflow';
    GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
EOSQL

# Create Superset user and database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE superset;
    CREATE USER "$SUPERSET_DB_USER" WITH PASSWORD '$SUPERSET_DB_PASS';
    GRANT ALL PRIVILEGES ON DATABASE superset TO "$SUPERSET_DB_USER";
EOSQL

# Create dbt user and database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE dbt_metadata;
    CREATE USER "$DBT_DB_USER" WITH PASSWORD '$DBT_DB_PASS';
    GRANT ALL PRIVILEGES ON DATABASE dbt_metadata TO "$DBT_DB_USER";
EOSQL

echo "Postgres init script: PostgreSQL initialization complete."
