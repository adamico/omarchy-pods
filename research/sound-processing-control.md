# Switching off the AirPods' own sound processing during a Hearing test

Research for [issue #14](https://github.com/adamico/omarchy-pods/issues/14).
Builds on [#3](https://github.com/adamico/omarchy-pods/issues/3) (Hearing aid
protocol) and [#4](https://github.com/adamico/omarchy-pods/issues/4) (Hearing test
method). Terms follow `GLOSSARY.md`: AirPods Pro 3, Hearing test, Hearing aid,
Audiogram, Self-test audiogram.

## Answer in short

Most of it, yes; one part, no.

- **Noise Cancellation**: the daemon already reads and sets it (`0x0D`, value `02`),
  measured on a real AirPods Pro 3. Forcing it also takes Hearing aid shaping out of
  the picture, because the Hearing aid only acts in Transparency.
- **Hearing aid shaping**: switched by `0x2C` plus `0x33`. It shapes ambient sound,
  not music played from Linux (one Linux user report). The daemon reads `0x2C` and
  can send it, but sends a different off value than the iPhone and never sends
  `0x33`.
- **Media Assist** (Apple's older name: Headphone Accommodation): `0x33` plus a
  140-byte opcode `0x53` message with a Phone byte and a Media byte. The upstream
  author found it has no effect on audio from non-Apple hosts, and thinks the Apple
  host applies the curve itself. Not measured on a Pro 3. The daemon has no code for
  `0x53`.
- **Personalized Volume**: control command `0x26`. Apple says it adjusts media
  volume on the AirPods, and upstream warns it "might randomly boost volume" on
  Android, so it probably breaks a locked volume. The daemon defines `0x26` but never
  sends or reads it.
- **Conversation Awareness**: control command `0x28`. When on, the AirPods change
  their own listening behaviour when the wearer speaks, and on Linux the daemon
  itself lowers the sink volume to 20 percent. The daemon reads and sets it today
  (`ca:on`, `ca:off`).
- **Adaptive EQ**: no control exists. Apple offers no switch for it on any device,
  no AAP command for it is known, and it runs on the AirPods from their inward
  microphones, so it almost certainly shapes Linux audio. The Hearing test has to
  live with it.

A newer audio-shaping setting also matters: the **custom equalizer** (opcode
`0x63`, firmware 9 and later). Upstream sets and reads it from Android.

## Sources

| Short name | What it is | Version read |
|---|---|---|
| Control docs | [`docs/control_commands.md`](https://github.com/librepods-org/librepods/blob/efccc4499b2c1fd2ac243e975ae1f42d8e828ffd/docs/control_commands.md), identifiers extracted from the iOS 19.1 beta Bluetooth stack | `main` at `efccc44`; identical on `android/rewrite` at `34076c8` |
| AAP doc | [`docs/AAP Definitions.md`](https://github.com/librepods-org/librepods/blob/efccc4499b2c1fd2ac243e975ae1f42d8e828ffd/docs/AAP%20Definitions.md), "As per AirPods Pro 2 (USB-C) Firmware 7A305" | same |
| Opcodes doc | [`docs/opcodes.md`](https://github.com/librepods-org/librepods/blob/efccc4499b2c1fd2ac243e975ae1f42d8e828ffd/docs/opcodes.md) | same |
| Android main | `android/.../bluetooth/AACPManager.kt`, `presentation/screens/AccessibilitySettingsScreen.kt` | `main` at `efccc44` |
| Android rewrite | `android/.../bluetooth/aacp/AACPManager.kt`, `aacp/types/Opcodes.kt`, `aacp/types/ControlCommand.kt`, `aacp/types/Capability.kt`, `aacp/types/CustomEq.kt`, `aacp/packet/CustomEqPacket.kt`, `presentation/screens/apple/AppleSettingsScreen.kt`, `presentation/screens/apple/HearingAidScreen.kt` | [`android/rewrite` at `34076c8`](https://github.com/librepods-org/librepods/tree/34076c85f0fc2eaf32ad1d5cad1bb7315df9c89c) |
| Gist | [rithvikvibhu, `aap.md`](https://gist.github.com/rithvikvibhu/45e24bbe5ade30125f152383daf07016), iPhone PacketLogger captures of the Hearing Assistance pages | updated 2026-02-16 |
| Fork daemon | `daemon/airpods_packets.h`, `daemon/BasicControlCommand.hpp`, `daemon/enums.h`, `daemon/main.cpp`, `daemon/media/mediacontroller.cpp`; `knowledge/airpods-pro-3-has-no-off-mode.md` | this repo, `main` at `fff7fec` |
| Issues | librepods-org/librepods [#20](https://github.com/librepods-org/librepods/issues/20), [#27](https://github.com/librepods-org/librepods/issues/27), [#328](https://github.com/librepods-org/librepods/issues/328), [#358](https://github.com/librepods-org/librepods/issues/358), [#398](https://github.com/librepods-org/librepods/issues/398), [#626](https://github.com/librepods-org/librepods/issues/626), [#630](https://github.com/librepods-org/librepods/issues/630) | read 2026-10-11 |
| Apple | [AirPods Pro 3 product page](https://www.apple.com/airpods-pro/); [Use hearing health features](https://support.apple.com/guide/airpods/devd9aac5b42); [Adjust listening mode settings on AirPods](https://support.apple.com/guide/airpods/dev6d977ff21/web); [Use Adaptive Audio with your AirPods](https://support.apple.com/en-au/104979) | read 2026-10-11 |

All control commands below use the standard frame (Control docs; fork
`BasicControlCommand.hpp`):

```
04 00 04 00 09 00 [identifier] [data1] [data2] 00 00
```

`01` means on and `02` means off unless stated. The AirPods report every control
command state after the daemon's request for notifications; the Android rewrite
keeps all of them in one `controlStates` map from that stream (`AACPManager.kt`,
`MessageOpcode.CONTROL_COMMAND`). Whether a Pro 3 reports each identifier listed
here has not been checked.

## Summary table

| Setting | Changes audio played from Linux? | Daemon reads it today? | Daemon sets it today? | Command to switch off for the test | Confidence |
|---|---|---|---|---|---|
| Noise Cancellation | Sets the listening mode the test needs; also stops Hearing aid shaping | yes, `noise_mode` in status | yes, `noise:anc` | `0x0D 02` | high: measured on a Pro 3 |
| Hearing aid shaping | No for music (one Linux report); yes for ambient in Transparency | `0x2C` only | `0x2C` only, off value differs from iPhone | `0x2C 01 02`, `0x33 02` | medium |
| Media Assist | Probably not (upstream author's test, one Linux report) | no | no | `0x33 02`, then `0x53` with Media byte `02` | medium for "no effect", low for the exact `0x53` bytes |
| Personalized Volume | Probably yes: changes media volume on the AirPods | no (`0x26` defined, unused) | no | `0x26 02` | medium |
| Conversation Awareness | Yes: AirPods react to speech, and the daemon lowers sink volume | yes, `conversational_awareness` | yes, `ca:on` and `ca:off` | `0x28 02` | high for the command, medium for its effect on the AirPods |
| Adaptive EQ | Almost certainly yes, always on | no, nothing to read | no, no command exists | none | medium (no switch: high; acts on Linux audio: inferred) |
| Custom equalizer (firmware 9 and later) | Probably yes | no | no | opcode `0x63` with state `01` | low to medium |

## 1. Noise Cancellation

- Listening mode is control command `0x0D`: `01` Off, `02` Noise Cancellation,
  `03` Transparency, `04` Adaptive. The AirPods echo the packet once applied
  (AAP doc, "Changing Noise Control").
- The fork sends it (`AirPodsPackets::NoiseControl`, `setNoiseControlMode` in
  `main.cpp`), parses the 11-byte echo into `noise_mode` in the status JSON, and
  offers the IPC verbs `noise:off`, `noise:anc`, `noise:transparency`,
  `noise:adaptive`, `noise:cycle`.
- Measured on a real AirPods Pro 3 (`knowledge/airpods-pro-3-has-no-off-mode.md`):
  Off is accepted and ignored; every mode change is ignored while the pods are out
  of the ears; in ear, other modes apply within about two seconds. `librepods-ctl`
  exits 0 even when the pods ignore the packet, so the Hearing test must check the
  echoed `noise_mode`, not the exit code.
- The setter returns early when the cached mode already matches, so a stale cache
  could skip the send. The test should send unconditionally or confirm the echo.
- Effect on Linux audio: Noise Cancellation adds anti-noise for the room; it is the
  mode the test wants. The Hearing aid only acts in Transparency (upstream author,
  #358), so Noise Cancellation also keeps Hearing aid shaping away from the ears.
- `0x2E` (Adaptive Audio noise level, 0 to 100) only acts in Adaptive mode (AAP doc)
  and does not matter in Noise Cancellation.

## 2. Hearing aid shaping

Covered in depth by the #3 research; the parts that matter here:

- Switch: `0x2C` (byte 1 enrolled, byte 2 enabled) and `0x33` (Hearing Assist).
  iPhone off sends `2F 02`, `33 02`, `2C 01 02` (Gist, "Heading Aid toggle"). The
  Android rewrite sends the same `2C 01 02` and `33 02` (`HearingAidScreen.kt`).
- Fork: `HearingAid::DISABLED` is `2C 02 02`, which also clears "enrolled";
  `HearingAssist` (`0x33`) is defined and never sent or parsed; `hearingAidEnabled`
  is a Qt property but is not in the status JSON or an IPC verb (`main.cpp`).
- Effect on Linux audio: a Linux user with the Hearing aid on heard Transparency
  amplified "without music when its played" (#398). The upstream author's reading:
  the AirPods store the curve and "expect the connected device to use the stored EQ
  for media and calls" (#398 comment). One report, Pro 2 or unstated model.
- For the Hearing test: Noise Cancellation alone already keeps Hearing aid shaping
  from acting. Switching it off as well is a second line of defence, not a
  requirement, if the #398 finding holds on a Pro 3. Whether `0x2C` and `0x33` need
  the Apple DeviceID is still unknown (#3 unknown 3).

## 3. Media Assist

- In the Gist, toggling Media Assist on an iPhone sends two messages (section
  "Media Assist toggle"):

  ```
  04 00 04 00 09 00 33 01 00 00 00             on   (33 02 for off)
  04 00 04 00 53 00 84 00 02 02 [Phone] [Media] [8 floats] x 4
  ```

  On: Phone `01`, Media `01`. Off: Phone `02`, Media `02`. The 32 floats are the
  same 8 values repeated 4 times, little-endian (in that capture about 17.8 to
  30.8, so not the 0 to 100 range the AAP doc gives).
- "Adjust Music and Video" sets the Media byte; "Adjust Calls and FaceTime" sets
  the Phone byte (Gist, "Media Assist options"). The byte before Phone is sometimes
  `00` instead of `02`.
- So `0x33` is shared: the iPhone sends it for both the Hearing aid and Media
  Assist toggles. Sending `33 02` to switch the Hearing aid off is therefore also
  the first half of switching Media Assist off.
- The AAP doc calls the `0x53` message "Headphone Accomodation" (Apple's earlier
  accessibility name) with the layout `84 00 02 02 [Phone] [Media] [EQ1..EQ8]`
  repeated.
- Upstream reads it: the AirPods send a 140-byte `0x53` message, which both Android
  branches parse (`HEADPHONE_ACCOMMODATION`, checks size 140 and byte 6 `0x84`).
  Upstream writes it: `sendPhoneMediaEQ` builds the same frame with Phone at frame
  byte 10 and Media at byte 11, as the Gist and AAP doc say. The parsers on both
  branches label byte 10 as Media and byte 11 as Phone, the opposite of the senders
  and the docs; the docs and the sender agree, so treat the parser as wrong.
- Hazard in Android main: `AccessibilitySettingsScreen.kt` sends `0x53` with eight
  `0.5` floats and Phone and Media `02` whenever the screen opens (a
  `LaunchedEffect` on default state). That overwrites whatever curve the AirPods
  held. The daemon must never write `0x53` without first reading the current
  floats and sending them back unchanged.
- Effect on Linux audio: the upstream author: "I have tried sending EQ to the
  airpods, but it seems to me that it has no effect on audio from non-apple
  devices" (#328), and the #398 comment above. Apple does not say where Media
  Assist is applied ([Use hearing health features](https://support.apple.com/guide/airpods/devd9aac5b42)).
  Not measured on a Pro 3.
- The fork has no code for opcode `0x53` at all: it neither parses the report nor
  sends it.

## 4. Personalized Volume

- Control command `0x26`, "Adaptive Volume Config", `01` on, `02` off (Control
  docs). The Android rewrite toggles it as Apple's "Personalized Volume"
  (`AppleSettingsScreen.kt`, `ADAPTIVE_VOLUME_CONFIG`) and reads its state from the
  control command stream. The rewrite also names an opcode `0x4C`
  `ADAPTIVE_VOLUME` and a capability `0x90` with no handling.
- Apple: "Personalised Volume will adjust the media volume on your AirPods" and
  "learns your listening preferences over time"
  ([Use Adaptive Audio](https://support.apple.com/en-au/104979));
  "takes into account your environmental conditions"
  ([Adjust listening mode settings](https://support.apple.com/guide/airpods/dev6d977ff21/web)).
- Upstream's own feature list: "Personalized Volume (use at your own risk - might
  randomly boost volume to some high level)" (#20); the author suggested turning it
  off for a volume problem on Android (#27). That points to the AirPods changing
  level on non-Apple hosts, but no source shows whether the change is in the
  AirPods' gain or in the AVRCP volume Linux sees.
- Fork: `AirPodsPackets::AdaptiveVolume` (`0x26`) is defined; nothing sends or
  parses it.
- For the Hearing test this matters more than any equalizer: a volume that drifts
  during the test breaks the locked hardware volume #4 relies on.

## 5. Conversation Awareness

- Control command `0x28`, `01` on, `02` off (Control docs; AAP doc "Toggle
  Conversational Awareness"). The AirPods report its state once after notifications
  are requested (AAP doc).
- What the AirPods do: "If enabled, the AirPods will switch to Transparency mode
  when the person wearing them starts speaking (and sends packet for notifying the
  device to reduce volume)" (AAP doc). Apple: it "lowers the volume of your media
  and enhances voices in front of you, while reducing background noise"
  ([Adjust listening mode settings](https://support.apple.com/guide/airpods/dev6d977ff21/web)).
- The volume part is the host's job on Linux: the AirPods send opcode `0x4B` levels
  and the fork's `MediaController::handleConversationalAwareness` sets the default
  sink to 20 percent of its starting volume on level `01`.
- The AAP doc says the `4D 00 FF` feature flags are needed for Conversation
  Awareness while audio plays; the fork sends `D7`, so whether it triggers during
  playback on a Pro 3 is not established. It does not matter if it is off.
- Fork: reads `0x28` into `conversational_awareness` in the status JSON and sets it
  with `ca:on` and `ca:off`. High confidence on the command.
- For the Hearing test: switch it off, and also have the daemon ignore `0x4B`
  while a test runs, since a user who says "yes" aloud would duck the tones.

## 6. Adaptive EQ

- Apple: "Adaptive EQ uses inward-facing microphones to tune music to your ears in
  real time" and "customizes a sound signature for your unique ear geometry and
  fit" ([AirPods Pro 3 page](https://www.apple.com/airpods-pro/)). No Apple support
  page offers a switch for it, on any device.
- No control command, opcode or capability for it appears in the Control docs, the
  Opcodes doc, or the rewrite's `Opcodes.kt` and `Capability.kt`.
- Inference: since it needs the in-ear microphones, it runs on the AirPods and so
  also shapes A2DP audio from Linux. No source tests this directly.
- Consequence for the Hearing test: it cannot be switched off. It adapts the low
  and mid range to fit, so it is part of the "device level" #4 already accepts.
  Its fit dependence adds to the 1000 Hz retest spread and to drift between
  sessions. The test should keep the existing fit advice and treat changes of a few
  dB at low frequencies with care.

## 7. Custom equalizer (not in the ticket, but it shapes audio)

- Apple announced a user equalizer for H2 AirPods with iOS 27. Upstream added it
  (#626, commit `7341e41`); it needs the latest beta firmware, installable only from
  an iOS 27 device (#630). The rewrite shows it only when the firmware version
  starts with 9 (`AppleSettingsScreen.kt`); a capability `PREFERENCE_EQ` (`0x37`)
  exists unparsed.
- Wire format (`CustomEq.kt`, `CustomEqPacket.kt`): opcode `0x63`, payload
  `05 00 01 [state] [low] [mid] [high]`, state `01` off and `02` on, bands 0 to 100.
  The AirPods report the same payload; the parser reads the state at payload byte 3.

  ```
  04 00 04 00 63 00 05 00 01 01 [low] [mid] [high]     custom equalizer off
  ```

- Whether it acts on non-Apple audio is not stated, but it exists in an Android app
  whose only use would be Android audio, and users asked for presets (#626).
- The fork has no code for `0x63`.

## What the daemon would need for a Hearing test

Inference from the facts above, for the build tickets:

1. Before the test, record the current state of each setting, then send:
   `0x0D 02` (confirm the echo), `0x28 02`, `0x26 02`, `0x2C 01 02`, `0x33 02`,
   `0x53` with Phone and Media `02` and the floats read back unchanged, and `0x63`
   state `01` with the bands unchanged when the firmware has it.
2. Ignore `0x4B` Conversation Awareness levels while the test runs.
3. After the test, restore what was recorded.
4. Expose the states it uses in the status JSON so the app can show and log them
   with each Self-test audiogram.

Missing from the fork today: parsing and sending `0x26`, `0x33`, `0x53`, `0x63`;
the iPhone-style `2C 01 02`; a test mode that pauses the Conversation Awareness
ducking.

## Unknowns

1. Whether Media Assist and Hearing aid shaping touch Linux A2DP audio on an AirPods
   Pro 3. Every finding is from other models or unstated ones.
2. Whether Personalized Volume changes the AirPods' internal gain or the AVRCP
   volume Linux sees, and whether it acts at all on a non-Apple host.
3. Whether `0x26`, `0x33`, `0x53` and `0x63` need the Apple DeviceID.
4. Whether a Pro 3 sends the 140-byte `0x53` report, and when, so the daemon can
   read the current curve before writing it.
5. Whether Adaptive EQ can be influenced in any way (none found), and how much it
   moves between fittings.
6. What the feature flag bits `FF` sets and `D7` leaves out (`0x08`, `0x20`) do.
7. Whether Apple's own Hearing test sends anything to the AirPods first (no capture).
8. What the `HEARING_TEST` capability (`0xD0`) a Pro 3 may report enables.
