#!/bin/bash

# Make backup script executable
chmod +x /home/nguyenhao/mimosatek_project/scripts/backup_db.sh

# Create cron job for 4 times daily backup
CRON_JOB="0 0,6,12,18 * * * /home/nguyenhao/mimosatek_project/scripts/backup_db.sh >> /var/log/db_backup.log 2>&1"

# Add cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job added successfully!"
echo "Database backup will run 4 times daily at: 00:00, 06:00, 12:00, 18:00"
echo "Logs will be saved to: /var/log/db_backup.log"

# Create log file with proper permissions
sudo touch /var/log/db_backup.log
sudo chown $USER:$USER /var/log/db_backup.log
