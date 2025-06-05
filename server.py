import network
import socket
import time
from machine import Pin, ADC
import dht
 
# Připojení k Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("zabry", "zabry000")
 
    timeout = 10
    while not wlan.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1
 
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"http://{ip}:8085")
        return ip
    else:
        return "0.0.0.0"
 
# Inicializace senzorů a výstupů
sensor = dht.DHT11(Pin(0))       # DHT11 na GPIO0
moisture = ADC(Pin(28))          # Půdní vlhkost (např. GPIO28 na Pico W)
relay = Pin(17, Pin.OUT)          # Relé na GPIO17
relay.off()
 
# Automatické zalévání
auto_watering = True
MIN_ADC = 60000  # suchá půda
MAX_ADC = 10000  # mokrá půda
 
def convert_to_percent(adc_value):
    if adc_value is None:
        return "N/A"
    adc_value = max(min(adc_value, MIN_ADC), MAX_ADC)
    return round((adc_value - MAX_ADC) / (MIN_ADC - MAX_ADC) * 100)
 
# Web stránka s zeleným designem
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
      margin: 0;
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
      color: #f0f8ff;
      text-align: center;
      padding: 20px;
    }}
    h1 {{
      font-size: 2.8em;
      margin-bottom: 25px;
      color: #a8e6cf;
      text-shadow: 2px 2px 5px rgba(0,0,0,0.4);
    }}
    .card {{
      background: rgba(255,255,255,0.05);
      border-radius: 15px;
      padding: 25px;
      max-width: 400px;
      margin: 20px auto;
      box-shadow: 0 0 20px rgba(0,0,0,0.3);
      backdrop-filter: blur(8px);
    }}
    .status {{
      font-size: 22px;
      margin: 15px 0;
      padding: 10px;
      border-radius: 8px;
      background-color: rgba(255,255,255,0.08);
    }}
    .temp {{ color: #ffa726; }}
    .hum {{ color: #29b6f6; }}
    .soil {{
      color: {{"#ef5350" if soil < 30 else "#66bb6a"}};
      font-weight: bold;
    }}
    .auto {{ color: #ffeb3b; }}
    button {{
      background: linear-gradient(to right, #43cea2, #185a9d);
      color: white;
      padding: 14px 24px;
      font-size: 17px;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      margin: 12px;
      transition: all 0.3s ease-in-out;
      box-shadow: 0 5px 10px rgba(0,0,0,0.4);
    }}
    button:hover {{
      transform: scale(1.05);
      background: linear-gradient(to right, #11998e, #38ef7d);
    }}
  </style>
</head>
<body>
  <h1>🌿 Chytrý květináč</h1>
  <div class="card">
    <div class="status temp">🌡️ <strong>Teplota:</strong> {temp}°C</div>
    <div class="status hum">💧 <strong>Vlhkost vzduchu:</strong> {hum}%</div>
    <div class="status soil">🌱 <strong>Vlhkost půdy:</strong> {soil}%</div>
    <div class="status auto">🤖 <strong>Automatika:</strong> {auto_status}</div>
    <form action="/water" method="get">
      <button>💦 Zalít nyní</button>
    </form>
    <form action="/toggle_auto" method="get">
      <button>🔁 {button_text} automatiku</button>
    </form>
  </div>
</body>
</html>"""
 
 
# Spuštění serveru
ip = connect_wifi()
addr = socket.getaddrinfo(ip, 8085)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
 
while True:
    try:
        cl, addr = s.accept()
        request = cl.recv(1024).decode()
 
        if "GET /water" in request:
            relay.on()
            time.sleep(2)
            relay.off()
 
        elif "GET /toggle_auto" in request:
            auto_watering = not auto_watering
 
        try:
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
        except:
            temp = "N/A"
            hum = "N/A"
 
        try:
            raw = moisture.read_u16()
            soil = convert_to_percent(raw)
        except:
            soil = "N/A"
 
        if auto_watering and isinstance(soil, (int, float)) and soil < 30:
            relay.on()
            time.sleep(2)
            relay.off()
 
        response = web_page(temp, hum, soil, auto_watering)
        cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        cl.send(response)
        cl.close()
 
    except:
        pass
