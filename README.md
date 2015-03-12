# Sound-Spectrometer
Creates spectra from playback and recording of sound waves


This is designed to create either a single frequency audio snippet
or chirped frequency sweep between 0-20KHz and play that sound through a speaker.

The output is recorded through a microphone and both the time data and FFT are 
displayed on screen

The program uses the current system default microphone and speaker devices sobe
sure to set these defaults before launching the software.


Currently only "emission" modes are working.  Support for absorbtion will be added

Averaging is currently not working as it would require a "stable" trigger instead
of using the system clock
