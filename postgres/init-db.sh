#!/bin/bash
# POSTGRES_MULTIPLE_DATABASES 환경변수에 지정된 DB를 순서대로 생성한다.
# 예: POSTGRES_MULTIPLE_DATABASES=orders,inventory
set -e

create_database() {
    local db=$1
    echo "  Creating database: $db"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $db;
        GRANT ALL PRIVILEGES ON DATABASE $db TO $POSTGRES_USER;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Multiple databases requested: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
        create_database "$db"
    done
    echo "Databases created."
fi
