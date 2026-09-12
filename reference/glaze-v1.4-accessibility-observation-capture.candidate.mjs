import {
  createBrowserOpticalCapabilityAdapter
} from '../js/glaze-v1.4-browser-capabilities.candidate.mjs';
import {
  createAccessibilityObservationCapture,
  observationCaptureCandidate
} from '../js/glaze-v1.4-accessibility-observation-capture.candidate.mjs';

const capabilityAdapter = createBrowserOpticalCapabilityAdapter({environment: globalThis});
const captureAdapter = createAccessibilityObservationCapture();

let loadedRecord = null;
let preferenceHints = captureAdapter.derivePreferenceHints(capabilityAdapter.snapshot());

const preferenceBody = document.querySelector('#glz14-observation-preferences');
const scenarioBody = document.querySelector('#glz14-observation-scenarios');
const packetFile = document.querySelector('#glz14-packet-file');
const exportButton = document.querySelector('#glz14-export-record');
const refreshHintsButton = document.querySelector('#glz14-refresh-hints');
const environmentRefs = document.querySelector('#glz14-environment-evidence');
const assistiveTechnologies = document.querySelector('#glz14-assistive-technologies');
const recordStatus = document.querySelector('#glz14-capture-status');
const sourceSummary = document.querySelector('#glz14-source-summary');

function splitLines(value) {
  return String(value ?? '')
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean);
}

function parseAssistiveTechnologies(value) {
  return splitLines(value).map((line, index) => {
    const parts = line.split('|').map(part => part.trim());
    if (parts.length !== 3 || parts.some(part => !part)) {
      throw new TypeError(`Assistive technology line ${index + 1} must use mode | name | version.`);
    }
    const [mode, name, version] = parts;
    return {mode, name, version};
  });
}

function replaceDefinitionList(target, entries) {
  target.replaceChildren();
  for (const [term, value] of entries) {
    const dt = document.createElement('dt');
    const dd = document.createElement('dd');
    dt.textContent = term;
    dd.textContent = value;
    target.append(dt, dd);
  }
}

function createSelect(values, selected, {disableNotApplicable = false} = {}) {
  const select = document.createElement('select');
  for (const value of values) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    option.selected = value === selected;
    if (disableNotApplicable && value === 'not-applicable') option.disabled = true;
    select.append(option);
  }
  return select;
}

function textarea(value = '', label) {
  const input = document.createElement('textarea');
  input.rows = 2;
  input.value = value;
  input.setAttribute('aria-label', label);
  return input;
}

function renderPreferenceRows(record) {
  preferenceBody.replaceChildren();
  for (const preference of observationCaptureCandidate.requiredPreferences) {
    const current = record.preferenceCoverage[preference];
    const hint = preferenceHints[preference];
    const row = document.createElement('tr');
    const name = document.createElement('th');
    name.scope = 'row';
    name.textContent = preference;
    const hintCell = document.createElement('td');
    hintCell.textContent = hint.localDetectionAvailable
      ? `local hint only: ${hint.suggestedState}`
      : 'local hint unavailable; remains not-tested';
    const stateCell = document.createElement('td');
    const state = createSelect(
      ['not-tested', 'tested-active', 'tested-inactive', 'not-supported'],
      current.state
    );
    state.dataset.preferenceState = preference;
    state.setAttribute('aria-label', `${preference} reviewer-confirmed state`);
    stateCell.append(state);
    const evidenceCell = document.createElement('td');
    const evidence = textarea(current.evidenceReferences.join('\n'), `${preference} evidence references`);
    evidence.dataset.preferenceEvidence = preference;
    evidenceCell.append(evidence);
    row.append(name, hintCell, stateCell, evidenceCell);
    preferenceBody.append(row);
  }
}

function requiredScenarioIds(record) {
  const required = new Set(observationCaptureCandidate.requiredScenarios);
  for (const [claimKey, scenarioId] of Object.entries(observationCaptureCandidate.conditionalScenarios)) {
    if (record.supportClaims?.[claimKey] === true) required.add(scenarioId);
  }
  return required;
}

function renderScenarioRows(record) {
  scenarioBody.replaceChildren();
  const required = requiredScenarioIds(record);
  for (const scenario of record.scenarioResults) {
    const row = document.createElement('tr');
    const name = document.createElement('th');
    name.scope = 'row';
    name.textContent = scenario.id;
    const requirement = document.createElement('td');
    requirement.textContent = required.has(scenario.id) ? 'required' : 'conditional / unclaimed';
    const resultCell = document.createElement('td');
    const result = createSelect(
      ['not-tested', 'pass', 'fail', 'not-applicable'],
      scenario.result,
      {disableNotApplicable: required.has(scenario.id)}
    );
    result.dataset.scenarioResult = scenario.id;
    result.setAttribute('aria-label', `${scenario.id} reviewer result`);
    resultCell.append(result);
    const evidenceCell = document.createElement('td');
    const evidence = textarea(scenario.evidenceReferences.join('\n'), `${scenario.id} evidence references`);
    evidence.dataset.scenarioEvidence = scenario.id;
    evidenceCell.append(evidence);
    const notesCell = document.createElement('td');
    const notes = textarea(scenario.notes, `${scenario.id} notes`);
    notes.dataset.scenarioNotes = scenario.id;
    notesCell.append(notes);
    row.append(name, requirement, resultCell, evidenceCell, notesCell);
    scenarioBody.append(row);
  }
}

