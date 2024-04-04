import atexit
from neopixel_python import shape
# import signal
import threading

# def LED_shutdown_signal(signum, frame):
#     print("Caught a signal: {}".format(signum))
#     LED_shutdown()

def LED_shutdown():
    print("Gracefully quitting all LED driver threads.")
    for t in threading.enumerate():
        if isinstance(t, shape.DriveLED):
            print("Stopping {}".format(type(t).__name__))
            t.stop()

atexit.register(LED_shutdown)

# https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/
# https://christopherdavis.me/blog/threading-basics.html
# signal.signal(signal.SIGTERM, LED_shutdown_signal)
# signal.signal(signal.SIGINT, LED_shutdown_signal)
