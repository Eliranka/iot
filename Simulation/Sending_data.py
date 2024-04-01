import paho.mqtt.client as mqtt
from personal_arguments import DEV_CRT, DEV_KEY, AWS_ENDPOINT, CA_CERT, CLIENT_ID
import ssl
import time
import json
import random


def generate_sensor_ids(number_of_sensors):
    # Generate sensor IDs starting from 1
    plant_ids = [f'plant_{i + 1}' for i in range(number_of_sensors)]
    return plant_ids


number_of_sensors = 100
plant_ids = generate_sensor_ids(number_of_sensors)
print("Sensor IDs:", plant_ids)

# MQTT topic to publish the temperature readings
MQTT_TOPIC = "sensor/data"
MQTT_TOPIC_COMMAND = "sensor/command"
# Define sensor ranges
temperature_range = (23, 24)  # Celsius
humidity_range = (60, 61)  # Percentage
water_level_range = (33000, 36000)  # Percentage


# Functions to be called based on the received command
def turn_pump_on():
    print("Turning the pump on.")
    time.sleep(5)


def low_temp():
    print("Temperature is low.")


def high_temp():
    print("Temperature is high.")


def change_humidity():
    print("Changing humidity levels.")


# Callback when connecting to the MQTT server
def on_connect(client, userdata, flags, rc, arg):
    print("Connected with result code " + str(rc))
    client.subscribe(MQTT_TOPIC_COMMAND)


# Callback when a message is received from the server
def on_message(client, userdata, msg):
    message = msg.payload.decode()
    if message.isdigit():
        message = int(message)
        if message == 1:
            turn_pump_on()
            time.sleep(5)
        elif message == 21:
            low_temp()
            time.sleep(5)
        elif message == 22:
            high_temp()
            time.sleep(5)
        elif message == 3:
            change_humidity()
            time.sleep(5)
        else:
            print(f"Received unknown command: {message}")
    else:
        print(f"Received non-numeric message: {message}")


# Initialize MQTT client for AWS
aws_mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
aws_mqtt_client.tls_set(ca_certs=CA_CERT,
                        certfile=DEV_CRT,
                        keyfile=DEV_KEY,
                        cert_reqs=ssl.CERT_REQUIRED,
                        tls_version=ssl.PROTOCOL_TLSv1_2,
                        ciphers=None)
aws_mqtt_client.on_connect = on_connect
aws_mqtt_client.on_message = on_message

aws_mqtt_client.connect(AWS_ENDPOINT, 8883, 60)

# Initialize MQTT client for mqtt-dashboard.com
dashboard_mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_server = 'mqtt-dashboard.com'
port = 1883  # Update with the port number provided by mqtt-dashboard.com if different
dashboard_mqtt_client.connect(mqtt_server, port, 60)

# Start the loop for both clients
aws_mqtt_client.loop_start()
dashboard_mqtt_client.loop_start()

try:
    while True:
        for plant_id in plant_ids:
            sensor_data = json.dumps({
                "plant_id": plant_id,
                "temperature": random.uniform(*temperature_range),
                "humidity": random.uniform(*humidity_range),
                "water_level": random.uniform(*water_level_range),
                "time": time.ctime()
            })
            # Publish to AWS IoT Core
            aws_mqtt_client.publish(MQTT_TOPIC, sensor_data)
            # Publish to mqtt-dashboard.com
            dashboard_mqtt_client.publish(MQTT_TOPIC, sensor_data)

            print(f"Published to AWS and mqtt-dashboard.com: {sensor_data}")

        # Wait before publishing the next set of readings
        time.sleep(2)
except KeyboardInterrupt:
    print("Interrupted by user, stopping...")
finally:
    # Stop the loop and disconnect cleanly from both clients
    aws_mqtt_client.loop_stop()
    aws_mqtt_client.disconnect()
    dashboard_mqtt_client.loop_stop()
    dashboard_mqtt_client.disconnect()

print("Finished publishing sensor readings.")
