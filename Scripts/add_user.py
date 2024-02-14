import sqlite3
import argparse
import sys
sys.path.append("..")

import db_interface
db = db_interface.db_interface("../prod.db")

def add_user_to_db(uid: int, name: str):
    # Check if the uid is 9 digits long
    if len(str(uid)) != 9:
        print("Error: The UID must be exactly 9 digits long.")
        return

    # Add the user to the database
    db.add_user(uid, name, is_admin=False, expiration_date="2023-01-01", duplicate=False)

    # Retrieve and print the user data from the database
    user_data = db._db_cursor.execute("SELECT * from users WHERE ramcard_uid = ?", [uid]).fetchall()
    print(user_data)

# Create the parser
parser = argparse.ArgumentParser(description="Add a user to the database")

# Add the arguments
parser.add_argument("uid", type=int, help="The user's RAMCard UID")
parser.add_argument("name", type=str, help="The user's full name")

# Parse the arguments
args = parser.parse_args()

# Call the function with the arguments
add_user_to_db(args.uid, args.name)