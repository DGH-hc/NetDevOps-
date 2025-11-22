#!/bin/bash

FILE=$1

if [ -z "$FILE" ]; then
  echo "Usage: ./db_restore.sh <backup-file.sql>"
  exit 1
fi

psql -U netdevops_user -h db -d netdevops_db < $FILE
