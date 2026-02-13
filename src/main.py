import requests
import network
import lcd
import json
from machine import I2C, Pin
import time


i2c = I2C(0, scl=Pin(1), sda=Pin(0))  # Use correct pins for your board
print("I2C scan:", i2c.scan())
lcd_display = lcd.Lcd_i2c(i2c)
lcd_display.clear()
lcd_display.set_cursor(0,0)

with open('config.json', 'r', encoding='utf-8') as file:
    datajson = json.load(file)
print(datajson)


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(datajson['SSID'], datajson['pass'])

# Check WiFi connection
max_attempts = 20
attempt = 0
while not wlan.isconnected() and attempt < max_attempts:
    lcd_display.write(f"Connecting to WiFi... (attempt {attempt + 1}/{max_attempts})")
    attempt += 1
    time.sleep(1)

if wlan.isconnected():
    print("Connected to WiFi successfully!")
    print(f"IP address: {wlan.ifconfig()[0]}")
else:
    print("Failed to connect to WiFi")
    exit()


url = f"https://api.openweathermap.org/data/2.5/forecast?lat=50.5&lon=14.25&appid={datajson['API_KEY']}&units=metric"

while True:
    try:
        data = requests.get(url)
        if(data.status_code == 200):
            raw = data.json()
            lcd_display.clear()
            print("======= Parsed data =======")
            
            # Get first forecast entry (current/next forecast)
            first_forecast = raw["list"][0]
            temp = first_forecast["main"]["temp"]
            pressure = first_forecast["main"]["pressure"]
            humidity = first_forecast["main"]["humidity"]
            
            lcd_display.write(f"temp: {temp} C")
            print(f"humidity:    {humidity} RH%")
            print(f"pressure:    {pressure} hPa")
            
        else:
            print("invalid request", data.status_code)
    except Exception as err:
        print("request failed: " + str(err))
    time.sleep(600)
