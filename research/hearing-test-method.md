# How should an uncalibrated Hearing test be run?

Research for [issue #4](https://github.com/adamico/omarchy-pods/issues/4), part of the
[AirPods Pro 3 health app map](https://github.com/adamico/omarchy-pods/issues/1).
Terms follow the project glossary: Hearing test, Self-test audiogram, Certified audiogram,
Hearing aid, Health history.

Researched 2026-10-11. Every claim cites the source that owns it. Lines marked
**Inference** are this document's reasoning from those sources, not a source's own statement.

## Answer in brief

Run a conventional manual-style procedure, automated: eight air-conduction frequencies
per ear (250 to 8000 Hz, the same eight a Certified audiogram uses), the modified
Hughson-Westlake rule (10 dB down after a response, 5 dB up after a miss, threshold at
two responses on ascending runs), tones of randomised length and spacing, silent catch
trials, and a 1000 Hz retest as the reliability check. Without calibration the app
cannot claim dB HL: it measures a level relative to the device at a locked volume.
That number is useful for trends on the same AirPods Pro 3 and, after the user anchors
it to one of their own Certified audiograms, for an estimate in dB HL with an error of
roughly 7 to 10 dB. Neither the AirPods microphones nor an uncalibrated laptop microphone
can certify the room as quiet enough; the laptop microphone can still catch transient
noise and pause the test.

## 1. Frequencies and order

- ASHA lists manual air-conduction thresholds at 250, 500, 1000, 2000, 3000, 4000, 6000
  and 8000 Hz (125 Hz in some cases), and orders the test as 1000, 2000, 3000, 4000, 6000,
  8000 Hz, a 1000 Hz retest, then 500, 250 (125) Hz. The 1000 Hz retest is not needed for
  the second ear. The better ear goes first when known.
  ([ASHA, Guidelines for Manual Pure-Tone Threshold Audiometry, 2005](https://www.asha.org/policy/gl2005-00014/))
- BSA uses the same idea: start at 1000 Hz on the better ear, then 2000, 4000, 8000, 500,
  250 Hz, retest 1000 Hz on the first ear only; 3000 and 6000 Hz are added where needed.
  ([BSA Recommended Procedure, Pure-tone air-conduction and bone-conduction threshold audiometry, 2018](https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf), section 6.4)
- Apple's Hearing Test plays tones from 250 to 8000 Hz and its detailed audiogram reports
  eight frequencies; its summary number is the four-frequency average (4PTA) of 500, 1000,
  2000 and 4000 Hz.
  ([Apple, Using AirPods Pro 2 with iPhone and iPad to Help Protect, Assess, and Assist Hearing, October 2024](https://images.apple.com/health/pdf/Hearing_Health_Features_on_AirPods_Pro_2_October_2024.pdf), pages 5, 6 and 13)
- **Inference:** use the eight ASHA frequencies. They match the eight-per-ear manual entry
  already decided for Certified audiograms, so a Self-test audiogram and a Certified
  audiogram can be compared point by point in the Health history.

## 2. Level stepping

- ASHA: start well below the expected threshold, rise in 5 dB steps to the first response,
  drop 10 dB after each response and begin another ascending series. Threshold is "the
  lowest decibel hearing level at which responses occur in at least one half" of ascending
  trials, with a minimum of two responses out of three at one level.
  ([ASHA 2005](https://www.asha.org/policy/gl2005-00014/))
- BSA (aligned with ISO 8253-1): familiarise at 1000 Hz with a clearly audible tone (about
  40 dB HL for normal hearing, never above 80 dB HL), then 10 dB down until no response,
  5 dB up until a response, repeat until the same level gets two responses out of two,
  three or four ascents. Start the next frequency about 30 dB above the adjacent threshold.
  ([BSA 2018](https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf), sections 6.6 and 6.7)
- Alternatives:
  - Apple uses a rule-based start at 1000 Hz, then Gaussian process classification of the
    audiogram curve with Bayesian active learning to pick the next tone, sampling any
    frequency and level at any time; Apple says this is more efficient than testing one
    frequency at a time.
    ([Apple white paper](https://images.apple.com/health/pdf/Hearing_Health_Features_on_AirPods_Pro_2_October_2024.pdf), page 5)
  - Békésy tracking (the listener holds a key while the tone is audible, the level falls
    while held and rises when released) gave the lowest calibration error in a comparison
    of seven methods for setting a reference level on uncalibrated home hardware.
    ([Masalski et al., JMIR 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC3906690))
- **Inference:** modified Hughson-Westlake is the right first choice. It is the procedure
  every audiologist and every Certified audiogram uses, its rules are short and testable,
  and its output is directly comparable. The Bayesian approach is faster but is a model, not
  a procedure, and Apple has not published its parameters. Keep it as a later option.

## 3. Stimulus timing, responses and catch trials

- Tone length: 1 to 2 s (ASHA); varied between 1 and 3 s (BSA). Gap between tones: varied,
  never shorter than the tone (ASHA); varied between 1 s and at least 3 s (BSA). BSA states
  the random variation "is intended as a check against false positive responses", and that
  tones must play their full length even after a response.
  ([ASHA 2005](https://www.asha.org/policy/gl2005-00014/); [BSA 2018](https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf), section 6.5)
- BSA advises against pulsed tones for threshold measurement because of calibration and
  perception problems ([BSA 2018](https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf), section 6.8),
  while Apple's test pulses each tone three times
  ([Apple Support 120991](https://support.apple.com/120991)). ASHA lists pulsing or warbling
  as one way to reduce false responses ([ASHA 2005](https://www.asha.org/policy/gl2005-00014/)).
- Response: one key or click per tone heard; missing tones is expected. Apple's test asks the
  user to tap when they hear a tone and shows continuously moving visuals that "avoid
  indicating correctness" so feedback does not bias the result.
  ([Apple white paper](https://images.apple.com/health/pdf/Hearing_Health_Features_on_AirPods_Pro_2_October_2024.pdf), page 11; [Apple Support 120991](https://support.apple.com/120991))
- Catch trials: automated audiometers (AMTAS, by Margolis) insert trials with no tone and
  compute a false alarm rate, responses on silent trials divided by silent trials, as a
  quality indicator; AMTAS tells the user when they responded with no tone present.
  ([Interacoustics Academy, AMTAS quality indicators](https://www.interacoustics.com/academy/audiometry-training/advanced-tests/ia-amtas-quality-indicators); [Grason-Stadler, How reliable is automated audiometry](https://www.grason-stadler.com/blog/2021/how-reliable-is-automated-audiometry))
  These are vendor sources; no peer-reviewed false alarm cutoff was found.
- Reliability check: if the 1000 Hz retest differs from the first value by more than 5 dB,
  BSA requires investigating and possibly re-instructing and repeating the ear; within 5 dB,
  keep the more sensitive value.
  ([BSA 2018](https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf), section 6.4)
- **Inference:** randomise tone length (1 to 2 s) and gaps (1 to 3 s or more), use steady
  tones, accept a response from tone onset until about 1 s after offset, count any other
  press as a false alarm, and mix in silent catch trials. Store the false alarm rate and the
  1000 Hz retest difference with the Self-test audiogram as quality fields, and mark the
  result as low quality when either is out of bounds. The bound for false alarms is an open
  choice.

## 4. Ambient noise

- Standard: for air conduction down to 0 dB HL with supra-aural earphones, ISO 8253-1 limits
  ambient noise per third-octave band, for example 18 dB SPL at 500 Hz, 23 dB at 1000 Hz,
  30 dB at 2000 Hz, 36 dB at 4000 Hz; to test only down to 10 dB HL, add 10 dB to every
  limit. BSA's general rule is not to proceed above 35 dB(A) on a calibrated sound level
  meter. Insert earphones relax these limits by their own attenuation, which has to be known.
  ([BSA 2018](https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf), section 4 and Appendix C)
- Apple: the test runs a noise check before starting, a fit check "for optimal ANC
  performance", pauses automatically on loud noise during the test and resumes when it
  drops. Apple tells users to avoid intermittent noise, talking, fans and air conditioning.
  ([Apple white paper](https://images.apple.com/health/pdf/Hearing_Health_Features_on_AirPods_Pro_2_October_2024.pdf), pages 5 and 11; [Apple Support 120991](https://support.apple.com/120991))
- AirPods microphones on Linux: over standard Bluetooth profiles a card cannot carry
  high-quality playback and a microphone at once; the only profiles with a source are
  16 kHz mSBC and 8 kHz CVSD, which replace the playback profile. A high-resolution
  microphone stream over Apple's AACP channel alongside A2DP exists only as an unmerged
  upstream implementation.
  ([this repo's AGENTS.md](../AGENTS.md); [librepods PR 655](https://github.com/kavishdevar/librepods/pull/655))
  So the AirPods microphones cannot monitor noise during a Linux Hearing test today.
- Noise control: AirPods Pro 3 have no Off listening mode, and mode changes are ignored
  while the pods are out of the ears ([knowledge/airpods-pro-3-has-no-off-mode.md](../knowledge/airpods-pro-3-has-no-off-mode.md)).
  The daemon can set Noise Cancellation.
- **Inference:** use the laptop (or any desktop) microphone only as a relative monitor. An
  uncalibrated microphone, often with automatic gain and noise suppression in the audio
  stack, cannot say whether the room is under 35 dB(A). It can measure a baseline before
  the test, refuse to start when the level is obviously high, and during the test discard
  and repeat any trial whose window had a jump above baseline. Force Noise Cancellation for
  the whole test through the daemon, as Apple's design leans on ANC. Store the noise
  baseline and the count of discarded trials with the result.

## 5. Output level and dB HL

- dB HL assumes calibrated equipment in a controlled room: ASHA requires the test room to
  meet ANSI S3.1 at all times ([ASHA 2005](https://www.asha.org/policy/gl2005-00014/)), and
  the US regulation for audiometers
  and automated audiometers ties exemption to compliance with ANSI S3.6 audiometer
  specification ([21 CFR 874.1050](https://www.law.cornell.edu/cfr/text/21/874.1050)).
- Calibration belongs to a sound source and headphone tested as a pair, and "cannot be
  transferred to another device even when it is the same model"; uncalibrated mobile tests
  show average differences above 14 dB from conventional audiometry, and only 67 percent
  of uHear thresholds fell within 10 dB even in a sound booth.
  ([Colsman et al., Frontiers in Psychology 2020](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.00744/full), citing Khoza-Shangase and Kassner 2013 and Szudek et al. 2012)
- Biological calibration, setting the reference level from a normal-hearing listener's
  threshold, brought the standard deviation of the difference from clinical audiometry to
  7.27 to 10.38 dB depending on method; per-frequency calibration was most accurate.
  ([Masalski et al., JMIR 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC3906690))
- Mimi, a non-certified consumer test, works around this by calibrating each supported
  headphone and phone combination in house
  ([Mimi FAQ](https://mimi.io/?p=2718); [Mimi Hearing Test](https://mimi.io/mimi-hearing-test)).
  hearWHO avoids the problem by measuring a signal-to-noise ratio with a digits-in-noise
  test, which "does not require absolute calibrated levels"
  ([Ceccato et al., Frontiers in Public Health 2021](https://www.frontiersin.org/articles/10.3389/fpubh.2021.725080/full); [WHO hearWHO FAQ](https://www.who.int/news-room/questions-and-answers/item/frequently-asked-questions-about-hearing-checks-and-the-hearwho-app)),
  but it gives no audiogram.
- Research on estimating the missing calibration offset from categorical loudness scaling
  exists but used simulated offsets ([Xu and Kollmeier, arXiv 2025](https://arxiv.org/abs/2508.14824)).
- Linux playback path: PipeWire maps the A2DP sink volume onto the AirPods' own volume
  through AVRCP absolute volume, and that hardware volume can be toggled with
  `bluez5.enable-hw-volume` in WirePlumber
  ([PipeWire merge request 603](https://gitlab.freedesktop.org/pipewire/pipewire/-/merge_requests/603); [Arch Wiki, Bluetooth headset](https://wiki.archlinux.org/title/Bluetooth_headset)).
- Apple's Media Assist applies hearing test results to music, video and calls in all noise
  control modes ([Apple, Use hearing health features](https://support.apple.com/guide/airpods/devd9aac5b42)).
  If it is active, test tones would be shaped by an earlier audiogram.
- **Inference:** the app measures a **device level**: tone amplitude in dB relative to full
  scale at a fixed, logged hardware volume, per frequency, on one pair of AirPods Pro 3.
  Three tiers follow from the sources above.
  1. Device level only: valid for trends across Self-test audiograms on the same pair at
     the same locked volume. Show changes, not absolute values.
  2. Anchored to a Certified audiogram: when the user has one, a Self-test audiogram taken
     soon after it gives a per-frequency offset, which converts later device levels into
     estimated dB HL. This is Masalski's per-frequency biological calibration with the
     user as their own reference, so expect an error around 7 to 10 dB, plus any drift if
     ear tips, firmware or the pair change.
  3. A per-model offset table measured on a coupler, as Mimi does. Not available to this
     project without equipment.
  The test must lock the hardware volume, keep the stream free of other audio and software
  gain, set Noise Cancellation, and make sure Media Assist and any Hearing aid shaping are
  off for the duration.

## 6. Duration

- Apple's test takes about five minutes ([Apple Support 120991](https://support.apple.com/120991));
  an independent study measured a median of 5.5 minutes for Apple's test against 10.0 for
  conventional audiometry ([Kruger, Manchaiah and Swanepoel, 2026](https://repository.up.ac.za/items/29b0be23-c977-42ac-8b8a-87c1679b7102)).
- Mimi states under two minutes per ear ([Mimi Hearing Test](https://mimi.io/mimi-hearing-test)).
- BSA warns that long tests tire some listeners and that testing fewer frequencies
  accurately beats a full test done poorly ([BSA 2018](https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf), section 6.8).
- **Inference:** a manual-style automated run of 16 thresholds plus a retest, catch trials
  and repeats for noise lands near conventional audiometry, around 10 to 15 minutes. Allow a
  pause between ears and save partial results per ear.

## 7. What the UI must say

- Comparable products:
  - hearWHO: "hearWHO is not a formal hearing test and does not replace the need to consult
    a health professional." Scores below 50 are told to see a professional.
    ([WHO hearWHO FAQ](https://www.who.int/news-room/questions-and-answers/item/frequently-asked-questions-about-hearing-checks-and-the-hearwho-app))
  - Apple (a regulated test, so it can grade results): 18 and older; wait if you had a cold,
    sinus or ear infection or loud exposure in the last 24 hours, or have allergies; quiet
    room for the whole test; "if you experience difficulty hearing or a sudden change in
    your hearing, talk to your doctor."
    ([Apple Support 120991](https://support.apple.com/120991))
- Regulation: in the US an audiometer or automated audiometer is a Class II device meant for
  "diagnostic hearing evaluations" ([21 CFR 874.1050](https://www.law.cornell.edu/cfr/text/21/874.1050)).
  FDA's general wellness policy covers software "unrelated to the diagnosis, cure,
  mitigation, prevention, or treatment of a disease or condition"
  ([FDA, General Wellness: Policy for Low Risk Devices, final, January 2026](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-wellness-policy-low-risk-devices)).
  EU rules were not researched.
- **Inference:** the UI should
  - say before every test that this is not a medical hearing test, the result is not a
    diagnosis, and the AirPods are not calibrated;
  - keep Apple's preparation advice (quiet room, recent illness or loud exposure, age) and
    the sudden-change advice to see a doctor;
  - never show WHO grades or "mild/moderate" labels for a Self-test audiogram, since an
    uncalibrated error of 8 to 17 dB is as wide as a whole grade (Apple's grades span 15
    to 20 dB);
  - label tier 1 results as relative change and tier 2 results as "estimated dB HL",
    always with the source "Self-test" next to them in the Health history;
  - show quality fields (false alarms, retest difference, noise interruptions) next to the
    result.

## Unknowns

- The SPL that AirPods Pro 3 produce per frequency at a given volume over Linux A2DP, and
  how much it varies between pairs and ear tip fits. Needs a coupler measurement.
- Whether Adaptive EQ, Media Assist or Hearing aid settings shape A2DP audio from a Linux
  source, and whether the daemon can read or disable them. Depends on the Hearing aid
  protocol research.
- Whether the AirPods report an ear tip fit or seal result over AACP that the daemon could
  use as Apple's fit check.
- Whether the AACP high-resolution microphone path (librepods PR 655) could carry ambient
  noise during playback, which would allow a real in-ear noise check.
- The lowest and highest usable device levels: the noise floor of the codec path near
  threshold and a safe maximum level, since the BSA cap of 80 dB HL cannot be expressed
  without calibration.
- A false alarm rate bound for marking a result low quality.
- EU regulatory position for a self-test app with no certification.

## Sources

- [ASHA, Guidelines for Manual Pure-Tone Threshold Audiometry (2005)](https://www.asha.org/policy/gl2005-00014/)
- [BSA, Recommended Procedure: Pure-tone air-conduction and bone-conduction threshold audiometry with and without masking (2018)](https://www.thebsa.org.uk/wp-content/uploads/2024/01/Recommended-Procedure-Pure-Tone-Audiometry-2018.pdf)
- [Apple, Using AirPods Pro 2 with iPhone and iPad to Help Protect, Assess, and Assist Hearing (October 2024)](https://images.apple.com/health/pdf/Hearing_Health_Features_on_AirPods_Pro_2_October_2024.pdf)
- [Apple Support, Take a Hearing Test with AirPods Pro 2 or AirPods Pro 3](https://support.apple.com/120991)
- [Apple Support, Use hearing health features with AirPods Pro 2 or AirPods Pro 3](https://support.apple.com/guide/airpods/devd9aac5b42)
- [Kruger, Manchaiah and Swanepoel, Apple hearing test feature for the AirPods Pro 2: accuracy, reliability, and time-efficiency](https://repository.up.ac.za/items/29b0be23-c977-42ac-8b8a-87c1679b7102)
- [Masalski, Grysiński and Kręcicki, Biological Calibration for Web-Based Hearing Tests, JMIR 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC3906690)
- [Colsman et al., Evaluation of Accuracy and Reliability of a Mobile Screening Audiometer in Normal Hearing Adults, Frontiers in Psychology 2020](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.00744/full)
- [Ceccato et al., French Version of the Antiphasic Digits-in-Noise Test for Smartphone Hearing Screening, Frontiers in Public Health 2021](https://www.frontiersin.org/articles/10.3389/fpubh.2021.725080/full)
- [Xu and Kollmeier, Calibration offset estimation in mobile hearing tests via categorical loudness scaling, arXiv 2025](https://arxiv.org/abs/2508.14824)
- [WHO, Frequently asked questions about hearing checks and the hearWHO app](https://www.who.int/news-room/questions-and-answers/item/frequently-asked-questions-about-hearing-checks-and-the-hearwho-app)
- [Mimi, Frequently asked questions](https://mimi.io/?p=2718) and [Mimi Hearing Test](https://mimi.io/mimi-hearing-test)
- [Interacoustics Academy, AMTAS quality indicators](https://www.interacoustics.com/academy/audiometry-training/advanced-tests/ia-amtas-quality-indicators)
- [Grason-Stadler, How reliable is automated audiometry](https://www.grason-stadler.com/blog/2021/how-reliable-is-automated-audiometry)
- [21 CFR 874.1050, Audiometer](https://www.law.cornell.edu/cfr/text/21/874.1050)
- [FDA, General Wellness: Policy for Low Risk Devices](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-wellness-policy-low-risk-devices)
- [PipeWire merge request 603, bluez5 hardware volume](https://gitlab.freedesktop.org/pipewire/pipewire/-/merge_requests/603)
- [Arch Wiki, Bluetooth headset](https://wiki.archlinux.org/title/Bluetooth_headset)
- [librepods PR 655, AACP microphone](https://github.com/kavishdevar/librepods/pull/655)
