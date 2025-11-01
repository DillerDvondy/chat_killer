import datetime
import time

def time_format(seconds):
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h}h {m}m {s}s"

x = int(time.time())
time.sleep(3)
print(int(time.time()) - x)
print(x)