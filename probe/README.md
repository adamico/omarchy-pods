# Heart rate probe (AirPods Pro 3, BlueZ)

A throwaway probe for [Try heart rate on your AirPods Pro 3, with and without the Apple DeviceID](https://github.com/adamico/omarchy-pods/issues/6). It is not meant to be merged.

Run on 2026-10-24 with an A3064 on firmware 9442752, from a Linux laptop with BlueZ's own DeviceID (no spoof). The AirPods were in the ears, and no iPhone was nearby.

- The AACP connect, the handshake (v3), the INFORMATION message and control 0x30 (HRM state = 1) all work from BlueZ.
- Starting on service 84 is acknowledged as `08 14` (service 20, no error), but no samples arrive. Re-sending the start every 15 s, and connecting service 0 first, change nothing.
- Starting on service 19 is answered with status `0xE00002C2` (kIOReturnBadArgument).
- The sensor descriptors list `devmotion6`, `activity` and `SPL0`, but no `HeartRateService`.
- Still untested: the Apple DeviceID spoof.

Logs: `hr-*.log`. Stop the daemon first (`systemctl --user stop librepods`), since only one host can hold PSM 0x1001.
