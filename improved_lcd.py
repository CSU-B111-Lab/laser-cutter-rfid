import RPi_I2C_driver as lcd_driver # https://gist.github.com/DenisFromHR/cc863375a6e19dce359d
import time

class lcd(lcd_driver.lcd):
  
  NOT_RECOGNIZED = "Not Recognized"
  NOT_AUTHORIZED = "Not Authorized"
  AUTHORIZED =     "AUTHORIZED"
  
  def __init__(self):
    super().__init__() # call original class constructor, then do custom setup
    self.setup()
  
  def setup(self):
    self.clear()
    self.backlight(1)
  
  def clear(self):
    self.lcd_clear()
  
  def display_string(self, string, row, display_last_20=True, align_left=False, clear=False):
    if(clear): self.clear()
    formatted_str = string
    if len(string) < 20:
      padding = (' ' * (20 - len(string)))
      if align_left:
        formatted_str = string + padding
      else:  # Center the string if align_left is False
        half_padding_len = len(padding) // 2
        formatted_str = padding[:half_padding_len] + string + padding[half_padding_len:]
    elif len(string) > 20 and display_last_20:
        formatted_str = string[-20:]
    self.lcd_display_string(formatted_str, row)
  
  def display_strings(self, string_with_newlines, display_last_20=True, align_left=False, clear=True):
    list_of_strings = string_with_newlines.split('\n')
    self.display_list_of_strings(list_of_strings, display_last_20, align_left)
  
  def display_list_of_strings(self, strings, display_last_20=True, align_left=False):
    if len(strings) > 4:
      raise ValueError("Expected <= 4 strings, but got " + str(len(strings)))
    
    for i, string in enumerate(strings):
      if i == 0:
        self.display_string(string, i+1, display_last_20, align_left, clear=True)
      else:
        self.display_string(string, i+1, display_last_20, align_left)
