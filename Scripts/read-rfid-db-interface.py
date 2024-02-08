#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()

import db_interface
db = db_interface.db_interface("first.db")

try:
  uid, text = reader.read()
  #print(hex(uid))
  #print(text)
  
  row, duplicate = db.get_row_from_uid(uid)
  
  if row:
    print("Hello, %s" % db._get_name(row))
    if db._is_admin(row): print("you are an admin!")
  if duplicate: print("duplicate detected")
  
  if db._check_uid(row): print("\nyou are authorized")
finally:
  GPIO.cleanup()
  db.close()
