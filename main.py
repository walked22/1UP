import sys
import time
from datetime import datetime, timedelta
import cv2
import os
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

from PyQt5 import QtWidgets, QtCore, QtGui, uic

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

	def loop(self):
		print("hello")
			                        

	def update_image(self, qt_pix):
		#pix = qt_pix.scaled(1280, 720, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
		self.cam0.setPixmap(qt_pix)

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec_())
