# GLAZE UI V1.3 Physical Qualification Support

**Frozen observed source:** `72ad63bf32d80420b25dc98bfd2def47bcc2a427`

This evidence-branch tooling supports the three remaining physical/native Candidate-stage lanes:

- `physical-device-native-platform-qualification`
- `physical-device-production-performance-qualification`
- `native-personalization-adapter-qualification`

It never creates `passed` evidence and never changes lifecycle state. Real physical-device/native observations and authorized human/combined review remain mandatory.

## Android physical/native packet

With exactly one authorized device connected through ADB:

```sh
python3 evidence/v1.3/tools/collect-device-qualification.py physical-device \
  --output artifacts/v1.3/device-qualification/physical-device-72ad63b
```

When several devices are connected, use `--serial` only as a transport selector. The collector deliberately does not retain the serial identifier in the packet.

## Linux/native-host packet

Run on the representative physical Linux host/session:

```sh
python3 evidence/v1.3/tools/collect-device-qualification.py native-host \
  --output artifacts/v1.3/device-qualification/native-host-72ad63b
```

This captures environment/compositor support information where tools are present. Human observation is still required for actual native windowing, pointer, keyboard, focus, resize, multi-window, fallback, and visual behavior.

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

## Packet integrity

Every packet contains `report.json`, raw supporting evidence, `README.txt`, and `SHA256SUMS.txt`. Verify it from inside the packet directory with:

```sh
sha256sum -c SHA256SUMS.txt
```

## Acceptance boundary

Do not move a packet into `evidence/v1.3/*.json`. After the real session is complete, create a separate immutable schema-v2 qualification record using the frozen source SHA and cite the packet or retained artifacts as inspectable evidence. `accepted_for_lifecycle_gate` must remain false until the authorized reviewer genuinely accepts the track.
