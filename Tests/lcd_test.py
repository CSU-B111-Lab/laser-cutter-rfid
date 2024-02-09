import sys
sys.path.append("..")
import improved_lcd

def main():
    lcd = improved_lcd.lcd()
    lcd.setup()
    lcd.display_string("Hello, World!", 1)
    lcd.display_string("Hello, World!", 2)
    lcd.display_string("Hello, World!", 3)
    lcd.display_string("Hello, World!", 4)

if __name__ == "__main__":
    main()