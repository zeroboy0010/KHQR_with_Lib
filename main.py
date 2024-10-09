import network
import urequests as requests
import ntptime
import machine
from utime import sleep
import ujson as json
import gc

def connect_wifi(ssid, password):
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, password)

    max_attempts = 10
    attempt = 0

    while not station.isconnected() and attempt < max_attempts:
        print(f'Connecting to Wi-Fi... Attempt {attempt + 1}')
        sleep(2)
        attempt += 1

    if not station.isconnected():
        raise RuntimeError('Failed to connect to Wi-Fi')

    print('Connected to Wi-Fi')
    print(station.ifconfig())

# Wi-Fi credentials
ssid = 'HomeSweetHome'
password = 'Kilo4resident'

# Connect to Wi-Fi
try:
    connect_wifi(ssid, password)
    sleep(5)
    # Set the RTC using NTP
    ntptime.settime()
    # Get the current time from RTC
    rtc = machine.RTC()
    current_time = rtc.datetime()
    print("RTC time after NTP sync:", current_time)
except RuntimeError as e:
    print(e)

from utime import sleep, mktime
from machine import Pin, I2C

from lib import ssd1306
from lib.khqr import KHQR

# ESP32 Pin assignment 
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
oled.poweron()

print("RTC time after NTP sync:", current_time)
local_hour = current_time[4] + 7
# Handle day overflow
if local_hour >= 24:
    local_hour -= 24
    # Increment the day, and handle month/year overflow if needed
    # Simplified: does not handle month/year changes
    local_day = current_time[2] + 1
else:
    local_day = current_time[2]

time_tuple = (current_time[0], current_time[1], local_hour, current_time[4], current_time[5], current_time[6], current_time[7], 0)

# Convert to Unix timestamp (seconds since epoch)
unix_time = mktime(time_tuple)

print("Current time in seconds since the Unix epoch:", unix_time * 1000)

# Create an instance of KHQR with Bakong Developer Token
khqr = KHQR('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiZWYyNjdhYmZmMGEwNDA2In0sImlhdCI6MTcyNzc2MzA0NiwiZXhwIjoxNzM1NTM5MDQ2fQ.7An4XxwkaxM8uM1-vZpZEdJKF9Z1tsL7oCdhVVKMEnU')

# Generate QR code data for a transaction
qr = khqr.create_qr(
    bank_account='kimhoir_na_2002@abaa', # Check your address under Bakong profile (Mobile App)
    merchant_name='Kimhoir',
    merchant_city='Phnom Penh',
    currency='KHR', # USD or KHR
    store_label='MShop',
    terminal_label='Buy one get one free',
    amount=100,
    phone_number='0183232096',
    bill_number='123456789'
)
# print(qr)

gc.collect()  # Call garbage collection to free up memory

# Import QRCode class and generate QR code matrix
from uQR import QRCode  
qr_code = QRCode()
qr_code.add_data(qr)
matrix = qr_code.get_matrix()
# Draw the QR code on the OLED

oled.fill(0)  # Clear the screen
for y in range(len(matrix)):                   # Scaling the bitmap by 2
    for x in range(len(matrix[0])):            # because my screen is tiny.
        value = not matrix[int(y)][int(x)]   # Inverting the values because
        oled.pixel(x, y, value)
gc.collect()
oled.show()

md5 = khqr.generate_md5(qr)

url = 'https://api-bakong.nbc.gov.kh/v1/check_transaction_by_md5'
# Headers for the POST request
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiZWYyNjdhYmZmMGEwNDA2In0sImlhdCI6MTcyNzc2MzA0NiwiZXhwIjoxNzM1NTM5MDQ2fQ.7An4XxwkaxM8uM1-vZpZEdJKF9Z1tsL7oCdhVVKMEnU'
}

data = {
    'md5': md5
}
data_json = json.dumps(data)
# Explicitly call garbage collection to free up memory
gc.collect()
# Check the status code and print the response
get_money = False
while not get_money:
    try:
        response = requests.post(url, headers=headers, data=data_json)
        if response.status_code == 200:
            data = response.json()
            if data['responseMessage'] == "Success":
                get_money = True
            try:
                print('Hash:', data['data']['hash'])
                print('From Account ID:', data['data']['fromAccountId'])
                print('To Account ID:', data['data']['toAccountId'])
                print('Currency:', data['data']['currency'])
                print('Amount:', data['data']['amount'])
                print('Description:', data['data']['description'])
                print('Created Date (ms):', data['data']['createdDateMs'])
                print('Acknowledged Date (ms):', data['data']['acknowledgedDateMs'])
            except KeyError:
                print("No data")
        else:
            print(f'POST request failed with status code {response.status_code}.')
        response.close()  # Close the response to free up memory
    except OSError as e:
        print(f'Network error: {e}')
        sleep(5)  # Wait before retrying
    except Exception as e:
        print(f'Error: {e}')
    sleep(1)
    gc.collect()  # Call garbage collection after each iteration

if get_money:
    print('Payment successful')
    oled.fill(0)  # Clear the screen
    oled.text("Payment", 0, 0)
    oled.text("successful", 0, 10)
    oled.text("Completed", 0, 20)
    oled.show()