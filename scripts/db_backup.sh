#!/bin/bash

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/app/backups"
mkdir -p $BACKUP_DIR

pg_dump -U netdevops_user -h db -d netdevops_db > $BACKUP_DIR/backup_$TIMESTAMP.sql

echo "Backup created: backup_$TIMESTAMP.sql"
