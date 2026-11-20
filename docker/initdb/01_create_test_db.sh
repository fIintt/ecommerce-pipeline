#!/bin/bash
set -e

if [ -n "${DB_NAME_TEST:-}" ] && [ "${DB_NAME_TEST}" != "${POSTGRES_DB}" ]; then
    psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL
        CREATE DATABASE "${DB_NAME_TEST}";
EOSQL
fi
