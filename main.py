import network
import secrets
import socket
from machine import Pin, Timer, ADC
import time
import ssl
import umail
import urequests
import json
from ubinascii import b64encode

# Configure the onboard LED and ADC pin
led = Pin("LED", Pin.OUT)
# Using ADC0 (GP26) for voltage monitoring
voltage_pin = ADC(26)

print("Starting up...")
print("Voltage monitoring setup on GP26 (ADC0)")

# Keep track of last state to detect changes
last_state = None

def get_current_time():
    try:
        response = urequests.get("http://worldtimeapi.org/api/timezone/America/New_York")
        time_data = json.loads(response.text)
        current_time = time_data['datetime'].split('.')[0]  # Remove milliseconds
        response.close()
        return current_time
    except Exception as e:
        print("Error fetching time:", str(e))
        return "Time unavailable"

def send_email(subject, message):
    print("Sending email notification...")
    try:
        sender = secrets.SMTP_USERNAME
        recipient = secrets.SMTP_TO_EMAIL
        
        # Get current time and add device info
        current_time = get_current_time()
        full_message = f"Device: {secrets.DEVICE}\n"
        full_message += f"Location: {secrets.LOCATION}\n"
        full_message += f"Time: {current_time}\n\n"
        full_message += message
        
        smtp = umail.SMTP(secrets.SMTP_SERVER, secrets.SMTP_PORT, ssl=True)
        smtp.login(secrets.SMTP_USERNAME, secrets.SMTP_PASSWORD)
        
        smtp.to(recipient)
        smtp.write("From: " + sender + "\n")
        smtp.write("To: " + recipient + "\n")
        smtp.write("Subject: " + subject + "\n")
        smtp.write("\n")  # End of headers
        smtp.write(full_message)
        smtp.send()
        smtp.quit()
        print("Email sent successfully")
    except Exception as e:
        print("Failed to send email:", str(e))

def send_sms(message):
    print("Sending SMS notification...")
    try:
        # Twilio API endpoint
        url = f"https://api.twilio.com/2010-04-01/Accounts/{secrets.TWILIO_ACCOUNT_SID}/Messages.json"
        
        # Get current time and add device info
        current_time = get_current_time()
        full_message = f"{secrets.DEVICE} - {secrets.LOCATION}\n"
        full_message += f"Time: {current_time}\n"
        full_message += message
        
        # Prepare the form data
        data = {
            'To': secrets.TWILIO_TO_NUMBER,
            'From': secrets.TWILIO_FROM_NUMBER,
            'Body': full_message
        }
        
        # Convert data to form-urlencoded format
        form_data = "&".join([f"{key}={urequests.quote(str(value))}" for key, value in data.items()])
        
        # Create auth header
        auth = b64encode(f"{secrets.TWILIO_ACCOUNT_SID}:{secrets.TWILIO_AUTH_TOKEN}".encode()).decode()
        
        # Send request
        response = urequests.post(
            url,
            data=form_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {auth}'
            }
        )
        
        if response.status_code == 201:
            print("SMS sent successfully")
        else:
            print("Failed to send SMS:", response.text)
        
        response.close()
    except Exception as e:
        print("Failed to send SMS:", str(e))

def read_voltage():
    # Take multiple readings and average them for stability
    readings = []
    for _ in range(5):
        # Convert ADC reading (0-65535) to voltage (0-3.3V)
        reading = (voltage_pin.read_u16() * 3.3) / 65535
        readings.append(reading)
        time.sleep(0.01)
    
    # Return average voltage
    avg_voltage = sum(readings) / len(readings)
    print(f"Current voltage: {avg_voltage:.2f}V")
    return avg_voltage

def is_high_voltage(voltage):
    # Consider anything above 2.5V as "high" to account for slight variations
    return voltage > 2.5

# Function to check voltage status
def check_voltage(timer=None):
    global last_state
    current_voltage = read_voltage()
    current_state = is_high_voltage(current_voltage)
    
    # Update LED based on voltage
    if current_state:  # High voltage = Low on coins
        led.on()
    else:  # Low voltage = Has coins
        led.off()
    
    if last_state is None:
        last_state = current_state
    elif last_state != current_state:
        if current_state:  # High voltage = Low on coins
            status = "LOW ON COINS"
            message = "ALERT: Coin dispenser is running low and needs to be refilled!"
        else:  # Low voltage = Has coins
            status = "COINS OK"
            message = "Coin dispenser has been refilled and is now operational."
            
        subject = f"{secrets.DEVICE} Status Alert"
        send_email(subject, message + f"\nVoltage Reading: {current_voltage:.2f}V")
        send_sms(message + f"\nVoltage Reading: {current_voltage:.2f}V")
        
        last_state = current_state
        print(f"Dispenser status changed to: {status}")

print("Initial voltage:", read_voltage())

# Network credentials
ssid = secrets.SSID
password = secrets.PASSWORD

# Initialize network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Wait for connection
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print('IP:', status[0])

# Send initial startup notification
send_email(f"{secrets.DEVICE} Started", "Voltage monitoring system has started")

# Set initial LED state based on voltage
initial_voltage = read_voltage()
if is_high_voltage(initial_voltage):  # High voltage = Low on coins
    led.on()
else:  # Low voltage = Has coins
    led.off()

# Start the monitoring timer (check every second)
monitor_timer = Timer(-1)
monitor_timer.init(period=5000, mode=Timer.PERIODIC, callback=check_voltage)

# Simple HTML response with inline styles
html = """HTTP/1.0 200 OK
Content-type: text/html

<html>
<head>
    <title>Coin Dispenser Monitor</title>
    <meta http-equiv="refresh" content="10">
</head>
<body style="text-align: center; padding: 20px;">
    <h1>{} Monitor</h1>
    <p>{}</p>
    <div style="padding: 20px; margin: 20px; border-radius: 8px; background-color: {}; color: {};">
        <h2>Status: {}</h2>
        <p>Voltage Reading: {:.2f}V</p>
        <p style="font-size: 0.9em;">{}</p>
    </div>
    <p style="color: #666;">Monitoring coin level sensor on GP26 (Pin 31)</p>
    <p style="color: #666;">Monitoring is active even when this page is closed</p>
</body>
</html>
"""

print("Setting up server...")
addr = ('0.0.0.0', 80)
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
print("Server listening on", addr)

# Web server loop
while True:
    try:
        print("Waiting for connection...")
        cl, addr = s.accept()
        print("Client connected from:", addr)
        
        request = cl.recv(1024)
        print("Request received")
        
        # Get current voltage for web display
        current_voltage = read_voltage()
        is_high = is_high_voltage(current_voltage)
        
        if is_high:  # High voltage = Low on coins
            bg_color = "#FFB6C1"  # Light red
            text_color = "#8B0000"  # Dark red
            status = "LOW ON COINS"
            status_detail = "Coin dispenser needs to be refilled!"
        else:  # Low voltage = Has coins
            bg_color = "#90EE90"  # Light green
            text_color = "#006400"  # Dark green
            status = "COINS OK"
            status_detail = "Coin dispenser is operational"
        
        # Send response
        response = html.format(
            secrets.DEVICE, 
            secrets.LOCATION, 
            bg_color, 
            text_color, 
            status, 
            current_voltage,
            status_detail
        )
        print("Sending response with status:", status)
        cl.send(response.encode())
        print("Response sent")
        
        cl.close()
        print("Connection closed")
        
    except Exception as e:
        print("Error occurred:", str(e))
        if 'cl' in locals():
            cl.close()
