import asyncio
from bleak import BleakScanner, BleakClient
import sys

WIFI_NAME_CHAR = "0000ffb1-0000-1000-8000-00805f9b34fb"
WIFI_PASS_CHAR = "0000ffb2-0000-1000-8000-00805f9b34fb"
MQTT_ADDR_CHAR = "0000ffc1-0000-1000-8000-00805f9b34fb"
MQTT_PASS_CHAR = "0000ffc2-0000-1000-8000-00805f9b34fb"

async def scan_for_charger():
    print("Scanning for Neebo Base Station (NC0)...")
    devices = await BleakScanner.discover(timeout=10.0)
    for d in devices:
        if d.name == "NC0":
            return d.address
    return None

async def run():
    print("==================================================")
    print("      Neebo Base Station MQTT Configurator        ")
    print("==================================================\n")
    print("This script will connect to your Neebo Base Station")
    print("over Bluetooth and redirect its traffic to your")
    print("local MQTT broker.\n")
    
    wifi_ssid = input("Enter your WiFi SSID (Name): ").strip()
    wifi_pass = input("Enter your WiFi Password: ").strip()
    mqtt_addr = input("Enter your MQTT Broker IP (e.g. 192.168.1.100): ").strip()
    mqtt_pass = input("Enter your MQTT Password (leave blank if none): ").strip()

    print("\nStarting scan... (Make sure the base station is plugged in)")
    address = await scan_for_charger()
    
    if not address:
        print("\n[!] Could not find the base station.")
        print("    Ensure it is powered on and near your computer.")
        return

    print(f"\n[+] Found base station at {address}. Connecting...")
    
    try:
        async with BleakClient(address, timeout=15.0) as client:
            print("[+] Connected! Writing configuration to device...")
            
            if wifi_ssid:
                await client.write_gatt_char(WIFI_NAME_CHAR, wifi_ssid.encode('utf-8'))
                print("    -> Wrote WiFi SSID")
                
            if wifi_pass:
                await client.write_gatt_char(WIFI_PASS_CHAR, wifi_pass.encode('utf-8'))
                print("    -> Wrote WiFi Password")
                
            if mqtt_addr:
                await client.write_gatt_char(MQTT_ADDR_CHAR, mqtt_addr.encode('utf-8'))
                print("    -> Wrote MQTT Address")
                
            if mqtt_pass:
                await client.write_gatt_char(MQTT_PASS_CHAR, mqtt_pass.encode('utf-8'))
                print("    -> Wrote MQTT Password")
                
            print("\n[✓] Configuration written successfully!")
            print("The base station should now attempt to connect to your WiFi and MQTT broker.")
            print("Watch your Home Assistant Mosquitto broker logs to see it try to connect!")
            print("(Note: If the broker requires a username, we'll need to see what username the base station guesses in the logs).")
            
    except Exception as e:
        print(f"\n[X] Failed to connect or write data: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nCancelled.")
