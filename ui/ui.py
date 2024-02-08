from ui.ui_lib import Ui_MainWindow
from ui.hotkey import Ui_Dialog
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QTimer
import os,json,wave

class Ui(Ui_MainWindow):
    def setupUi(self, mainsystem, MainWindow):
        self.mainwindow = MainWindow
        self.mainsystem = mainsystem
        super().setupUi(MainWindow)
        self.init()
        self.rename()
        self.bind()
        
    
    def bind(self):
        self.add_sound_button.clicked.connect(self.addSound)
        self.edit_sound_button.clicked.connect(self.editSound)
        self.remove_sound_button.clicked.connect(self.removeSound)
        self.listen_sound.stateChanged.connect(self.listenStateChanged)
        self.listen_microphone.stateChanged.connect(self.listenStateChanged)
        self.choose_microphone.currentTextChanged.connect(self.setDevice)
        self.choose_speaker.currentTextChanged.connect(self.setDevice)
        

    def rename(self):
        self.mainwindow.setWindowTitle("麦克疯")
        self.groupBox.setTitle("麦克风")
        self.label_2.setText("设备")
        self.groupBox_2.setTitle("预览")
        self.listen_microphone.setText("预览麦克风音频")
        self.listen_sound.setText("预览音频")
        self.label_4.setText("设备")
        self.sounds_box.setTitle("音频")
        self.add_sound_button.setText("+")
        self.remove_sound_button.setText("-")
        self.edit_sound_button.setText("编辑")
        self.showSounds()
    
    def showSounds(self):
        self.sounds_list.clear()
        sounds = os.listdir("./sounds")
        if "停止播放" not in sounds:
            f = wave.open("sounds/停止播放","wb",)
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            f.setnframes(0)
            f.writeframes(b'')
            f.close()
        sounds = os.listdir("./sounds")
        hotkeys = {}
        try:
            with open("./hotkey.json","r") as f:
                hotkeys = json.load(f)
        except Exception as e:
            pass
        remove_ = []
        for hotkey in hotkeys:
            if hotkey not in sounds:
                remove_.append(hotkey)
        for hotkey in remove_:
            hotkeys.pop(hotkey)
        wav = []
        for sound in sounds:
            if ".wav" in sound or sound == "停止播放":
                wav.append(sound)
                if sound not in hotkeys:
                    hotkeys[sound] = []
            
        with open("./hotkey.json","w") as f:
            json.dump(hotkeys,f)

        self.sounds_list.addItems(wav)
        self.mainsystem.hotkeys = hotkeys
    
    def addSound(self):
        path = QFileDialog.getOpenFileName(filter="wav音频文件 (*.wav)")[0]
        if path == "":
            return
        with open(path,"rb") as f:
            data = f.read()
        filename = path.split('/')[-1]
        with open(f"./sounds/{filename}","wb") as f:
            f.write(data)
        self.showSounds()
    
    def getHotKey(self,sound,hotkeys):
        self.mainsystem.hotkeys[sound] = hotkeys
        with open("./hotkey.json","w") as f:
            hotkeys = json.dump(self.mainsystem.hotkeys,f)
    
    def editSound(self):
        item = self.sounds_list.currentItem()
        if item is None:
            return
        sound = item.text()
        self.mainsystem.setDialog(Hotkey(sound,self.mainsystem.hotkeys[sound],self.getHotKey))
    
    def removeSound(self):
        item = self.sounds_list.currentItem()
        if item is None:
            return
        os.remove(f"sounds/{item.text()}")
        self.showSounds()
    
    def listenStateChanged(self):
        self.mainsystem.listen_microphone = self.listen_microphone.isChecked()
        self.mainsystem.listen_sound = self.listen_sound.isChecked()
        with open("config.json","r") as f:
            data = json.load(f)
        data["listen_sound"] = self.mainsystem.listen_sound
        data["listen_microphone"] = self.mainsystem.listen_microphone
        with open("config.json","w") as f:
            json.dump(data,f)
    
    def init(self):
        data = {
            "microphone_index": self.mainsystem.microphone_index,
            "speaker_index": self.mainsystem.speaker_index,
            "listen_sound": True,
            "listen_microphone": True
        }
        try:
            with open("config.json","r") as f:
                data = json.load(f)
        except:
            pass
        self.mainsystem.microphone_index = data["microphone_index"]
        self.mainsystem.speaker_index = data["speaker_index"]
        self.mainsystem.listen_sound = data["listen_sound"]
        self.mainsystem.listen_microphone = data["listen_microphone"]
        with open("config.json","w") as f:
            json.dump(data,f)
        print(self.mainsystem.microphones.values())
        self.choose_microphone.addItems(list(self.mainsystem.microphones.values()))
        self.choose_speaker.addItems(list(self.mainsystem.speakers.values()))
        self.choose_microphone.setCurrentText(self.mainsystem.microphones[self.mainsystem.microphone_index])
        self.choose_speaker.setCurrentText(self.mainsystem.speakers[self.mainsystem.speaker_index])

        self.listen_microphone.setChecked(data["listen_microphone"])
        self.listen_sound.setChecked(data["listen_sound"])
    
    def setDevice(self):
        microphone_text = self.choose_microphone.currentText()
        speaker_text = self.choose_speaker.currentText()
        for i in self.mainsystem.microphones:
            if self.mainsystem.microphones[i] == microphone_text:
                self.mainsystem.microphone_index = i
                break
        for i in self.mainsystem.speakers:
            if self.mainsystem.speakers[i] == speaker_text:
                self.mainsystem.speaker_index = i
                break
        
        with open("config.json","r") as f:
            data = json.load(f)
        data["microphone_index"] = self.mainsystem.microphone_index
        data["speaker_index"] = self.mainsystem.speaker_index
        with open("config.json","w") as f:
            json.dump(data,f)
        self.mainsystem.getDevice()
        

