# How the Hearing aid is read and written on AirPods Pro 3

Research for [issue #3](https://github.com/adamico/omarchy-pods/issues/3).
Terms follow `GLOSSARY.md`: AirPods Pro 3, Audiogram, Hearing aid.

## Answer in short

The Hearing aid has two halves on two different channels.

1. **The data** (the Audiogram plus every adjustment) is one 104-byte value at
   handle `0x002A` of an ATT server the AirPods expose on L2CAP PSM 31. It is
   read with an ATT Read Request and written back whole with an ATT Write. The
   value is little-endian 32-bit floats: 8 Audiogram thresholds per ear in
   dB HL, then 4 adjustments per ear, then one shared float.
2. **The switch** is two control commands on the AAP control channel (L2CAP
   PSM `0x1001`, the channel the daemon already owns): `0x2C` (two bytes,
   "enrolled" and "enabled") and `0x33` (Hearing Assist, one byte). The
   Hearing aid only acts on sound in Transparency.

The ATT half only answers when the host's Device ID profile record names Apple
(`DeviceID = bluetooth:004C:0000:0000` in BlueZ). The AirPods cache the vendor
they saw when the host first connected, so after changing it the AirPods must
be re-paired, sometimes more than once.

No primary source contains a capture of the Hearing aid on an AirPods Pro 3.
Everything below about the wire format was captured or reported on other
models (AirPods Pro 2 where the model is stated) and is assumed to hold for the
Pro 3 until it is measured.

## Sources

| Short name | What it is | Version read |
|---|---|---|
| Gist | [rithvikvibhu, "Apple Airpods" `aap.md`](https://gist.github.com/rithvikvibhu/45e24bbe5ade30125f152383daf07016), iPhone PacketLogger captures of the Hearing Assistance pages. Credited by the librepods README for the Hearing aid work. | updated 2026-02-16 |
| Linux script | [`linux/hearing-aid-adjustments.py`](https://github.com/librepods-org/librepods/blob/efccc4499b2c1fd2ac243e975ae1f42d8e828ffd/linux/hearing-aid-adjustments.py), byte-identical to this fork's `daemon/hearing-aid-adjustments.py` | upstream `main` at `efccc44` (2026-10-06) |
| Android main | `android/.../data/HearingAid.kt`, `bluetooth/ATTManager.kt`, `presentation/screens/HearingAidScreen.kt`, `services/AirPodsService.kt`, `cpp/l2c_fcr_hook.cpp` | `main` at `efccc44` |
| Android rewrite | `android/.../bluetooth/att/types/HearingAid.kt`, `bluetooth/att/ATTManager.kt`, `devices/AppleDevice.kt`, `devices/AirPods.kt`, `bluetooth/aacp/types/Capability.kt` | `android/rewrite` at `34076c8` (2026-10-10) |
| Control docs | [`docs/control_commands.md`](https://github.com/librepods-org/librepods/blob/efccc4499b2c1fd2ac243e975ae1f42d8e828ffd/docs/control_commands.md), identical on both branches | `efccc44` |
| Fork daemon | `daemon/airpods_packets.h`, `daemon/BasicControlCommand.hpp`, `daemon/main.cpp`, `daemon/README.md` | this branch |
| Issues | librepods-org/librepods [#227](https://github.com/librepods-org/librepods/issues/227), [#358](https://github.com/librepods-org/librepods/issues/358), [#398](https://github.com/librepods-org/librepods/issues/398), [#464](https://github.com/librepods-org/librepods/issues/464), [#558](https://github.com/librepods-org/librepods/issues/558), [#659](https://github.com/librepods-org/librepods/issues/659), PR [#333](https://github.com/librepods-org/librepods/pull/333) | read 2026-10-11 |

The upstream repository moved from `kavishdevar/librepods` to
`librepods-org/librepods`; issue numbers are the same.

## 1. The data: ATT handle 0x2A on PSM 31

### The channel

- A plain L2CAP connection (`SOCK_SEQPACKET`, `BTPROTO_L2CAP`) to the AirPods
  on PSM 31 carries raw ATT PDUs, no GATT discovery. (Linux script `connect`;
  Android main opens the same with PSM 31 in `AirPodsService.kt`.)
- Three handles are known, the same on every branch: `0x18` Transparency
  customization, `0x1B` Loud Sound Reduction, `0x2A` Hearing aid. Each
  characteristic's notification descriptor is the handle plus one, so the
  Hearing aid one is `0x2B`. (Linux script `ATT_HANDLES`; Android main
  `ATTHandles`; Android rewrite `ATTHandle`.)
- Android main keeps PSM 31 open only when the vendor hook is on
  (`vendor_id_hook`, `AirPodsService.kt`), which ties this channel to the Apple
  DeviceID.

### Read

```
host    -> 0A 2A 00                    ATT Read Request, handle 0x002A
airpods <- 0B <104 bytes>              ATT Read Response
```

Without the Apple DeviceID the same request is refused:

```
airpods <- 01 0A 2A 00 0E              ATT Error Response, "Unlikely Error"
```

(Both from the logs in #227. The refusal disappeared after the DeviceID was set,
BlueZ was restarted and the AirPods were re-paired.)

### Write

The Linux script and both Android branches use a Write Request and wait for
the Write Response:

```
host    -> 12 2A 00 <104 bytes>        ATT Write Request
airpods <- 13                          ATT Write Response
```

The iPhone sends the same value with a Write Command, opcode `0x52`, which has
no response (every capture in the Gist starts `52 2A 00`). The AirPods accept
both (the `13` responses in #358).

All three librepods implementations do read-modify-write: read the current
104 bytes, overwrite the floats, set byte 2 to `0x64`, write all 104 back
(Linux script `send_hearing_aid_settings`, Android `sendHearingAidSettings`,
commented "for some reason").

### Notifications

The Linux script writes `01 00` to `0x2B` and gets `13` back, then listens for
`1B 2A 00 <value>` (Handle Value Notification). Android main writes a single
`01`. The Android rewrite drops notifications on purpose and polls once a
second instead, with this comment in `devices/AppleDevice.kt`:

> can't use att notifications; keeping ATT connected causes airpods to
> disconnect every few seconds for some reason

In the rewrite the ATT read and write are stubs that return early (`// TODO`
in `bluetooth/att/ATTManager.kt`), so the rewrite does not yet talk to the
Hearing aid at all. Its intended design opens PSM 31, does one exchange and
closes it, per call.

### The 104-byte value

Offsets are into the value, after the 3-byte ATT header. All floats are IEEE
754 single precision, little-endian.

| Offset | Size | Field | Values seen |
|---|---|---|---|
| 0 | 1 | unknown | always `02` |
| 1 | 1 | unknown, see below | `00` on AirPods never given an Audiogram, `02` once one is written the iPhone way |
| 2 | 1 | unknown | `60` when read, `64` when written (iPhone and librepods both write `64`) |
| 3 | 1 | unknown | `00` |
| 4 | 32 | left Audiogram, 8 floats | thresholds in dB HL at 250, 500, 1000, 2000, 3000, 4000, 6000, 8000 Hz |
| 36 | 4 | left amplification | net amplification plus or minus the balance shift |
| 40 | 4 | left tone | -1 darker to +1 brighter |
| 44 | 4 | left conversation boost | `0.0` off, `1.0` on |
| 48 | 4 | left ambient noise reduction | 0 less to 1 more |
| 52 | 32 | right Audiogram, 8 floats | same frequencies |
| 84 | 4 | right amplification | as left |
| 88 | 4 | right tone | as left |
| 92 | 4 | right conversation boost | as left |
| 96 | 4 | right ambient noise reduction | as left |
| 100 | 4 | own voice amplification | `0.5` in every capture |

Facts behind the table, all from the Gist unless noted:

- **Audiogram values are the dB HL numbers themselves**, no scaling. Left
  250 Hz = 31 dB HL is written as `00 00 F8 41` (31.0).
- **Exactly 8 frequencies per ear.** iOS drops 125 Hz and 750 Hz from the
  Audiogram it was given, and fills frequencies the Audiogram lacks with
  averages of their neighbours before writing. (Audiogram 2 had no 3000 Hz;
  the written value at 3000 Hz is the mean of 2000 and 4000.) The app must do
  this mapping itself.
- **Amplification** is -1 to +1. **Balance** has no field of its own: it moves
  at most 0.5 of amplification from one ear to the other, so with
  amplification 1 and balance full left the ears read 1.5 and 0.5. Tone,
  conversation boost and ambient noise reduction are set to the same value in
  both ears by iOS.
- **Reset All Tunings** writes 0 to amplification, tone, conversation boost and
  ambient noise reduction, and leaves the Audiogram and own voice alone.
- **Own voice amplification** at offset 100 is labelled "constant" in the Gist.
  The Linux script hides its slider with the comment "seems to have no effect".

### Byte 1 matters when the AirPods have never had an Audiogram

From #358 (AirPods Pro 2, Ubuntu, Apple DeviceID set). AirPods that had never
been given an Audiogram returned `02 00 60 00` followed by zeros. The Linux
script copied byte 1 unchanged and wrote `02 00 64 00 ...`: the AirPods
answered `13`, but the next read was all zeros again and nothing could be
heard. Writing the iPhone header `02 02 64 00 ...` by hand made the value
stick; after that, reads returned `02 02 60 00 ...` and the Linux script's own
writes stuck too.

Neither the upstream author nor the reporter could explain why (#358,
2025-12-08). Reading this as "byte 1 is an Audiogram-present flag, and the
first write must set it to `02`" is my inference from these two logs; no
source states it.

## 2. The switch: control commands 0x2C and 0x33

These go over the AAP control channel the daemon already holds, as standard
control commands: header `04 00 04 00 09 00`, identifier, then four value
bytes (`daemon/BasicControlCommand.hpp`).

| Identifier | Meaning | Value |
|---|---|---|
| `0x2C` | Hearing aid: byte 1 "enrolled", byte 2 "enabled" | `01` yes, `02` no, per byte |
| `0x33` | Hearing Assist config | `01` on, `02` off |
| `0x2F` | Swipe to control amplification (stem swipe) | `01` on, `02` off |
| `0x0D` | Listening mode | `03` Transparency |

(Control docs, sections 0x2C and 0x33; `0x2F` from the Gist "Swipe to Control
Amplification".)

### What the iPhone sends

Hearing aid toggle on (Gist):

```
04 00 04 00 09 00 2F 02 00 00 00
04 00 04 00 09 00 33 01 00 00 00
04 00 04 00 09 00 2C 01 01 00 00
```

Hearing aid toggle off (Gist):

```
04 00 04 00 09 00 2F 02 00 00 00
04 00 04 00 09 00 33 02 00 00 00
04 00 04 00 09 00 2C 01 02 00 00
```

Off keeps "enrolled" at `01` and clears only "enabled".

After a new Audiogram is saved (Gist, "Update Hearing Test Results"), in this
order: the 107-byte ATT write, then `2C 01 01` or `2C 01 02`, `2F 02`,
`33 01`, `2C 01 01`, `0D 03` (switch to Transparency), `33 01`, and a 140-byte
Headphone Accommodation packet (opcode `0x53`), which is a separate feature.

The upstream author: "the Hearing Aid is only active in transparency mode"
(#358, 2025-12-08). AirPods Pro 3 has no Off listening mode (this fork's
`knowledge/airpods-pro-3-has-no-off-mode.md`), so that is not a conflict.

### Reading the state

The AirPods report `0x2C` on the control channel like any other control
command. Android main counts the Hearing aid as on only when both `0x2C` byte 2
is `01` and `0x33` byte 1 is `01` (`HearingAidScreen.kt`). The fork daemon
parses only `0x2C`: on when the two bytes are `01 01`, off when either is `02`
(`HearingAid::parseState`).

### How the implementations differ from the iPhone

| Implementation | On | Off | Sends 0x33 |
|---|---|---|---|
| iPhone (Gist) | `2C 01 01` | `2C 01 02` | yes |
| Android main | `2C 01 01` | `2C 01 02` | yes |
| PR #333 script | `2C 01 01` | `2C 02 02` | yes |
| Upstream Linux daemon and this fork | `2C 01 01` | `2C 02 02` | **no** |

The fork defines `HearingAssist` (`0x33`) in `airpods_packets.h` but nothing in
`main.cpp` sends or parses it, and the Hearing aid state is not in the status
JSON or the control socket verbs.

### The recipe that made it audible on Linux

In #358 the settings stuck and were heard only after this sequence, sent by
hand on the control channel (from a contributor, confirmed working by the
reporter on AirPods Pro 2):

```
00 00 04 00 01 00 02 00 00 00 00 00 00 00 00 00   handshake
04 00 04 00 4D 00 FF 00 00 00 00 00 00 00         feature flags FF
04 00 04 00 0F 00 FF FF FF FF                     request notifications
04 00 04 00 09 00 2C 01 01 00 00
04 00 04 00 09 00 33 01 00 00 00
04 00 04 00 09 00 2F 01 00 00 00
04 00 04 00 09 00 0D 03 00 00 00                  Transparency
```

The fork daemon already sends the handshake and request notifications on
every connect, but sends feature flags `D7`, not `FF`
(`Connection::SET_SPECIFIC_FEATURES`; the Android rewrite also sends `D7`).
Whether the bits `D7` leaves out matter to the Hearing aid is not known.

## 3. The Apple DeviceID

### What it is

The Device ID profile record the host publishes over SDP. With vendor `0x004C`
(Apple, vendor ID source `0x0001` Bluetooth SIG) the AirPods treat the host as
an Apple device. On Linux it is the `DeviceID` line in `/etc/bluetooth/main.conf`
followed by a BlueZ restart (upstream README "VendorID Spoofing"; fork
`daemon/README.md` "Hearing Aid"). Android main does the same by hooking
`BTA_DmSetLocalDiRecord` to overwrite `vendor` and `vendor_id_source`
(`cpp/l2c_fcr_hook.cpp`).

### When it is needed

| Operation | Needs the Apple DeviceID | Source |
|---|---|---|
| ATT read or write of `0x2A` (Audiogram, adjustments) | **yes**: refused with error `0x0E` without it | #227 logs |
| Notifications on `0x2B` | yes, same channel | as above |
| `0x2C` and `0x33` on the control channel | listed as needing it; not measured separately | upstream README feature table marks Hearing Aid "needs VendorID spoofing" |
| Loud Sound Reduction, Transparency customization (`0x1B`, `0x18`) | yes | upstream README feature table |

Nothing in any source ties heart rate to the DeviceID; that is for the heart
rate research.

### Whether a re-pair is needed

Yes, at least when switching it on. The AirPods cache the vendor they saw at
first connection:

- "you might need to re-pair your AirPods because they seem to cache this info"
  (Linux README, Hearing Aid).
- "restart the bluetooth service ... and then probably re-pair your AirPods
  because they cache this information and do not check for it every
  connection" (#227).
- "you need to restart Bluetooth and re-pair your AirPods a few times ... AirPods
  cache the VendorID your phone sends it when you first connect and is not
  updated immediately" (#558). The same comment gives a check: with the Apple
  vendor cached, the AirPods accept two hosts at once (multipoint); if they
  stay connected to both, the new vendor took.
- #464 says the same for Android.

No source says whether switching the DeviceID back off also needs a re-pair to
take effect.

### Costs of leaving it on

- With the Apple vendor the AirPods allow multipoint, and an Apple device in
  range can cause the Linux host to be disconnected "unless some specific
  information is sent to the iDevice" (#227). The Linux README advises
  changing the DeviceID back after adjusting the Hearing aid, and warns the
  AirPods may disconnect with the disconnect sound while it is set.
- A second Apple device connected at the same time can block the ATT
  connection the Hearing aid needs (#558: turn Bluetooth off on other Apple
  devices first).
- With the vendor hook on, the AirPods do not send their settings immediately
  on connect but after a few seconds, and there is no known request for them
  (#284).

## 4. AirPods Pro 3 against Pro 2

What is known:

- **No capture on a Pro 3.** The Gist names no model; #358 is a Pro 2; #227
  does not say. Handles `0x18`, `0x1B`, `0x2A` are hard-coded for every model
  on every branch.
- The Android rewrite gives AirPods Pro 3 (`A3063`, `A3064`, `A3065`) the same
  `HEARING_AID` base capability as both AirPods Pro 2 variants, plus `PPE` and
  `HRM` (`devices/AirPods.kt`). It does not treat the Pro 3 Hearing aid
  differently.
- The AirPods report a capability list (AAP opcode `0x02`) that the rewrite
  parses. It has two Hearing aid entries, `HEARING_AID` (`0x22`) and
  `HEARING_AID_V2` (`0x31`), plus `UNKNOWN_HEARING_AID_2` (`0xC0`) and
  `HEARING_TEST` (`0xD0`) (`bluetooth/aacp/types/Capability.kt`). Nothing in
  the code says which models report `HEARING_AID_V2` or what changes with it.
- #659 (AirPods Pro 3, Pixel 8, librepods Play build): after connecting to
  librepods on Android the Hearing aid settings were gone and the AirPods
  behaved as reset; the user reset them and re-paired with an iPad, which still
  held the Audiogram, and turned the Hearing aid back on there. The upstream
  author says the app should not overwrite settings; cause not found.
- The fork's `FEATURES_ACK` parse is commented "Only tested with airpods pro 2"
  (`airpods_packets.h`); the fork's daemon itself runs on an AirPods Pro 3
  (`A3064`, `knowledge/airpods-pro-3-identity.md`).

## 5. What the Hearing aid does to sound

- It shapes ambient sound in Transparency. Music is not amplified (#398). The
  upstream author's guess: the Audiogram is stored on the AirPods and an Apple
  host applies it to media itself. Unverified.
- The Audiogram on the AirPods survives connecting to other hosts: "Nope it
  won't be disabled" when re-pairing with an iPhone (#358). #659 is a
  counterexample on a Pro 3.

## Unknowns

1. Whether any of this holds on AirPods Pro 3 firmware: the 104-byte layout,
   handle `0x2A`, the header bytes, and whether a Pro 3 reports
   `HEARING_AID_V2` and expects something else.
2. The meaning of value bytes 0 to 3, in particular whether byte 1 `02` is
   required on the first write (inferred above, not stated).
3. Whether `0x2C` and `0x33` work without the Apple DeviceID.
4. Whether turning the DeviceID back off needs its own re-pair, and whether a
   re-pair loses Hearing aid state on a Pro 3 (#659).
5. Whether feature flags `D7` (the daemon) instead of `FF` (#358 recipe) block
   the Hearing aid.
6. Whether holding PSM 31 open causes the disconnects the rewrite describes,
   which decides between notifications and short read-write sessions.
7. Whether the Linux daemon's `2C 02 02` for off (clearing "enrolled") does
   harm compared with the iPhone's `2C 01 02`.
8. What own voice amplification at offset 100 controls.
