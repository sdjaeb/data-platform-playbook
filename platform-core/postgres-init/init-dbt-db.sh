#!/bin/bash
set -e

# This script will be executed by the official postgres container on startup.

# Read user and password for dbt from the secrets mounted into the postgres container.
DBT_USER=$(cat /run/secrets/dbt_db_user)
DBT_PASSWORD=$(cat /run/secrets/dbt_db_pass)

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create the dbt user if it doesn't exist
    DO \$\$
    BEGIN
      IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DBT_USER') THEN
        CREATE ROLE $DBT_USER WITH LOGIN PASSWORD '$DBT_PASSWORD';
      END IF;
    END
    \$\$;

    -- Create the dbt database if it doesn't exist and grant privileges
    SELECT 'CREATE DATABASE dbt_metadata' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dbt_metadata')\gexec
    GRANT ALL PRIVILEGES ON DATABASE dbt_metadata TO $DBT_USER;
EOSQL