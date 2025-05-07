import network
import socket
import time
from machine import Pin, ADC
import dht

# Wi-Fi připojení
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("zabry", "zabry000")

    timeout = 10
    while not wlan.isconnected() and timeout > 0:
        print("⏳ Připojuji se k Wi-Fi...")
        time.sleep(1)
        timeout -= 1

    if wlan.isconnected():
        print("✅ Připojeno:", wlan.ifconfig())
        return wlan.ifconfig()[0]
    else:
        print("❌ Nepodařilo se připojit k Wi-Fi.")
        return "0.0.0.0"

# Inicializace komponent
sensor = dht.DHT11(Pin(15))  # Senzor teploty a vlhkosti
moisture = ADC(Pin(26))  # ADC pro měření vlhkosti půdy
relay = Pin(16, Pin.OUT)
relay.off()

# Parametry
auto_watering = True
THRESHOLD = 30000  # Hodnota prahu pro suchou půdu

# Kalibrace senzoru: Minimální (suchá) a maximální (mokrá) hodnota
MIN_ADC = 60000  # Hodnota ADC pro suchou půdu (experimentálně)
MAX_ADC = 10000  # Hodnota ADC pro mokrou půdu (experimentálně)

# Funkce pro převod hodnoty ADC na procenta
def convert_to_percent(adc_value):
    if adc_value == None:  # Pokud není hodnota k dispozici (např. senzor není připojen)
        return "N/A"
    
    # Zajištění, že hodnota ADC bude v intervalu 0-100
    if adc_value > MIN_ADC:
        adc_value = MIN_ADC
    elif adc_value < MAX_ADC:
        adc_value = MAX_ADC
    
    # Převod na procenta
    return (MIN_ADC - adc_value) / (MIN_ADC - MAX_ADC) * 100

# HTML šablona
def web_page(temp, hum, soil, auto):
    auto_status = "ANO" if auto else "NE"
    button_text = "Vypnout" if auto else "Zapnout"
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            background-color: #111111; /* Černé pozadí */
            color: white; /* Bílý text */
            text-align: center;
        }}
        h1 {{
            font-size: 36px;
            margin-top: 20px;
            color: #FF4500; /* Oranžovo-červený text pro nadpis */
        }}
        .box {{
            background: #222222;
            border-radius: 10px;
            padding: 30px;
            margin: 20px auto;
            width: 80%;
            max-width: 500px;
            box-shadow: 0px 0px 10px rgba(255, 69, 0, 0.8); /* Oranžovo-červený stín */
        }}
        .status {{
            font-size: 18px;
            margin: 10px 0;
        }}
        button {{
            padding: 12px 30px;
            font-size: 18px;
            border: none;
            background-color: #FF6347; /* Červená tlačítka */
            color: white;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px;
        }}
        button:hover {{
            background-color: #FF4500; /* Oranžovo-červená při najetí */
        }}
        .emoji {{
            font-size: 36px;
        }}
    </style>
</head>
<body>
    <h1>🌿 Chytrý květináč</h1>
    <div class="box">
        <div class="status">🌡️ <strong>Teplota:</strong> {temp}°C</div>
        <div class="status">💧 <strong>Vlhkost vzduchu:</strong> {hum}%</div>
        <div class="status">🌱 <strong>Vlhkost půdy:</strong> {soil}%</div>
        <div class="status">🤖 <strong>Automatické zalévání:</strong> {auto_status}</div>
    </div>
    <form action="/water" method="get">
        <button type="submit">💦 Zalít nyní</button>
    </form>
    <form action="/toggle_auto" method="get">
        <button type="submit">🔁 {button_text} automatiku</button>
    </form>
</body>
</html>"""

# Spuštění webserveru
ip = connect_wifi()
addr = socket.getaddrinfo(ip, 8080)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print("🌐 Server běží na http://", ip, ":8080")

# Hlavní smyčka
while True:
    try:
        cl, addr = s.accept()
        print("🔗 Připojeno od", addr)
        request = cl.recv(1024).decode()
        print("📩 Request:", request)

        # Obsluha akcí podle URL
        if "GET /water" in request:
            print("💧 Ruční zalévání...")
            relay.on()
            time.sleep(2)
            relay.off()
        elif "GET /toggle_auto" in request:
            auto_watering = not auto_watering
            print("🔁 Přepnuto automatické zalévání:", auto_watering)

        # Čtení senzorů
        try:
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
        except Exception as e:
            temp = "N/A"
            hum = "N/A"
            print("❌ Chyba čtení DHT11:", e)

        # Čtení vlhkosti půdy
        try:
            soil = moisture.read_u16()
            soil_percent = convert_to_percent(soil)  # Převod na procenta
        except Exception as e:
            soil_percent = "N/A"
            print("❌ Chyba čtení vlhkosti půdy:", e)

        print(f"📊 Půdní vlhkost: {soil_percent}%")

        # Automatické zalévání
        if auto_watering and isinstance(soil_percent, (int, float)) and soil_percent < 30:  # Například zapnout, když vlhkost klesne pod 30%
            print("⚠️ Sucho! Zalévám automaticky.")
            relay.on()
            time.sleep(2)
            relay.off()

        # Odpověď
        response = web_page(temp, hum, soil_percent, auto_watering)
        cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        cl.send(response)
        cl.close()

    except Exception as e:
        print("💥 Chyba:", e)