function renderLoadedRecord(record) {
  replaceDefinitionList(sourceSummary, [
    ['Source revision', record.target.sourceRevision],
    ['Source tree revision', record.target.sourceTreeRevision],
    ['Platform family', record.environment.platformFamily],
    ['Operating system', `${record.environment.operatingSystem.name} ${record.environment.operatingSystem.version}`],
    ['Browser', record.environment.browser ? `${record.environment.browser.name} ${record.environment.browser.version}` : 'not recorded'],
    ['Review authority', record.reviewAuthority.authority],
    ['Human review status', record.reviewAuthority.humanReviewStatus],
    ['Accessibility qualified', String(record.disposition.acceptedForAccessibilityQualification)],
    ['Lifecycle gate accepted', String(record.disposition.acceptedForLifecycleGate)]
  ]);
  environmentRefs.value = record.environment.evidenceReferences.join('\n');
  assistiveTechnologies.value = record.environment.assistiveTechnologies
    .map(item => `${item.mode} | ${item.name} | ${item.version}`)
    .join('\n');
  renderPreferenceRows(record);
  renderScenarioRows(record);
  exportButton.disabled = false;
  recordStatus.textContent = 'Prepared packet loaded. Local detection is shown only as a reviewer hint; no state is auto-confirmed.';
}

function collectPreferenceObservations() {
  const output = {};
  for (const preference of observationCaptureCandidate.requiredPreferences) {
    const state = document.querySelector(`[data-preference-state="${preference}"]`).value;
    const evidenceReferences = splitLines(document.querySelector(`[data-preference-evidence="${preference}"]`).value);
    output[preference] = {state, evidenceReferences};
  }
  return output;
}

function collectScenarioObservations(record) {
  const output = {};
  for (const scenario of record.scenarioResults) {
    output[scenario.id] = {
      result: document.querySelector(`[data-scenario-result="${scenario.id}"]`).value,
      evidenceReferences: splitLines(document.querySelector(`[data-scenario-evidence="${scenario.id}"]`).value),
      notes: document.querySelector(`[data-scenario-notes="${scenario.id}"]`).value.trim()
    };
  }
  return output;
}

function downloadJson(record) {
  const blob = new Blob([`${JSON.stringify(record, null, 2)}\n`], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `glaze-v1.4-accessibility-observation-${record.target.sourceRevision.slice(0, 12)}.json`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

packetFile.addEventListener('change', async () => {
  exportButton.disabled = true;
  try {
    const file = packetFile.files?.[0];
    if (!file) throw new TypeError('Select a prepared qualification-record.json packet.');
    const parsed = JSON.parse(await file.text());
    captureAdapter.assertEligible(parsed);
    loadedRecord = parsed;
    renderLoadedRecord(parsed);
  } catch (error) {
    loadedRecord = null;
    preferenceBody.replaceChildren();
    scenarioBody.replaceChildren();
    sourceSummary.replaceChildren();
    recordStatus.textContent = `Packet rejected: ${error.message}`;
  }
});

refreshHintsButton.addEventListener('click', () => {
  preferenceHints = captureAdapter.derivePreferenceHints(capabilityAdapter.snapshot());
  if (loadedRecord) renderPreferenceRows(loadedRecord);
  recordStatus.textContent = 'Local preference hints refreshed. The qualification record was not changed.';
});

exportButton.addEventListener('click', () => {
  if (!loadedRecord) return;
  try {
    const captured = captureAdapter.capture(loadedRecord, {
      environmentEvidenceReferences: splitLines(environmentRefs.value),
      assistiveTechnologies: parseAssistiveTechnologies(assistiveTechnologies.value),
      preferenceObservations: collectPreferenceObservations(),
      scenarioObservations: collectScenarioObservations(loadedRecord)
    });
    downloadJson(captured);
    loadedRecord = captured;
    renderLoadedRecord(captured);
    recordStatus.textContent = 'Observation record exported locally. Human review remains pending; no qualification or lifecycle acceptance was granted.';
  } catch (error) {
    recordStatus.textContent = `Export blocked: ${error.message}`;
  }
});
