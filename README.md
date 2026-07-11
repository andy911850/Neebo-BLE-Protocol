<p align="center">
  <img src="custom_components/neebo/logo.png" width="200" alt="Neebo Local Integration">
</p>

# Neebo Baby Monitor (Local Rescue Project)

Welcome! If you are here, you are likely a frustrated parent who woke up one day to find that your expensive Neebo baby monitor stopped working because Daatrics (the manufacturer) shut down their cloud servers. 

**Don't throw your Neebo away! The hardware still works perfectly.** 

This project was built by a fellow parent to completely rescue the Neebo ecosystem. We have successfully reverse-engineered the hardware so that it no longer relies on the cloud at all. You can now connect your Neebo directly to [Home Assistant](https://www.home-assistant.io/) (a free, private smart home system) and get all of your baby's vitals—Heart Rate, Oxygen, Temperature, and Sleep tracking—working flawlessly again, entirely locally.

---

## 📱 The Neebo Rescue iPhone App

Want a beautiful native dashboard for your iPhone that connects to this Home Assistant integration *and* supports direct Bluetooth Travel Mode when you leave the house? 

We built a custom React Native iOS application! Check out the [Neebo Rescue App repository](https://github.com/andy911850/Neebo-Rescue-App) to download and compile it for your phone.

---

## Home Assistant Integration

This custom integration is incredibly easy to install and gives you two different ways to connect your Neebo:

1. **Option A: Base Station Setup (Recommended!)**
   If you still have the egg-shaped Neebo Base Station, we highly recommend using this. The base station connects to your home WiFi, meaning you can walk anywhere in your house and the base station will quietly push your baby's vitals directly to your Home Assistant dashboard.
   
2. **Option B: Direct Bluetooth Setup**
   If you lost your base station or prefer to travel with the bracelet, Home Assistant can connect directly to the Neebo bracelet over standard Bluetooth.

---

### Step 1: Install the Integration via HACS

If you already have Home Assistant running, the easiest way to install this is through HACS (Home Assistant Community Store).

1. Open your Home Assistant dashboard and click on **HACS** in the sidebar.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Paste `https://github.com/andy911850/Neebo-BLE-Protocol` into the Repository URL field.
4. Select **Integration** as the Category and click **Add**.
5. Search for "Neebo" in HACS, click Download, and **restart Home Assistant**.

---

### Step 2: Connect Your Neebo

#### Option A: Base Station Setup (WiFi)
*This setup uses your Base Station to extend the range of the bracelet across your entire house.*

**Prerequisite:** You must have the official [Mosquitto Broker Add-on](https://github.com/home-assistant/addons/tree/master/mosquitto) installed in Home Assistant (Settings -> Add-ons).

1. Pick up your Neebo Base Station and look at the sticker on the bottom. You will see a serial number (for example, `NC1XXXX`).
2. Go to **Settings -> Add-ons -> Mosquitto broker** and click the **Configuration** tab.
3. Scroll down to the **Logins** section and click **Add**.
4. Type your exact serial number (e.g. `NC1XXXX`) as the **Username**, and type `neebo123` as the **Password**.
5. Click **Save** at the bottom right. Then go to the **Info** tab and click **Restart** to apply the new login.
6. Now, go to **Settings -> Devices & Services -> Add Integration** and search for "Neebo".
7. Select **Base Station (MQTT)** from the menu.
8. Follow the on-screen wizard! It will ask for your WiFi network and password. Once you hit submit, it will magically connect to your Base Station over Bluetooth and reprogram it to use your home WiFi!

#### Option B: Direct Bluetooth Setup (No Base Station)
*Use this if you just want to connect the bracelet directly to your Home Assistant server via Bluetooth.*

**Important:** The Neebo bracelet is very clingy! It will try to stay connected to your old mobile app. Please go into the Settings of any iPhone/Android that was previously paired with the Neebo and completely turn **OFF** Bluetooth.
1. Go to **Settings -> Devices & Services -> Add Integration** and search for "Neebo".
2. Choose **Direct Bluetooth (Bracelet)**.
3. Select your `NB0` device from the dropdown list. You're done!

---

### What Can This Integration Do?

Once connected, a new "Neebo Monitor" device will magically appear in your Home Assistant dashboard with the following live sensors:

- ❤️ **Heart Rate** (BPM)
- 💨 **Oxygen Saturation** (SpO2 %)
- 🌡️ **Temperature** (°C)
- 🔋 **Battery Level** (%)
- ✋ **Placement** (Tells you if it falls off the wrist!)
- 👶 **Activity State** (Awake, Asleep, Active, or Disconnected)

> [!TIP]
> **Want to track Hours Slept?**
> The old app used to tell you how long your baby slept. You can easily recreate this in Home Assistant! Just add a "History Stats" sensor to your `configuration.yaml` file that counts how many hours the `sensor.neebo_activity_state` is set to `Asleep` each day.

---

## For Developers: The Raw Bluetooth Protocol

If you are a developer looking to build your own mobile app or script, we have completely documented the raw Bluetooth GATT services that the Neebo uses. There is **no authentication, pairing PIN, or encryption** required to read the real-time biometric data!

The primary service UUID is `0000ffe0-0000-1000-8000-00805f9b34fb`. 

### Vitals Characteristic (Heart Rate, SpO2, Temperature)
**UUID:** `0000ffe7-0000-1000-8000-00805f9b34fb` (Notify)

When subscribed, the Neebo streams a 9-byte payload:
- **Byte 0:** Heart Rate State (0 = Valid)
- **Byte 1:** SpO2 State (0 = Valid)
- **Byte 2:** Temperature State (0 = Valid)
- **Bytes 3-4:** Heart Rate in BPM (Little Endian UInt16)
- **Bytes 5-6:** Oxygen Saturation in % (Little Endian UInt16)
- **Bytes 7-8:** Temperature in Celsius (Little Endian UInt16, divide by 10.0)

### Power Control / Standby
**UUID:** `0000ff51-0000-1000-8000-00805f9b34fb` (Write Without Response)
- Write `0x55`: **Wake Up**
- Write `0x33`: **Standby Mode** (Low power, keeps BLE active)
- Write `0x11`: **Deep Power Off** (Requires charging station to turn back on)

### Time Synchronization
**UUID:** `0000fffe-0000-1000-8000-00805f9b34fb` (Write)
- Write the current UNIX timestamp (Little Endian UInt32) upon connection to sync the hardware clock.

### Base Station Provisioning (WiFi & MQTT)
If you want to build your own tool to connect the Base Station (`NC0`) to a custom MQTT server, you must write the following characteristics over Bluetooth:
- **`0000ffb1`**: WiFi SSID (UTF-8 String)
- **`0000ffb2`**: WiFi Password (UTF-8 String)
- **`0000ffc1`**: MQTT Broker IP/Hostname (UTF-8 String)
- **`0000ffc2`**: MQTT Broker Password (UTF-8 String)

Once these are written, the base station will automatically reboot, connect to your WiFi, and authenticate with your MQTT broker using its Serial Number (e.g. `NC1XXXX`) as the Username.

### Base Station MQTT Payload
Once connected to WiFi, the base station subscribes and publishes to the MQTT broker. It streams all biometric data in real-time JSON format to the following topic:

**Topic:** `/nbo_charger/v1.0/{SERIAL_NUMBER}/get/advertising`

**Example JSON Payload:**
```json
{
  "battery": 100,
  "placement": 2,
  "activity_state": 1,
  "standby": 0,
  "vitals": [
    {
      "hr": {
        "value": 76,
        "state": 0
      }
    },
    {
      "ox": {
        "value": 99,
        "state": 0
      }
    },
    {
      "temp": {
        "value": 32.4,
        "state": 0
      }
    }
  ]
}
```
*Note: If the bracelet goes out of range or disconnects from the base station, the payload will continue to be published but the vital `value`s will change to `0` and `activity_state` will change to `14`.*

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
