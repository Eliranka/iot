import time
from machine import Pin, ADC
from umqtt.simple import MQTTClient
import json
import random

# DHT11
from dht import DHT11

# Sensor setup
sensor = DHT11(Pin(16, Pin.OUT, Pin.PULL_DOWN))

# Pump setup
motor1A = Pin(14, Pin.OUT)
motor2A = Pin(15, Pin.OUT)

# Water level sensor setup
water_level = ADC(28)

# MQTT Broker Setup
mqtt_server = 'mqtt-dashboard.com'
client_id = 'Eliran'
# publish_topic = b'sensor/data'  # Topic to publish sensor data
# control_topic = b'pump/control'  # Topic to subscribe for pump control commands
publish_topic = b'Test'
control_topic = b'Test11'  # Topic to subscribe for ending the loop

# Initialize MQTT client and connect
client = MQTTClient(client_id, mqtt_server)
client.connect()


def pumping(state):
    if state == "on":
        print("hi")
        motor1A.high()
        motor2A.low()
    else:
        print("bye")
        motor1A.low()
        motor2A.low()


def mqtt_callback(topic, msg):
    print("Received message '{}' on topic '{}'".format(msg, topic))
    try:
        msg = msg
        print(msg)
        if msg == b"1":
            pumping("on")
        elif msg == b"0":
            pumping("off")
    except ValueError:
        print("Message decoding failed")


client.set_callback(mqtt_callback)
client.subscribe(control_topic)


def publish_sensor_data():
    # sensor.measure()
    data = {
        "temperature": sensor.temperature,
        "humidity": sensor.humidity,
        "water_level": water_level.read_u16()
        "date":  time.localtime()  
    }
    client.publish(publish_topic, json.dumps(data))


def main():
    print("Starting sensor data transmission")
    while True:
        publish_sensor_data()
        client.check_msg()  # Check for new messages on subscribed topics
        time.sleep(2)


try:
    main()
except KeyboardInterrupt:
    print('Interrupted')
finally:
    client.disconnect()
    print("Disconnected from MQTT.")
