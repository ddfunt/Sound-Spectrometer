
"""PyAudio example: Record a few seconds of audio and save to a WAVE file."""

import PySide
from pyqtgraph import QtGui, QtCore
import pyqtgraph as pg
import pyaudio
import wave
import numpy as np
from matplotlib import pyplot as plt
from scipy.io.wavfile import read, write
import struct


class Audio(object):

    def __init__(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        self.r_time = .5
        self.output_name = "output.wav"

        #self.stream = self.setup_device()

    def setup_device(self):


        self.p = pyaudio.PyAudio()
        for i in range(self.p.get_device_count()):
            print i, self.p.get_device_info_by_index(i)

        #self.p.terminate()

        #print p.get_device_info_by_index(0)['defaultSampleRate']
        #raw_input()
        self.stream = self.p.open(format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        output=True,
                        frames_per_buffer=self.chunk,
                        input_device_index=0)



    def record(self):


        print("* recording")

        frames = []

        for i in range(0, int(self.rate / self.chunk * self.r_time)):

            data = self.stream.read(self.chunk)
            frames.append(data)

        print("* done recording")


        return frames

    def stop_stream(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()




    def save_wav(self, frames):
        wf = wave.open(self.output_name, 'w')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        return True

    def open_recording(self):
        a = read("output.wav")
        chan = np.array(a[1], dtype=float)
        return chan

    def average(self, avgs=20):
        try:
            for i in range(avgs):
                frames = self.record()
                self.save_wav(frames)
                if i == 0:
                    chan = self.open_recording()
                else:
                    chan += self.open_recording()
                #print chan
        except:
            chan = np.zeros((10,2))
        return chan

def play(name = 'output2.wav'):
    CHUNK = 1024

    filename = name

    wf = wave.open(filename, 'rb')
    #print wf


    # instantiate PyAudio (1)
    p = pyaudio.PyAudio()

    #print wf.getframerate()
    # open stream (2)
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # read data
    data = wf.readframes(CHUNK)
    #print data, 'dada'
    # play stream (3)
    while data != '':
        stream.write(data)
        data = wf.readframes(CHUNK)

    # stop stream (4)
    stream.stop_stream()
    stream.close()

    # close PyAudio (5)
    p.terminate()





def write_sine(frequency=1E3, t = 3):

    rate = 44100.

    time = np.array([i*(1/rate) for i in range(int(t*rate))], dtype='float32')

    d = np.sin(time*2*np.pi*frequency)*10000
    values = []
    for value in d:
        packed_value = struct.pack('h', value)
        values.append(packed_value)
        values.append(packed_value)

    output = wave.open('sin.wav', 'w')
    output.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
    output.writeframes("".join(values))
    output.close()

def write_chirp(start=100, stop=15E3, t = 3):

    rate = 44100.

    time = np.array([i*(1/rate) for i in range(int(t*rate))], dtype='float32')
    k = (stop - start)/2
    d = np.sin(2*np.pi*(start*time + (k/2)*time**2))*10000
    values = []
    for value in d:
        packed_value = struct.pack('h', value)
        values.append(packed_value)
        values.append(packed_value)

    output = wave.open('chirp.wav', 'w')
    output.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
    output.writeframes("".join(values))
    output.close()

class GUI(QtGui.QWidget):

    def __init__(self):
        super(GUI, self).__init__()
        self.complete = True
        self.audio = Audio()
        self.avg_thread = Average(self.audio)
        #self.play = PlaySound(self.audio)

        self.setup_gui()
        self.connect_signals()
        self.set_defaults()

    def connect_signals(self):

        self.start_btn.pressed.connect(self.play_sound)
        self.avg_thread.dataReady.connect(self.plot_data)
        self.sin_radio.pressed.connect(self.show_sin)
        self.chirp_radio.pressed.connect(self.show_chirp)
        #self.contin.pressed.connect(self.play_contin)

    def show_sin(self):
        self.chirp_settings.hide()
        self.sin_settings.show()

    def show_chirp(self):
        self.sin_settings.hide()
        self.chirp_settings.show()

    def plot_data(self, chan):

        chan[:, 1] = chan[:, 1] * np.kaiser(len(chan[:, 1]), 8)
        #print chan
        #print len(chan)
        z = np.zeros(len(chan)*4)
        z[0:len(chan)] = chan[:, 1]

        fft = abs(np.fft.fft(z)[0:len(z)/2])
        freq = np.fft.fftfreq(len(fft)*2, 1/44100.)[0:len(z)/2]
        self.data.setData(freq, fft)
        self.audio.stop_stream()
        self.complete = True
        if self.contin.isChecked():
            #pass
            self.play_sound()



    def play_sound(self):
        if self.complete:
            self.complete = False
            self.audio.setup_device()
            if self.sin_radio.isChecked():
                #self.play.sound = "sin.wav"
                #write_sine(frequency=self.sin_freq.value())
                pass
            else:
                self.play.sound = "chirp.wav"
                write_chirp(start=self.chirp_start.value(), stop=self.chirp_stop.value())
            #write_chirp()
            self.avg_thread.start()
            #self.play.start()

    def setup_gui(self):
        layout = QtGui.QGridLayout()
        mode_layout = QtGui.QHBoxLayout()
        pulse_layout = QtGui.QHBoxLayout()
        chirp_layout = QtGui.QHBoxLayout()
        sin_layout = QtGui.QHBoxLayout()
        self.setLayout(layout)

        self.start_btn = QtGui.QPushButton()
        self.chirp_radio = QtGui.QRadioButton()
        self.sin_radio = QtGui.QRadioButton()
        self.mode_group = QtGui.QGroupBox()
        self.pulse_group = QtGui.QGroupBox()
        self.emission = QtGui.QRadioButton()
        self.absorbption = QtGui.QRadioButton()
        self.graph = pg.GraphicsWindow()
        self.sin_settings = QtGui.QGroupBox()
        self.chirp_settings = QtGui.QGroupBox()
        self.sin_freq_lbl = QtGui.QLabel()
        self.sin_freq = QtGui.QDoubleSpinBox()
        self.chirp_start = QtGui.QDoubleSpinBox()
        self.chirp_stop = QtGui.QDoubleSpinBox()
        self.chirp_start_lbl = QtGui.QLabel()
        self.chirp_stop_lbl = QtGui.QLabel()
        self.contin = QtGui.QCheckBox()

        self.start_btn.setText("Start")
        self.chirp_radio.setText("Chirped Pulse")
        self.sin_radio.setText("Sin Wave")
        self.emission.setText("Emission")
        self.absorbption.setText("Absorption")
        self.mode_group.setTitle("Detection Mode")
        #self.mode_group.set
        self.pulse_group.setTitle("Pulse Mode")
        self.chirp_start_lbl.setText("Start Frequency")
        self.chirp_stop_lbl.setText("Stop Frequency")
        self.sin_freq_lbl.setText("Frequency")
        self.sin_settings.setTitle("Settings")
        self.chirp_settings.setTitle("Settings")


        layout.addWidget(self.start_btn, 4, 0)
        layout.addWidget(self.mode_group, 1, 0)
        layout.addWidget(self.pulse_group, 2, 0)
        layout.addWidget(self.graph, 0, 0)
        layout.addWidget(self.sin_settings, 3, 0)
        layout.addWidget(self.chirp_settings, 3, 0)
        layout.addWidget(self.contin, 5, 0)

        sin_layout.addWidget(self.sin_freq_lbl)
        sin_layout.addWidget(self.sin_freq)
        chirp_layout.addWidget(self.chirp_start_lbl)
        chirp_layout.addWidget(self.chirp_start)
        chirp_layout.addWidget(self.chirp_stop_lbl)
        chirp_layout.addWidget(self.chirp_stop)
        mode_layout.addWidget(self.emission)
        mode_layout.addWidget((self.absorbption))
        pulse_layout.addWidget(self.sin_radio)
        pulse_layout.addWidget(self.chirp_radio)


        self.mode_group.setLayout(mode_layout)
        self.pulse_group.setLayout(pulse_layout)
        self.sin_settings.setLayout(sin_layout)
        self.chirp_settings.setLayout(chirp_layout)


        pen = pg.mkPen(color='k', width=2)
        #layout = QtGui.QGridLayout()
        #self.view.setLayout(layout)
        l2 = self.graph.addLayout(colspan=3, border=None)
        l2.setContentsMargins(10, 10, 10, 10)
        l2.addLabel('Intensity(mV)', angle=-90, border=None, color='k')

        self.plot = l2.addPlot()

        l2.nextRow()
        l2.addLabel('Frequency (MHz)', colspan=2, border=None, color='k')

        self.data = self.plot.plot()

    def set_defaults(self):
        self.absorbption.setChecked(True)
        self.sin_radio.setChecked(True)
        self.sin_freq.setMinimum(20)
        self.sin_freq.setMaximum(20000)
        self.chirp_stop.setMaximum(20000)
        self.chirp_start.setMaximum(20000)
        self.chirp_start.setMinimum(20)
        self.chirp_stop.setMinimum(20)
        self.chirp_settings.hide()
        self.sin_freq.setValue(1000)
        self.chirp_start.setValue(100)
        self.chirp_stop.setValue(15000)




class PlaySound(QtCore.QThread):

    def __init__(self, audio):
        super(PlaySound, self). __init__()
        self.sound = 'sin.wav'
        self.audio

    def run(self):

        self.audio.play(name=self.sound)

class Average(QtCore.QThread):
    dataReady = QtCore.Signal(object)
    def __init__(self, audio):
        super(Average, self).__init__()

        self.avgs = 1
        self.audio = audio

    def run(self):
        datax = (self.audio.average(self.avgs))
        #print "playing"
        #play()
        self.dataReady.emit(datax)


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)

    blarg = GUI()
    blarg.show()
    app.exec_()