class Hotkey(Ui_Dialog):
    def __init__(self,sound,default,callback):
        self.callback = callback
        self.sound = sound
        self.hotkeys = default
        self.started = False

    def setupUi(self, mainsystem, Dialog):
        self.mainsystem = mainsystem
        self.dialog = Dialog
        super().setupUi(Dialog)
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(100)
        self.rename()
        self.bind()
    
    def tick(self):
        if self.started:
            for key in self.mainsystem.key_down:
                if key == "Key.ctrl_l" or key == "Key.ctrl_r":
                    self.started = False
                    self.showButton()
                    return
                if key not in self.hotkeys:
                    self.hotkeys.append(key)
                    self.show_label.setText(f"<html><head/><body><p align=\"center\"><span style=\" font-size:18pt;\">{'+'.join(self.hotkeys)}</span></p></body></html>")

    def bind(self):
        self.start.clicked.connect(self.start_)
        self.ok.clicked.connect(self.ok_)
        self.cancel.clicked.connect(self.cancel_)

    def rename(self):
        self.dialog.setWindowTitle("Dialog")
        self.label_2.setText("按[Ctrl]结束录制")
        self.label_3.setText("不要使用Ctrl键录制")
        self.show_label.setText(f"<html><head/><body><p align=\"center\"><span style=\" font-size:18pt;\">{'+'.join(self.hotkeys)}</span></p></body></html>")
        self.start.setText("开始录制")
        self.ok.setText("确定")
        self.cancel.setText("取消")
    
    def start_(self):
        self.started = True
        self.hotkeys = []
        self.show_label.setText(f"<html><head/><body><p align=\"center\"><span style=\" font-size:18pt;\">请输入</span></p></body></html>")
        self.hideButton()
    
    def cancel_(self):
        self.dialog.close()
    
    def ok_(self):
        self.callback(self.sound,self.hotkeys)
        self.dialog.close()
    
    def showButton(self):
        self.start.show()
        self.ok.show()
        self.cancel.show()
    
    def hideButton(self):
        self.start.hide()
        self.ok.hide()
        self.cancel.hide()
    