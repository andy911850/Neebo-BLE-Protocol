# Neebo BLE Protocol Documentation

This repository documents the reverse-engineered Bluetooth Low Energy (BLE) protocol for the Neebo baby wellness monitor. 

After Daatrics (the manufacturer) shut down their cloud services, the official mobile applications ceased to function, rendering the hardware effectively useless for many users. However, the device itself still functions locally and broadcasts its data over standard BLE.

This documentation allows anyone to connect to their Neebo locally without the cloud and integrate it into smart home systems like Home Assistant.

## Home Assistant Integration (HACS)

This repository includes a **fully-native Home Assistant integration** that supports two distinct connection modes:
1. **Direct Bluetooth:** Connects directly to the Neebo Bracelet via Home Assistant's Bluetooth proxy.
2. **Base Station (MQTT):** (Recommended) Provisions the official Neebo Base Station to connect to your WiFi and push data to your local MQTT broker seamlessly.

### Installation & Setup

1. Open Home Assistant and go to **HACS**.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Paste `https://github.com/andy911850/Neebo-BLE-Protocol` into the Repository URL field.
4. Select **Integration** as the Category and click Add.
5. Search for "Neebo" in HACS, click Download, and restart Home Assistant.

### Option A: Base Station Setup (MQTT)
If you own the Neebo Base Station, you can use it to massively extend the range of the bracelet (since the base station communicates over WiFi).

**Prerequisite:** You must have the [Mosquitto Broker Add-on](https://github.com/home-assistant/addons/tree/master/mosquitto) installed in Home Assistant.
1. Look at the sticker on the bottom of your Neebo Base Station. You will see a serial number (e.g., `NC1XXXX`).
2. Open the Mosquitto Broker Add-on configuration in Home Assistant.
3. Under the **Logins** section, click **Add**.
4. Enter your serial number exactly as it appears (e.g. `NC1XXXX`) as the **Username**, and choose a **Password** (e.g. `neebo123`).
5. Click **Save** at the bottom right, go to the Info tab, and **Restart** the Mosquitto Add-on.
6. Go to **Settings -> Devices & Services -> Add Integration** and search for "Neebo".
7. Choose **Base Station (MQTT)** and follow the UI wizard to provision your base station!

### Option B: Direct Bluetooth Setup
If you do not have a base station, or prefer a direct BLE connection:
1. Turn **OFF** Bluetooth on any smartphone that was previously paired with the device.
2. Go to **Settings -> Devices & Services -> Add Integration** and search for "Neebo".
3. Choose **Direct Bluetooth (Bracelet)** and select your `NB0` device from the list.

The integration automatically creates sensors for **Heart Rate, SpO2, Temperature, Battery, and Placement**, as well as a switch to toggle **Standby Mode**!

---
## Pairing & Connection

**Important:** The Neebo monitor maintains an aggressive connection with the official mobile app if your phone is nearby and Bluetooth is enabled. 
To discover and connect to the Neebo from a third-party client:
1. Turn **OFF** Bluetooth on any smartphone that was previously paired with the device (do this from the Settings menu, not just the Control Center).
2. The Neebo will immediately begin advertising locally as `NB0`.
3. You can now connect to its MAC address.

> **Authentication:** There is **no authentication, pairing PIN, or encryption** required to read the real-time biometric data. The vitals are broadcast in plain text to any connected client that subscribes to the characteristic notifications.

---

## GATT Services & Characteristics

The primary service UUID for Neebo data is `0000ffe0-0000-1000-8000-00805f9b34fb`. 

### Vitals (Heart Rate, SpO2, Temperature)
**Characteristic:** `0000ffe7-0000-1000-8000-00805f9b34fb` (Notify)

When subscribed to this characteristic, the Neebo streams a 9-byte payload containing the live vitals.
- **Byte 0:** Heart Rate State (0 = Valid)
- **Byte 1:** SpO2 State (0 = Valid)
- **Byte 2:** Temperature State (0 = Valid)
- **Bytes 3-4:** Heart Rate in BPM (Little Endian UInt16)
- **Bytes 5-6:** Oxygen Saturation in % (Little Endian UInt16)
- **Bytes 7-8:** Temperature in Celsius (Little Endian UInt16, divide by 10.0)

*Example Payload:* `00 00 00 4C 00 63 00 44 01`
- HR: `0x004C` = 76 bpm
- SpO2: `0x0063` = 99%
- Temp: `0x0144` = 324 -> 32.4°C

### Battery Level
**Service:** `0000180f-0000-1000-8000-00805f9b34fb` (Standard Battery Service)
**Characteristic:** `00002a19-0000-1000-8000-00805f9b34fb` (Read/Notify)
- **Byte 0:** Battery percentage (0-100)

### Placement (On/Off Wrist)
**Characteristic:** `0000ffe4-0000-1000-8000-00805f9b34fb` (Notify)
- **Byte 0:** Status (`0x02` = On Wrist, `0x00` = Off Wrist)

### Power Control / Standby
**Characteristic:** `0000ff51-0000-1000-8000-00805f9b34fb` (Write Without Response)

You can control the power state of the Neebo by writing a single byte to this characteristic:
- Write `0x55`: **Wake Up / Power On** (Resumes normal monitoring)
- Write `0x33`: **Standby Mode** (Lowest power consumption, BLE remains active to wake it up later)
- Write `0x11`: **Deep Power Off** (Turns the device completely off. It can *only* be turned back on by placing it on the charging station).

### Time Synchronization
**Characteristic:** `0000fffe-0000-1000-8000-00805f9b34fb` (Write)
- The official app writes the current UNIX timestamp (Little Endian UInt32) to this characteristic upon connection to sync the hardware clock.

### Audio Stream (Listen Feature)
**Characteristic:** `0000ffa1-0000-1000-8000-00805f9b34fb` (Notify)
- When the audio streaming mode is activated, the Neebo streams compressed raw audio data in rapid 20-byte payloads over this characteristic. The first byte acts as a looping sequence number (`0x18` to `0x1F`).

### Device Information
**Service:** `0000180a-0000-1000-8000-00805f9b34fb`
- `00002a29`: Manufacturer Name String (Daatrics ltd)
- `00002a24`: Model Number String
- `00002a26`: Firmware Revision String
- `00002a27`: Hardware Revision String

---
## Legal Disclaimer & Terms of Use

> [!WARNING]
> **Not a Medical Device**
> The hardware, software, and documentation provided in this repository are for educational, research, and hobbyist purposes only. This project is **not** a medical device, nor is it intended to be used for the diagnosis, cure, mitigation, treatment, or prevention of any disease or medical condition (including SIDS). Do not rely on this project or the Neebo hardware for life-saving or medical monitoring.

> [!CAUTION]
> **No Warranty or Liability**
> This project is provided "AS IS", without warranty of any kind, express or implied. The authors and contributors of this repository shall not be held liable for any damages, injury, or loss of life arising from the use or misuse of this software or the associated hardware. By using this software, you agree to assume all risks associated with its use.

> [!NOTE]
> **Trademarks & Affiliation**
> This repository is not affiliated with, endorsed by, or sponsored by Daatrics Ltd. "Neebo" and related trademarks are the property of their respective owners. This project was created to restore local functionality to abandoned hardware after the manufacturer's cloud services ceased operations.
