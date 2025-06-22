#!/bin/bash

# Configuration
DB_HOST="localhost"
DB_PORT="35432"
DB_NAME="mimosatek_db"
DB_USER="mimosatek_user"
DB_PASSWORD="mimosatek_password"
MINIO_ENDPOINT="http://localhost:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin123"
BUCKET_NAME="database-backups"

# Create timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="mimosatek_db_backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="mimosatek_db_backup_${TIMESTAMP}.tar.gz"

echo "Starting database backup at $(date)"

# Create backup directory if not exists
mkdir -p /tmp/backups

# Export password for pg_dump
export PGPASSWORD=$DB_PASSWORD

# Create database dump
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > /tmp/backups/$BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "Database dump created successfully"
    
    # Compress the backup
    cd /tmp/backups
    tar -czf $COMPRESSED_FILE $BACKUP_FILE
    
    if [ $? -eq 0 ]; then
        echo "Backup compressed successfully"
        
        # Install mc (MinIO client) if not exists
        if ! command -v mc &> /dev/null; then
            wget https://dl.min.io/client/mc/release/linux-amd64/mc
            chmod +x mc
            sudo mv mc /usr/local/bin/
        fi
        
        # Configure MinIO client
        mc alias set myminio $MINIO_ENDPOINT $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
        
        # Create bucket if not exists
        mc mb myminio/$BUCKET_NAME --ignore-existing
        
        # Upload compressed backup to MinIO
        mc cp $COMPRESSED_FILE myminio/$BUCKET_NAME/
        
        if [ $? -eq 0 ]; then
            echo "Backup uploaded to MinIO successfully"
            
            # Clean up local files
            rm -f $BACKUP_FILE $COMPRESSED_FILE
            echo "Local backup files cleaned up"
            
            # Keep only last 30 backups in MinIO
            mc ls myminio/$BUCKET_NAME/ | head -n -30 | awk '{print $5}' | xargs -I {} mc rm myminio/$BUCKET_NAME/{}
            
        else
            echo "Failed to upload backup to MinIO"
        fi
    else
        echo "Failed to compress backup"
    fi
else
    echo "Failed to create database dump"
fi

echo "Backup process completed at $(date)"
