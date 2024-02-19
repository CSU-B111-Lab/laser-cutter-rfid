#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import db_interface
db = db_interface.db_interface("../prod.db")

try:
  fullname = input("Enter your full name: ")
  while not isinstance(fullname, str) or fullname == '':
    print("Invalid input. Please enter a string.")
    fullname = input("Enter your full name: ")

  id = input("Enter your 9 digit ID number: ")
  while not id.isdigit() or len(id) != 9:
    print("Invalid input. Please enter a 9 digit number.")
    id = input("Enter your 9 digit ID number: ")

  print("Scan your RamCard")
  
  uid, text = reader.read()
  
  db.add_admin(uid, id, fullname)
  
  result = db._db_cursor.execute("SELECT * from users WHERE ramcard_uid = ?", [uid])
  print(result.fetchall())
  
finally:
  GPIO.cleanup()
  db.close()
