# This script is the initial test implementation of key authentication on the mifare classic cards using the mfrc522 reader
# It will use the key (removed for security) and authenticate and read sector 1 of the Ramcard to get csu id

from mfrc522 import MFRC522
import signal
import time

def end_read(signal, frame):
    print("Ctrl+C captured, ending read.")
    reader.Close_MFRC522()
    exit()

signal.signal(signal.SIGINT, end_read)

reader = MFRC522()

print("Please place the RFID tag on the reader...")

while True:
    (status, tag_type) = reader.MFRC522_Request(reader.PICC_REQIDL)
    if status == reader.MI_OK:
        (status, uid) = reader.MFRC522_Anticoll()
        if status == reader.MI_OK:
            reader.MFRC522_SelectTag(uid)

            key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # Replace with your actual key
            sector = 1  # Replace with the sector number you want to read
            block_addr = sector * 4  # Calculate the block address based on the sector number

            status = reader.MFRC522_Auth(reader.PICC_AUTHENT1A, block_addr, key, uid)
            if status == reader.MI_OK:
                print("Authentication successful")
                data = reader.MFRC522_Read(block_addr)
                if data:
                    print("Data read from sector", sector)
                    trimmed_data = data[3:8]  # Adjust indices as needed
                    decimal_value = int.from_bytes(trimmed_data, byteorder='big')
                    print("CSU ID:", decimal_value)
                    print(trimmed_data)
                else:
                    print("Failed to read data from sector", sector)
            else:
                print("Authentication failed")

            reader.MFRC522_StopCrypto1()
            break
    else:
        print("Waiting for RFID tag...")
        time.sleep(1)

reader.Close_MFRC522()