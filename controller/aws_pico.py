# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# AWS IoT Core - RPi Pico W Demo

# Required imports
import time
import machine
import network
import ujson
import ubinascii
from umqtt.simple import MQTTClient


# DHT11
from dht import DHT11

# Sensor setup
sensor = DHT11(Pin(16, Pin.OUT, Pin.PULL_DOWN))

# Pump setup
motor1A = Pin(14, Pin.OUT)
motor2A = Pin(15, Pin.OUT)

# Water level sensor setup
water_level = ADC(28)
 

# AWS IoT Core publish topic
PUB_TOPIC = b'sensor/data'
# AWS IoT Core subscribe  topic
SUB_TOPIC = b'/' + CLIENT_ID + '/light'



DEV_KEY = "private.pem.key"
DEV_CRT = "certificate.pem.crt"

# Define light (Onboard Green LED) and set its default state to off
light = machine.Pin("LED", machine.Pin.OUT)
light.off()


# Wifi Connection Setup
def wifi_connect():
    print('Connecting to wifi...')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASS)
    while wlan.isconnected() == False:
        light.on()
        print('Waiting for connection...')
        time.sleep(0.5)
        light.off()
        time.sleep(0.5)
    print('Connection details: %s' % str(wlan.ifconfig()))

def get_water_level():
    # Example conversion for water level sensor, adjust the formula as needed
    raw = water_level.read_u16()
    # Example conversion, adjust according to your sensor
    level = (raw / 65535) * 100  # Convert to percentage
    return level

def pumping(state):
    if state == "on":
        print("hi")
        motor1A.high()
        motor2A.low()
    else:
        print("bye")
        motor1A.low()
        motor2A.low()


# Callback function for all subscriptions
def mqtt_subscribe_callback(topic, msg):
    print("Received topic: %s message: %s" % (topic, msg))
    if topic == SUB_TOPIC:
        mesg = ujson.loads(msg)
        if 'state' in mesg.keys():
            if mesg['state'] == 'on' or mesg['state'] == 'ON' or mesg['state'] == 'On':
                pumping("on")
                print('Pumping is ON')
            else:
                pumping("off")
                print('Pumping is OFF')


# Read current temperature from RP2040 embeded sensor
def get_rpi_temperature():
    sensor = machine.ADC(4)
    voltage = sensor.read_u16() * (3.3 / 65535)
    temperature = 27 - (voltage - 0.706) / 0.001721
    return temperature


def read_pem(file):
    with open(file, "r") as input:
        test = input.read().strip()
        split_test = test.split("\n")
        base64_text = "".join(split_test[1:-1])
        return ubinascii.a2b_base64(base64_text)

# Connect to wifi
wifi_connect()

# Set AWS IoT Core connection details
mqtt = MQTTClient(
    client_id=CLIENT_ID,
    server=AWS_ENDPOINT,
    port=8883,
    keepalive=5000,
    ssl=True,
    ssl_params={'key':read_pem(DEV_KEY), 'cert':read_pem(DEV_CRT), 'server_side':False})

# Establish connection to AWS IoT Core
mqtt.connect()

# Set callback for subscriptions
mqtt.set_callback(mqtt_subscribe_callback)

# Subscribe to topic
mqtt.subscribe(SUB_TOPIC)


# Main loop - with 5 sec delay
while True:
    sensor.measure()  # Trigger a measurement for DHT11
    temperature = sensor.temperature()  # Get temperature from DHT11
    humidity = sensor.humidity()  # Get humidity from DHT11
    water_level = get_water_level()  # Get water level from ADC
    current_time = time.localtime()  # Get the current time
    date_string = "{year}-{month}-{day}".format(year=current_time[0], month=current_time[1], day=current_time[2])
    
    # Format the message as a JSON string
    message = ujson.dumps({
        "temperature": temperature,
        "water_level": water_level,
        "humidity": humidity,
        "date": date_string
    })
    
    # Convert the message to bytes
    message_bytes = message.encode('utf-8')
    
    print('Publishing topic %s message %s' % (PUB_TOPIC, message_bytes))
    mqtt.publish(topic=PUB_TOPIC, msg=message_bytes, qos=0)

    # Check subscriptions for message
    mqtt.check_msg()
    time.sleep(5)

