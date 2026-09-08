# GLAZE UI V1.3 Physical Qualification Support

**Frozen observed source:** `72ad63bf32d80420b25dc98bfd2def47bcc2a427`

This evidence-branch tooling supports the three remaining physical/native Candidate-stage lanes:

- `physical-device-native-platform-qualification`
- `physical-device-production-performance-qualification`
- `native-personalization-adapter-qualification`

The GoreeCloud project owner has attested that all human verification components passed. The human-review portion of these combined lanes is therefore no longer a blocker. Their retained physical/native evidence requirements remain mandatory and fail closed.

This tooling never creates `passed` evidence and never changes lifecycle state. Real physical-device/native evidence and authorized combined acceptance remain mandatory.

## Android physical/native packet

With exactly one authorized device connected through ADB:

```sh
python3 evidence/v1.3/tools/collect-device-qualification.py physical-device \
  --output artifacts/v1.3/device-qualification/physical-device-72ad63b
```

When several devices are connected, use `--serial` only as a transport selector. The collector deliberately does not retain the serial identifier in the packet.

Validate the resulting packet before review:

```sh
python3 evidence/v1.3/tools/validate-device-qualification-packet.py packet \
  artifacts/v1.3/device-qualification/physical-device-72ad63b \
  --mode physical-device
```

## Linux/native-host packet

Run on the representative physical Linux host/session:

```sh
python3 evidence/v1.3/tools/collect-device-qualification.py native-host \
  --output artifacts/v1.3/device-qualification/native-host-72ad63b
```

This captures environment/compositor support information where tools are present. Human observation is still required for actual native windowing, pointer, keyboard, focus, resize, multi-window, fallback, and visual behavior.

Validate the packet:

```sh
python3 evidence/v1.3/tools/validate-device-qualification-packet.py packet \
  artifacts/v1.3/device-qualification/native-host-72ad63b \
  --mode native-host
```

## Production-performance packet

Run against a representative physical device and the actual package under test:

```sh
python3 evidence/v1.3/tools/collect-device-qualification.py performance \
  --package <PACKAGE_UNDER_TEST> \
  --samples 10 \
  --interval 2 \
  --output artifacts/v1.3/device-qualification/performance-72ad63b
```

The packet captures repeated `meminfo`, `gfxinfo ... framestats`, CPU, thermal, battery, and SurfaceFlinger inventory data. It does not invent a performance budget or judge a pass. The reviewer must retain the accepted budget reference, measurement method, sample window, device state, raw evidence, and disposition.

Validate structural and cryptographic completeness before review:

```sh
python3 evidence/v1.3/tools/validate-device-qualification-packet.py packet \
  artifacts/v1.3/device-qualification/performance-72ad63b \
  --mode performance
```

## Native Personalization packet

Capture a state before the real adapter interaction:

```sh
python3 evidence/v1.3/tools/collect-device-qualification.py personalization \
  --phase before \
  --output artifacts/v1.3/device-qualification/personalization-before-72ad63b
```

Perform the real appearance/personalization operation, then capture the after state:

```sh
python3 evidence/v1.3/tools/collect-device-qualification.py personalization \
  --phase after \
  --output artifacts/v1.3/device-qualification/personalization-after-72ad63b
```

No raw wallpaper image bytes are read or transmitted. The collector retains only bounded wallpaper metadata output and system appearance/motion/text-scale state. The reviewer must still observe persistence, system-appearance integration, wallpaper-source behavior where claimed, failure/fallback behavior, and accessibility precedence.

Validate both packets as one pair before combined review:

```sh
python3 evidence/v1.3/tools/validate-device-qualification-packet.py personalization-pair \
  artifacts/v1.3/device-qualification/personalization-before-72ad63b \
  artifacts/v1.3/device-qualification/personalization-after-72ad63b
```

The pair validator additionally verifies that both packets target the same physical device/build identity and that the phases are correctly ordered.

## Packet integrity and intake rules

Every packet contains `report.json`, raw supporting evidence, `README.txt`, and `SHA256SUMS.txt`. The intake validator checks all of the following before a packet is eligible for combined review:

- every non-manifest file is listed exactly once in `SHA256SUMS.txt`;
- every SHA-256 digest matches;
- manifest paths are relative and path traversal is forbidden;
- the packet schema is the governed V1.3 support-packet schema;
- `frozen_source_revision` is exactly `72ad63bf32d80420b25dc98bfd2def47bcc2a427`;
- `qualification_credit` remains `false`;
- `accepted_for_lifecycle_gate` remains `false`;
- manual/combined review remains required;
- mode-specific evidence files and metadata are complete;
- performance sample files match the reported sample count;
- personalization packets contain metadata only and no image payloads;
- a Personalization before/after pair identifies the same physical device/build.

You can also verify raw hashes directly from inside a packet directory with:

```sh
sha256sum -c SHA256SUMS.txt
```

A validator success means only **structurally and cryptographically ready for combined review**. It is not a qualification pass.

## Current qualification state

- Human Optical: accepted.
- Manual Assistive Technology: accepted.
- Candidate-stage qualification: **2/5**.
- Stable qualification overall: **2/6**.
- Physical-device/native-platform: human portion passed; retained physical/native packet evidence pending.
- Physical production performance: human portion passed; retained physical measurement and accepted-budget evidence pending.
- Native Personalization adapter: human portion passed; retained native before/after evidence pending.

Candidate remains inactive until all five Candidate-stage tracks are genuinely accepted.

## Acceptance boundary

Do not move a packet into `evidence/v1.3/*.json`. After the real session is complete, validate the packet, perform the required combined review, and then create a separate immutable schema-v2 qualification record using the frozen source SHA and citing the retained packet/artifacts as inspectable evidence. `accepted_for_lifecycle_gate` must remain false until the authorized combined review genuinely accepts the track.
