const RECORD_KIND = 'glaze-v1.4-accessibility-qualification-evidence-candidate';
const TARGET_PRODUCT = 'Glaze UI V1.4 — Optical Material and Chromatic Depth';
const TARGET_VERSION = '1.4.0-candidate';
const ZERO_SHA = '0'.repeat(40);
const SHA40 = /^[0-9a-f]{40}$/;

const REQUIRED_PREFERENCES = Object.freeze([
  'reducedTransparency',
  'increasedContrast',
  'reducedMotion',
  'forcedColors'
]);

const REQUIRED_SCENARIOS = Object.freeze([
  'source-and-runtime-identity',
  'multi-preference-composition',
  'reduced-transparency-solid-fallback',
  'increased-contrast-separation',
  'reduced-motion-motion-suppression',
  'forced-colors-system-color-path',
  'large-text-zoom-reflow',
  'keyboard-focus-order',
  'color-independent-semantic-state'
]);

const CONDITIONAL_SCENARIOS = Object.freeze({
  screenReaderClaimed: 'screen-reader-semantics-and-announcements',
  voiceControlClaimed: 'voice-control-purpose-and-operation',
  switchControlClaimed: 'switch-control-operability'
});

const PREFERENCE_STATES = new Set([
  'tested-active',
  'tested-inactive',
  'not-supported',
  'not-tested'
]);
const SCENARIO_RESULTS = new Set(['pass', 'fail', 'not-tested', 'not-applicable']);
const ASSISTIVE_TECH_MODES = new Set(['screen-reader', 'voice-control', 'switch-control', 'keyboard', 'other']);

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function requireCondition(condition, message) {
  if (!condition) throw new TypeError(message);
}

function requireSha(value, label) {
  requireCondition(typeof value === 'string' && SHA40.test(value) && value !== ZERO_SHA, `${label} must be an immutable non-placeholder 40-character lowercase SHA`);
}

function normalizeReferences(value, label) {
  if (value == null) return [];
  requireCondition(Array.isArray(value), `${label} must be an array`);
  const normalized = value.map(item => {
    requireCondition(typeof item === 'string' && item.trim().length > 0, `${label} entries must be non-empty strings`);
    return item.trim();
  });
  requireCondition(new Set(normalized).size === normalized.length, `${label} entries must be unique`);
  return normalized;
}

function normalizeAssistiveTechnologies(value) {
  if (value == null) return null;
  requireCondition(Array.isArray(value), 'assistiveTechnologies must be an array');
  return value.map((entry, index) => {
    requireCondition(entry && typeof entry === 'object' && !Array.isArray(entry), `assistiveTechnologies[${index}] must be an object`);
    const name = String(entry.name ?? '').trim();
    const version = String(entry.version ?? '').trim();
    const mode = String(entry.mode ?? '').trim();
    requireCondition(name.length > 0, `assistiveTechnologies[${index}].name must not be empty`);
    requireCondition(version.length > 0, `assistiveTechnologies[${index}].version must not be empty`);
    requireCondition(ASSISTIVE_TECH_MODES.has(mode), `assistiveTechnologies[${index}].mode is invalid`);
    return {name, version, mode};
  });
}

function eligibleRequiredScenarioIds(record) {
  const required = [...REQUIRED_SCENARIOS];
  const claims = record.supportClaims ?? {};
  for (const [claimKey, scenarioId] of Object.entries(CONDITIONAL_SCENARIOS)) {
    if (claims[claimKey] === true) required.push(scenarioId);
  }
  return new Set(required);
}

export function assertObservationCaptureEligible(record) {
  requireCondition(record && typeof record === 'object' && !Array.isArray(record), 'qualification record must be an object');
  requireCondition(record.schemaVersion === 1, 'qualification record schemaVersion must remain 1');
  requireCondition(record.recordKind === RECORD_KIND, 'qualification record kind is not eligible for V1.4 observation capture');
  requireCondition(record.target?.product === TARGET_PRODUCT, 'qualification target product is invalid');
  requireCondition(record.target?.targetVersion === TARGET_VERSION, 'qualification target version is invalid');
  requireSha(record.target?.sourceRevision, 'source revision');
  requireSha(record.target?.sourceTreeRevision, 'source tree revision');
  requireCondition(record.status === 'in-progress', 'observation capture only accepts in-progress qualification records');
  requireCondition(record.reviewAuthority?.humanReviewStatus === 'pending', 'observation capture requires pending human review');
  requireCondition(record.disposition?.acceptedForAccessibilityQualification === false, 'observation capture cannot load an accessibility-accepted record');
  requireCondition(record.disposition?.acceptedForLifecycleGate === false, 'observation capture cannot load a lifecycle-accepted record');
  requireCondition(record.disposition?.evaluatorDisposition !== 'accepted', 'observation capture cannot load an evaluator-accepted record');
  requireCondition(record.environment && typeof record.environment === 'object', 'qualification environment is required');
  requireCondition(record.supportClaims && typeof record.supportClaims === 'object' && !Array.isArray(record.supportClaims), 'supportClaims must be an object');
  for (const claimKey of Object.keys(CONDITIONAL_SCENARIOS)) {
    requireCondition(typeof record.supportClaims[claimKey] === 'boolean', `support claim ${claimKey} must be boolean`);
  }
  requireCondition(record.preferenceCoverage && typeof record.preferenceCoverage === 'object', 'preferenceCoverage is required');
  requireCondition(Array.isArray(record.scenarioResults), 'scenarioResults must be an array');
  for (const preference of REQUIRED_PREFERENCES) {
    requireCondition(record.preferenceCoverage[preference] && typeof record.preferenceCoverage[preference] === 'object', `missing preference coverage entry: ${preference}`);
  }
  const rawScenarioIds = record.scenarioResults.map(entry => entry?.id);
  requireCondition(rawScenarioIds.every(id => typeof id === 'string' && id.length > 0), 'scenarioResults entries must have non-empty string ids');
  const scenarioIds = new Set(rawScenarioIds);
  requireCondition(scenarioIds.size === rawScenarioIds.length, 'scenarioResults must not contain duplicate scenario ids');
  for (const scenarioId of [...REQUIRED_SCENARIOS, ...Object.values(CONDITIONAL_SCENARIOS)]) {
    requireCondition(scenarioIds.has(scenarioId), `missing scenario entry: ${scenarioId}`);
  }
  return true;
}

