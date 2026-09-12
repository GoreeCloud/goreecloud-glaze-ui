import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {
  assertObservationCaptureEligible,
  captureAccessibilityQualificationObservations,
  createAccessibilityObservationCapture,
  derivePreferenceObservationHints,
  observationCaptureCandidate
} from '../js/glaze-v1.4-accessibility-observation-capture.candidate.mjs';

const SOURCE = 'a'.repeat(40);
const TREE = 'b'.repeat(40);

function preparedRecord() {
  const required = [
    'source-and-runtime-identity',
    'multi-preference-composition',
    'reduced-transparency-solid-fallback',
    'increased-contrast-separation',
    'reduced-motion-motion-suppression',
    'forced-colors-system-color-path',
    'large-text-zoom-reflow',
    'keyboard-focus-order',
    'color-independent-semantic-state'
  ];
  const conditional = [
    'screen-reader-semantics-and-announcements',
    'voice-control-purpose-and-operation',
    'switch-control-operability'
  ];
  return {
    schemaVersion: 1,
    recordKind: 'glaze-v1.4-accessibility-qualification-evidence-candidate',
    target: {
      product: 'Glaze UI V1.4 — Optical Material and Chromatic Depth',
      targetVersion: '1.4.0-candidate',
      sourceRevision: SOURCE,
      sourceTreeRevision: TREE
    },
    status: 'in-progress',
    observedAt: '2026-09-12T00:00:00Z',
    reviewAuthority: {mode: 'combined', authority: 'Reviewer', humanReviewStatus: 'pending'},
    environment: {
      platformFamily: 'web',
      operatingSystem: {name: 'Test OS', version: '1'},
      browser: {name: 'Test Browser', version: '1'},
      physicalDevice: true,
      assistiveTechnologies: [],
      evidenceReferences: []
    },
    supportClaims: {
      screenReaderClaimed: false,
      voiceControlClaimed: false,
      switchControlClaimed: false
    },
    preferenceCoverage: {
      reducedTransparency: {state: 'not-tested', evidenceReferences: []},
      increasedContrast: {state: 'not-tested', evidenceReferences: []},
      reducedMotion: {state: 'not-tested', evidenceReferences: []},
      forcedColors: {state: 'not-tested', evidenceReferences: []}
    },
    scenarioResults: [
      ...required.map(id => ({id, result: 'not-tested', evidenceReferences: [], notes: 'PENDING'})),
      ...conditional.map(id => ({id, result: 'not-applicable', evidenceReferences: [], notes: 'Unclaimed'}))
    ],
    issues: [{summary: 'Prepared packet only', severity: 'info', resolved: false, reference: null}],
    disposition: {
      evaluatorDisposition: 'blocked',
      acceptedForAccessibilityQualification: false,
      acceptedForLifecycleGate: false,
      notes: 'prepared'
    }
  };
}

test('prepared qualification record is capture eligible', () => {
  assert.equal(assertObservationCaptureEligible(preparedRecord()), true);
});

test('zero source revision is rejected', () => {
  const record = preparedRecord();
  record.target.sourceRevision = '0'.repeat(40);
  assert.throws(() => assertObservationCaptureEligible(record), /source revision/);
});

test('duplicate scenario ids are rejected', () => {
  const record = preparedRecord();
  record.scenarioResults.push(structuredClone(record.scenarioResults[0]));
  assert.throws(() => assertObservationCaptureEligible(record), /duplicate scenario ids/);
});

test('support claim fields must remain boolean', () => {
  const record = preparedRecord();
  record.supportClaims.screenReaderClaimed = 'yes';
  assert.throws(() => assertObservationCaptureEligible(record), /support claim screenReaderClaimed must be boolean/);
});

test('malformed observedAt is rejected', () => {
  assert.throws(() => captureAccessibilityQualificationObservations(preparedRecord(), {
    observedAt: 'not-a-date'
  }), /ISO-compatible date-time/);
});

