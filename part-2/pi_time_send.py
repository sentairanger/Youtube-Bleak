import asyncio
from bleak import BleakClient, uuids
from gpiozero import LED
import time

now = time.localtime()
today = time.strftime("%Y-%m-%d %H:%M:%S", now)
connected = False

led = LED(17)

# Replace with the MAC address of your Raspberry Pi Pico W
pico_address = "28:CD:C1:08:4E:39C"  # Update this with your Pico W's address
# pico_address = "D8:3A:DD:8D:CF:DE"

# Service UUID (0x1848) - but we need to normalize it to 128-bit UUID
SERVICE_UUID = uuids.normalize_uuid_16(0x1848)
WRITE_CHARACTERISTIC_UUID = uuids.normalize_uuid_16(0x2A6E) # Central writes here
READ_CHARACTERISTIC_UUID = uuids.normalize_uuid_16(0x2A6F)  # Central reads here

async def send_data_task(client):
    """Send data to the peripheral device."""
    message = today.encode("utf-8")
    while True:
        # print(f"Central sending: {message}")
        await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, message)
        await asyncio.sleep(2)

async def receive_data_task(client):
    """Receive data from the peripheral device."""
    while True:
        try:
            # print("Central waiting for data from peripheral...")
            response = await client.read_gatt_char(READ_CHARACTERISTIC_UUID)
            print(f"Central received: {response.decode('utf-8')}")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

async def blink_task():
    global connected 
    print("blink task started")
    toggle = True 
    while True:
        if toggle:
            led.on() 
        else:
            led.off()
        toggle = not toggle 
        blink = 1000  if connected else 250
        await asyncio.sleep(blink / 1000)

async def connect_and_communicate(address):
    global connected
    """Connect to the peripheral and manage data exchange."""
    print(f"Connecting to {address}...")

    async with BleakClient(address) as client:
        connected = client.is_connected
        print(f"Connected: {connected}")

        # Create tasks for sending and receiving data
        tasks = [
            asyncio.create_task(send_data_task(client)),
            asyncio.create_task(receive_data_task(client)),
            asyncio.create_task(blink_task())
        ]
        await asyncio.gather(*tasks)
    connected = False

# Run the connection and communication
loop = asyncio.get_event_loop()
loop.run_until_complete(connect_and_communicate(pico_address))
