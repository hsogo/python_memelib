#coding: utf-8

from memelib import memelib
import sys
import time

meme = memelib()
ports = meme.get_port_list()
if len(ports) == 0:
    print('Error: cannot find ports.')
    sys.exit()
if not meme.open_port(ports[0]):
    print('Error: cannot open {}'.format(ports[0]))
    sys.exit()
if not meme.scan_device():
    print('Error: cannot find device')
    sys.exit()
if not meme.connect_device():
    print('Error: cannot connect to {}'.format(meme.device_address))
    sys.exit()

meme.open_datafile('foo.csv')

print('start recording')
meme.start_recording()
for i in range(10):
    time.sleep(1)
    meme.record_event('Count: {}'.format(i))
meme.stop_recording()
print('stop recording')

meme.disconnect_device()
meme.close_port()

meme.close_datafile()
