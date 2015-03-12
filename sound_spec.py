
"""This is designed to create either a single frequency audio snippet
or chirped frequency sweep between 0-20KHz and play that sound through a speaker.

The output is recorded through a microphone and both the time data and FFT are 
displayed on screen

The program uses the current system default microphone and speaker devices sobe
sure to set these defaults before launching the software.


Currently only "emission" modes are working.  Support for absorbtion will be added

Currently pulse lengths are fixed in code(but can be manually edited) and the FFT
window can be changed in the UI by dragging the vertical slider bars on the graph. 

Averaging is currently not working as it would require a "stable" trigger instead
of using the system clock"""

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
import array


### Global functions to write output waveform files

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

    output = wave.open('tmp/sin.wav', 'w')
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

    output = wave.open('tmp/chirp.wav', 'w')
    output.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
    output.writeframes("".join(values))
    output.close()

class Audio(QtCore.QThread):
    """contains nessicary functions for recording audio and transfering it
    to the user interface
    """
    dataReady= QtCore.Signal(object)
    full_data =  QtCore.Signal(object)
    
    def __init__(self):
        super(Audio, self).__init__()
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
        wf = wave.open('tmp/sin.wav', 'rb')
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
        
        #records audio in small chunks both to not overrun the system buffer
        #and allow for real time viewing of the audio capture on screen
        #too small of chunks will cause lag and "skipping" in the recording
        while data_p != '':
            data = stream.read(CHUNK)
            stream.write(data_p)#, CHUNK)
            data_p = wf.readframes(CHUNK)
            #f = ''.join(frames)
            self.dataReady.emit(data)
            #map(ord, data)
            #nums = np.array('h', data)
            frames.append(data)
            

        print("* done")
        stream.stop_stream()
        stream.close()
   
        p.terminate()
        wf.close()
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
                
        except:
            #this should return an error however if a recording fails it jsut returns
        #a  zero array
            chan = np.zeros((10,2))
        #    print 'Likely buffer error in record'
            
	self.full_data.emit(True)        
	#return chan
    def run(self):
	self.average(avgs=1)


class GUI(QtGui.QWidget):

    def __init__(self):
        super(GUI, self).__init__()
        self.complete = True
        self.audio = Audio()
        self.avg_thread = Average(self.audio)
        self.play = PlaySound(self.audio)

        self.setup_gui()
        self.wav = []
        self.connect_signals()
        self.set_defaults()
	self.raw_data = []
	self.timer = QtCore.QTimer()
	self.timer.timeout.connect(self.real_time)
	self.timer.start(100)

    def connect_signals(self):

        self.start_btn.pressed.connect(self.play_sound)
        self.audio.full_data.connect(self.plot_data)
        self.sin_radio.pressed.connect(self.show_sin)
        self.chirp_radio.pressed.connect(self.show_chirp)
        self.audio.dataReady.connect(self.get_chunk)
        #self.contin.pressed.connect(self.play_contin)
    def get_data(self):
	self.audio.setup_device()
        #datax = (self.audio.average(self.avgs))
	self.audio.start()
	#self.dataReady.emit(data)
        self.audio.stop_stream()

    def real_time(self):
	if not self.complete:
	    self.time_data.setData(self.raw_data)
    def get_chunk(self, f):
        nums = array.array('h', f)
	left = nums[1::2]
	self.raw_data += left

        #self.time_data.setData(self.raw_data)
        #print data[1]

    def show_sin(self):
        self.chirp_settings.hide()
        self.sin_settings.show()

    def show_chirp(self):
        self.sin_settings.hide()
        self.chirp_settings.show()

    def plot_data(self, chan):
        #self.raw_data = chan[:, 1]
        self.time_data.setData(self.raw_data)
        self.fft_data()

    def fft_data(self):

	self.raw_data = np.array(self.raw_data)
        region =  self.lr.getRegion()
        cut_data = self.raw_data[region[0]: region[1]]
        if not True:
            cut_data = cut_data * np.kaiser(len(cut_data), 8)
        #print chan
        #print len(chan)
        z = np.zeros(len(cut_data)*4)
        z[0:len(cut_data)] = cut_data

        if len(z)> 0:
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
	    self.raw_data = []

            if self.sin_radio.isChecked():
                self.audio.waveform = 'tmp/sin.wav'
                write_sine(frequency=self.sin_freq.value(), t=self.pulse_len.value())
                pass
            else:
                self.audio.waveform = 'tmp/chirp.wav'
                write_chirp(start=self.chirp_start.value(), stop=self.chirp_stop.value(), t=self.pulse_len.value())
	    
	    self.get_data()
    
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
        self.pulse_len = QtGui.QDoubleSpinBox()
        self.len_label = QtGui.QLabel()


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
        self.len_label.setText('Length(s)')

        
        layout.addWidget(self.start_btn, 4, 0)
        layout.addWidget(self.mode_group, 1, 0)
        layout.addWidget(self.pulse_group, 2, 0)
        layout.addWidget(self.graph, 0, 0)
        layout.addWidget(self.sin_settings, 3, 0)
        layout.addWidget(self.chirp_settings, 3, 0)
        layout.addWidget(self.contin, 5, 0)

        sin_layout.addWidget(self.sin_freq_lbl)
        sin_layout.addWidget(self.sin_freq)
        sin_layout.addWidget(self.len_label)
        sin_layout.addWidget(self.pulse_len)
        chirp_layout.addWidget(self.chirp_start_lbl)
        chirp_layout.addWidget(self.chirp_start)
        chirp_layout.addWidget(self.chirp_stop_lbl)
        chirp_layout.addWidget(self.chirp_stop)
        chirp_layout.addWidget(self.len_label)
        chirp_layout.addWidget(self.pulse_len)
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
        self.emission.setChecked(True)
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
        self.pulse_len.setMinimum(0.1)
        self.pulse_len.setMaximum(3)
        self.pulse_len.setValue(0.5)
        self.pulse_len.setSingleStep(.2)
        
        

        self.absorbption.setEnabled(False)



class PlaySound(QtCore.QThread):

    def __init__(self, audio):
        super(PlaySound, self). __init__()
        self.folder = 'tmp'
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
        self.audio.full_data.connect(self.get_data)
        self.sound = 'sin.wav'
    def get_data(self, data):
        self.dataReady.emit(data)
        self.audio.stop_stream()
    def run(self):
        self.audio.setup_device()
        #datax = (self.audio.average(self.avgs))
        self.audio.start()
        #print "playing"
        #play()
        


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)

    blarg = GUI()
    blarg.show()
    app.exec_()
