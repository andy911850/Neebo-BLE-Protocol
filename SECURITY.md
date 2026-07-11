# Security Policy

## Supported Versions

Only the latest commit on the `main` branch is actively supported.

## Security Posture

### Unencrypted Bluetooth (GATT)
By manufacturer design, the Neebo hardware does not use Bluetooth pairing, authentication, or encryption. This means:
1. Anyone within Bluetooth range (~30ft) can read your baby's real-time biometric stream.
2. During the Base Station provisioning process, your Wi-Fi SSID and Password are sent over the air in cleartext.

This integration does not change or secure the underlying hardware protocol because it is impossible to do so. **Please act accordingly.**

### Home Assistant Integration
The custom component codebase itself is completely local and does not phone home to any cloud servers. 

## Reporting a Vulnerability

If you discover a vulnerability in the Python integration code that could compromise a Home Assistant instance, please report it privately before public disclosure. You can securely report issues by opening a private GitHub Security Advisory on this repository.
