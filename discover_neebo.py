import asyncio
import sys
from bleak import BleakClient

# The UUID macOS assigned to the "NB0" device
ADDRESS = "<YOUR_MAC_ADDRESS>"

async def run(address):
    print(f"Attempting to connect to {address}...")
    try:
        async with BleakClient(address, timeout=15.0) as client:
            print(f"Connected: {client.is_connected}")
            
            print("Fetching services...")
            services = client.services
            
            for service in services:
                print(f"\n[Service] {service.uuid}: {service.description}")
                for char in service.characteristics:
                    print(f"  └─ [Characteristic] {char.uuid} ({','.join(char.properties)}): {char.description}")
                    # If it's readable, try to read the initial value
                    if "read" in char.properties:
                        try:
                            value = await client.read_gatt_char(char.uuid)
                            print(f"       Value: {value.hex()} | String: {value.decode('utf-8', errors='ignore')}")
                        except Exception as e:
                            print(f"       Read Error: {e}")
                            
    except Exception as e:
        print(f"Failed to connect or discover: {e}")

if __name__ == "__main__":
    asyncio.run(run(ADDRESS))
