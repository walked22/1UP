import serial
import adafruit_gps
import time
 
uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=10)
gps = adafruit_gps.GPS(uart, debug=False)

gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,100")

last_print = time.monotonic()
while True:
    gps.update()
    current = time.monotonic()
    if current - last_print >= 0.1:
        last_print = current
        if not gps.has_fix:
            print("Waiting for fix...")
            continue
        print("=" * 40)
        print(f"Latitude: {gps.latitude:.6f} degrees")
        print(f"Longitude: {gps.longitude:.6f} degrees")
        print(f"Fix quality: {gps.fix_quality}")
        if gps.satellites is not None:
            print(f"Satellites: {gps.satellites}")
        if gps.altitude_m is not None:
            print(f"Altitude: {gps.altitude_m} meters")
        if gps.speed_knots is not None:
            print(f"Speed: {gps.speed_knots} knots")