export function derivePreferenceObservationHints(snapshot) {
  const media = snapshot?.evidence?.media ?? {};
  const hints = {};
  for (const preference of REQUIRED_PREFERENCES) {
    const evidence = media[preference];
    const available = evidence?.available === true;
    hints[preference] = Object.freeze({
      suggestedState: available ? (evidence?.matches === true ? 'tested-active' : 'tested-inactive') : 'not-tested',
      localDetectionAvailable: available,
      localDetectionMatched: available && evidence?.matches === true,
      qualificationEvidence: false,
      requiresReviewerConfirmation: true,
      requiresReviewerEvidenceReference: true
    });
  }
  return Object.freeze(hints);
}

function applyPreferenceObservations(record, observations) {
  if (observations == null) return;
  requireCondition(observations && typeof observations === 'object' && !Array.isArray(observations), 'preferenceObservations must be an object');
  for (const [preference, observation] of Object.entries(observations)) {
    requireCondition(REQUIRED_PREFERENCES.includes(preference), `unknown preference observation: ${preference}`);
    requireCondition(observation && typeof observation === 'object' && !Array.isArray(observation), `preference observation ${preference} must be an object`);
    const state = observation.state;
    requireCondition(PREFERENCE_STATES.has(state), `invalid preference state for ${preference}`);
    const evidenceReferences = normalizeReferences(observation.evidenceReferences, `${preference}.evidenceReferences`);
    if (state === 'not-tested') {
      requireCondition(evidenceReferences.length === 0, `not-tested preference ${preference} must not carry qualification evidence references`);
    } else {
      requireCondition(evidenceReferences.length > 0, `${state} preference ${preference} requires explicit reviewer evidence references`);
    }
    record.preferenceCoverage[preference] = {state, evidenceReferences};
  }
}

function applyScenarioObservations(record, observations) {
  if (observations == null) return;
  requireCondition(observations && typeof observations === 'object' && !Array.isArray(observations), 'scenarioObservations must be an object');
  const requiredIds = eligibleRequiredScenarioIds(record);
  const scenarioMap = new Map(record.scenarioResults.map(entry => [entry.id, entry]));
  for (const [scenarioId, observation] of Object.entries(observations)) {
    requireCondition(scenarioMap.has(scenarioId), `unknown scenario observation: ${scenarioId}`);
    requireCondition(observation && typeof observation === 'object' && !Array.isArray(observation), `scenario observation ${scenarioId} must be an object`);
    const result = observation.result;
    requireCondition(SCENARIO_RESULTS.has(result), `invalid scenario result for ${scenarioId}`);
    requireCondition(!(result === 'not-applicable' && requiredIds.has(scenarioId)), `required or claimed scenario ${scenarioId} cannot be not-applicable`);
    const evidenceReferences = normalizeReferences(observation.evidenceReferences, `${scenarioId}.evidenceReferences`);
    if (result === 'pass' || result === 'fail') {
      requireCondition(evidenceReferences.length > 0, `${result} scenario ${scenarioId} requires explicit reviewer evidence references`);
    } else {
      requireCondition(evidenceReferences.length === 0, `${result} scenario ${scenarioId} must not carry qualification evidence references`);
    }
    scenarioMap.set(scenarioId, {
      id: scenarioId,
      result,
      evidenceReferences,
      notes: String(observation.notes ?? '').trim()
    });
  }
  record.scenarioResults = record.scenarioResults.map(entry => scenarioMap.get(entry.id));
}

