############################################################
#
# AIOC Test
# aioc_test.py
#
# Requires: aioc_test.ini
# Platform: Windows 10
# Tested hardware: AIOC hardware v1.0
# Tested firmware: v1.4.1.
#
# Ken McMullan, Feb 2026
#
# The plan is to use my Quansheng UV-K5 as an Allstar node,
# but my Raspberry Pi Zero 2 W hasn't arrived yet! My AIOC
# has arrived, and I can't resist having a play with it.
#
# Initially, I wrote the code to employ the serial DTR/RTS
# interface PTT, but I reapidly realised that the firmware
# I'd flashed to the AIOC defaulted to using the CM108 PTT
# mode. So the serial code is still in here, but it's
# untested. Otherwise, the program proadcasts a high C
# tone for a few seconds, then records for a few seconds
# as a .WAV file.
#
# You'll be pleased to know my AIOC adapter works.
#
############################################################


import time
import configparser
import numpy as np
import sounddevice as sd
import soundfile as sf

import serial
import hid

############################################################
# Read Config
############################################################

cfg = configparser.ConfigParser()
cfg.read("aioc_test.ini")

TX_DEV_NAME = cfg["aioc"]["tx_device_name"]
RX_DEV_NAME = cfg["aioc"]["rx_device_name"]

PTT_MODE = cfg["ptt"]["mode"].lower()
print(f"PTT MODE: {PTT_MODE}")

SAMPLE_RATE = int(cfg["audio"]["sample_rate"])
TX_DURATION = float(cfg["audio"]["tx_duration"])
RX_RECORD_TIME = float(cfg["audio"]["rx_record_time"])
TX_TONE_HZ = float(cfg["audio"]["tx_tone_hz"])

RX_WAV_FILE = "aioc_rx_test.wav"

############################################################
# Subs
############################################################

def find_device(name, direction):
    for idx, dev in enumerate(sd.query_devices()):
        if name.lower() in dev["name"].lower():
            if direction == "out" and dev["max_output_channels"] > 0:
                return idx
            if direction == "in" and dev["max_input_channels"] > 0:
                return idx
    raise RuntimeError(f"{direction} device '{name}' not found")

def generate_tx_audio(duration, fs, freq):
    t = np.linspace(0, duration, int(fs * duration), False)
    tone = 0.6 * np.sin(2 * np.pi * freq * t)
    return tone.astype(np.float32)

############################################################
# PTT Classes
############################################################

class HidPtt:
    def __init__(self, cfg):
        self.vid = int(cfg["ptt"]["hid_vid"], 16)
        self.pid = int(cfg["ptt"]["hid_pid"], 16)
        self.gpio = int(cfg["ptt"]["hid_gpio_ptt"], 16)

        self.h = hid.device()
        self.h.open(self.vid, self.pid)

    def set(self, on: bool):
        mask = self.gpio
        value = self.gpio if on else 0x00
        # report_id = 0x00
        self.h.write([0x00, mask, value])

    def close(self):
        self.h.close()


class SerialPtt:
    def __init__(self, cfg):
        self.port = cfg["ptt"]["com_port"]
        self.active_low = cfg.getboolean("ptt", "serial_active_low")
        self.settle = float(cfg["ptt"]["serial_settle_time"])

        self.ser = serial.Serial(self.port, baudrate=9600)
        print(f"Initial RTS: {self.ser.rts}, Initial DTR: {self.ser.dtr}")

        # Force known OFF state
        off = not self.active_low
        self.ser.rts = off
        self.ser.dtr = off
        time.sleep(0.1)

    def set(self, on: bool):
        level = not on if self.active_low else on
        self.ser.dtr = level
        time.sleep(0.02)
        self.ser.rts = level
        time.sleep(self.settle)

    def close(self):
        self.ser.close()

############################################################
# Main
############################################################

def main():
    print(f'Locating AIOC devices "{TX_DEV_NAME}", "{RX_DEV_NAME}" ...')
    tx_dev = find_device(TX_DEV_NAME, "out")
    rx_dev = find_device(RX_DEV_NAME, "in")

    print(f"TX device index: {tx_dev}, RX device index: {rx_dev}")

    print(f"PTT mode: {PTT_MODE}")

    if PTT_MODE == "hid":
        ptt = HidPtt(cfg)
    elif PTT_MODE == "serial":
        ptt = SerialPtt(cfg)
    else:
        raise RuntimeError('Invalid PTT mode ("{PTT_MODE}") in config')

    tx_audio = generate_tx_audio(
        TX_DURATION,
        SAMPLE_RATE,
        TX_TONE_HZ
    )

    print("Asserting PTT...")
    ptt.set(True)
    time.sleep(0.1)

    print("Transmitting audio...")
    sd.play(
        tx_audio,
        samplerate=SAMPLE_RATE,
        device=tx_dev,
        blocking=True
    )

    print("Releasing PTT...")
    ptt.set(False)

    print(f"Recording RX audio to {RX_WAV_FILE} ...")
    rx_audio = sd.rec(
        int(RX_RECORD_TIME * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        device=rx_dev,
        dtype="float32"
    )
    sd.wait()

    sf.write(RX_WAV_FILE, rx_audio, SAMPLE_RATE)

    ptt.close()
    print("Test complete.")

############################################################

if __name__ == "__main__":
    main()


