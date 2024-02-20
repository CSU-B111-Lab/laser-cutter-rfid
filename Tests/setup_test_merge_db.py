# CREATE TABLE users(ramcard_uid, fullname, is_admin, expiration_date, duplicate)
# Setup test db
import sqlite3
import datetime

def setup():
  testdb = sqlite3.connect("merge_test.db")
  cur = testdb.cursor()
  
  # delete old tables
  cur.execute("DROP TABLE IF EXISTS users")
  cur.execute("DROP TABLE IF EXISTS users_log")
  cur.execute("DROP TABLE IF EXISTS laser_log")
  
  # create new table and fill in
  cur.execute("CREATE TABLE users(ramcard_uid, fullname, is_admin, expiration_date, duplicate)")
  
  now = datetime.datetime.today()
  six_months = datetime.timedelta(days = 180)
  expiration_date = int((now + six_months).timestamp())
  date_in_the_past = int((now - six_months).timestamp())
  
  cur.execute("""
    INSERT INTO users VALUES
      (151493474601, 'David Rohrbaugh', 1, %d, False),
      (12345678, 'Expired User2', 0, %d, False),
      (9876543, 'Expired Admin2', 1, %d, False),
      (86080340, 'Test User2', 0, %d, False),
      (15149347461, 'Duplicate Admin', 1, %d, True)
  """ % (expiration_date, date_in_the_past, date_in_the_past, expiration_date, expiration_date))
  
  cur.execute("CREATE TABLE users_log(timestamp, action, data)")
  
  cur.execute("CREATE TABLE laser_log(timestamp, action, data)")
  
  testdb.commit()
  
  testdb.close()

if __name__ == "__main__":
  setup()