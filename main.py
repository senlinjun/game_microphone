import pyaudio,sys,wave,os
import numpy as np
from PyQt5.QtWidgets import QApplication,QMainWindow,QDialog
from pynput import keyboard
from ui.ui import Ui
from threading import Thread

def single2dual(data:bytes):
    data = np.frombuffer(data)
    return np.column_stack((data,data)).tobytes()

def dual2single(data:bytes):
    data = np.frombuffer(data)
    return np.mean(data,axis=1).tobytes()

def safeWaveData(data:bytes,channels,ending_channels):
    if channels == ending_channels:
        return data
    if channels < ending_channels:
        return single2dual(data)
    return dual2single(data)

def mixSound(data1:bytes,data2:bytes):
    data1 = np.frombuffer(data1)
    data2 = np.frombuffer(data2)
    mix_data = data1+data2
    return mix_data.tobytes()
class Main:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.RATE = 44100
        self.p = pyaudio.PyAudio()
        self.getDevice()
        self.speaker_index = list(self.speakers.keys())[0]
        self.cable_input_index = self.getCable()
        self.microphone_index = list(self.microphones.keys())[0]
        self.mainloop = False
        self.hotkeys = {}
        self.key_down = []
        self.dialog = None
        self.mainwindow = None
        self.listen_microphone = True
        self.listen_sound = True
        if "sounds" not in os.listdir():
            os.mkdir("sounds")
    def getDevice(self):
        microphones = {}
        speakers = {}
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if device_info["maxInputChannels"] > 0:
                if device_info['name'] not in list(microphones.values()):
                    microphones[i] = device_info['name']
            if device_info["maxOutputChannels"] > 0:
                if device_info['name'] not in list(speakers.values()):
                    speakers[i] = device_info['name']
        self.speakers = speakers
        self.microphones = microphones            
    
    def getCable(self):
        for id in self.speakers:
            if "CABLE Input" in self.speakers[id]:
                return id
    
    def mainLoop(self):
        self.mainloop = True
                
        self.getStream()
        self.SOUNDCHANNELS = 0
        while self.mainloop:
            microphone_data = self.microphone.read(self.CHUNK)
            microphone_data = safeWaveData(microphone_data,self.MICROPHONECHANNELS,self.SPEAKERCHANNELS)
            if self.SOUNDCHANNELS:
                file_data = self.f.readframes(self.CHUNK)
                if file_data == b'':
                    self.f.close()
                    self.SOUNDCHANNELS = 0
                    continue
                file_data = safeWaveData(file_data,self.SOUNDCHANNELS,self.SPEAKERCHANNELS)
                self.speaker1.write(file_data)
                if self.listen_sound:
                    self.listen_speaker1.write(file_data)
            self.speaker.write(microphone_data)
            if self.listen_microphone:
                self.listen_speaker.write(microphone_data)
            
        for stream in [self.speaker,self.speaker1,self.listen_speaker,self.listen_speaker1,self.microphone]:
            stream.stop_stream()
            stream.close()
        print("Close")

    def showUi(self):
        self.app = QApplication(sys.argv)
        self.mainwindow = QMainWindow()
        self.ui = Ui()
        self.ui.setupUi(self,self.mainwindow)
        self.mainwindow.show()
        self.app.exec_()
    
    def setDialog(self,ui):
        if self.dialog is not None:
            try:
                self.dialog.close()
            except:
                pass
        self.dialog = QDialog()
        self.dialog_ui = ui
        self.dialog_ui.setupUi(self,self.dialog)
        self.dialog.show()
    
    def onPress(self,key):
        self.onKeyAction(key,0)

    def onRelease(self,key):
        self.onKeyAction(key,1)
    
    def onKeyAction(self,key,ktype:bool):
        '''
        ktype: 0:press;1:release
        '''
        key = str(key)
        if "\\" in key:
            return
        if key[0] == key[-1] and key[0] == "'":
            key = key[1:-1]
        if key[0] == '<' and key[-1] == '>':
            key = f"numpad_{int(key[1:-1])-96}"

        if ktype:
            if key in self.key_down:
                self.key_down.remove(key)
        else:
            if key not in self.key_down:
                self.key_down.append(key)
        for sound in self.hotkeys:
            flag = True
            if self.hotkeys[sound] == []:
                continue
            for key in self.hotkeys[sound]:
                if key not in self.key_down:
                    flag = False
            if flag:
                self.f = wave.open(f"sounds/{sound}","rb")
                self.SOUNDCHANNELS = self.f.getnchannels()

    def listenKeyboard(self):
        with keyboard.Listener(on_press=self.onPress, on_release=self.onRelease) as listener:
            listener.join()
    
    def getStream(self):
        self.MICROPHONECHANNELS = self.p.get_device_info_by_index(self.microphone_index)["maxInputChannels"]
        self.SPEAKERCHANNELS = self.p.get_device_info_by_index(self.speaker_index)["maxOutputChannels"]
        self.microphone = self.p.open(
            format=self.FORMAT,
            channels=self.MICROPHONECHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            input_device_index = self.microphone_index)
        self.speaker = self.p.open(
            output_device_index = self.cable_input_index,
            rate=self.RATE,
            channels=self.SPEAKERCHANNELS,
            format=self.FORMAT,
            output=True
            )
        self.speaker1 = self.p.open(
            output_device_index = self.cable_input_index,
            rate=self.RATE,
            channels=self.SPEAKERCHANNELS,
            format=self.FORMAT,
            output=True
            )
        self.listen_speaker = self.p.open(
            output_device_index = self.speaker_index,
            rate=self.RATE,
            channels=self.SPEAKERCHANNELS,
            format=self.FORMAT,
            output=True
            )
        self.listen_speaker1 = self.p.open(
            output_device_index = self.speaker_index,
            rate=self.RATE,
            channels=self.SPEAKERCHANNELS,
            format=self.FORMAT,
            output=True
            )

m = Main()
Thread(target=m.listenKeyboard,daemon=True).start()
Thread(target=m.mainLoop).start()
m.showUi()
m.mainloop = False