test('accepted record is rejected', () => {
  const record = preparedRecord();
  record.reviewAuthority.humanReviewStatus = 'accepted';
  assert.throws(() => assertObservationCaptureEligible(record), /pending human review/);
});

test('local preference detection produces hints only', () => {
  const hints = derivePreferenceObservationHints({
    evidence: {
      media: {
        reducedTransparency: {available: true, matches: true},
        increasedContrast: {available: true, matches: false},
        reducedMotion: {available: false, matches: false},
        forcedColors: {available: true, matches: true}
      }
    }
  });
  assert.equal(hints.reducedTransparency.suggestedState, 'tested-active');
  assert.equal(hints.increasedContrast.suggestedState, 'tested-inactive');
  assert.equal(hints.reducedMotion.suggestedState, 'not-tested');
  assert.equal(hints.forcedColors.suggestedState, 'tested-active');
  for (const hint of Object.values(hints)) {
    assert.equal(hint.qualificationEvidence, false);
    assert.equal(hint.requiresReviewerConfirmation, true);
    assert.equal(hint.requiresReviewerEvidenceReference, true);
  }
});

test('capture never auto-applies preference hints or scenario passes', () => {
  const record = preparedRecord();
  const captured = captureAccessibilityQualificationObservations(record, {}, {
    clock: () => new Date('2026-09-12T01:00:00Z')
  });
  assert.deepEqual(captured.preferenceCoverage, record.preferenceCoverage);
  assert.deepEqual(captured.scenarioResults, record.scenarioResults);
  assert.equal(captured.status, 'in-progress');
  assert.equal(captured.reviewAuthority.humanReviewStatus, 'pending');
  assert.equal(captured.disposition.acceptedForAccessibilityQualification, false);
  assert.equal(captured.disposition.acceptedForLifecycleGate, false);
});

test('tested preference requires explicit reviewer evidence reference', () => {
  assert.throws(() => captureAccessibilityQualificationObservations(preparedRecord(), {
    preferenceObservations: {
      reducedTransparency: {state: 'tested-active', evidenceReferences: []}
    }
  }), /requires explicit reviewer evidence references/);
});

test('reviewer-confirmed preference observation is recorded', () => {
  const captured = captureAccessibilityQualificationObservations(preparedRecord(), {
    preferenceObservations: {
      reducedTransparency: {state: 'tested-active', evidenceReferences: ['artifact:reduced-transparency.json']}
    }
  });
  assert.deepEqual(captured.preferenceCoverage.reducedTransparency, {
    state: 'tested-active',
    evidenceReferences: ['artifact:reduced-transparency.json']
  });
});

test('scenario pass requires explicit evidence and remains non-promoting', () => {
  const captured = captureAccessibilityQualificationObservations(preparedRecord(), {
    scenarioObservations: {
      'keyboard-focus-order': {
        result: 'pass',
        evidenceReferences: ['artifact:keyboard-focus-order.json'],
        notes: 'Reviewed manually.'
      }
    }
  });
  const entry = captured.scenarioResults.find(item => item.id === 'keyboard-focus-order');
  assert.equal(entry.result, 'pass');
  assert.equal(captured.reviewAuthority.humanReviewStatus, 'pending');
  assert.equal(captured.disposition.evaluatorDisposition, 'blocked');
  assert.equal(captured.disposition.acceptedForAccessibilityQualification, false);
  assert.equal(captured.disposition.acceptedForLifecycleGate, false);
});

test('required scenario cannot be not-applicable', () => {
  assert.throws(() => captureAccessibilityQualificationObservations(preparedRecord(), {
    scenarioObservations: {
      'keyboard-focus-order': {result: 'not-applicable', evidenceReferences: [], notes: ''}
    }
  }), /cannot be not-applicable/);
});

