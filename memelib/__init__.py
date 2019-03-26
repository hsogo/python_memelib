import clr
import time
import sys
import os
import codecs

import numpy as np
import re

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    clr.AddReference("MEMELib_Academic")
    from MEMELib_Academic import MEMELib
except:
    raise ImportError('Can\'t import MEMELib_Academic.  Copy MEMELib_Academic.dll to any directory in your PATH environment variable or {}.'.format(os.path.abspath(os.path.dirname(__file__))))

if sys.platform == 'win32':
    timefunc = time.clock
else:
    timefunc = time.time

# MEMELib.MEMEAccelRange.Range2G
# MEMELib.MEMEAccelRange.Range4G
# MEMELib.MEMEAccelRange.Range16G
# MEMELib.MEMEGyroRange.Range1000dps
# MEMELib.MEMEGyroRange.Range2000dps
# MEMELib.MEMEGyroRange.Range250dps
# MEMELib.MEMEGyroRange.Range500dps

# fullData.Cnt
# fullData.BattLv
# fullData.AccX
# fullData.AccY
# fullData.AccZ
# fullData.GyroX
# fullData.GyroY
# fullData.GyroZ
# fullData.EogL
# fullData.EogR
# fullData.EogH
# fullData.EogV

# #######################################
# Recording
# #######################################

class memelib:
    com = ''
    device_address = ''
    callback_scan_ok = False
    callback_connect_ok = False
    data = []
    eventdata = []
    isConnected = False
    isOpened = False
    isRecording = False
    datafile = None
    recording_start_time = 0

    def __init__(self, com='', device_address=''):
        self.com = com
        self.device_address = device_address
        self._memelib = MEMELib()
        
        self._memelib.memePeripheralFound += MEMELib.memePeripheralFoundDelegate(self.callback_found)
        self._memelib.memePeripheralConnected += MEMELib.memePeripheralConnectedDelegate(self.callback_connected)
        self._memelib.memeAcademicFullDataReceived += MEMELib.memeAcademicFullDataReceivedDelegate(self.callback_received);

    
    def callback_found(self, sender, result, address):
        if result == MEMELib.MEMEStatus.MEMELIB_OK:
            self.device_address = address
        self.callback_scan_ok = True
    
    def callback_connected(self, sender, result):
        if result == MEMELib.MEMEStatus.MEMELIB_OK:
            self.isConnected = True
        elif result == MEMELib.MEMEStatus.MEMELIB_TIMEOUT:
            self.isConnected = False
        self.callback_connect_ok = True

    def callback_received(self, sender, full_data):
        t = 1000*(timefunc() - self.recording_start_time)
        self.data.append([t, full_data.Cnt,
                     full_data.AccX, full_data.AccY, full_data.AccZ,
                     full_data.GyroX,  full_data.GyroY, full_data.GyroZ,
                     full_data.EogL,  full_data.EogR, full_data.EogH, full_data.EogV])

    def get_port_list(self):
        memePortList = MEMELib.GetComPortNameList(self._memelib)
        return memePortList
        #return [memePortList[i] for i in range(memePortList.Count)]

    def open_port(self, port):
        res = self._memelib.ConnectComPort(port)
        if res == MEMELib.MEMEStatus.MEMELIB_OK:
            self.isOpened = True
            return True
        else:
            return False

    def scan_device(self, timeout=5, wait=5):
        self.callback_scan_ok = False
        self.device_address = ''  #todo: disconnect device if connected
        self._memelib.startScanningPeripherals()
        start = time.clock()
        while not self.callback_scan_ok and time.clock()-start < timeout:
            time.sleep(0.5)
        self._memelib.stopScanningPeripherals()
        if self.device_address != '':
            time.sleep(wait)
            return True
        return False
    
    def connect_device(self, timeout=10):
        self.callback_connect_ok = False
        self._memelib.connectPeripheral(self.device_address)
        start = time.clock()
        while not self.callback_connect_ok:
            time.sleep(0.5)
            if time.clock()-start > timeout:
                return False
        return self.isConnected
    
    def disconnect_device(self):
        self._memelib.disconnectPeripheral()
        self.isConnected = False
    
    def close_port(self):
        self._memelib.DisconnectComPort()
        self.isOpened = False
    
    def start_recording(self):
        self.data = []
        self.eventdata = []
        self._memelib.startDataReport()
        self.recording_start_time = timefunc()
        self.isRecording = True
    
    def stop_recording(self, write=True):
        self._memelib.stopDataReport()
        if self.datafile is not None and write:
            self.datafile.write('#start_rec\n')
            self.datafile.write('time,count,AccX,AccY,AccZ,GyrX,GyrY,GyrZ,EogL,EogR,EogH,EogV\n')
            for data in self.data:
                self.datafile.write('{:.1f},{:d},{:d},{:d},{:d},{:d},{:d},{:d},'
                        '{:d},{:d},{:d},{:d}\n'.format(*data))
            self.datafile.write('time,event\n')
            for data in self.eventdata:
                self.datafile.write('{:.1f},{}\n'.format(*data))
                        
            self.datafile.write('#stop_rec\n')
            self.datafile.flush()
        self.isRecording = False
    
    def record_event(self, msg):
        if self.isRecording:
            t = 1000*(timefunc() - self.recording_start_time)
            self.eventdata.append([t,msg])
    
    def open_datafile(self, filename):
        if self.datafile != None:
            self.datafile.close()
        
        self.datafile = codecs.open(filename, 'w', 'utf-8')
        self.datafile.write('#memelib_data\n')
    
    def close_datafile(self):
        if self.datafile != None:
            self.datafile.close()
        
        self.datafile = None

