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
until pg_isready -p 5432 -U "$POSTGRES_USER"; do
  echo "Postgres init script: Waiting for PostgreSQL to be ready..."
  sleep 1
done

echo "Postgres init script: Initializing PostgreSQL users and databases..."

# Note: Airflow's default setup often expects 'airflow' user/db.
# Create Airflow database if it does not exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" \
  --tuples-only --no-align \
  -c "SELECT 1 FROM pg_database WHERE datname = 'airflow';" | grep -q 1 || \
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" \
    -c "CREATE DATABASE airflow;"

# Create Airflow user and grant privileges
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-'EOSQL'
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'airflow') THEN
      CREATE USER airflow WITH PASSWORD 'airflow';
   END IF;
END
$$;
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
EOSQL

# Create Superset database if it does not exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" \
  --tuples-only --no-align \
  -c "SELECT 1 FROM pg_database WHERE datname = 'superset';" | grep -q 1 || \
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" \
    -c "CREATE DATABASE superset;"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<EOSQL
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$SUPERSET_DB_USER') THEN
      CREATE USER "$SUPERSET_DB_USER" WITH PASSWORD '$SUPERSET_DB_PASS';
   END IF;
END
\$\$;
GRANT ALL PRIVILEGES ON DATABASE superset TO "$SUPERSET_DB_USER";
EOSQL

# Create dbt database if it does not exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" \
  --tuples-only --no-align \
  -c "SELECT 1 FROM pg_database WHERE datname = 'dbt_metadata';" | grep -q 1 || \
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" \
    -c "CREATE DATABASE dbt_metadata;"

# Create dbt user and grant privileges
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<EOSQL
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DBT_DB_USER') THEN
      CREATE USER "$DBT_DB_USER" WITH PASSWORD '$DBT_DB_PASS';
   END IF;
END
\$\$;
GRANT ALL PRIVILEGES ON DATABASE dbt_metadata TO "$DBT_DB_USER";
EOSQL

echo "Postgres init script: PostgreSQL initialization complete."
