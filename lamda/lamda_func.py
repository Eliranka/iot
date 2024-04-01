import json
import boto3

# Define the AWS IoT Core endpoint
# You should replace 'your-endpoint' with your actual AWS IoT Core endpoint
AWS_IOT_ENDPOINT = "your-endpoint.iot.your-region.amazonaws.com"

# Define the MQTT topic to publish the command messages
COMMAND_TOPIC = "sensor/command"

# Define min and max values for each parameter
WATER_LEVEL_RANGE = (33000, 36000)  # Example range
TEMP_RANGE = (23, 24)  # Example range
HUMIDITY_RANGE = (60, 61)  # Example range

# Initialize the boto3 IoT Data Plane client
iot_client = boto3.client('iot-data', endpoint_url=f'https://{AWS_IOT_ENDPOINT}')

def lambda_handler(event, context):
    # Extract the sensor data from the event
    water_level = event.get('water_level')
    temp = event.get('temp')
    humidity = event.get('humidity')

    messages_to_publish = []

    # Check water level
    if not WATER_LEVEL_RANGE[0] <= water_level <= WATER_LEVEL_RANGE[1]:
        messages_to_publish.append(1)  # Assuming 1 is the command for adjusting water level

    # Check temperature
    if temp < TEMP_RANGE[0]:
        messages_to_publish.append("21")  # Command for low temp
    elif temp > TEMP_RANGE[1]:
        messages_to_publish.append("22")  # Command for high temp

    # Check humidity
    if not HUMIDITY_RANGE[0] <= humidity <= HUMIDITY_RANGE[1]:
        messages_to_publish.append("3")  # Assuming "3" is also used for adjusting humidity

    # Publish messages for each condition that's not met
    for message in messages_to_publish:
        publish_command(message)

    return {
        'statusCode': 200,
        'body': json.dumps('Processed sensor data successfully.')
    }

def publish_command(command):
    """Publishes a command message to the AWS IoT Core topic."""
    response = iot_client.publish(
        topic=COMMAND_TOPIC,
        qos=1,
        payload=json.dumps({"command": command})
    )
    return response
