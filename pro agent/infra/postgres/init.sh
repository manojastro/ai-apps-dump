#!/bin/sh
# Creates the application database (owned by a migration role, used by a non-owner
# runtime role so row-level security applies) and the isolated supplier fixture database.
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<SQL
CREATE ROLE procnav_owner LOGIN PASSWORD '${PROCNAV_OWNER_PASSWORD}' BYPASSRLS;
CREATE ROLE procnav_app LOGIN PASSWORD '${PROCNAV_APP_PASSWORD}' NOBYPASSRLS;
CREATE ROLE suppliers LOGIN PASSWORD '${SUPPLIERS_DB_PASSWORD}';
CREATE DATABASE procnav OWNER procnav_owner;
CREATE DATABASE suppliers OWNER suppliers;
REVOKE ALL ON DATABASE suppliers FROM PUBLIC;
REVOKE ALL ON DATABASE procnav FROM PUBLIC;
GRANT CONNECT ON DATABASE procnav TO procnav_app;
SQL
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname procnav <<SQL
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO procnav_app;
ALTER DEFAULT PRIVILEGES FOR ROLE procnav_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO procnav_app;
ALTER DEFAULT PRIVILEGES FOR ROLE procnav_owner IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO procnav_app;
SQL