test('claimed assistive technology scenario cannot be not-applicable', () => {
  const record = preparedRecord();
  record.supportClaims.screenReaderClaimed = true;
  record.scenarioResults.find(item => item.id === 'screen-reader-semantics-and-announcements').result = 'not-tested';
  assert.throws(() => captureAccessibilityQualificationObservations(record, {
    scenarioObservations: {
      'screen-reader-semantics-and-announcements': {result: 'not-applicable', evidenceReferences: [], notes: ''}
    }
  }), /cannot be not-applicable/);
});

test('capture preserves exact source and tree identity and does not mutate input', () => {
  const record = preparedRecord();
  const original = structuredClone(record);
  const captured = captureAccessibilityQualificationObservations(record, {
    environmentEvidenceReferences: ['artifact:environment.json'],
    assistiveTechnologies: [{name: 'Keyboard', version: 'system', mode: 'keyboard'}]
  });
  assert.deepEqual(record, original);
  assert.deepEqual(captured.target, original.target);
  assert.deepEqual(captured.environment.evidenceReferences, ['artifact:environment.json']);
  assert.deepEqual(captured.environment.assistiveTechnologies, [{name: 'Keyboard', version: 'system', mode: 'keyboard'}]);
});

test('capture candidate forbids automatic acceptance and remote collection', () => {
  const adapter = createAccessibilityObservationCapture();
  assert.equal(adapter.networkAccessRequired, false);
  assert.equal(adapter.telemetryRequired, false);
  assert.equal(adapter.analyticsRequired, false);
  assert.equal(adapter.persistentStorageRequired, false);
  assert.equal(adapter.browserIdentitySniffingAllowed, false);
  assert.equal(adapter.automaticScenarioPassAllowed, false);
  assert.equal(adapter.automaticHumanAcceptanceAllowed, false);
  assert.equal(adapter.automaticAccessibilityQualificationAllowed, false);
  assert.equal(adapter.automaticLifecycleAcceptanceAllowed, false);
  assert.equal(observationCaptureCandidate.exportRequiresExplicitUserAction, true);
});

test('source has no network, telemetry, persistence, identity sniffing, or capture APIs', () => {
  const source = readFileSync(new URL('../js/glaze-v1.4-accessibility-observation-capture.candidate.mjs', import.meta.url), 'utf8');
  for (const forbidden of [
    'fetch(', 'XMLHttpRequest', 'sendBeacon', 'WebSocket',
    'localStorage', 'sessionStorage', 'indexedDB',
    'navigator.userAgent', 'navigator.userAgentData', 'navigator.platform',
    'getUserMedia', 'getDisplayMedia'
  ]) {
    assert.equal(source.includes(forbidden), false, `forbidden source pattern found: ${forbidden}`);
  }
});

test('local observation capture reference surface has no remote collection path', () => {
  const runtime = readFileSync(new URL('../reference/glaze-v1.4-accessibility-observation-capture.candidate.mjs', import.meta.url), 'utf8');
  const html = readFileSync(new URL('../reference/glaze-v1.4-accessibility-observation-capture.candidate.html', import.meta.url), 'utf8');
  for (const forbidden of [
    'fetch(', 'XMLHttpRequest', 'sendBeacon', 'WebSocket',
    'localStorage', 'sessionStorage', 'indexedDB',
    'navigator.userAgent', 'navigator.userAgentData', 'navigator.platform',
    'getUserMedia', 'getDisplayMedia', 'http://', 'https://'
  ]) {
    assert.equal(runtime.includes(forbidden), false, `forbidden reference runtime pattern found: ${forbidden}`);
    assert.equal(html.includes(forbidden), false, `forbidden reference HTML pattern found: ${forbidden}`);
  }
  assert.equal(runtime.includes('file.text()'), true);
  assert.equal(runtime.includes('new Blob'), true);
  assert.equal(runtime.includes('URL.createObjectURL'), true);
  assert.equal(runtime.includes('URL.revokeObjectURL'), true);
  assert.equal(html.includes('does not auto-pass scenarios'), true);
  assert.equal(html.includes('export happens only when you choose the export action'), true);
});
