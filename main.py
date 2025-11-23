import sys
import time
from datetime import datetime, timedelta
import cv2
import os
import serial
import adafruit_gps
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)
from PyQt5 import QtWidgets, QtCore, QtGui, uic
import math
import board
import busio
import adafruit_mlx90614
from sense_hat import SenseHat

class VideoThread(QtCore.QThread):
	frame_received = QtCore.pyqtSignal(QtGui.QPixmap)  # send frames to main thread

	def __init__(self):
		super().__init__()
		self.cap = cv2.VideoCapture(0)
		self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
		self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
		self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
		width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
		height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

		print(f"Camera resolution: {int(width)} x {int(height)}")

	def run(self):
		while True:
			ret, frame = self.cap.read()
			if ret:
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				h, w, ch = frame.shape
				qimg = QtGui.QImage(frame.data, w, h, ch * w, QtGui.QImage.Format_RGB888)
				pixmap = QtGui.QPixmap.fromImage(qimg)
				self.frame_received.emit(pixmap)
			self.msleep(30)
			

class MainWindow(QtWidgets.QMainWindow):        
	def __init__(self, parent=None):
		super().__init__(parent)
		uic.loadUi("lemun.ui", self)
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.loop)
		self.timer.start(100)
		self.count = 0

		self.thread = VideoThread()
		self.thread.frame_received.connect(self.update_image)
		self.thread.start()
		
		#GPS stuff
		uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=10)
		self.gps = adafruit_gps.GPS(uart, debug=False)
		self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
		self.gps.send_command(b"PMTK220,100")
		self.last_print = time.monotonic()
		
		self.angle = 0

		#Temp sensor stuff
		i2c = busio.I2C(board.SCL, board.SDA)
		self.mlx = adafruit_mlx90614.MLX90614(i2c)
		
		#Sense Hat
		self.sense = SenseHat()
		#self.sense.show_message("Go FASTER!")
		
		#north = self.sense.get_compass()

		self.colors = [
		'(0,0,255)', '(0,8,247)', '(0,15,240)', '(0,23,232)', '(0,31,224)', 
		'(0,38,217)', '(0,46,209)', '(0,54,201)', '(0,61,194)', '(0,69,186)', 
		'(0,76,178)', '(0,84,171)', '(0,92,163)', '(0,99,156)', '(0,107,148)', 
		'(0,115,140)', '(0,122,133)', '(0,130,125)', '(0,138,117)', '(0,145,110)', 
		'(0,153,102)', '(0,161,94)', '(0,168,87)', '(0,176,79)', '(0,184,71)', 
		'(0,191,64)', '(0,199,56)', '(0,207,48)', '(0,214,41)', '(0,222,33)', 
		'(0,229,26)', '(0,237,18)', '(0,245,10)', '(0,252,3)', '(5,255,0)', 
		'(13,255,0)', '(20,255,0)', '(28,255,0)', '(36,255,0)', '(43,255,0)', 
		'(51,255,0)', '(59,255,0)', '(66,255,0)', '(74,255,0)', '(82,255,0)', 
		'(89,255,0)', '(97,255,0)', '(105,255,0)', '(112,255,0)', '(120,255,0)', 
		'(127,255,0)', '(135,255,0)', '(143,255,0)', '(150,255,0)', '(158,255,0)', 
		'(166,255,0)', '(173,255,0)', '(181,255,0)', '(189,255,0)', '(196,255,0)', 
		'(204,255,0)', '(212,255,0)', '(219,255,0)', '(227,255,0)', '(235,255,0)', 
		'(242,255,0)', '(250,255,0)', '(255,252,0)', '(255,245,0)', '(255,237,0)', 
		'(255,230,0)', '(255,222,0)', '(255,214,0)', '(255,207,0)', '(255,199,0)', 
		'(255,191,0)', '(255,184,0)', '(255,176,0)', '(255,168,0)', '(255,161,0)', 
		'(255,153,0)', '(255,145,0)', '(255,138,0)', '(255,130,0)', '(255,122,0)', 
		'(255,115,0)', '(255,107,0)', '(255,99,0)', '(255,92,0)', '(255,84,0)', 
		'(255,77,0)', '(255,69,0)', '(255,61,0)', '(255,54,0)', '(255,46,0)', 
		'(255,38,0)', '(255,31,0)', '(255,23,0)', '(255,15,0)', '(255,8,0)'
		]

	def loop(self):
		self.count+=1
		self.gps.update()
		current = time.monotonic()
		if current - self.last_print >= 0.1:
			last_print = current
			if not self.gps.has_fix:
				print("Waiting for fix...")
			else:
				self.latLabel.setText(f"LAT:       {self.gps.latitude:.6f}")
				self.longLabel.setText(f"LONG:  {self.gps.longitude:.6f}")
				if self.gps.satellites is not None:
					self.satLabel.setText(f"SAT:       {self.gps.satellites}")
				if self.gps.altitude_m is not None:
					self.altLabel.setText(f"ALT:       {self.gps.altitude_m} m")
				if self.gps.speed_knots is not None:
					speed = float(self.gps.speed_knots)*1.151
					self.speedLabel.setText(f"{speed:.0f} MPH")
		accel = self.sense.get_accelerometer_raw()
		self.get_angle(accel['x'], accel['y'])
		if self.count == 10:
			t = self.mlx.object_temperature*(9/5)+32
			color = self.value_to_color(round(t))
			self.frontDTemp.setText(str(round(t))+ " F")
			self.frontDriver.setStyleSheet("background-color: rgb" + color + "; border-radius: 8px;")
			self.count = 0

	def update_image(self, qt_pix):
		#pix = qt_pix.scaled(1280, 720, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
		painter = QtGui.QPainter(qt_pix)
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		
		# --- Circle setup ---
		center = QtCore.QPoint(1180, 150)
		radius = 50
		circle_pen = QtGui.QPen(QtCore.Qt.red, 3)
		painter.setPen(circle_pen)
		painter.setBrush(QtCore.Qt.NoBrush)
		painter.drawEllipse(center, radius, radius)

		# --- Arrow setup ---
		# Angle is assumed in degrees, 0 = pointing right, positive CCW
		angle_rad = math.radians(self.angle)

		# Outer point of the arrow (on circle perimeter)
		outer_x = center.x() + radius * math.cos(angle_rad)
		outer_y = center.y() - radius * math.sin(angle_rad)  # minus because Qt y+ is down
		outer_point = QtCore.QPointF(outer_x, outer_y)

		# Inner point (not at center, pulled back from radius)
		inner_radius = radius * 0.8  # adjust so it doesn’t go to center
		inner_x = center.x() + inner_radius * math.cos(angle_rad)
		inner_y = center.y() - inner_radius * math.sin(angle_rad)
		inner_point = QtCore.QPointF(inner_x, inner_y)

		# Draw arrowhead (triangle at outer_point)
		arrow_size = 12
		line = QtCore.QLineF(inner_point, outer_point)

		# Left side of arrowhead
		line.setLength(arrow_size)
		line.setAngle(line.angle() + 150)
		left = line.p2()

		# Right side of arrowhead
		line.setAngle(line.angle() - 300)  # reset base angle -150
		right = line.p2()

		painter.setBrush(QtCore.Qt.red)
		arrow_head = QtGui.QPolygonF([outer_point, left, right])
		painter.drawPolygon(arrow_head)
		
		font = QtGui.QFont("Arial", 20, QtGui.QFont.Bold)
		painter.setFont(font)
		painter.drawText(1160, 160, "G's")

		painter.end()
		self.cam0.setPixmap(qt_pix)
		
	def value_to_color(self, x):
		min = 50
		max = 100
		if min<x<max:
			t =(x - min) * (100 / (max - min))
			color =self.colors[round(t)]
			#print(color)
			return(color)
		else:
			return("(0,0,0)")

	def get_angle(self, x, y):
		# Convert 0–1 to -1 to +1
		cx = (x - 0.5) * 2
		cy = (y - 0.5) * 2

		# Compute angle in degrees using atan2
		angle = math.degrees(math.atan2(cy, cx))

		# Convert from (-180..180) → (0..360)
		if angle < 0:
			angle += 360

		self.angle = angle

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec_())
