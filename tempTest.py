import board
import busio
import adafruit_mlx90614
import time

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize the MLX90614 sensor
mlx = adafruit_mlx90614.MLX90614(i2c)

while True:
    ambient_temp = float(mlx.ambient_temperature*(9/5)+32)
    object_temp = float(mlx.object_temperature*(9/5)+32)

    print(f"Ambient Temperature: {ambient_temp:.2f}°F")
    print(f"Object Temperature: {object_temp:.2f}°F")

    time.sleep(1)
