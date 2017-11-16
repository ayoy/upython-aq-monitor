import time
from os import dupterm
from uio import StringIO
from _thread import start_new_thread

def log_console():
    console = StringIO()
    dupterm(console)
    logfile = '/flash/console-{}.log'.format(time.time())
    while True:
        logH = open(logfile, 'w+')
        logH.write(console.getvalue())
        logH.close()
        time.sleep(1)

start_new_thread(log_console, ())
