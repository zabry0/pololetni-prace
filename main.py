import time
import Adafruit_DHT
from machine 
import GPIO

# Nastavení GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pin pro relé
RELAY_PIN = 17
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Pin pro DHT11 senzor
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4

# Funkce pro čtení vlhkosti
def get_humidity():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if humidity is not None:
        return humidity
    else:
        print("Chyba při čtení senzoru!")
        return None

# Funkce pro zapnutí čerpadla (relé)
def water_plants():
    print("Zalévám květináč!")
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Zapnutí relé
    time.sleep(5)                      # Čerpadlo běží 5 sekund
    GPIO.output(RELAY_PIN, GPIO.LOW)   # Vypnutí relé
    print("Zalévání dokončeno.")

# Hlavní smyčka
try:
    while True:
        humidity = get_humidity()
        if humidity is not None:
            print(f"Aktuální vlhkost: {humidity}%")

            if humidity < 40:  # Pokud je vlhkost pod 40%, zaléváme
                water_plants()

        time.sleep(60)  # Kontrola každou minutu

except KeyboardInterrupt:
    print("Program ukončen.")
    GPIO.cleanup()  # Uvolní GPIO piny
