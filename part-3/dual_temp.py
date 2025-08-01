import aioble
import bluetooth
import asyncio
from machine import Pin
from picozero import pico_temp_sensor

led = Pin("LED", Pin.OUT)

temp_c = pico_temp_sensor.temp
temp_f = (temp_c * 9 / 5) + 32

connected = False
# Show the MAC address for the current Pico
ble = bluetooth.BLE()
ble.active(True)
_, mac_address = ble.config('mac')
formatted_mac = ':'.join(f'{b:02X}' for b in mac_address)
print(f"Bluetooth MAC Address for this device is: {formatted_mac}")
ble.active(False)
ble = None

# Define UUIDs for the service and characteristics
_SERVICE_UUID = bluetooth.UUID(0x1848)
_WRITE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)  # Central writes here
_READ_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6F)   # Peripheral writes here

IAM = "Peripheral"

MESSAGE = f"Hello from {IAM}!"

# Bluetooth parameters
BLE_NAME = f"{IAM}"  # Dynamic name for the device
BLE_SVC_UUID = _SERVICE_UUID
BLE_APPEARANCE = 0x0300
BLE_ADVERTISING_INTERVAL = 2000

# state variables
message_count = 0

def encode_message(message):
    """Encode a message to bytes."""
    return message.encode('utf-8')

def decode_message(message):
    """Decode a message from bytes."""
    return message.decode('utf-8')

async def blink_led_task():
    global connected
    toggle = True
    while True:
        led.value(toggle)
        toggle = not toggle
        blink = 1000 if connected else 250
        await asyncio.sleep_ms(blink)

async def receive_data_task(read_characteristic):
    while True:
        try:
            data = read_characteristic.read()
            if data:
                print(f"Received: {decode_message(data)}")
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

async def send_data_task(connection, write_characteristic):
    """Send data to the central device."""
    global message_count
    while True:
        message = f"{temp_f:.2f}°F"
        #print(f"Sending: {message}")

        try:
            msg = encode_message(message)
            write_characteristic.write(msg)  # Peripheral writes data here
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error while sending data: {e}")
            continue

async def run_peripheral_mode():
    """Run the peripheral mode."""
    global connected
    # Set up the Bluetooth service and characteristics
    ble_service = aioble.Service(BLE_SVC_UUID)
    
    # Characteristic for the central to write
    write_characteristic = aioble.Characteristic(
        ble_service, _WRITE_CHARACTERISTIC_UUID,
        read=True, write=True, capture=False
    )

    # Characteristic for the peripheral to write
    read_characteristic = aioble.Characteristic(
        ble_service, _READ_CHARACTERISTIC_UUID,
        read=True, write=True, capture=False
    )

    aioble.register_services(ble_service)

    print(f"{BLE_NAME} starting to advertise")

    while True:
        async with await aioble.advertise(
            BLE_ADVERTISING_INTERVAL, name=BLE_NAME, services=[BLE_SVC_UUID],
            appearance=BLE_APPEARANCE) as connection:
            connected = True
            print(f"{BLE_NAME} connected to {connection.device}")

            # Create tasks for sending and receiving data
            tasks = [
                asyncio.create_task(send_data_task(connection, read_characteristic)),
                asyncio.create_task(receive_data_task(write_characteristic)),
                asyncio.create_task(blink_led_task()),
            ]
            await asyncio.gather(*tasks)
            connected = False
            print(f"{IAM} disconnected")
            break

asyncio.run(run_peripheral_mode())


