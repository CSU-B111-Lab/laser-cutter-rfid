import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_interface import print_users_table, print_users_log_table, print_laser_log_table

# replace 'your_database.db' with your actual database name
db_name = '../prod.db'

print_users_table(db_name)
print_users_log_table(db_name)
print_laser_log_table(db_name)