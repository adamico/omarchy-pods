# Heart rate on AirPods Pro 3: how upstream starts, reads and stops it

Research for [adamico/omarchy-pods#2](https://github.com/adamico/omarchy-pods/issues/2).
Researched 2026-10-11. No Bluetooth device was touched; everything below comes from
source code, upstream docs, issues and pull requests.

## Answer

Upstream librepods (`android/rewrite`) turns Heart rate samples on and off with a single
AACP message, opcode `0x17` (buddy command). Its body is a protobuf `SensorDataWX` holding a
`SensorServiceSetting` for the heart rate sensor service. The setting says "report every
1 second" to start and "report every 0" to stop. Firmware with a version string that starts
with `9` or higher is addressed as service 84 (`HEARTRATE_COMMAND`), and older firmware as
service 19 (`HEARTRATE`). While the AirPods Pro 3 are worn, they send back one opcode `0x17`
message per second. Each one carries an 18 byte sensor payload under service 19 or 20, with
beats per minute in byte 1 as an unsigned byte. Byte 17 marks the sample as not yet valid.
Nothing in upstream's path needs the Apple DeviceID. The fork's daemon has the AACP socket
and handshake but lacks everything specific to heart rate (details at the end).

## Sources

Upstream moved from `kavishdevar/librepods` to `librepods-org/librepods`; the old URL
redirects. Code is quoted from `android/rewrite` at commit
[`34076c8`](https://github.com/librepods-org/librepods/commit/34076c85f0fc2eaf32ad1d5cad1bb7315df9c89c)
(2026-10-11, "android: fix heart rate parsing, the value is an unsigned byte"). The paths
below are relative to `android/app/src/main/kotlin/me/kavishdevar/librepods/` unless they
start with `android/` or `docs/`.

| Short name | File |
|---|---|
| AppleDevice | `devices/AppleDevice.kt` (`startHr`, `stopHr`, lines 338 to 365) |
| RTBuddyManager | `bluetooth/aacp/RTBuddyManager.kt` |
| RTBuddyPacket | `bluetooth/aacp/packet/RTBuddyPacket.kt` |
| AACPPacket | `bluetooth/aacp/packet/AACPPacket.kt` |
| AACPManager | `bluetooth/aacp/AACPManager.kt` (connection setup lines 78 to 161, dispatch 341 to 364, sensor handler 1147 to 1235) |
| InformationPacket | `bluetooth/aacp/packet/InformationPacket.kt` |
| rtbuddy.proto | `android/app/src/main/proto/rtbuddy.proto` |
| Descriptors | `bluetooth/aacp/types/RTBuddyDescriptor.kt` |
| Capability, ControlCommand | `bluetooth/aacp/types/Capability.kt`, `bluetooth/aacp/types/ControlCommand.kt` |
| AAP Definitions | `docs/AAP Definitions.md`, section "Head Tracking" |
| control_commands | `docs/control_commands.md`, `0x30` |

Upstream discussion, all first hand reports from people running the code on hardware:

- [PR 806](https://github.com/librepods-org/librepods/pull/806) (open, base `android/rewrite`): byte layout observed on AirPods Pro 3 A3063, firmware `9442752`, on an unrooted Galaxy S26 Ultra.
- [PR 807](https://github.com/librepods-org/librepods/pull/807) (open): crash when the firmware version is not known yet.
- [PR 811](https://github.com/librepods-org/librepods/pull/811) (open): samples only flow while worn, so the start is sent again on ear in.
- [PR 702](https://github.com/librepods-org/librepods/pull/702) (open, base `main`, a separate implementation): discovers the service number from sensor descriptors and validates samples more strictly. It builds on [tomppi/airpods_rtbuddy_v37_probe](https://github.com/tomppi/airpods_rtbuddy_v37_probe).
- [Issue 308](https://github.com/librepods-org/librepods/issues/308) and [issue 713](https://github.com/librepods-org/librepods/issues/713): background only; neither contains packets that were checked on hardware.

The upstream README on the same branch still lists Heart Rate Monitoring as not implemented
on Android or Linux and says it will "most likely need root". The code and the pull requests
above are newer than that line, and the PR testing used no root.

## Framing

Every AACP message upstream sends is `type 00 service 00 opcode 00 payload`
(AACPPacket, `rawPacket`). For messages that is `04 00 04 00 <opcode> 00`. Opcode `0x17` is
`MessageOpcode.BUDDY_COMMAND`. Its payload is an RTBuddy envelope (RTBuddyPacket `create`
and `parse`):

| Offset in payload | Size | Meaning |
|---|---|---|
| 0 | 4, little endian | descriptor; `0x00100000` is `SENSOR_DATA_WX` (Descriptors) |
| 4 | 2, little endian | length of the protobuf that follows |
| 6 | length | `rtbuddy.SensorDataWX` protobuf |

The protobuf fields that matter (rtbuddy.proto):

```
SensorDataWX { int32 seq = 1; int32 log_type = 2; ...;
               SensorDescriptor sensor_descriptor = 5;
               SensorCommand command = 7;            // samples arrive here
               SensorServiceSetting service_settings = 8; // start and stop go here
               SensorTypeAck start_ack = 9; SensorTypeAck command_ack = 12; }
SensorCommand        { SensorServiceType service = 1; bytes payload = 3; }
SensorServiceSetting { SensorServiceType service = 1; int32 setting = 2; bytes configuration = 3; }
SensorServiceType: HEARTRATE = 19, HEARTRATEv2 = 20, HEARTRATE_COMMAND = 84, ACTIVITY = 14, DEVMOTION6 = 16
```

## Start and stop

`AppleDevice.startHr()` calls `setSensorServiceReportInterval(service, 1.seconds)` and
`stopHr()` calls it with `Duration.ZERO`. The service is chosen by
`metadata.version3.first().digitToInt() >= 9`: `HEARTRATE_COMMAND` (84) if so, `HEARTRATE`
(19) otherwise. `RTBuddyManager.sendSensorServiceSetting` always uses `setting = 2` and
`configuration = 01` followed by the interval in microseconds as 4 bytes little endian.
`seq` is a per connection counter that starts at 0 and goes up by one per message; nothing
is sent for `log_type`.

Encoded with that layout, the frames are:

| Message | Bytes |
|---|---|
| Start, service 84, `seq` 0 | `04 00 04 00 17 00 00 00 10 00 0D 00 42 0B 08 54 10 02 1A 05 01 40 42 0F 00` |
| Stop, service 84, `seq` 1 | `04 00 04 00 17 00 00 00 10 00 0F 00 08 01 42 0B 08 54 10 02 1A 05 01 00 00 00 00` |
| Start, service 19, `seq` 0 | `04 00 04 00 17 00 00 00 10 00 0D 00 42 0B 08 13 10 02 1A 05 01 40 42 0F 00` |
| Stop, service 19, `seq` 1 | `04 00 04 00 17 00 00 00 10 00 0F 00 08 01 42 0B 08 13 10 02 1A 05 01 00 00 00 00` |

`40 42 0F 00` is 1,000,000 microseconds. Proto3 leaves out a field whose value is 0, so
`seq` 0 produces no `08 xx` pair. I checked the encoder by having it reproduce the documented
head tracking start frame byte for byte (AAP Definitions:
`04 00 04 00 17 00 00 00 10 00 10 00 08 A1 02 42 0B 08 0E 10 02 1A 05 01 40 9C 00 00`, which
is service 14, `seq` 289, 40 ms). The heart rate frames here are derived from the code, not
captured. PR 807 confirms that a frame beginning `04 00 04 00 17` goes out and samples follow,
on firmware `9442752`.

PR 702 builds the same `service_settings` frame (fields 1, 2 = 2, 3 = `01` + interval) but
its `seq` starts at 9059. The probe repository uses `0x2363`. So the AirPods do not seem to
require any particular starting `seq`.

## Samples

`AACPManager.processPacket` only accepts input that starts with `04 00 04 00`. For opcode
`0x17` it parses the envelope and, for descriptor `SENSOR_DATA_WX`, runs `handleSensorData`.
A Heart rate sample is a `SensorDataWX` with `command` (field 7) set, where:

- `command.service` is 19 or 20. The handler does not match 84, so on firmware 9 the start is
  addressed to 84 while the samples come back as 19 or 20. Which of the two shows up on
  firmware 9 is not recorded anywhere I found.
- `command.payload` is exactly 18 bytes. Any other size is logged and dropped.
- Upstream drops the sample if `payload[17] != 0`.
- Beats per minute is `payload[1] and 0xFF`. Before `34076c8` it was read signed, which lost
  every reading of 128 or more (PR 806, item 3).
- The timestamp is the host clock when the message arrives (`Clock.System.now()`). Nothing in
  the payload is used as a time.

The first valid sample moves `hrmState` from `WAITING` to `ACTIVE`.

What else is known about the 18 bytes comes from observation, not from code (PR 806, item 6,
and PR 702's decoder):

| Byte | Observed |
|---|---|
| 1 | beats per minute, unsigned |
| 2 | looks like confidence: 20 during warm up, 120 to 237 after |
| 3 | sample sequence number |
| 15 | `0x10` or `0x20` in every accepted sample (PR 702) |
| 16, 17 | `82 81` on the first sample, then `02 81` during warm up; `00 00` once settled; briefly `00 80` during motion |

Samples during warm up are wrong (169, 100, 76, 76 while resting at about 75). There are
about four of them per session.

There are three validity rules in circulation, and they disagree:

- Upstream today drops anything with `payload[17] != 0`. That also drops the `00 80` motion
  samples.
- PR 806 proposes dropping only when bit 0 of `payload[17]` is set. That keeps the motion
  samples, and a 112 sample replay checked it (4 dropped, 108 kept).
- PR 702 and the probe accept only a known tail at bytes 15 to 17 (`10 00 00`, `10 00 80`,
  `20 00 00`, `20 80 00`, `20 02 80`, `20 82 80`). They also require 30 to 220 beats per
  minute, and `log_type` (field 2) of 1 or 3. The probe saw `log_type` 3 on live samples.

## Prerequisites and conditions

- **AACP connection.** Classic L2CAP PSM `0x1001` (`createSocket(..., 4097)` in AACPManager).
  Upstream sends a connect for service 4 with protocol version 3
  (`00 00 04 00 01 00 03 00 00 00 00 00 00 00 00 00`), then
  `SOURCE_FEATURE_CAPABILITIES` (`4D`, `d7 00 ...`), `REQUEST_NOTIFICATIONS`
  (`0F`, `ff ff ff ff`), `SET_COUNTRY_CODE`, and a magic keys request. Heart rate code never
  waits on any of these, and nothing shows which of them it needs. PR 702 and the probe also
  connect service 0 first.
- **Firmware version.** The `INFORMATION` message (opcode `0x1D`) carries NUL separated
  strings. The firmware version upstream uses is string 10 after the first is dropped
  (InformationPacket, `version3`), for example `9442752`. Until that message has arrived,
  upstream cannot pick a service. PR 807 shows that a reconnect then crashes with
  `NoSuchElementException`.
- **Worn.** The sensor only streams while the AirPods Pro 3 are in the ears. A start sent
  while they are in the case delivered nothing for 58 s; sending it again after ear in
  produced samples within 2 s (PR 811). An app that offers live heart rate has to send the
  start again on every ear in event.
- **Connected first.** A start sent while the socket is still connecting is lost (PR 811).
- **Apple DeviceID: does not appear to be needed.** Nothing in the heart rate path checks the
  host's identity. The PR 806, 807 and 811 testing ran on an unrooted phone using native
  L2CAP. Upstream's "act as Apple device" switch needs Xposed (README, VendorID spoofing
  section), so that phone was not presenting Apple's vendor ID. This is an inference from
  Android tests, not a Linux test: BlueZ presents its own DeviceID by default, and I found
  nobody who has tried heart rate from BlueZ. Upstream lists Loud Sound Reduction as needing
  the Apple DeviceID; heart rate is not on that list.
- **Capability and control bits.** The AirPods advertise capability `0x26`
  (`HEART_RATE_MONITOR`). Upstream parses it but does not use it to gate heart rate. Control
  command `0x30` (`HRM_STATE`, "HRM enable/disable state") exists. The probe sends
  "`0x30` = enabled" before starting; upstream `android/rewrite` never sends it. The
  maintainer guessed that the iOS "Heart Rate" privacy toggle is `0400040009003001`
  (issue 308).
- **Service number.** Upstream hard codes 19 or 84 by firmware. PR 702 reads it from sensor
  descriptor messages instead. It takes the service whose descriptor metadata contains the
  ASCII text `HeartRateService`, and never one whose metadata says `HostLibHID`. It falls back
  to 19 if no descriptor names one.

## What the fork's daemon lacks

Checked against `daemon/` at `fff7fec`.

What it already has: the L2CAP AACP socket, a handshake, `SET_SPECIFIC_FEATURES` (the same
`4D d7` message), `REQUEST_NOTIFICATIONS`, ear detection parsing, the `status.json` state
file, and the `$XDG_RUNTIME_DIR/librepods.sock` verbs.

What it lacks:

1. **No opcode `0x17` handling at all.** `parseData` has no branch for it, so samples would
   fall through to "Unrecognized packet format".
2. **No RTBuddy envelope or protobuf.** The daemon has no protobuf dependency. The messages
   are small enough to encode and decode by hand: varint, length delimited fields 1, 2, 3, 5,
   7 and 8. This avoids adding a protobuf library.
3. **No firmware version.** `parseMetadata` reads only the first three strings (name, model
   number, manufacturer) and stops. It needs to read on to `version3`, and to persist it so a
   reconnect knows the service before the `INFORMATION` message arrives.
4. **Handshake version.** The daemon's `HANDSHAKE` is
   `00 00 04 00 01 00 02 00 ...`, protocol version 2. Upstream's heart rate testing used
   version 3 (`03`). Whether version 2 is enough for sensor data is unknown.
5. **No per connection `seq` counter, no start and stop verbs, and no re-start on ear in.**
   The ear detection parser exists, but nothing would hook a re-start onto it.
6. **No way to hand samples to the app.** `status.json` is written only on state changes and
   holds a single state. A stream of one Heart rate sample per second needs either a new
   field there or a streaming verb on the local socket. Which one is a decision for the app
   and daemon interface.
7. **Message boundaries.** `readyRead` hands `readAll()` to `parseData` as one message. A
   sample frame is about 40 bytes, so two frames could arrive in one read. Upstream reads at
   most 1024 bytes per read and has the same weakness; PR 702's decoder reassembles frames.
   The daemon should split frames by their declared length.

## Unknowns

- Whether firmware 9 samples arrive as service 19 or 20, and what service 20 means compared
  with 19.
- Whether `HRM_STATE` (`0x30`) must be enabled first, for example after the user turned heart
  rate off in iOS settings.
- Whether BlueZ's default DeviceID is accepted. This needs a test on hardware from Linux.
- Whether protocol version 2 in the fork's handshake is enough.
- What bytes 0, 4 to 14 and 15 mean. Which validity rule is right, and whether `00 80`
  motion samples should be kept.
- What `start_ack` (field 9) and `command_ack` (field 12) look like. Upstream defines them
  but never reads them, so there is no confirmation that a start was accepted beyond the
  first sample arriving.
- Whether a report interval other than 1 s is honoured.
