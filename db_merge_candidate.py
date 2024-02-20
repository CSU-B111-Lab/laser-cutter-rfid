import sqlite3
import os
import argparse

def merge_databases(db_file, output_db_file):
    """
    Migrates user data from a source SQLite database to a target SQLite database,
    handling potential differences in column names and types.

    Args:
        source_db_file (str): Path to the source .db file.
        target_db_file (str): Path to the target .db file.
    """

    # Connect to source database
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
    except sqlite3.Error as e:
        print(f"Error connecting to source database: {e}")
        return
    
    # Connect to the output database
    try:
        output_conn = sqlite3.connect(output_db_file)
        output_cursor = output_conn.cursor()

        tables = {
            'users': 'CREATE TABLE IF NOT EXISTS users(ramcard_uid TEXT, csu_id TEXT, fullname TEXT, is_admin INTEGER, expiration_date INTEGER)',
            'users_log': 'CREATE TABLE IF NOT EXISTS users_log(timestamp TEXT, action TEXT, data TEXT)',
            'laser_log': 'CREATE TABLE IF NOT EXISTS laser_log(timestamp TEXT, action TEXT, data TEXT)'
        }

        for table, creation_query in tables.items():
          output_cursor.execute(creation_query)
          print(f"Table {table} created.")
    except sqlite3.Error as e:
        print(f"Error connecting to the output database: {e}")
        conn.close()  # Close first connection on error
        return

    # Fetch data from first database
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    # Insert into target database, handling data conversions
    for row in rows:
        ramcard_uid = int(row[0])  # Convert to TEXT if needed
        fullname = str(row[1])
        is_admin = int(row[2])  # Convert boolean to INTEGER (0 or 1)
        expiration_date = int(row[3])  # Convert to INTEGER if needed
        # Dont add duplicate

        output_cursor.execute(
            """
            INSERT INTO users (ramcard_uid, csu_id, fullname, is_admin, expiration_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ramcard_uid, "", fullname, is_admin, expiration_date)  # Blank csu_id
        )

    # Save changes
    conn.close()
    output_conn.commit()
    output_conn.close()
    print("Data migration successful!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Merge data from two databases into a new database.')
    parser.add_argument('db_file', help='Source .db filename')
    parser.add_argument('output_db_file', help='Output .db filename')

    args = parser.parse_args()

    db_file = args.db_file
    output_db_file = args.output_db_file

    # Make sure input files exist
    if not os.path.isfile(db_file):
        print(f"First database file not found: {db_file}")
    else:
        merge_databases(db_file, output_db_file)