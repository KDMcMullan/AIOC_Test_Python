# AIOC_Test_Python
Python script for Windows 10 to test AIOC

Using an [AIOC](https://github.com/skuep/AIOC) connected between Windows 10 and a suitable handheld transceiver, broadcasts a high C tone for a few seconds, then records for a few seconds.

The plan is to use my Quansheng UV-K5 as an Allstar node, but my Raspberry Pi Zero 2 W hasn't arrived yet! My AIOC has arrived, and I can't resist having a play with it.

Initially, I wrote the code to employ the serial DTR/RTS interface PTT, but I reapidly realised that the firmware I'd flashed to the AIOC defaulted to using the CM108 PTT mode. So the serial code is still in here, but it's
untested. Otherwise, the program proadcasts a high C tone for a few seconds, then records for a few seconds as a .WAV file.

You'll be pleased to know my AIOC adapter works.

You'll need the .INI file and he .PY file. Hopefully the .INI file is self-evident.

Ken McMullan, Feb 2026