# #######################################
# Data
# #######################################


def convert_datafile(file):
    
    all_data = []
    
    with open(file, 'r') as fp:
        if fp.readline().rstrip() != '#memelib_data':
            return all_data
            
        for line in fp:
            if line[:10] == '#start_rec':
                data = []
                msg = []
                in_data = False
                in_msg = False
            elif line[:9] == '#stop_rec':
                all_data.append(memedata(data, msg))
            elif line[:10] == 'time,count':
                in_data = True
                in_msg = False
            elif line[:10] == 'time,event':
                in_data = False
                in_msg = True
            else:
                if in_data:
                    d = list(map(float, line.rstrip().split(',')))
                    data.append(d)
                elif in_msg:
                    d = line.rstrip().split(',')
                    d[0] = float(d[0])
                    msg.append(d)
    
    
    return all_data


class message(object):
    time = 0
    text = ''
    
    def __init__(self, time, text):
        self.time = time
        self.text = text
    
    """
    def __repr__(self):
        msg = '<{}.{}, '.format(self.__class__.__module__,
                                self.__class__.__name__)
        
        if len(self.text) > 16:
            text = self.text[:13]+'...'
        else:
            text = self.text
        
        if sys.version_info[0] == 2:
            msg += '{:.3f}s, {}>'.format(self.time/1000.0, text.encode(locale.getpreferredencoding()))
        else:
            msg += '{:.3f}s, {}>'.format(self.time/1000.0, text)
        
        return msg
    """



class memedata(object):
    T = []
    E = []
    H = []
    msg = []
    
    def __init__(self, data=None, msg=None, reset_timestamp=True):

        if isinstance(data, np.ndarray):
            data_array = data
        else:
            data_array = np.array(data)
        
        
        self.T = data_array[:,0]
        start_time = self.T[0]
        self.H = data_array[:,2:8]
        self.E = data_array[:,10:12]
        
        if reset_timestamp:
            self.T -= start_time
            for m in msg:
                self.msg.append(message(m[0]-start_time, m[1]))
        else:
            for m in msg:
                self.msg.append(message(m[0], m[1]))
        
    def extract(self, period):
        if len(period) != 2:
            raise ValueError('Period must be (start, end).')
        
        if period[0] is None:
            si = 0
        else:
            si = np.where(self.T >= period[0])[0][0]
        
        if period[1] is None:
            ei = -1
        else:
            ei = np.where(self.T <= period[1])[0][-1]
            
        return [self.T[si:ei], self.H[si:ei], self.E[si:ei]]
    
    def find_message_index(self, text, regexp=False):
        res = []
        
        if regexp:
            p = re.compile(text)
            for idx, msg in enumerate(self.msg):
                if p.search(msg.text):
                    res.append(idx)
        else:
            for idx, msg in enumerate(self.msg):
                if text in msg.text:
                    res.append(idx)
        return res

