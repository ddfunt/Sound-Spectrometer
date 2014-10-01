
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
import time


class Audio(object):

    def __init__(self):
        self.chunk = 128
        self.format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        self.r_time = 1
        self.output_name = "output.wav"
        self.width = 2
        self.waveform = ''

        #self.stream = self.setup_device()

    def setup_device(self):

        pass
    def open_playback(self):
        wf = wave.open('sin.wav', 'rb')
        return wf
    def record(self):

        CHUNK = 128
        WIDTH = 2
        CHANNELS = 2
        RATE = 44100
        RECORD_SECONDS = .5

        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(WIDTH),
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=CHUNK)

        print("* recording")
        wf = wave.open(self.waveform, 'rb')
        data_p = wf.readframes(CHUNK)
        frames = []
        #for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        while data_p != '':
            data = stream.read(CHUNK)
            stream.write(data_p)#, CHUNK)
            data_p = wf.readframes(CHUNK)
            frames.append(data)
            #print i, int(RATE / CHUNK * RECORD_SECONDS)

        print("* done")


        stream.stop_stream()
        stream.close()

        p.terminate()
        wf.close()
        #print 'here'
        wf = wave.open(self.output_name, 'w')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(p.get_format_from_width(WIDTH)))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return frames


    def stop_stream(self):
        """
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        """
        pass




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
                print 'herex'
                #self.save_wav(frames)
                print 'here'
                if i == 0:
                    chan = self.open_recording()
                else:
                    chan += self.open_recording()

        except:
            chan = np.zeros((10,2))
            print 'Likely buffer error in record'
        return chan




def write_sine(frequency=1E3, t = .5, t_tot=3):

    rate = 44100.

    time = np.array([i*(1/rate) for i in range(int(t*rate))], dtype='float32')
    d = np.zeros((t_tot*rate))
    wav = np.sin(time*2*np.pi*frequency)*10000
    d[:len(wav)] = wav

    values = []
    for value in d:
        packed_value = struct.pack('h', value)
        values.append(packed_value)
        values.append(packed_value)

    output = wave.open('sin.wav', 'w')
    output.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
    output.writeframes("".join(values))
    output.close()

def write_chirp(start=100, stop=15E3, t = .5, t_tot = 3):

    rate = 44100.

    time = np.array([i*(1/rate) for i in range(int(t*rate))], dtype='float32')
    k = (stop - start)/float(t)
    d = np.zeros((t_tot*rate))
    print start
    wav = np.sin(2*np.pi*(start*time + (k/2)*time**2))*10000
    d[:len(wav)] = wav
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
        self.play = PlaySound(self.audio)

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
        self.raw_data = chan[:, 1]
        self.time_data.setData(self.raw_data)
        self.fft_data()

    def fft_data(self):


        region =  self.lr.getRegion()
        cut_data = self.raw_data[region[0]: region[1]]
        if not True:
            cut_data = cut_data * np.kaiser(len(cut_data), 8)
        #print chan
        #print len(chan)
        z = np.zeros(len(cut_data)*4)
        z[0:len(cut_data)] = cut_data

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

            if self.sin_radio.isChecked():
                self.audio.waveform = 'sin.wav'
                write_sine(frequency=self.sin_freq.value())
                pass
            else:
                self.audio.waveform = 'chirp.wav'
                write_chirp(start=self.chirp_start.value(), stop=self.chirp_stop.value())

            #wf = wave.open('sin.wav', 'rb')
            #self.audio.chunk = wf.getnframes()

            #time.sleep(1)
            self.avg_thread.start()
            #self.play.start()
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


        pen = pg.mkPen(color='w', width=2)
        #layout = QtGui.QGridLayout()
        #self.view.setLayout(layout)
        l2 = self.graph.addLayout(colspan=3, border=None)
        l2.setContentsMargins(10, 10, 10, 10)
        l2.addLabel('Intensity(mV)', angle=-90, border=None, color='w')

        self.plot = l2.addPlot()
        l2.nextRow()
        l2.addLabel('Frequency (Hz)', colspan=2, border=None, color='w')
        l2.nextRow()
        l2.addLabel('Intensity', angle=-90, border=None, color='w')

        self.time = l2.addPlot()
        self.lr = pg.LinearRegionItem([400,700])
        self.lr.setZValue(-10)
        self.time.addItem(self.lr)
        self.lr.sigRegionChanged.connect(self.fft_data)
        l2.nextRow()

        l2.addLabel('Time ', colspan=2, border=None, color='w')

        self.data = self.plot.plot()
        self.time_data = self.time.plot()

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
        #self.sin_freq.setValue(1000)
        self.chirp_start.setValue(100)
        self.chirp_stop.setValue(15000)




class PlaySound(QtCore.QThread):

    def __init__(self, audio):
        super(PlaySound, self). __init__()
        self.sound = 'sin.wav'
        self.audio = audio

    def run(self):

        self.audio.play()

class Average(QtCore.QThread):
    dataReady = QtCore.Signal(object)
    def __init__(self, audio):
        super(Average, self).__init__()

        self.avgs = 1
        self.audio = audio
        self.sound = 'sin.wav'
    def run(self):
        self.audio.setup_device()
        datax = (self.audio.average(self.avgs))
        #print "playing"
        #play()
        self.dataReady.emit(datax)
        self.audio.stop_stream()


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)

    blarg = GUI()
    blarg.show()
    app.exec_()
