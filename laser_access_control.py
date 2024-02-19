#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522 # https://pypi.org/project/mfrc522/
import db_interface
import improved_lcd
import time
import keyboard # https://pypi.org/project/keyboard/
import signal
import sys

# Laser access control system
# Set to run on startup by adding the following line to /etc/rc.local:
#  sudo python3 /home/pi/senior_design_FA23/laser-cutter-rfid/laser_access_control.py &
# TODO systemd service

# TODO move constants to laser_access_control class?

# timing constants
LASER_OFF_POLLING_RATE_SECONDS = 0.5
LASER_ON_POLLING_RATE_SECONDS  = 1
LASER_ON_GRACE_PERIOD_SECONDS  = 20
ADD_USER_TIMEOUT_SECONDS       = 30

# pin number constants
LASER_RELAY_PIN_NUMBER = 8
DONE_BUTTON_PIN_NUMBER = 10
RED_LED_PIN_NUMBER = 32
GREEN_LED_PIN_NUMBER = 33
BLUE_LED_PIN_NUMBER = 35

shift_chars = {'1':'!', '2':'@', '3':'#', '4':'$', '5':'%', '6':'^', '7':'&', '8':'*', '9':'(', '0':')', '-':'_', '=':'+', '\\':'|', '`':'~', '[':'{', ']':'}', ';':':', '\'':'"', ',':'<', '.':'>', '/':'?'}

# ---------- keyboard handling stuff ---------

def process_key_press(event):
  global name_from_keyboard, id_from_keyboard, keyboard_done, shift_pressed, accepting_keyboard_input, input_mode
  
  if event.name == 'shift':
    shift_pressed = True
  
  if not accepting_keyboard_input:
    return
  
  if event.name == 'enter':
    keyboard_done = True
    if input_mode == 'name':
      input_mode = 'id'
    elif input_mode == 'id' and len(id_from_keyboard) != 9:
      print("Invalid input. Please enter a 9 digit number.")
      keyboard_done = False
    return
  
  if event.name == 'backspace':
    if input_mode == 'name':
      name_from_keyboard = name_from_keyboard[:-1]
    elif input_mode == 'id':
      id_from_keyboard = id_from_keyboard[:-1]
  
  elif event.name == 'delete':
    if input_mode == 'name':
      name_from_keyboard = ''
    elif input_mode == 'id':
      id_from_keyboard = ''
  
  elif event.name == 'space':
    if input_mode == 'name':
      name_from_keyboard += ' '
    elif input_mode == 'id':
      id_from_keyboard += ' '
  
  elif len(event.name) == 1:
    if shift_pressed:
      if event.name in shift_chars.keys():
        char_to_add = shift_chars[event.name]
      else:
        char_to_add = event.name.upper()
    else:
      char_to_add = event.name

    if input_mode == 'name':
      name_from_keyboard += char_to_add
    elif input_mode == 'id':
      if char_to_add.isdigit() and len(id_from_keyboard) < 9:
        id_from_keyboard += char_to_add
  
def process_shift_release(event):
  global shift_pressed
  
  shift_pressed = False

# ---------- end keyboard handling stuff -----

# standardize checking done button
#  since the button is connected between the input pin and ground
#  when pressed it will pull the pin LOW
#  when not pressed, the pin is pulled high by a built-in pull-up resistor on the Pi
def is_done_button_pressed():
  return not GPIO.input(DONE_BUTTON_PIN_NUMBER)

