# What an audiogram looks like in an Apple Health export

Research for [issue #5](https://github.com/adamico/omarchy-pods/issues/5), under the map in [issue #1](https://github.com/adamico/omarchy-pods/issues/1). Terms follow the project glossary: an **Audiogram** is hearing thresholds per ear at a set of frequencies, dated and attributed to its source; a **Certified audiogram** is one measured by a hearing professional or a certified test and entered into the app.

## Answer

Each audiogram in the Health app's "Export All Health Data" archive is one `<Audiogram>` element at the top level of `export.xml`, a sibling of `<Record>`. It carries `type="HKDataTypeIdentifierAudiogram"`, `sourceName`, optional `sourceVersion`, `device` and `creationDate`, and required `startDate` and `endDate`. Its children are public `<MetadataEntry key value>` elements and one `<SensitivityPoint>` per frequency, with `frequencyValue`/`frequencyUnit` (Hz) and, per ear, `leftEarValue`/`leftEarUnit` and `rightEarValue`/`rightEarUnit` (dBHL). Since export version 14 (iOS 18.1) each ear also gets `...EarMasked` (`YES`/`NO`) and optional `...EarClampingRangeLowerBound`/`...UpperBound`. Only air conduction is exported, because it is the only conduction type HealthKit has. `export_cda.xml` does not contain audiograms. The export drops every private metadata key, so whether a sample came from Apple's own Hearing Test, from manual entry in the Health app or from a third-party app can only be guessed from `sourceName`, `device` and the public `HKWasUserEntered` key.

## The XML shape

### The DTD Apple ships

The DTD is written inline at the top of every `export.xml`. The audiogram part of the current one (export version 14, introduced in iOS 18.1 and unchanged in version 17, which ships with iOS 27) is:

```xml
<!ELEMENT Audiogram ((MetadataEntry|SensitivityPoint)*)>
<!ATTLIST Audiogram
  type          CDATA #REQUIRED
  sourceName    CDATA #REQUIRED
  sourceVersion CDATA #IMPLIED
  device        CDATA #IMPLIED
  creationDate  CDATA #IMPLIED
  startDate     CDATA #REQUIRED
  endDate       CDATA #REQUIRED
>
<!ELEMENT SensitivityPoint EMPTY>
<!ATTLIST SensitivityPoint
  frequencyValue   CDATA #REQUIRED
  frequencyUnit    CDATA #REQUIRED
  leftEarValue     CDATA #IMPLIED
  leftEarUnit      CDATA #IMPLIED
  leftEarMasked      CDATA #IMPLIED
  leftEarClampingRangeLowerBound   CDATA #IMPLIED
  leftEarClampingRangeUpperBound   CDATA #IMPLIED
  rightEarValue    CDATA #IMPLIED
  rightEarUnit     CDATA #IMPLIED
  rightEarMasked      CDATA #IMPLIED
  rightEarClampingRangeLowerBound  CDATA #IMPLIED
  rightEarClampingRangeUpperBound  CDATA #IMPLIED
>
```

Source: the DTD string embedded in the HealthToolbox framework, as extracted in the ipsw-diffs for [iOS 18.1 beta](https://github.com/blacktop/ipsw-diffs/blob/main/iOS/18_1_22B5045h__vs_18_1_22B5054e/DYLIBS/HealthToolbox.md) (where `leftEarMasked` and the clamping attributes first appear, with `<!-- HealthKit Export Version: 14 -->`) and for [iOS 26.5 versus iOS 27.0 beta](https://github.com/blacktop/ipsw-diffs/blob/main/iOS/26_5_23F77_vs_27_0_24A5355q/DYLIBS/System/Library/PrivateFrameworks/HealthToolbox.framework/HealthToolbox.md) (version 17, same audiogram elements). Before version 14 the `SensitivityPoint` attributes were only the frequency pair and the two value and unit pairs, as in this [version 11 export](https://github.com/opendroid/hk/blob/main/public/sampleexport-2.xml) and the [`healthkit11.dtd`](https://github.com/AlekSi/applehealth/blob/main/healthkit11.dtd) in AlekSi/applehealth. The root element allows `Audiogram` among `Record|Correlation|Workout|ActivitySummary|ClinicalRecord|Audiogram|VisionPrescription`.

### A real sample (export version 11, iOS 14)

From a donated export in [opendroid/hk](https://github.com/opendroid/hk/blob/main/public/sampleexport-2.xml), lines 219 to 229. The sample has been trimmed to two points and hand indented by that repository's author; the attribute set is Apple's.

```xml
<Audiogram type="HKDataTypeIdentifierAudiogram" sourceName="Hearing Test" sourceVersion="3092"
           creationDate="2021-01-22 20:31:37 -0800" startDate="2021-01-22 20:30:50 -0800"
           endDate="2021-01-22 20:30:50 -0800">
    <MetadataEntry key="HKMetadataKeySyncVersion" value="1"/>
    <MetadataEntry key="HKExternalUUID" value="479728a4-8e83-4de1-bb71-f75f5a691a6c"/>
    <MetadataEntry key="HKMetadataKeySyncIdentifier" value="479728a4-8e83-4de1-bb71-f75f5a691a6c"/>
    <SensitivityPoint frequencyValue="250" frequencyUnit="Hz" leftEarValue="35.0459" leftEarUnit="dBHL"
                      rightEarValue="20.0452" rightEarUnit="dBHL"/>
    <SensitivityPoint frequencyValue="500" frequencyUnit="Hz" leftEarValue="29.6554" leftEarUnit="dBHL"
                      rightEarValue="17.6095" rightEarUnit="dBHL"/>
</Audiogram>
```

This one predates Apple's own Hearing Test (iOS 18.1), so `sourceName="Hearing Test"` here is a third-party app of that name writing through HealthKit, not Apple's feature.

### What a version 14 or later point looks like

Not a captured export; assembled from the writer code below, so the attribute order and formatting are what that code emits:

```xml
<SensitivityPoint frequencyValue="1000" frequencyUnit="Hz"
  leftEarValue="20" leftEarUnit="dBHL" leftEarMasked="NO"
  rightEarValue="65" rightEarUnit="dBHL" rightEarMasked="YES"
  rightEarClampingRangeUpperBound="80"/>
```

## How the exporter writes it

The decompiled `WDExportManager` from HealthToolbox in iOS 26.1 ([`WDExportManager.mm`](https://github.com/EthanArbuckle/iPhone18-3_26.1_23B85_Restore/blob/main/System/Library/PrivateFrameworks/HealthToolbox.framework/HealthToolbox/WDExportManager.mm)) shows the exact rules. Decompiled code is a reconstruction, but the string literals and call order are reliable.

- `_writeXMLAudiogramStartWithAudiogram:` writes `type` (the sample type identifier), `sourceName` (the source's display name), `sourceVersion` only when non-empty, `device` only when the `HKDevice` description is non-empty, `creationDate` only when known, then `startDate`, `endDate`, then the metadata.
- Dates use the format `yyyy-MM-dd HH:mm:ss ZZZ`, for example `2021-01-22 20:30:50 -0800`.
- `device` is the Objective-C description of `HKDevice`, not structured data, for example `<<HKDevice: 0x2820680f0>, name:Apple Watch, manufacturer:Apple Inc., model:Watch, hardware:Watch4,2, software:7.2>` (seen on `Record` elements in the same sample file). An importer has to parse it as text, and it is XML escaped (`&lt;`, `&gt;`).
- `_writeXMLMetadataEntries:` skips every key for which `_HKMetadataKeyIsPrivate()` is true. Values are written with `description`, so a Boolean is `1` or `0`.
- `_writeXMLAudiogramSensitivityPoint:` writes `frequencyValue` with `%g` and the unit string of the frequency quantity (`Hz`). For the left ear it takes the first test whose `type` is air (0) and `side` is left (0); for the right ear, side right (1). If such a test exists it writes the value with `%g`, the unit string (`dBHL`), `leftEarMasked` / `rightEarMasked` as `YES` or `NO`, and each clamping bound only if present. If there is no test for an ear, that ear's attributes are absent.
- Points are written in the order the sample stores them, which HealthKit validates as strictly ascending by frequency.

`%g` gives at most six significant digits, so values such as `35.0459` are already rounded by the exporter.

## The HealthKit model behind it

| Concept | API | Since | Source |
| --- | --- | --- | --- |
| The sample | `HKAudiogramSample`, a subclass of `HKSample`; "stores the results from a hearing test ... as an array of sensitivity points" | iOS 13 | [Apple docs](https://developer.apple.com/documentation/healthkit/hkaudiogramsample) |
| One frequency | `HKAudiogramSensitivityPoint` with `frequency` (Hz) | iOS 13 | [Apple docs](https://developer.apple.com/documentation/healthkit/hkaudiogramsensitivitypoint) |
| Per-ear value, old | `leftEarSensitivity`, `rightEarSensitivity` (dBHL), deprecated in iOS 18.1 in favour of `tests` | iOS 13 to 18.1 | SDK header [`HKAudiogramSensitivityPoint.h`](https://github.com/xybp888/iOS-SDKs/blob/master/iPhoneOS26.2.sdk/System/Library/Frameworks/HealthKit.framework/Headers/HKAudiogramSensitivityPoint.h) |
| Per-ear value, new | `tests: [HKAudiogramSensitivityTest]`, each with `sensitivity` (dBHL), `type`, `masked`, `side`, optional `clampingRange` | iOS 18.1 | [Apple docs](https://developer.apple.com/documentation/healthkit/hkaudiogramsensitivitytest), SDK header [`HKAudiogramSensitivityTest.h`](https://github.com/xybp888/iOS-SDKs/blob/master/iPhoneOS26.2.sdk/System/Library/Frameworks/HealthKit.framework/Headers/HKAudiogramSensitivityTest.h) |
| Conduction | `HKAudiogramConductionType`: only `air = 0`. Bone conduction does not exist in HealthKit | iOS 18.1 | [Apple docs](https://developer.apple.com/documentation/healthkit/hkaudiogramconductiontype) |
| Ear | `HKAudiogramSensitivityTestSide`: `left = 0`, `right = 1` | iOS 18.1 | [Apple docs](https://developer.apple.com/documentation/healthkit/hkaudiogramsensitivitytestside) |
| Clamping | `HKAudiogramSensitivityPointClampingRange` with optional `lowerBound`, `upperBound`; marks a value clamped "for user safety, hardware limitations, or algorithm features" | iOS 18.1 | [Apple docs](https://developer.apple.com/documentation/healthkit/hkaudiogramsensitivitypointclampingrange) |
| Unit | `HKUnit.decibelHearingLevel()`, "dBHL", intensity relative to the quietest sound a typical young healthy person hears | iOS 13 | [Apple docs](https://developer.apple.com/documentation/healthkit/hkunit/decibelhearinglevel()) |

Validation rules HealthKit enforces on every sample, so an export always satisfies them. From the decompiled [`HKAudiogramSample.mm`](https://github.com/EthanArbuckle/iPhone18-3_26.1_23B85_Restore/blob/main/System/Library/Frameworks/HealthKit.framework/HealthKit/HKAudiogramSample.mm), [`HKAudiogramSensitivityPoint.mm`](https://github.com/EthanArbuckle/iPhone18-3_26.1_23B85_Restore/blob/main/System/Library/Frameworks/HealthKit.framework/HealthKit/HKAudiogramSensitivityPoint.mm) and [`HKAudiogramSensitivityTest.mm`](https://github.com/EthanArbuckle/iPhone18-3_26.1_23B85_Restore/blob/main/System/Library/Frameworks/HealthKit.framework/HealthKit/HKAudiogramSensitivityTest.mm), plus the [initializer docs](https://developer.apple.com/documentation/healthkit/hkaudiogramsample/init(sensitivitypoints:start:end:device:metadata:)):

- 1 to 30 sensitivity points per sample; "Frequencies must be unique, and ordered ascending."
- Frequency between 0 and 30000 Hz.
- Sensitivity between -20 and 160 dBHL.
- At most two tests per point and at most one air conduction test per ear ("Sensitivity point cannot contain more than 1 test per ear"). So a point holds either the masked or the unmasked threshold for an ear, never both, and the exporter's "first test per ear" loses nothing today.
- At least one ear must have a value at each point.

## Frequencies

HealthKit does not fix a frequency set. Any ascending list up to 30 points is valid, so an importer must read whatever frequencies are present and must not assume the standard eight.

- Apple's Hearing Test plays tones "across a range of frequencies from 250Hz to 8000Hz" and uses Bayesian active learning that "dynamically samples over the entire frequency and dBHL ranges", producing a continuous estimate ([Apple white paper, October 2024](https://images.apple.com/health/pdf/Hearing_Health_Features_on_AirPods_Pro_2_October_2024.pdf), page 4). Its clinical validation compared thresholds at 500, 1000, 2000 and 4000 Hz and the eight-frequency average at 250, 500, 1000, 2000, 3000, 4000, 6000 and 8000 Hz. Which discrete frequencies it writes into the sample is not stated.
- The headline per-ear number in the Health app is an average of 500, 1000, 2000 and 4000 Hz (same white paper, page 12), with the grades no loss up to 25 dBHL, mild 26 to 40, moderate 41 to 60, severe 61 to 80, profound 81 and over. HealthKit has an internal `hearingLevelSummary` on the sample, but it is not exported.
- The project's manual entry decision (8 frequencies per ear) matches 250, 500, 1000, 2000, 3000, 4000, 6000, 8000 Hz; an imported Certified audiogram may have more or fewer points, including 125, 750 or 1500 Hz.

## Apple's Hearing Test versus entered audiograms

Inside HealthKit the distinction is explicit, but the export hides it:

- `isFirstPartyHearingTestResult` is true when the private metadata key `_HKPrivateMetadataKeyHearingTestTakenFromFirstParty` is true, `HKWasUserEntered` is not true, and the sample has a `device`.
- `_firstPartyIngestion` (an audiogram entered or scanned in Apple's own UI) is true when `_HKPrivateMetadataKeyAudiogramManualIngestionFromFirstParty` is true, or the source bundle identifier is `com.apple.Health` or `com.apple.Preferences`.

Both from the decompiled [`HKAudiogramSample.mm`](https://github.com/EthanArbuckle/iPhone18-3_26.1_23B85_Restore/blob/main/System/Library/Frameworks/HealthKit.framework/HealthKit/HKAudiogramSample.mm). The export never writes the private keys (see the metadata filter above) and never writes the bundle identifier, only the source name. What survives:

| Origin | What to expect in `export.xml` | Confidence |
| --- | --- | --- |
| Apple's Hearing Test with AirPods Pro 2 or AirPods Pro 3 (iOS 18.1 or later) | A `device` attribute describing the AirPods (the API requires a device for a first-party test result), no `HKWasUserEntered=1`, values at fractional dBHL, possibly clamping bounds | Inferred from the code; exact `sourceName` and device text not observed |
| Audiogram entered or scanned from paper in Settings or the Health app ("Add Hearing Test Result", [Apple support](https://support.apple.com/guide/airpods/devd9aac5b42/web)) | `sourceName` is the name of the Health or Settings source on that iPhone, probably no `device`; masked flags set from the entry screen (the ingestion UI has per-ear masked toggles, `AIAudiogramFrequencyInputCell setLeftEarMasked:`); integer values in 5 dB steps typical of clinics | Inferred; not observed |
| Third-party app writing through HealthKit (Mimi, hearing aid apps, clinic apps) | `sourceName` is the app's name, `sourceVersion` its build, arbitrary metadata such as `HKMetadataKeySyncIdentifier`, `HKExternalUUID` | Observed in the version 11 sample |

None of these says "certified". An importer cannot tell from the file whether an audiogram was measured by a professional; the person importing has to say so.

## `export_cda.xml`

The same exporter writes `export_cda.xml` (HL7 CDA R2) only from the quantity type path (`_writeQuantityType:` to `_writeCDAEntryWithValue:...`, into "vital signs" and "results" sections). `_writeDataForAudiogramType` writes XML elements to `export.xml` only. So audiograms are not in the CDA file, and an importer should ignore it. Source: same [`WDExportManager.mm`](https://github.com/EthanArbuckle/iPhone18-3_26.1_23B85_Restore/blob/main/System/Library/PrivateFrameworks/HealthToolbox.framework/HealthToolbox/WDExportManager.mm).

Both file names come from localized strings (`EXPORT_DATA_FILE_XML`, `EXPORT_DATA_FILE_CDA`), so on an iPhone set to another language the files inside the zip may not be called `export.xml`. An importer should look for the XML file whose root element is `HealthData` rather than match the English name.

## Open-source parsers

- [opendroid/hk `export/records.go`](https://github.com/opendroid/hk/blob/main/export/records.go) models `Audiogram` and `SensitivityPoint`, but its `SensitivityPoint` struct tags lack `,attr`, so Go's `encoding/xml` would look for child elements and leave every value empty. It also has no masked or clamping fields.
- [bry-guy/apple-health-report `cmd/main.go`](https://github.com/bry-guy/apple-health-report/blob/main/cmd/main.go) models the same pre-14 attributes correctly as attributes; no masked or clamping fields.
- No parser found handles `leftEarMasked` or the clamping bounds. None is worth depending on; the format is small enough to parse directly.

## What an importer needs

1. Accept the zip or the extracted folder; find the XML with root `HealthData` (name may be localized); read the export version from the `<!-- HealthKit Export Version: N -->` comment for diagnostics.
2. Stream it (exports are often hundreds of MB to several GB); only `Audiogram` elements matter, all at depth one.
3. For each `Audiogram`: take `startDate` as the audiogram date (`yyyy-MM-dd HH:mm:ss ZZZ`), keep `sourceName`, `sourceVersion`, the raw `device` text and public metadata for attribution, and keep `HKMetadataKeySyncIdentifier` or `HKExternalUUID` if present to detect re-imports.
4. For each `SensitivityPoint`: frequency in Hz; per ear an optional threshold in dBHL, an optional masked flag (absent before version 14, which means unknown, not unmasked), and optional clamping bounds. Check the unit strings and refuse anything that is not `Hz` and `dBHL`.
5. Do not require the eight standard frequencies or both ears at every point; show gaps as gaps.
6. Let the person choose which audiograms to import and mark them as Certified audiograms; the file cannot prove certification. Show Apple Hearing Test results, identified heuristically by an AirPods `device`, as a separate kind if the app wants to distinguish them.
7. Keep values as exported (they are already rounded to six significant digits) and treat clamped values as "at least" or "at most", not exact.

## Unknowns

- The exact `sourceName`, `device` text and metadata of an Apple Hearing Test audiogram and of a manually entered one in a real version 14 or later export. Settling it needs one real export from an iPhone with an Apple Hearing Test result and one manual entry.
- Which discrete frequencies Apple's Hearing Test writes into the sample (the algorithm is continuous; the stored points are not documented).
- Whether `_HKMetadataKeyIsPrivate` filters exactly the `_HKPrivate` prefix. Inferred from the name; the function body was not read.
- Whether manual entry in Apple's UI sets `HKWasUserEntered`.
- Whether HealthKit will add bone conduction later; the enum has room for it but the export DTD has no attribute for conduction type, so a future export would need a new attribute.
