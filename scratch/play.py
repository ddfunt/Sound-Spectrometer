"""PyAudio Example: Play a wave file."""

import pyaudio
import wave
import sys

CHUNK = 1024

filename = 'output2.wav'

wf = wave.open(filename, 'rb')

# instantiate PyAudio (1)
p = pyaudio.PyAudio()

print wf.getframerate()
# open stream (2)
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)

# read data
data = wf.readframes(CHUNK)

# play stream (3)
while data != '':
    stream.write(data)
    data = wf.readframes(CHUNK)

# stop stream (4)
stream.stop_stream()
stream.close()

# close PyAudio (5)
p.terminate()