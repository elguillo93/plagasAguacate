import network, time, urequests
import ujson
from machine import Pin, ADC
from utime import sleep, sleep_ms, ticks_us
from dht import DHT22
from umqtt.simple import MQTTClient
from time import sleep
#creando motion sensor pir y pin
motion = False
def handle_interrupt(pin):
  global motion
  motion = True
  global interrupt_pin
  interrupt_pin = pin
cero = Pin(26, Pin.OUT)
led = Pin(4, Pin.OUT)
pir = Pin(13, Pin.IN)
pir.irq(trigger=Pin.IRQ_RISING, handler=handle_interrupt)

# creando objeto ADC en el pin
moisture = ADC(Pin(35, Pin.IN))
# creando sensor DHT22 en el pin
sensor = DHT22(Pin(2))
m = 100
min_moisture=0
max_moisture=4095
# MQTT parametros servidor
MQTT_CLIENT_ID = "gceballos5"
MQTT_BROKER    = "broker.hivemq.com"
#MQTT_BROKER    = "192.168.20.25"  #  en docker apuntar al host local
MQTT_USER      = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC     = "andina"


def conectaWifi (red, password):
      global miRed
      miRed = network.WLAN(network.STA_IF)     
      if not miRed.isconnected():              #Si no está conectado…
          miRed.active(True)                   #activa la interface
          miRed.connect(red, password)         #Intenta conectar con la red
          print('Conectando a la red', red +"…")
          timeout = time.time ()
          while not miRed.isconnected():           #Mientras no se conecte..
              if (time.ticks_diff (time.time (), timeout) > 10):
                  return False
      return True

# conexion a red wifi
if conectaWifi ("MASMELO 2.4G", "Mobiioc.59"):

    print ("Conexión exitosa!")
    cero.value(1)
    print('Datos de la red (IP/netmask/gw/DNS):', miRed.ifconfig())
     
    print("Conectando a  MQTT server... ",MQTT_BROKER,"...", end="")
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, user=MQTT_USER, password=MQTT_PASSWORD)
    client.connect()
    
    print("Conectado al Broker!")
    
    # Configure the ADC attenuation to 11dB for full range
    moisture.atten(moisture.ATTN_11DB) #Full range: 3.3v
    moisture.width(moisture.WIDTH_12BIT) #range 0 to 4095
    
while True:
    try:
        sensor.measure()
        tem = sensor.temperature()
        hum = sensor.humidity() 
        print("Tem: {}°C, Hum: {}% ".format(tem, hum))

        # Leer datos del sensor PIR
        pir_data = "Se Detecto Plaga" if motion else "SIN MOVIMIENTO"
        print("PIR: {}".format(pir_data))

        # Encender o apagar el LED según si se detectó movimiento
        if motion:
            led.value(1) # Encender el LED
            sleep(2)
            led.value(0) # Apagar el LED
            motion = False

        # Leer datos del sensor de humedad del suelo
        soil_moisture = moisture.read()
        soil_moisture_percentage = round((soil_moisture - min_moisture) * 100 / (max_moisture - min_moisture))
        print("Humedad del suelo: {}%".format(soil_moisture_percentage))

        # Publicar datos en MQTT
        message = ujson.dumps({
            "Humedad_Ambiente": hum,
            "Temperatura": tem,
            "Sensor_De_Movimiento": pir_data,
            "Humedad_Del_Suelo": soil_moisture_percentage
        })
        print("Reportando a MQTT topic {}: {}".format(MQTT_TOPIC, message))
        client.publish(MQTT_TOPIC, message)
        sleep(3)
    except OSError as e:
        print('No hay conexión')
