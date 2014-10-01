"""
PyAudio Example: Make a wire between input and output (i.e., record a
few samples and play them back immediately).
"""

import pyaudio
import wave

CHUNK = 128
WIDTH = 2
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 1

p = pyaudio.PyAudio()

stream = p.open(format=p.get_format_from_width(WIDTH),
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK)

print("* recording")
wf = wave.open('sin.wav', 'rb')
data_p = wf.readframes(CHUNK)
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    stream.write(data_p)#, CHUNK)
    data_p = wf.readframes(CHUNK)

print("* done")


stream.stop_stream()
stream.close()

p.terminate()
