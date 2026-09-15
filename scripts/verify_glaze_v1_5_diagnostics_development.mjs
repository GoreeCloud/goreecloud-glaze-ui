import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
  normalizeGlazeContext,
  resolveGlazeAdaptation,
  mapV141OpticalCapabilities
} from '../js/glaze-v1.5-context-capability.dev.mjs';
import {
  resolveGlazeComposition,
  resolveGlazeNavigation
} from '../js/glaze-v1.5-composition.dev.mjs';
import {resolveGlazeActionPrioritization} from '../js/glaze-v1.5-actions.dev.mjs';
import {
  createGlazeDiagnosticReport,
  summarizeGlazeDiagnosticReport,
  glazeDiagnosticsDevelopmentContract
} from '../js/glaze-v1.5-diagnostics.dev.mjs';

const conformance = JSON.parse(fs.readFileSync(new URL('../conformance/v1.5-diagnostics-development-matrix.json', import.meta.url), 'utf8'));

const capabilities = [
  {id:'device.cast', domain:'device', state:'unsupported', provenance:{provider:'private-device-adapter', authority:'platform', observedAt:'2026-09-15T12:00:00Z'}},
  {id:'service.cloud-save', domain:'service', state:'offline', provenance:{provider:'private-sync-service', authority:'service', observedAt:'2026-09-15T12:00:00Z'}},
  {id:'application.local-save', domain:'application', state:'available', provenance:{provider:'private-app-runtime', authority:'application'}},
  {id:'service.search', domain:'service', state:'degraded', provenance:{provider:'private-search-service', authority:'service'}}
];

const normalizedContext = normalizeGlazeContext({
  layout:{category:'expanded'},
  task:{kind:'searching', topic:'private-case-omega'},
  accessibility:{largeText:true},
  connectivity:{class:'offline'}
});

const composition = resolveGlazeComposition({
  context:{layout:{category:'expanded'}, accessibility:{largeText:true}},
  intent:{supportsMultiPane:true}
});
assert.ok(composition.reasonCodes.includes('large-text-spacing-authority'));

const navigation = resolveGlazeNavigation({
  currentId:'cast',
  capabilities,
  destinations:[
    {id:'home', label:'Home'},
    {id:'cast', label:'Cast', capabilityId:'device.cast', visibilityPolicy:'omit-unsupported', fallbackId:'home'},
    {id:'search', label:'Search', capabilityId:'service.search'}
  ]
});
assert.equal(navigation.acceptedCurrentId, 'home');
assert.equal(navigation.currentDestinationChanged, true);

const actions = resolveGlazeActionPrioritization({
  context:{task:{kind:'searching'}, connectivity:{class:'offline'}},
  capabilities,
  actions:[
    {
      id:'cloud-save',
      label:'Save to cloud',
      primary:true,
      requiredCapabilities:['service.cloud-save'],
      fallbackActionId:'local-save',
      stateMessages:{offline:'Private project private-case-omega cannot sync right now.'}
    },
    {id:'local-save', label:'Save locally', primary:true, requiredCapabilities:['application.local-save']},
    {id:'search', label:'Search', requiredCapabilities:['service.search'], relevance:[{domain:'task', key:'kind', values:['searching']}]}
  ]
});
assert.equal(actions.actions.find(item => item.id === 'cloud-save').suggestedFallbackActionId, 'local-save');

const adaptation = resolveGlazeAdaptation({
  accessibility:{reducedTransparency:true, reducedMotion:true},
  capabilities:mapV141OpticalCapabilities({capabilities:{backdropBlur:true, motion:true}}),
  actions:[]
});
assert.equal(adaptation.optical.mode, 'solid-reduced-transparency');

const report = createGlazeDiagnosticReport({
  context:normalizedContext,
  composition,
  navigation,
  actions,
  adaptation,
  capabilities
});

