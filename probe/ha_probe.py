#!/usr/bin/env python3
"""Read-only Hearing aid probe for AirPods Pro 3 over BlueZ (ATT, L2CAP PSM 31).

Answers: does a Pro 3 answer a read of the 104-byte Hearing aid value at handle 0x2A,
and what does it hold? Layout from research/hearing-aid-protocol.md. Never writes.

Usage: ha_probe.py <AIRPODS_MAC> [--handles 2a,18,1b]
Writes every frame to ha-<timestamp>.log.
"""
import argparse
import socket
import struct
import sys
import time

PSM_ATT = 31
FREQS = (250, 500, 1000, 2000, 3000, 4000, 6000, 8000)
ATT_ERRORS = {0x02: "read not permitted", 0x05: "insufficient authentication",
              0x0E: "unlikely error", 0x0A: "attribute not found", 0x01: "invalid handle"}


def decode_hearing_aid(v, note):
    if len(v) != 104:
        note(f"value is {len(v)} bytes, not 104: layout unknown")
        return
    note(f"header: {v[:4].hex(' ')}")
    f = struct.unpack("<25f", v[4:])
    for side, base in (("left", 0), ("right", 12)):
        gram = ", ".join(f"{hz}: {f[base + i]:.1f}" for i, hz in enumerate(FREQS))
        note(f"{side} audiogram dB HL: {gram}")
        note(f"{side} amplification {f[base + 8]:.3f}, tone {f[base + 9]:.3f}, "
             f"conversation boost {f[base + 10]:.3f}, ambient noise reduction {f[base + 11]:.3f}")
    note(f"own voice: {f[24]:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mac")
    ap.add_argument("--handles", default="2a,18,1b")
    a = ap.parse_args()

    log = open(f"ha-{time.strftime('%Y%m%d-%H%M%S')}.log", "w")

    def note(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
    note(f"connecting {a.mac} psm {PSM_ATT}")
    s.connect((a.mac, PSM_ATT))
    s.settimeout(3.0)

    for h in (int(x, 16) for x in a.handles.split(",")):
        pdu = bytes([0x0A, h & 0xFF, h >> 8])
        note(f"-> read 0x{h:02x}: {pdu.hex(' ')}")
        s.send(pdu)
        try:
            while True:
                r = s.recv(1024)
                note(f"<- {r.hex(' ')}")
                if r[0] == 0x1B:  # notification, keep waiting for the response
                    continue
                break
        except socket.timeout:
            note("no response")
            continue
        if r[0] == 0x01:
            note(f"error 0x{r[4]:02x} ({ATT_ERRORS.get(r[4], '?')}) on handle 0x{h:02x}")
        elif r[0] == 0x0B:
            note(f"handle 0x{h:02x}: {len(r) - 1} bytes")
            if h == 0x2A:
                decode_hearing_aid(r[1:], note)
    s.close()
    note("done")


if __name__ == "__main__":
    sys.exit(main())
