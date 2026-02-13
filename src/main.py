import network
import ujson
import utime
import ntptime
import urequests
from machine import I2C, Pin
import lcd


# ---------------- LCD ----------------

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
print("I2C scan:", [hex(x) for x in i2c.scan()])

display = lcd.Lcd_i2c(i2c, cols=16, rows=2)
display.clear()


def pad(text):
    text = "" if text is None else str(text)
    return text[:16] + " " * (16 - len(text[:16]))

def line(row, txt):
    display.set_cursor(0, row)
    display.write(pad(txt))


# ---------------- CONFIG ----------------

def load_config():
    with open("config.json") as f:
        return ujson.loads(f.read())


cfg = load_config()
SSID = cfg["SSID"]
PASS = cfg["pass"]
API_KEY = cfg["API_KEY"]


# ---------------- WIFI ----------------

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASS)

    for i in range(20):
        if wlan.isconnected():
            return wlan
        line(0, "Connecting WiFi")
        line(1, "Try {}/20".format(i+1))
        utime.sleep(1)

    raise Exception("WiFi failed")


wlan = connect_wifi()
print("IP:", wlan.ifconfig()[0])


# ---------------- TIME (NTP) ----------------

def sync_time():
    for i in range(5):
        try:
            line(0, "Syncing time")
            line(1, "Attempt {}".format(i+1))
            ntptime.settime()  # UTC
            return True
        except:
            utime.sleep(2)
    return False

sync_time()


def clock_str():
    # CET offset +1h (3600s)
    t = utime.time() + 3600
    tm = utime.localtime(t)
    return "{:02d}:{:02d}:{:02d}".format(tm[3], tm[4], tm[5])


# ---------------- GEO (IP API) ----------------

def get_location():
    line(0, "Getting location")
    line(1, "via IP...")

    r = urequests.get("http://ip-api.com/json/")
    data = r.json()
    r.close()

    lat = data["lat"]
    lon = data["lon"]
    city = data.get("city", "")

    print("Location:", city, lat, lon)
    return lat, lon, city


LAT, LON, CITY = get_location()


# ---------------- WEATHER ----------------

def fetch_weather():
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        "?lat={}&lon={}&appid={}&units=metric"
    ).format(LAT, LON, API_KEY)

    r = urequests.get(url)
    j = r.json()
    r.close()

    main = j["main"]

    return {
        "temp": main["temp"],
        "hum": main["humidity"],
        "press": main["pressure"]
    }


weather = None
last_weather = 0


# ---------------- MAIN LOOP ----------------

while True:

    # každých 10 minut počasí
    if utime.time() - last_weather > 600 or weather is None:
        line(0, "Updating weather")
        line(1, CITY[:16])
        try:
            weather = fetch_weather()
        except Exception as e:
            print("weather error:", e)
        last_weather = utime.time()

    # každou sekundu hodiny
    time_txt = clock_str()

    if weather:
        line0 = "{} T:{:.1f}".format(time_txt, weather["temp"])
        line1 = "H:{}% P:{}".format(weather["hum"], weather["press"])
    else:
        line0 = time_txt + " no data"
        line1 = "weather error"

    display.clear()
    line(0, line0)
    line(1, line1)

    utime.sleep(1)
