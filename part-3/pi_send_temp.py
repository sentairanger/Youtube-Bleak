import asyncio
from bleak import BleakClient, uuids
from gpiozero import LED, CPUTemperature

connected = False

led = LED(17)
cpu = CPUTemperature()
temp = cpu.temperature
temp_f = round(temp * 9 / 5 + 32, 2)

# Replace with the MAC address of your Raspberry Pi Pico W
pico_address = "28:CD:C1:08:4E:39"  # Update this with your Pico W's address
# pico_address = "D8:3A:DD:8D:CF:DE"

# Service UUID (0x1848) - but we need to normalize it to 128-bit UUID
SERVICE_UUID = uuids.normalize_uuid_16(0x1848)
WRITE_CHARACTERISTIC_UUID = uuids.normalize_uuid_16(0x2A6E) # Central writes here
READ_CHARACTERISTIC_UUID = uuids.normalize_uuid_16(0x2A6F)  # Central reads here

async def send_data_task(client):
    """Send data to the peripheral device."""
    message = f"{temp_f}".encode("utf-8")
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
