import shutil
import datetime

def backup_db(db_file, backup_dir):
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    backup_file = f"{backup_dir}/{db_file}-{date_str}"
    shutil.copy(db_file, backup_file)

backup_db('prod.db', '/home/pi/senior_design_FA23/Backups')