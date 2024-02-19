import shutil
import datetime

# This function will backup the database file to the backup directory
# Backups are named with the current date
# Example: backup_db('prod.db', '/home/pi/senior_design_FA23/Backups')
# Run periodically using cron
# Example: 0 0 * * * /usr/bin/python3 /home/pi/senior_design_FA23/laser-access-control/db_backup.py

def backup_db(db_file, backup_dir):
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    backup_file = f"{backup_dir}/{db_file}-{date_str}"
    shutil.copy(db_file, backup_file)

backup_db('prod.db', '/home/pi/senior_design_FA23/Backups')