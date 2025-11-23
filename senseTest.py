#from sense_hat import SenseHat
#import time
#sense = SenseHat()
#sense.show_message("Go FASTER!")
#while True:
#	print(sense.get_orientation_degrees())

from sense_hat import SenseHat

x = y = 4
hat = SenseHat()

def update_screen():
    hat.clear()
    hat.set_pixel(x, y, 0, 0, 255)

def clamp(value, min_value=0, max_value=7):
    return min(max_value, max(min_value, value))

def move_dot(event):
    global x, y
    if event.action in ('pressed', 'held'):
        x = clamp(x + {
            'left': -1,
            'right': 1,
            }.get(event.direction, 0))
        y = clamp(y + {
            'up': -1,
            'down': 1,
            }.get(event.direction, 0))

update_screen()
while True:
    for event in hat.stick.get_events():
        move_dot(event)
        update_screen()