function applyIssues(record, issues) {
  if (issues == null) return;
  requireCondition(Array.isArray(issues), 'issues must be an array');
  const normalized = issues.map((issue, index) => {
    requireCondition(issue && typeof issue === 'object' && !Array.isArray(issue), `issues[${index}] must be an object`);
    const summary = String(issue.summary ?? '').trim();
    const severity = String(issue.severity ?? '').trim();
    const resolved = issue.resolved;
    const reference = issue.reference == null ? null : String(issue.reference).trim();
    requireCondition(summary.length > 0, `issues[${index}].summary must not be empty`);
    requireCondition(['info', 'low', 'medium', 'high', 'critical'].includes(severity), `issues[${index}].severity is invalid`);
    requireCondition(typeof resolved === 'boolean', `issues[${index}].resolved must be boolean`);
    return {summary, severity, resolved, reference: reference || null};
  });
  record.issues = [...record.issues, ...normalized];
}

export function captureAccessibilityQualificationObservations(preparedRecord, observations = {}, {clock = () => new Date()} = {}) {
  assertObservationCaptureEligible(preparedRecord);
  requireCondition(observations && typeof observations === 'object' && !Array.isArray(observations), 'observations must be an object');
  const record = cloneJson(preparedRecord);
  const originalTarget = cloneJson(record.target);

  if (observations.environmentEvidenceReferences != null) {
    record.environment.evidenceReferences = normalizeReferences(observations.environmentEvidenceReferences, 'environmentEvidenceReferences');
  }
  const assistiveTechnologies = normalizeAssistiveTechnologies(observations.assistiveTechnologies);
  if (assistiveTechnologies !== null) record.environment.assistiveTechnologies = assistiveTechnologies;

  applyPreferenceObservations(record, observations.preferenceObservations);
  applyScenarioObservations(record, observations.scenarioObservations);
  applyIssues(record, observations.issues);

  const observedAt = observations.observedAt == null
    ? clock().toISOString()
    : String(observations.observedAt).trim();
  requireCondition(observedAt.length > 0, 'observedAt must not be empty');
  const observedTime = Date.parse(observedAt);
  requireCondition(Number.isFinite(observedTime), 'observedAt must be an ISO-compatible date-time');
  record.observedAt = observedAt;

  // Observation capture is intentionally non-promoting. A separate evaluator and
  // authorized review must decide whether captured evidence is review-ready/accepted.
  record.status = 'in-progress';
  record.reviewAuthority.humanReviewStatus = 'pending';
  record.disposition = {
    evaluatorDisposition: 'blocked',
    acceptedForAccessibilityQualification: false,
    acceptedForLifecycleGate: false,
    notes: 'OBSERVATION CAPTURE ONLY. Local/manual observations were recorded, but no human acceptance, accessibility qualification, consumer conformance, or lifecycle promotion is granted.'
  };

  requireCondition(JSON.stringify(record.target) === JSON.stringify(originalTarget), 'observation capture may not alter exact source/tree identity');
  assertObservationCaptureEligible(record);
  return record;
}

export function createAccessibilityObservationCapture({clock = () => new Date()} = {}) {
  return Object.freeze({
    kind: 'glaze-v1.4-accessibility-observation-capture-candidate',
    releaseLifecycle: 'proposed',
    consumerEligible: false,
    lifecycleAuthority: false,
    localOnly: true,
    networkAccessRequired: false,
    telemetryRequired: false,
    analyticsRequired: false,
    persistentStorageRequired: false,
    browserIdentitySniffingAllowed: false,
    automaticPreferenceAcceptanceAllowed: false,
    automaticScenarioPassAllowed: false,
    automaticHumanAcceptanceAllowed: false,
    automaticAccessibilityQualificationAllowed: false,
    automaticLifecycleAcceptanceAllowed: false,
    assertEligible: assertObservationCaptureEligible,
    derivePreferenceHints: derivePreferenceObservationHints,
    capture(record, observations = {}) {
      return captureAccessibilityQualificationObservations(record, observations, {clock});
    }
  });
}

export const observationCaptureCandidate = Object.freeze({
  targetVersion: TARGET_VERSION,
  releaseLifecycle: 'proposed',
  consumerEligible: false,
  lifecycleAuthority: false,
  qualificationApiStability: 'candidate-not-frozen',
  stableSource: '1.3.0',
  recordKind: RECORD_KIND,
  requiredPreferences: REQUIRED_PREFERENCES,
  requiredScenarios: REQUIRED_SCENARIOS,
  conditionalScenarios: CONDITIONAL_SCENARIOS,
  localDetectionIsQualificationEvidence: false,
  automaticPreferenceAcceptanceAllowed: false,
  automaticScenarioPassAllowed: false,
  automaticHumanAcceptanceAllowed: false,
  automaticAccessibilityQualificationAllowed: false,
  automaticLifecycleAcceptanceAllowed: false,
  networkAccessRequired: false,
  telemetryRequired: false,
  analyticsRequired: false,
  persistentStorageRequired: false,
  browserIdentitySniffingAllowed: false,
  exportRequiresExplicitUserAction: true
});
