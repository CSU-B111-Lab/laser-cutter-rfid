import sqlite3
import datetime

# TODO extend dict instead of just having a dict?
# could be useful when sqlite requires a dict or dict subclass

# ========================== TABLES ==========================
# users(ramcard_uid, csu_id, fullname, is_admin, expiration_date)
# users_log(timestamp, action, data)
# laser_log(timestamp, action, data)
class user_entry:
  
  def __init__(self, uid: int, csu_id: int, name: str, is_admin: int, expiration_date):
    self.data = {'ramcard_uid': uid, 'csu_id': csu_id, 'fullname': name, 'is_admin': is_admin, 'expiration_date': expiration_date}
  
  def get_uid(self):
    return self.data['ramcard_uid']
  
  def get_csu_id(self):
    return self.data['csu_id']
  
  def get_name(self):
    return self.data['fullname']
  
  def is_admin(self):
    if self.data['is_admin'] == 1:
      return True
    return False
  
  def is_expired(self):
    now = int(datetime.datetime.today().timestamp())
    expiration = self.data['expiration_date']
    if now > expiration: return True
    return False

class db_interface:

  USER_ADD_ACTION = "ADD"
  USER_UPDATE_ACTION = "UPDATE"
  USER_DELETE_ACTION = "DELETE"
  USER_REMOVEEXPIRED_ACTION = "REMOVE EXPIRED"
  
  def __init__(self, db_name: str):
    self._db = None
    self._db_cursor = None
    self.current_db = None
    self.connect_to_db(db_name)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()

  def connect_to_db(self, db_name: str):
    self._db = sqlite3.connect(db_name)
    if not self._db:
      raise Exception("Could not connect to database %s" % db_name)
    self._db_cursor = self._db.cursor()
    self.current_db = db_name

  def close(self):
    if self._db:
      self._db.close()
  
  def delete_entry(self, uid: int):
    # Delete the user from the users table
    self._db_cursor.execute("DELETE FROM users WHERE ramcard_uid = ?", [uid])
    # Log the action in user_log
    # TODO user_log changes
    self._db_cursor.execute("INSERT INTO users_log VALUES (?, ?, ?)", [int(datetime.datetime.today().timestamp()), self.USER_DELETE_ACTION, uid])
    self._db.commit()

  def _add_entry(self, ramcard_uid: int, csu_id: int, fullname: str, is_admin: int):
    action = self.USER_ADD_ACTION
    
    # Delete existing entry if it exists
    res = self._db_cursor.execute("DELETE FROM users WHERE ramcard_uid = ?", [ramcard_uid])
    # If the entry existed, then we are updating it
    if res.rowcount > 0:
      action = self.USER_UPDATE_ACTION
    self._db_cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", [ramcard_uid, csu_id, fullname, is_admin, calculate_expiration_date_timestamp()])
    # Log the action in user_log
    # TODO user_log changes
    self._db_cursor.execute("INSERT INTO users_log VALUES (?, ?, ?, ?)", [int(datetime.datetime.today().timestamp()), action, ramcard_uid, csu_id])
    self._db.commit()

  def add_user(self, ramcard_uid: int, csu_id: int, fullname: str):
    self._add_entry(ramcard_uid, csu_id, fullname, 0)

  def add_admin(self, ramcard_uid: int, csu_id: int, fullname: str):
    self._add_entry(ramcard_uid, csu_id, fullname, 1)

  def get_row_from_uid(self, ramcard_uid: int):
    # Fetch the user from the users table
    res = self._db_cursor.execute("SELECT * FROM users WHERE ramcard_uid = ?", [ramcard_uid])
    # Fetch the first row from result set
    row = res.fetchone()
    # If the row is empty, set was empty, 
    if not row:
      return None
    # Fetch again to see if there are duplicates
    duplicate = res.fetchone()
    #if duplicate:
      # TODO Print to log file
    # Return the first user entry even if there is duplicates
    # TODO duplicate handling (shouldnt happen)
    return user_entry(row[0], row[1], row[2], row[3], row[4])
  
  def check_uid(self, ramcard_uid: int):
    data = self.get_row_from_uid(ramcard_uid)
    return self._check_uid(data)
  
  def _check_uid(self, row):
    # If the row is empty, set was empty, return False
    if not row:
      return False
    # If the user is an admin or their account is not expired, log the unlock action and return True
    if row.is_admin() or not row.is_expired():
      self.log_unlock(row.get_uid())
      return True
    # False if not admin or expired (not authorized)
    return False
  
  # only remove expired users, leave expired admins
  def remove_expired_users(self):
    res = self._db_cursor.execute("DELETE FROM users WHERE is_admin != 1 AND expiration_date < ?", [int(datetime.datetime.today().timestamp())])
    # Log the action in user_log
    # TODO user_log changes
    self._db_cursor.execute("INSERT INTO users_log VALUES (?, ?, ?)", [int(datetime.datetime.today().timestamp()), self.USER_REMOVEEXPIRED_ACTION, res.rowcount])
    self._db.commit()
  
  # remove all expired entries, admins included
  def remove_expired_entries(self):
    res = self._db_cursor.execute("DELETE FROM users WHERE expiration_date < ?", [int(datetime.datetime.today().timestamp())])
    # Log the action in user_log
    # TODO user_log changes
    self._db_cursor.execute("INSERT INTO users_log VALUES (?, ?, ?)", [int(datetime.datetime.today().timestamp()), self.USER_REMOVEEXPIRED_ACTION, res.rowcount])
    self._db.commit()
  
  def close(self):
    self._db.close()
  
  def log_unlock(self, uid):
    self._db_cursor.execute("INSERT INTO laser_log VALUES (?, ?, ?)", [int(datetime.datetime.today().timestamp()), "UNLOCK", uid])
    self._db.commit()
  
  ##### GET METHODS #####
  
  def get_name(self, uid: int):
    data = self.get_row_from_uid(uid)
    
    return data.get_name()
  
  ##### IS METHODS #####
  
  def is_admin(self, uid: int):
    data = self.get_row_from_uid(uid)
    
    return data.is_admin()
  
  def is_expired(self, uid: int):
    data = self.get_row_from_uid(uid)
    
    return data.is_expired()

# TODO change this to be something like
#  - end of the current semester
#  - end or current year
#  - one of the above or 3 months, whichever is longer
def calculate_expiration_date_timestamp():
  now = datetime.datetime.today()
  six_months = datetime.timedelta(days = 180)
  return int((now + six_months).timestamp())

def print_users_table(db_name):
  db = sqlite3.connect(db_name)
  res = db.cursor().execute("SELECT * FROM users")
  print(res.fetchall())
  db.close()

def print_users_log_table(db_name):
  db = sqlite3.connect(db_name)
  res = db.cursor().execute("SELECT * FROM users_log")
  print(res.fetchall())
  db.close()

def print_laser_log_table(db_name):
  db = sqlite3.connect(db_name)
  res = db.cursor().execute("SELECT * FROM laser_log")
  print(res.fetchall())
  db.close()