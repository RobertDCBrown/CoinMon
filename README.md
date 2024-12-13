# Coin Dispenser Monitor

A Raspberry Pi Pico W project that monitors coin dispenser status using voltage readings and sends notifications via email and SMS.

## Hardware Requirements

- Raspberry Pi Pico W
- Coin Dispenser with voltage output (0-3.3V) (Resistors can be used to drop voltage to a safe ammount for the Pico)
- Jumper wires

## Wiring

- Connect coin dispenser voltage output to GP26 (ADC0)
- Connect coin dispenser ground to Pico GND
- The onboard LED will indicate status:
  - LED ON = Low on coins (High voltage)
  - LED OFF = Coins OK (Low voltage)

## Features

- Real-time voltage monitoring using ADC
- Email notifications via SMTP server
- SMS notifications via Twilio
- Web interface for status monitoring
- Onboard LED status indicator
- Automatic time synchronization

## Configuration

### secrets.py
Create a `secrets.py` file with the following credentials:
```python
# WiFi Settings
SSID = 'your_wifi_ssid'
PASSWORD = 'your_wifi_password'

# Device Information
DEVICE = 'Coin Machine 1'
LOCATION = '12345 Main Street'

# SMTP Settings
SMTP_SERVER = 'SMTPserver'
SMTP_PORT = 465
SMTP_USERNAME = 'your_email@domain.com'
SMTP_PASSWORD = 'your_smtp_password'
SMTP_TO_EMAIL = 'recipient@domain.com'

# Twilio Settings
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_FROM_NUMBER = '+1234567890'  # Your Twilio number
TWILIO_TO_NUMBER = '+1234567890'    # Recipient number
```

## Operation

1. The system continuously monitors the voltage on GP26
2. Voltage thresholds:
   - Above 2.5V = Low on coins (needs refill)
   - Below 2.5V = Coins OK
3. When the status changes:
   - Sends email notification
   - Sends SMS notification
   - Updates LED status
   - Updates web interface

## Web Interface

Access the web interface by navigating to the Pico W's IP address in a web browser. The interface shows:
- Current voltage reading
- Status message
- Last update time

## Notifications

### Email Format
```
Subject: [Device Name] Status Alert

Device: Coin Machine 1
Location: 12345 Main Street
Time: [current time]

[Status Message]
Voltage Reading: X.XXV
```

### SMS Format
```
[Device Name] - [Location]
Time: [current time]
[Status Message]
Voltage Reading: X.XXV
```

## Troubleshooting

1. LED not working:
   - Check if Pico W is powered
   - Verify code is running

2. No notifications:
   - Check WiFi credentials
   - Verify email/SMS credentials
   - Check internet connection

3. Incorrect readings:
   - Verify voltage connection to GP26
   - Check ground connection
   - Calibrate voltage threshold if needed

## Dependencies

- MicroPython libraries:
  - network
  - machine
  - umail
  - urequests
  - ubinascii (for Twilio auth)

## Updates and Maintenance

- Monitor voltage readings periodically
- Check notification delivery
- Update credentials if needed
- Adjust voltage threshold if required
