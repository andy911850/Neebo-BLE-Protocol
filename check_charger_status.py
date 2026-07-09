import asyncio
from bleak import BleakScanner, BleakClient

WIFI_STATUS_CHAR = "0000ffb3-0000-1000-8000-00805f9b34fb"
MQTT_STATUS_CHAR = "0000ffc3-0000-1000-8000-00805f9b34fb"

async def scan_for_charger():
    print("Scanning for Neebo Base Station (NC0)...")
    devices = await BleakScanner.discover(timeout=5.0)
    for d in devices:
        if d.name == "NC0":
            return d.address
    return None

async def run():
    address = await scan_for_charger()
    if not address:
        print("Could not find the base station.")
        return

    print(f"Connecting to {address}...")
    async with BleakClient(address) as client:
        wifi_val = await client.read_gatt_char(WIFI_STATUS_CHAR)
        mqtt_val = await client.read_gatt_char(MQTT_STATUS_CHAR)
        
        print("\n=== Base Station Status ===")
        print(f"WiFi Status Code: {wifi_val[0]}")
        print(f"MQTT Status Code: {mqtt_val[0]}")
        print("===========================")

if __name__ == "__main__":
    asyncio.run(run())