assert.equal(report.version, '1.5.0-dev.1');
assert.equal(report.lifecycle, 'development');
assert.deepEqual(report.contextDomains, ['layout', 'task', 'accessibility', 'connectivity']);
assert.ok(report.composition.reasonCodes.includes('large-text-spacing-authority'));
assert.equal(report.navigation.acceptedCurrentId, 'home');
assert.equal(report.navigation.currentDestinationChanged, true);
assert.deepEqual(report.navigation.omittedDestinations.map(item => item.id), ['cast']);
const cloudDiagnostic = report.actions.states.find(item => item.id === 'cloud-save');
assert.equal(cloudDiagnostic.state, 'offline');
assert.equal(cloudDiagnostic.explanationPresent, true);
assert.equal(cloudDiagnostic.explanationTextIncluded, false);
assert.equal(cloudDiagnostic.suggestedFallbackActionId, 'local-save');
assert.equal(report.optical.mode, 'solid-reduced-transparency');
assert.ok(report.optical.reasonCodes.includes('reduced-transparency-authority'));
assert.equal(report.capabilities.find(item => item.id === 'service.search').authority, 'service');
assert.ok(report.capabilities.every(item => item.providerIdentityIncluded === false));
assert.ok(report.capabilities.every(item => item.observedAtIncluded === false));
assert.equal(report.authority.operationalAuthorityGranted, false);
assert.equal(report.privacy.rawContextIncluded, false);
assert.equal(report.privacy.providerIdentityIncluded, false);
assert.equal(report.privacy.explanationTextIncluded, false);
assert.equal(report.privacy.telemetryRequired, false);
assert.equal(report.privacy.remoteAnalysisRequired, false);

const encoded = JSON.stringify(report);
for (const forbidden of [
  'private-case-omega',
  'Private project',
  'private-device-adapter',
  'private-sync-service',
  'private-app-runtime',
  'private-search-service',
  '2026-09-15T12:00:00Z'
]) assert.equal(encoded.includes(forbidden), false, `Diagnostic leaked forbidden detail: ${forbidden}`);

const summary = summarizeGlazeDiagnosticReport(report);
assert.equal(summary.navigationChanged, true);
assert.equal(summary.omittedNavigationCount, 1);
assert.equal(summary.actionStateCount, 3);
assert.equal(summary.capabilityStateCount, 4);
assert.equal(summary.operationalAuthorityGranted, false);
assert.equal(summary.rawContextIncluded, false);
assert.equal(summary.providerIdentityIncluded, false);
assert.equal(summary.remoteAnalysisRequired, false);

assert.equal(glazeDiagnosticsDevelopmentContract.explainsCompositionDecisions, true);
assert.equal(glazeDiagnosticsDevelopmentContract.explainsNavigationContinuity, true);
assert.equal(glazeDiagnosticsDevelopmentContract.explainsActionStates, true);
assert.equal(glazeDiagnosticsDevelopmentContract.explainsOpticalDowngrades, true);
assert.equal(glazeDiagnosticsDevelopmentContract.exposesCapabilityAuthorityClass, true);
assert.equal(glazeDiagnosticsDevelopmentContract.providerIdentityIncludedByDefault, false);
assert.equal(glazeDiagnosticsDevelopmentContract.rawContextIncluded, false);
assert.equal(glazeDiagnosticsDevelopmentContract.operationalAuthorityGranted, false);

const requiredScenarioIds = [
  'diagnostics.composition-semantic-reasons',
  'diagnostics.navigation-continuity',
  'diagnostics.action-state-and-fallback',
  'diagnostics.optical-downgrade',
  'diagnostics.capability-authority-class',
  'diagnostics.raw-context-redacted',
  'diagnostics.provider-identity-redacted'
];
const scenarioIds = new Set(conformance.scenarios.map(item => item.id));
for (const id of requiredScenarioIds) assert.ok(scenarioIds.has(id), `Missing diagnostics scenario: ${id}`);
assert.equal(conformance.scenarios.length, 7);
assert.ok(conformance.scenarios.every(item => item.machineCovered === true));
assert.equal(conformance.promotionBoundary.machineCoverageAloneQualifiesReleaseCandidate, false);
assert.equal(conformance.promotionBoundary.machineCoverageAloneQualifiesStable, false);
assert.equal(conformance.promotionBoundary.privacyReviewRequired, true);

console.log('GLAZE UI 1.5.0-dev.1 explainable diagnostics verification: PASS');
console.log('Composition/navigation/action/optical explanations: semantic-only');
console.log('Capability provenance: authority class retained, provider identity redacted');
console.log('Raw context/application explanation text/observedAt: redacted');
console.log('Operational authority granted by diagnostics: false');
