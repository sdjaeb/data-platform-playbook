#!/bin/bash
set -e

# This script will be executed by the official postgres container on startup.

# Read user and password for Superset from the secrets mounted into the postgres container.
SUPERSET_USER=$(cat /run/secrets/superset_db_user)
SUPERSET_PASSWORD=$(cat /run/secrets/superset_db_pass)

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create the Superset user if it doesn't exist
    DO \$\$
    BEGIN
      IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$SUPERSET_USER') THEN
        CREATE ROLE $SUPERSET_USER WITH LOGIN PASSWORD '$SUPERSET_PASSWORD';
      END IF;
    END
    \$\$;

    -- Create the Superset database if it doesn't exist and grant privileges
    SELECT 'CREATE DATABASE superset' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'superset')\gexec
    GRANT ALL PRIVILEGES ON DATABASE superset TO $SUPERSET_USER;
EOSQL