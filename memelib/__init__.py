import clr
import time
import sys
import os
import codecs

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
        self.start_recording_time = timefunc()
        self.isRecording = True
    
    def stop_recording(self):
        self._memelib.stopDataReport()
        if self.datafile is not None:
            self.datafile.write('time,count,AccX,AccY,AccZ,GyrX,GyrY,GyrZ,EogL,EogR,EogH,EogV\n')
            for data in self.data:
                self.datafile.write('{:.1f},{:d},{:d},{:d},{:d},{:d},{:d},{:d},'
                        '{:d},{:d},{:d},{:d}\n'.format(*data))
            self.datafile.write('time,event\n')
            for data in self.eventdata:
                self.datafile.write('{:.1f},{}\n'.format(*data))
                        
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
    
    def close_datafile(self):
        if self.datafile != None:
            self.datafile.close()
        
        self.datafile = None