class laser_access_control:
  
  def __init__(self):
    self.setup()
  
  def setup(self):
    global shift_pressed, accepting_keyboard_input
    
    shift_pressed = False
    accepting_keyboard_input = False
    
    # -- keyboard setup --
    keyboard.on_press(process_key_press)
    keyboard.on_release_key('shift', process_shift_release)
    
    # -- GPIO setup --
    self.GPIO_setup()
    
    # -- rfid setup --
    self.reader = SimpleMFRC522()
    
    # connect to database
    #  use absolute path because when this script runs at boot (using /etc/rc.local),
    #  it is not launched from this folder that it is in
    self.db = db_interface.db_interface("/home/pi/senior_design_FA23/laser-cutter-rfid/prod.db")
    
    # -- LCD setup --
    self.lcd = improved_lcd.lcd()
  
  def GPIO_setup(self):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(LASER_RELAY_PIN_NUMBER, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(DONE_BUTTON_PIN_NUMBER, GPIO.IN, pull_up_down=GPIO.PUD_UP) # enable Pi's built-in pull-up resistor for this pin
    
    GPIO.setup(RED_LED_PIN_NUMBER, GPIO.OUT);
    GPIO.setup(GREEN_LED_PIN_NUMBER, GPIO.OUT);
    GPIO.setup(BLUE_LED_PIN_NUMBER, GPIO.OUT);
    
    self.red = GPIO.PWM(RED_LED_PIN_NUMBER, 2);
    self.green = GPIO.PWM(GREEN_LED_PIN_NUMBER, 2);
    self.blue = GPIO.PWM(BLUE_LED_PIN_NUMBER, 2);
    
    self.green.start(0)
    self.red.start(0)
    self.blue.start(0)
  
  # params should range from 0 - 100, inclusive
  def set_LED(self, r, g, b):
    self.red.ChangeDutyCycle(r)
    self.green.ChangeDutyCycle(g)
    self.blue.ChangeDutyCycle(b)
  
  def add_user_mode(self):
    # indicate that the system is adding users
    self.set_LED(100, 0, 100) # purple
    self.lcd.display_string("Adding Users!", 2, clear=True)
    time.sleep(3)

    while True:
      # continue_loop = False # Flag to continue the outer loop
      update_entry = False
      uid_to_add = self.reader.read_id_no_block()
      
      # if a card is not read within ADD_USER_TIMEOUT_SECONDS,
      #  exit add user mode
      timeout = ADD_USER_TIMEOUT_SECONDS
      while not uid_to_add:
        uid_to_add = self.reader.read_id_no_block()
        time.sleep(1)
        timeout -= 1
        self.lcd.display_string("Scan new RamCard", 1)
        self.lcd.display_string("or wait %d seconds" % timeout, 2)
        self.lcd.display_string("to exit add mode", 3)

        if timeout == 0: 
          self.lcd.clear()
          return # exit add user mode if no card is read within ADD_USER_TIMEOUT_SECONDS
        
        # Exit adding user mode if DONE button is pressed
        if is_done_button_pressed():
          self.lcd.display_string("Exiting add mode", 2, clear=True)
          time.sleep(2)
          return
      
      data = self.db.get_row_from_uid(uid_to_add)
      # check if there is an existing entry with this uid
      if (data):
        if data.is_admin(): # admin cards should not be updated
          self.lcd.display_list_of_strings(["Admin card cannot", "be updated"])
          time.sleep(1)
          continue
        existing_name = data.get_name()[:15]
        self.lcd.display_list_of_strings(["Update entry for", "%s?" % existing_name, "press and hold", "DONE to confirm"])
        
        start_time = time.time()
        while time.time() - start_time < 7: # give 7 seconds for user to push button
          if is_done_button_pressed():
            # only change the entry if the DONE button was pressed
            self.lcd.display_list_of_strings(["", "Entry will", "be updated"])
            update_entry = True
            time.sleep(2)
            break
        if not update_entry:
          self.lcd.display_list_of_strings(["", "Entry will not", "be updated"])
          # continue_loop = True
          time.sleep(2)
          continue # go back to top of outer while loop
      
      # TODO multiple updated entries or skipped updated entries has not been tested.
      # user types in their name on the keyboard
      name_to_add, csu_id_to_add = self.activate_keyboard_and_get_name()
      
      # add them to the database as a user
      self.db.add_user(uid_to_add, csu_id_to_add, name_to_add)
      
      self.lcd.display_list_of_strings(["Added user", name_to_add, "with uid", hex(uid_to_add)])
      time.sleep(3)
      self.lcd.clear()
  
  def main(self):
    print("System ready")
    while True:
      
      uid = self.reader.read_id_no_block()
      
      # if no card is detected ...
      if not uid:
        # ... display the idle message, wait,
        #  and then go back to the top of this while loop
        self.set_LED(0, 0, 100) # blue
        self.lcd.display_string("Scan RamCard", row=2, align_left=False, clear=False)
        continue
      
      row = self.db.get_row_from_uid(uid)
      
      # if the DONE button is pressed
      if is_done_button_pressed():
        # ... and an admin has scanned their card ...
        if row and row.is_admin():
          
          # ... enter a mode where multiple users can be added in succession
          #  without an admin re-scanning their card ...
          self.add_user_mode()
          
          # ... then go back to the top of this while loop
          continue
        
        # if the card that was scanned is in the database,
        #  display the corresponding name
        elif row:
          self.lcd.display_string(row.get_name(), 1)
        
        # otherwise, display this generic text
        else:
          self.lcd.display_string("Card uid:", 1)
        
        # and with the first LCD row set up,
        #  display the uid on the second row
        self.lcd.display_string(hex(uid), 2, clear=False)
        time.sleep(2)
        continue
      
      # if the uid is not in the database ...
      if not row:
        # ... indicate that the card is not recognized
        #  and then go back to the top of this while loop
        self.set_LED(100, 0, 0) # red
        self.lcd.display_string(self.lcd.NOT_RECOGNIZED, 3, clear=False, align_left=False)
        time.sleep(3)
        self.lcd.clear()
        continue
      
      # this uid is in the database,
      #  so get corresponding name from uid and display it
      name = row.get_name()
      self.lcd.display_string(name, 2)
      
      # if this user is not authorized to use the laser
      #  (i.e. if their acces has expired) ...
      if not self.db._check_uid(row):
        # ... indicate that this user is not authorized
        # and then go back to the top of this while loop
        self.set_LED(100, 0, 0) # red
        self.lcd.display_string(self.lcd.NOT_AUTHORIZED, 3)
        time.sleep(3)
        self.lcd.clear()
        continue
      
      # this user is authorized, so turn on the laser
      self.lcd.display_string(self.lcd.AUTHORIZED, 3, clear=False)
      self.set_LED(0, 100, 0) # green
      GPIO.output(LASER_RELAY_PIN_NUMBER, GPIO.HIGH)
      
      times_card_missing = 0
      max_times_card_missing = LASER_ON_GRACE_PERIOD_SECONDS / LASER_ON_POLLING_RATE_SECONDS
      current_user_uid = uid
      
      while True:
        time.sleep(LASER_ON_POLLING_RATE_SECONDS)
        
        display_card_missing = True
        
        # if the user is pressing the DONE button ...
        if is_done_button_pressed():
          # ... turn off the laser ...
          GPIO.output(LASER_RELAY_PIN_NUMBER, GPIO.LOW)
          self.lcd.display_string(name + " DONE", 2)
          # ... wait for the user to remove their card ...
          self.lcd.display_string("Remove RamCard", 3, clear=False)
          # ... and break out of this inner while loop
          time.sleep(5)
          self.lcd.clear()
          break
        
        # if the card is missing for too long, shut off the laser
        #  and break out of this inner while loop
        if times_card_missing >= max_times_card_missing:
          self.lcd.display_string("Time's up!", 2)
          GPIO.output(LASER_RELAY_PIN_NUMBER, GPIO.LOW) # laser and chiller OFF
          self.set_LED(100, 0, 0) # red
          time.sleep(2)
          self.lcd.clear()
          break
        
        # begin checking that a card is still present
        uid = self.reader.read_id_no_block()
        if not uid: uid = self.reader.read_id_no_block() # try again immediately if first read failed
        
        # if a card is present, check it against the database
        if uid:
          
          if uid == current_user_uid:
            times_card_missing = 0
            self.set_LED(0, 100, 0) # green
            self.lcd.display_string(name, 2)
            self.lcd.display_string(self.lcd.AUTHORIZED, 3, clear=False)
            continue
          
          row = self.db.get_row_from_uid(uid)
          
          if row:
            name = row.get_name()
            self.lcd.display_string(name, 2, clear=False)
            
            # if the new uid is authorized,
            #  update LED and LCD and go back to the top of this inner while loop
            if self.db._check_uid(row):
              current_user_uid = uid
              times_card_missing = 0
              self.set_LED(0, 100, 0) # green
              self.lcd.display_string(self.lcd.AUTHORIZED, 3, clear=False)
              continue
            
            self.set_LED(100, 0, 0) # red
            display_card_missing = False
            self.lcd.display_string(self.lcd.NOT_AUTHORIZED, 3, clear=False)
          
          else:
            self.set_LED(100, 0, 0) # red
            display_card_missing = False
            self.lcd.display_string(self.lcd.NOT_RECOGNIZED, 2, clear=False)
        
        # a card is not present or the card is not valid,
        #  so increment the number of times a check has not detected a valid card
        times_card_missing += 1
        
        # alert the user that they need to return their card to the reader
        #  and update how much time they have left to do so
        if display_card_missing:
          self.lcd.display_string("Card missing!", 2)
          self.set_LED(50, 0, 0) # blink red at 2 Hz
        time_str = "%d sec to return" % ((max_times_card_missing - times_card_missing) * LASER_ON_POLLING_RATE_SECONDS)
        self.lcd.display_string(time_str, 3, clear=False)
  
  def cleanup(self):
    # if this program errors out,
    #  "turn off" the lcd and LED and close the connection to the database
    #  before exiting
    self.lcd.clear()
    self.lcd.backlight(0)
    self.set_LED(0, 0, 0)
    self.db.close()
    GPIO.cleanup()
  
  def activate_keyboard_and_get_name(self):
    global name_from_keyboard, id_from_keyboard, keyboard_done, accepting_keyboard_input, input_mode
    
    name_from_keyboard = ""
    id_from_keyboard = ""
    keyboard_done = False
    accepting_keyboard_input = True
    
    #  prompt the user to enter their name with the keyboard
    input_mode = 'name'
    self.lcd.display_string("Enter your name:", 1, clear=True)
    
    while not keyboard_done:
      self.lcd.display_string(name_from_keyboard, 2, clear=False)
      #time.sleep(0.25)
    
    keyboard_done = False  # Reset for next input
    
    #  prompt the user to enter their CSU ID with the keyboard
    input_mode = 'id'
    self.lcd.display_string("Enter your CSU id:", 3, clear=False)
    
    while not keyboard_done:
      self.lcd.display_string(id_from_keyboard, 4, clear=False)
      #time.sleep(0.25)
    
    accepting_keyboard_input = False
    
    return name_from_keyboard, id_from_keyboard

def signal_handler(sig, frame):
    access_controller.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
  
if __name__ == "__main__":
  access_controller = laser_access_control()
  
  try:
    access_controller.main()
  except Exception as e:
    print(f"An exception occurred: {e}")
    access_controller.cleanup()
    raise e