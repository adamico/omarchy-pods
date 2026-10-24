#!/usr/bin/env python3
"""Heart rate probe for AirPods Pro 3 over BlueZ (AACP, L2CAP PSM 0x1001).

Answers: does a Linux host with BlueZ's own DeviceID get Heart rate samples?
Frames follow research/heart-rate-protocol.md (librepods android/rewrite 34076c8).

Usage: hr_probe.py <AIRPODS_MAC> [--service 84|19] [--hs-version 2|3] [--hrm-state] [--seconds N]
Stop the omarchy-pods / librepods daemon first: only one host may hold PSM 0x1001.
Writes every received frame to hr-<timestamp>.log and samples to hr-<timestamp>.csv.
"""
import argparse
import csv
import socket
import struct
import sys
import time

PSM = 0x1001
HDR = bytes.fromhex("04000400")


def varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def field(num, wire, payload):
    key = varint((num << 3) | wire)
    if wire == 0:
        return key + varint(payload)
    return key + varint(len(payload)) + payload


def read_varint(buf, i):
    shift = n = 0
    while True:
        b = buf[i]
        i += 1
        n |= (b & 0x7F) << shift
        if not b & 0x80:
            return n, i
        shift += 7


def parse_proto(buf):
    """Flat protobuf decode: {field: [values]} with bytes for length-delimited."""
    out, i = {}, 0
    while i < len(buf):
        key, i = read_varint(buf, i)
        num, wire = key >> 3, key & 7
        if wire == 0:
            v, i = read_varint(buf, i)
        elif wire == 2:
            ln, i = read_varint(buf, i)
            v, i = buf[i:i + ln], i + ln
        elif wire == 5:
            v, i = buf[i:i + 4], i + 4
        elif wire == 1:
            v, i = buf[i:i + 8], i + 8
        else:
            raise ValueError(f"wire type {wire}")
        out.setdefault(num, []).append(v)
    return out


def sensor_setting(seq, service, interval_us):
    setting = field(1, 0, service) + field(2, 0, 2) + field(3, 2, b"\x01" + struct.pack("<I", interval_us))
    body = (field(1, 0, seq) if seq else b"") + field(8, 2, setting)
    envelope = struct.pack("<IH", 0x00100000, len(body)) + body
    return HDR + b"\x17\x00" + envelope


def handshake(version):
    return bytes.fromhex(f"000004000100{version:02x}000000000000000000")


SETUP = [
    bytes.fromhex("040004004d00d700000000000000"),  # SET_SPECIFIC_FEATURES
    bytes.fromhex("040004000f00ffffffffff"),        # REQUEST_NOTIFICATIONS
]
HRM_STATE_ON = bytes.fromhex("0400040009003001000000")  # control 0x30 = 1 (guess, issue 308)


def firmware_from_info(payload):
    strings = payload.split(b"\x00")
    strings = [s.decode(errors="replace") for s in strings if s]
    return strings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mac")
    ap.add_argument("--service", type=int, help="default: from firmware (>=9 -> 84)")
    ap.add_argument("--hs-version", type=int, default=3, choices=(2, 3))
    ap.add_argument("--hrm-state", action="store_true", help="send control 0x30=1 before starting")
    ap.add_argument("--seconds", type=int, default=90)
    ap.add_argument("--service0", action="store_true", help="AACP connect service 0 first (PR 702 / rtbuddy probe)")
    ap.add_argument("--resend", type=int, default=0, help="re-send start every N s and on each ear event")
    a = ap.parse_args()

    stamp = time.strftime("%Y%m%d-%H%M%S")
    log = open(f"hr-{stamp}.log", "w")
    out = csv.writer(open(f"hr-{stamp}.csv", "w", newline=""))
    out.writerow(["host_time", "service", "bpm", "b2_confidence", "b17_flags", "kept", "payload_hex"])

    def note(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
    note(f"connecting {a.mac} psm 0x{PSM:04x}")
    s.connect((a.mac, PSM))
    s.settimeout(1.0)

    def send(b, what):
        note(f"-> {what}: {b.hex(' ')}")
        s.send(b)

    if a.service0:
        send(bytes.fromhex("00000000010003000000000000000000"), "connect service 0")
        time.sleep(0.3)
        send(bytes.fromhex("04000000010000"), "caps request service 0")
        time.sleep(0.3)
    send(handshake(a.hs_version), f"handshake v{a.hs_version}")
    time.sleep(0.3)
    for b in SETUP:
        send(b, "setup")
        time.sleep(0.2)

    seq = 0
    fw = None
    started = None
    deadline = time.time() + a.seconds
    info_wait_until = time.time() + 5
    samples = 0
    while time.time() < deadline:
        if started is None and (fw is not None or time.time() > info_wait_until):
            service = a.service or (84 if fw and fw[:1].isdigit() and int(fw[0]) >= 9 else 19)
            if a.hrm_state:
                send(HRM_STATE_ON, "control 0x30 = 1")
                time.sleep(0.2)
            send(sensor_setting(seq, service, 1_000_000), f"start HR service {service} seq {seq}")
            seq += 1
            started = time.time()
        if started is not None and a.resend and time.time() - started > a.resend:
            send(sensor_setting(seq, service, 1_000_000), f"re-start HR service {service} seq {seq}")
            seq += 1
            started = time.time()
        try:
            data = s.recv(2048)
        except socket.timeout:
            continue
        if not data:
            note("socket closed")
            break
        note(f"<- {data.hex(' ')}")
        if not data.startswith(HDR) or len(data) < 6:
            continue
        op = data[4]
        if op == 0x1D:
            strs = firmware_from_info(data[6:])
            note(f"INFORMATION strings: {strs}")
            # librepods: version3 = strings[10] after dropping the first
            # version3 is the bare numeric build (e.g. 9442752); index varies with the binary prefix
            nums = [x for x in strs if x.isdigit() and 6 <= len(x) <= 8]
            if nums:
                fw = nums[0]
                note(f"firmware version3 = {fw}")
        elif op == 0x06:
            note(f"ear detection: {data[6:].hex(' ')}")
            if started is not None and a.resend:
                started = 0  # force a re-send on the next loop
        elif op == 0x17:
            env = data[6:]
            desc, ln = struct.unpack_from("<IH", env)
            if desc != 0x00100000:
                note(f"rtbuddy descriptor 0x{desc:08x}")
                continue
            msg = parse_proto(env[6:6 + ln])
            note(f"SensorDataWX fields: { {k: [v.hex() if isinstance(v, bytes) else v for v in vs] for k, vs in msg.items()} }")
            for cmd in msg.get(7, []):
                c = parse_proto(cmd)
                svc = c.get(1, [None])[0]
                p = c.get(3, [b""])[0]
                if len(p) == 18:
                    kept = p[17] == 0
                    samples += 1
                    note(f"HR sample service {svc}: {p[1]} bpm (conf {p[2]}, flags {p[16]:02x} {p[17]:02x}){'' if kept else ' [warm-up/invalid]'}")
                    out.writerow([time.strftime("%H:%M:%S"), svc, p[1], p[2], f"{p[17]:02x}", kept, p.hex()])
    if started is not None:
        try:
            send(sensor_setting(seq, a.service or service, 0), "stop HR")
        except OSError:
            pass
    note(f"done: {samples} heart rate samples")
    s.close()


if __name__ == "__main__":
    sys.exit(main())
