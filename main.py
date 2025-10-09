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

		self.thread = VideoThread()
		self.thread.frame_received.connect(self.update_image)
		self.thread.start()
		
		uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=10)
		self.gps = adafruit_gps.GPS(uart, debug=False)
		self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
		self.gps.send_command(b"PMTK220,100")
		self.last_print = time.monotonic()
		
		self.angle = 0

	def loop(self):
		self.angle+=1
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
		

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec_())
