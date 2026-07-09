import asyncio
import struct
from bleak import BleakClient

ADDRESS = "<YOUR_MAC_ADDRESS>"

# The characteristics we actually care about (Vitals and Activity)
NOTIFY_CHARS = [
    "0000ffe7-0000-1000-8000-00805f9b34fb", # Vitals (HR, SpO2, Temp)
    "0000ffea-0000-1000-8000-00805f9b34fb", # Activity Status
    "0000ffe4-0000-1000-8000-00805f9b34fb", # Placement (On/Off wrist)
]

def decode_vitals(data):
    if len(data) >= 9:
        # Byte 0: HR state, Byte 1: SpO2 state, Byte 2: Temp state
        hr_state = data[0]
        ox_state = data[1]
        temp_state = data[2]
        
        # Bytes 3-4: Heart Rate (Little Endian uint16)
        # Bytes 5-6: Oxygen (Little Endian uint16)
        # Bytes 7-8: Temperature (Little Endian uint16) / 10.0
        hr_val, ox_val, temp_val = struct.unpack_from('<HHH', data, 3)
        temp_c = temp_val / 10.0
        
        print(f"[VITALS] ❤️  HR: {hr_val} bpm  |  💨 SpO2: {ox_val}%  |  🌡️  Temp: {temp_c}°C")

def decode_placement(data):
    if len(data) >= 1:
        status = data[0]
        if status == 2:
            print("[PLACEMENT] 👶 Neebo is ON the wrist!")
        elif status == 0:
            print("[PLACEMENT] 📭 Neebo is OFF the wrist!")
        else:
            print(f"[PLACEMENT] Status: {status}")

def decode_activity(data):
    if len(data) >= 2:
        val = struct.unpack_from('<H', data, 0)[0]
        time_active = val & 0x0FFF
        state = (val & 0xF000) >> 12
        print(f"[ACTIVITY] State: {state} | Time: {time_active}")

def handle_notify(sender, data):
    uuid_short = str(sender).split('-')[0].upper()
    
    if "FFE7" in uuid_short:
        decode_vitals(data)
    elif "FFE4" in uuid_short:
        decode_placement(data)
    elif "FFEA" in uuid_short:
        decode_activity(data)

async def run():
    print(f"Connecting to Neebo ({ADDRESS})...")
    async with BleakClient(ADDRESS) as client:
        print("Connected! Subscribing to Vitals streams...")
        for char_uuid in NOTIFY_CHARS:
            try:
                await client.start_notify(char_uuid, handle_notify)
            except Exception as e:
                print(f"  [X] Could not subscribe to {char_uuid.split('-')[0]}: {e}")
        
        print("\n=======================================================")
        print(" Listening for decoded vitals... (Press Ctrl+C to stop) ")
        print("=======================================================\n")
        
        while True:
            await asyncio.sleep(1.0)

if __name__ == "__main__":
    asyncio.run(run())
