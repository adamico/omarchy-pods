# Heart rate probe (AirPods Pro 3, BlueZ)

A throwaway probe for [Try heart rate on your AirPods Pro 3, with and without the Apple DeviceID](https://github.com/adamico/omarchy-pods/issues/6). It is not meant to be merged.

Run on 2026-10-24 with an A3064 on firmware 9442752, from a Linux laptop with BlueZ's own DeviceID (no spoof). The AirPods were in the ears, and no iPhone was nearby.

- The AACP connect, the handshake (v3), the INFORMATION message and control 0x30 (HRM state = 1) all work from BlueZ.
- Starting on service 84 is acknowledged as `08 14` (service 20, no error), but no samples arrive. Re-sending the start every 15 s, and connecting service 0 first, change nothing.
- Starting on service 19 is answered with status `0xE00002C2` (kIOReturnBadArgument).
- The sensor descriptors list `devmotion6`, `activity` and `SPL0`, but no `HeartRateService`.
- With the Apple DeviceID (`DeviceID = bluetooth:004C:0000:0000`, AirPods re-paired, run on 2026-10-24 at 21:08, `hr-20261024-210806.log`): nothing changes. Service 84 is still acknowledged as `08 14`, there are still no samples over 60 s with re-sends every 15 s, and the descriptors are still `devmotion6`, `activity` and `SPL0`, with no `HeartRateService`. The DeviceID alone is not the gate.

Logs: `hr-*.log`. Stop the daemon first (`systemctl --user stop librepods`), since only one host can hold PSM 0x1001.

## Hearing aid read probe

For [Read the current Hearing aid settings from your AirPods Pro 3](https://github.com/adamico/omarchy-pods/issues/7). `ha_probe.py` only reads. It never writes.

Run on 2026-10-26 at 10:37 (`ha-20261026-103726.log`) with the same A3064. BlueZ's own DeviceID was in use (`usb:v1D6Bp0246d0557`), the AirPods had just been re-paired, and the daemon was running with feature flags `D7`.

- The ATT read of `0x2A` on PSM 31 is **answered without the Apple DeviceID**: `0b` plus 104 bytes, header `02 00 60 00`, both Audiograms and all adjustments 0.0, own voice 0.5. The layout matches the Pro 2 research.
- `0x18` (Transparency customization) is also 104 bytes, all zero except own voice 0.5. `0x1b` (Loud Sound Reduction) is `01`.
- From `hr-20261024-210806.log` (Apple DeviceID on): the capability list (opcode `0x02`) has `HEARING_AID` 0x22 = 01, `HEARING_AID_V2` 0x31 = 01, 0xC0 = 02, `HEARING_TEST` 0xD0 = 02, `HEART_RATE_MONITOR` 0x26 = 01. Control `0x2C` reads `02 00` (not enrolled) and `0x33` reads `00`.
