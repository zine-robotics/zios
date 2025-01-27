import serial
import json
import time
import queue

serial_port = "/dev/cu.usbserial-0001"
baud_rate = 115200

class SerialInterface:
    def __init__(self, manager, port=serial_port, baud_rate=baud_rate):
        self.manager = manager
        self.port = port
        self.baud_rate = baud_rate
        self.is_connected = False
        self.data_queue = queue.Queue()

    def send_data(self, data):
        """Add data to the queue to be sent over serial."""
        if not self.is_connected:
            return
        
        print(f"Sending data to serial: {data}")
        self.data_queue.put(data)

    def start(self):
        """Main loop for handling serial communication."""
        try:
            with serial.Serial(self.port, self.baud_rate, timeout=1) as ser:
                self.is_connected = True
                print(f"Connected to serial port {self.port} at {self.baud_rate} baud")

                while self.manager.running:
                    # Read from serial if data is available
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8').strip()
                        try:
                            data = json.loads(line)
                            if data.get('succ', False):
                                self.manager.process_serial_data(data)
                            else:
                                print(f"Error received from serial: {data}")
                        except json.JSONDecodeError:
                            print(f"Invalid JSON received: {line}")

                    # Write to serial if there's data in the queue
                    if not self.data_queue.empty():
                        data = self.data_queue.get()
                        json_data = json.dumps(data)
                        ser.write((json_data + '\n').encode('utf-8'))

                    # Sleep to prevent high CPU usage
                    time.sleep(0.1)
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        finally:
            self.is_connected = False
            print("Serial connection closed.")

