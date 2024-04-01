from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from personal_arguments import DEV_CRT, DEV_KEY, AWS_ENDPOINT, CA_CERT, CLIENT_ID
import time
import json
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import queue
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import collections


# Simulated sensor IDs
sensor_ids = [f'sensor_{i + 1}' for i in range(100)]
plant_ids = [f'plant_{i + 1}' for i in range(100)]
sensor_windows = {}

# Initialize a dictionary of queues for thread-safe data transfer, one for each sensor
sensor_queues = {}

# Dictionaries to store data for each sensor
data_store = {
    'timestamps': {},
    'temperatures': {},
    'humidities': {},
    'water_levels': {}
}

# Custom MQTT message callback function
def customCallback(client, userdata, message):
    # Parse the message payload and enqueue it
    global data_store
    payload = json.loads(message.payload)
    plant_id = payload['plant_id']

    if plant_id not in data_store:
        # Initialize storage for a new sensor
        data_store[plant_id] = {
            'timestamps': collections.deque(maxlen=50),
            'temperatures': collections.deque(maxlen=50),
            'humidities': collections.deque(maxlen=50),
            'water_levels': collections.deque(maxlen=50)
        }

    # Update data for the sensor
    # timestamp = datetime.strptime(payload['time'], "%a %b %d %H:%M:%S %Y")
    data_store[plant_id]['timestamps'].append(datetime.strptime(payload['time'], "%a %b %d %H:%M:%S %Y"))
    data_store[plant_id]['temperatures'].append(payload['temperature'])
    data_store[plant_id]['humidities'].append(payload['humidity'])
    data_store[plant_id]['water_levels'].append(payload['water_level'])


# Replace with your AWS IoT endpoint, client ID, and paths to your certificates and private key
myMQTTClient = AWSIoTMQTTClient(CLIENT_ID)
myMQTTClient.configureEndpoint(AWS_ENDPOINT, 8883)
myMQTTClient.configureCredentials(CA_CERT, DEV_KEY, DEV_CRT)

# Connect and subscribe to AWS IoT
myMQTTClient.connect()
myMQTTClient.subscribe("sensor/data", 1, customCallback)


def fetch_latest_sensor_data(plant_id):
    """Simulate fetching the latest sensor data."""
    global data_store
    # Extract data
    # sensor_id = payload['sensor_id']
    # temperature = payload['temperature']
    # humidity = payload['humidity']
    water_level = data_store[plant_id]['water_levels']
    timestamp = data_store[plant_id]['timestamps']

    # timestamps = np.arange(10)
    # values = np.random.rand(10) * 100  # Simulate data as an example
    return timestamp, water_level

# def update_plot(sensor_id, fig, ax, canvas):
#     """Simulate updating the plot with new data."""
#     timestamps, values = fetch_latest_sensor_data(sensor_id)
#     ax.clear()  # Clear the existing plot
#     ax.plot(timestamps, values, marker='o', linestyle='-')  # Plot new data
#     ax.set_title(f"{sensor_id} Data")
#     ax.set_xlabel("Time")
#     ax.set_ylabel("Value")
#     canvas.draw()  # Redraw the canvas with the new plot
#     sensor_windows[sensor_id].after(1000, update_plot, sensor_id, fig, ax, canvas)


def update_plot(plant_id, fig, axs, canvas):
    global data_store

    # Define the function to format the x-axis to prevent overlap for upper plots
    def format_ax(ax, ylabel):
        ax.clear()  # Clear the existing plot
        ax.set_ylabel(ylabel)
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)  # Hide x-axis labels for upper plots

    # Define the function to format the x-axis to prevent overlap for the bottom plot
    def format_bottom_ax(ax, xlabel, ylabel):
        ax.clear()  # Clear the existing plot
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis='x', rotation=45)  # Rotate x-axis labels to prevent overlap

        #ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M:%S'))

    temperatures = data_store[plant_id]['temperatures']
    humidities = data_store[plant_id]['humidities']
    water_levels = data_store[plant_id]['water_levels']
    timestamps = data_store[plant_id]['timestamps']

    fig.suptitle(f"{plant_id} Data", fontsize='large')

    # Plot temperatures
    format_ax(axs[0], 'Temperature (°C)')
    axs[0].plot(timestamps, temperatures, marker='o', linestyle='-')

    # Plot humidities
    format_ax(axs[1], 'Humidity (%)')
    axs[1].plot(timestamps, humidities, marker='o', linestyle='-')

    # Plot water levels
    format_bottom_ax(axs[2], 'Time', 'Water Level (%)')
    axs[2].plot(timestamps, water_levels, marker='o', linestyle='-')

    # Adjust subplot spacing to prevent overlap
    plt.subplots_adjust(hspace=0.4, bottom=0.15)
    fig.autofmt_xdate()  # Auto format x-axis labels to fit and prevent overlap

    canvas.draw()  # Redraw the canvas with the new plot

    # Assuming sensor_windows is a dictionary that holds Tkinter windows, and after is a method to schedule updates
    sensor_windows[plant_id].after(1000, update_plot, plant_id, fig, axs, canvas)


def show_sensor_data(plant_id):
    if plant_id in sensor_windows:
        return  # Window already open for this sensor

    # Create a new window for the sensor data
    sensor_window = tk.Toplevel(root)
    sensor_window.title(f"Data for {plant_id}")
    sensor_windows[plant_id] = sensor_window

    # Ensure the window is removed from the tracking dict when closed
    sensor_window.protocol("WM_DELETE_WINDOW",
                           lambda sid=plant_id: (sensor_window.destroy(), sensor_windows.pop(sid, None)))

    # Create a Matplotlib figure and axes
    fig, axs = plt.subplots(3, 1)
    canvas = FigureCanvasTkAgg(fig, master=sensor_window)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Button to close the sensor data window
    ttk.Button(sensor_window, text="Return",
               command=lambda sid=plant_id: (sensor_window.destroy(), sensor_windows.pop(sid, None))).pack(
        side=tk.BOTTOM)

    # Start periodic update of the plot
    update_plot(plant_id, fig, axs, canvas)


try:
    while True:
        # Main Tkinter window

        root = tk.Tk()
        root.title("Sensor Data Viewer")
        # Set Geometry(widthxheight)
        root.geometry('500x500')
        # Create a Canvas and a Scrollbar
        canvas = tk.Canvas(root)
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)

        # Create a frame inside the canvas
        scrollable_frame = ttk.Frame(canvas)

        # Link a scrollable region with the scrollable frame
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        # Create a window inside the canvas that contains the scrollable_frame
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack the scrollbar to the right and fill in the y-direction
        scrollbar.pack(side="right", fill="y")
        # Pack the canvas to expand and fill in both directions
        canvas.pack(side="left", fill="both", expand=True)

        # Create style Object
        style = ttk.Style()

        style.configure('TButton', font=
        ('calibri', 20, 'bold'),
                        borderwidth='4')

        style.map('TButton', foreground=[('active', '!disabled', 'green')],
                  background=[('active', 'black')])

        # Generate a button for each sensor
        for plant_id in plant_ids:
            ttk.Button(scrollable_frame, text=plant_id, command=lambda sid=plant_id: show_sensor_data(sid)).pack()


        # Function to handle mouse scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


        # Bind the mousewheel event to the canvas
        canvas.bind_all("<MouseWheel>", _on_mousewheel)


        root.mainloop()
except KeyboardInterrupt:
    print("Disconnecting...")
    myMQTTClient.disconnect()
    plt.close('all')


