import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
  resolveGlazeInterface,
  summarizeGlazeInterfaceResolution,
  glazeResolutionDevelopmentContract
} from '../js/glaze-v1.5-resolution.dev.mjs';

const conformance = JSON.parse(fs.readFileSync(new URL('../conformance/v1.5-resolution-development-matrix.json', import.meta.url), 'utf8'));

const providers = [
  {
    id: 'platform-runtime',
    authority: 'platform',
    context: {
      layout: {category: 'compact'},
      input: {primary: 'touch'},
      connectivity: {class: 'offline'},
      'device-posture': {posture: 'folded'}
    },
    capabilities: [
      {id: 'device.cast', domain: 'device', state: 'unsupported'},
      {id: 'connectivity.network', domain: 'connectivity', state: 'offline'}
    ]
  },
  {
    id: 'application-runtime',
    authority: 'application',
    context: {task: {kind: 'composing'}},
    capabilities: [
      {id: 'application.compose', domain: 'application', state: 'available'},
      {id: 'application.local-save', domain: 'application', state: 'available'}
    ]
  },
  {
    id: 'cloud-service',
    authority: 'service',
    capabilities: [
      {id: 'service.cloud-save', domain: 'service', state: 'offline'},
      {id: 'service.search', domain: 'service', state: 'degraded'}
    ]
  },
  {
    id: 'policy-authority',
    authority: 'policy',
    capabilities: [
      {id: 'authorization.admin', domain: 'authorization', state: 'restricted'}
    ]
  },
  {
    id: 'accessibility-authority',
    authority: 'accessibility',
    context: {accessibility: {reducedMotion: true}}
  }
];

const destinations = [
  {id: 'home', label: 'Home'},
  {id: 'cast', label: 'Cast', capabilityId: 'device.cast', visibilityPolicy: 'omit-unsupported', fallbackId: 'home'},
  {id: 'admin', label: 'Administration', capabilityId: 'authorization.admin'}
];

const actions = [
  {id: 'compose', label: 'Compose', primary: true, requiredCapabilities: ['application.compose']},
  {
    id: 'cloud-save',
    label: 'Save to cloud',
    primary: true,
    requiredCapabilities: ['service.cloud-save'],
    fallbackActionId: 'local-save',
    stateMessages: {offline: 'Cloud save is unavailable offline. Local save remains available.'}
  },
  {
    id: 'local-save',
    label: 'Save locally',
    requiredCapabilities: ['application.local-save'],
    relevance: [{domain: 'connectivity', key: 'class', values: ['offline']}]
  },
  {id: 'search', label: 'Search', requiredCapabilities: ['service.search']},
  {id: 'admin', label: 'Administration', requiredCapabilities: ['authorization.admin']}
];

const result = resolveGlazeInterface({
  providers,
  actions,
  destinations,
  currentDestinationId: 'cast',
  intent: {supportsMultiPane: true}
});

assert.equal(result.version, '1.5.0-dev.1');
assert.equal(result.lifecycle, 'development');
assert.equal(result.stableBaseline, '1.4.1');
assert.equal(result.providerSummary.providerCount, 5);
assert.equal(result.providerSummary.authorityOwnershipEnforced, true);
assert.equal(result.providerSummary.providerIdsIncluded, false);
assert.deepEqual(result.conflicts.contextDomains, []);
assert.deepEqual(result.conflicts.capabilityIds, []);

assert.equal(result.composition.paneMode, 'single-pane');
assert.equal(result.composition.controlDensity, 'comfortable');
assert.equal(result.composition.commandSurface, 'direct-controls');
assert.equal(result.composition.motionPreference, 'reduced');
assert.equal(result.composition.taskStateReset, false);
assert.equal(result.composition.pageReloadRequired, false);

assert.deepEqual(result.navigation.visibleDestinationIds, ['home', 'admin']);
assert.equal(result.navigation.acceptedCurrentId, 'home');
assert.equal(result.navigation.currentDestinationChanged, true);
assert.equal(result.navigation.destinations.find(item => item.id === 'admin').state, 'restricted');
assert.equal(result.navigation.destinations.find(item => item.id === 'admin').enabled, false);
assert.equal(result.navigation.automaticNavigationAllowed, false);

assert.deepEqual(result.actions.primaryActionIds, ['compose', 'cloud-save']);
assert.equal(result.actions.primaryActionOrderStable, true);
const cloudAction = result.actions.actions.find(item => item.id === 'cloud-save');
assert.equal(cloudAction.state, 'offline');
assert.equal(cloudAction.enabled, false);
assert.equal(cloudAction.suggestedFallbackActionId, 'local-save');
assert.equal(cloudAction.automaticExecutionAllowed, false);
const localAction = result.actions.actions.find(item => item.id === 'local-save');
assert.equal(localAction.enabled, true);
assert.equal(localAction.contextuallyRelevant, true);
const searchAction = result.actions.actions.find(item => item.id === 'search');
assert.equal(searchAction.state, 'degraded');
assert.equal(searchAction.enabled, true);
assert.equal(searchAction.degraded, true);

const cloudControl = result.controls.find(item => item.id === 'cloud-save');
assert.equal(cloudControl.presentationState, 'offline');
assert.equal(cloudControl.enabled, false);
const adminControl = result.controls.find(item => item.id === 'admin');
assert.equal(adminControl.presentationState, 'restricted');
assert.equal(adminControl.enabled, false);

assert.equal(result.adaptation.optical.mode, 'solid-fallback');
assert.equal(result.adaptation.optical.motionAllowed, false);
assert.equal(result.adaptation.authorizationInferred, false);
assert.equal(result.adaptation.automaticConsequentialExecutionAllowed, false);

assert.equal(result.acceptedPresentation.paneMode, 'single-pane');
assert.equal(result.acceptedPresentation.acceptedDestinationId, 'home');
assert.deepEqual(result.acceptedPresentation.orderedActionIds, result.actions.orderedActionIds);
assert.equal(result.acceptedPresentation.opticalMode, 'solid-fallback');

assert.equal(result.diagnostics.navigation.acceptedCurrentId, 'home');
assert.equal(result.diagnostics.actions.states.find(item => item.id === 'cloud-save').suggestedFallbackActionId, 'local-save');
assert.equal(result.diagnostics.privacy.rawContextIncluded, false);
assert.equal(result.diagnostics.privacy.providerIdentityIncluded, false);
assert.equal(result.diagnostics.authority.operationalAuthorityGranted, false);

assert.equal(result.authority.glazeAuthority, 'presentation-only');
assert.equal(result.authority.authorizationInferred, false);
assert.equal(result.authority.permissionGranted, false);
assert.equal(result.authority.providerPrecedenceInferred, false);
assert.equal(result.authority.operationalAuthorityGranted, false);
assert.equal(result.authority.automaticNavigationAllowed, false);
assert.equal(result.authority.automaticPermissionRequestAllowed, false);
assert.equal(result.authority.automaticConsequentialExecutionAllowed, false);
assert.equal(result.authority.automaticFallbackExecutionAllowed, false);
assert.equal(result.continuity.taskStateReset, false);
assert.equal(result.continuity.pageReloadRequired, false);
assert.equal(result.privacy.telemetryRequired, false);
assert.equal(result.privacy.remoteAnalysisRequired, false);

const encodedResult = JSON.stringify(result.diagnostics);
for (const providerId of ['platform-runtime', 'application-runtime', 'cloud-service', 'policy-authority', 'accessibility-authority']) {
  assert.equal(encodedResult.includes(providerId), false, `Diagnostics leaked provider identity: ${providerId}`);
}

const summary = summarizeGlazeInterfaceResolution(result);
assert.equal(summary.lifecycle, 'development');
assert.equal(summary.navigationChanged, true);
assert.equal(summary.primaryActionOrderStable, true);
assert.equal(summary.operationalAuthorityGranted, false);
assert.equal(summary.providerIdsIncluded, false);
assert.equal(summary.diagnosticRawContextIncluded, false);
assert.equal(summary.telemetryRequired, false);
assert.equal(summary.remoteAnalysisRequired, false);

const conflictResult = resolveGlazeInterface({
  providers: [
    {id: 'service-one', authority: 'service', capabilities: [{id: 'service.search', domain: 'service', state: 'available'}]},
    {id: 'service-two', authority: 'service', capabilities: [{id: 'service.search', domain: 'service', state: 'degraded'}]}
  ],
  actions: [{id: 'search', requiredCapabilities: ['service.search']}]
});
assert.deepEqual(conflictResult.conflicts.capabilityIds, ['service.search']);
assert.equal(conflictResult.capabilities.byId['service.search'], undefined);
const conflictedSearch = conflictResult.actions.actions.find(item => item.id === 'search');
assert.equal(conflictedSearch.state, 'unknown');
assert.equal(conflictedSearch.enabled, false);
assert.ok(conflictedSearch.reasonCodes.includes('capability-unknown'));
assert.equal(conflictResult.authority.providerPrecedenceInferred, false);

assert.equal(glazeResolutionDevelopmentContract.developerFacingUnifiedResolver, true);
assert.equal(glazeResolutionDevelopmentContract.authoritativeProviderSnapshotRequired, true);
assert.equal(glazeResolutionDevelopmentContract.providerConflictsFailClosed, true);
assert.equal(glazeResolutionDevelopmentContract.compositionResolved, true);
assert.equal(glazeResolutionDevelopmentContract.navigationResolved, true);
assert.equal(glazeResolutionDevelopmentContract.actionPrioritizationResolved, true);
assert.equal(glazeResolutionDevelopmentContract.controlPresentationResolved, true);
assert.equal(glazeResolutionDevelopmentContract.opticalPresentationResolved, true);
assert.equal(glazeResolutionDevelopmentContract.privacySafeDiagnosticsResolved, true);
assert.equal(glazeResolutionDevelopmentContract.authorizationInferred, false);
assert.equal(glazeResolutionDevelopmentContract.automaticPermissionRequestAllowed, false);
assert.equal(glazeResolutionDevelopmentContract.automaticConsequentialExecutionAllowed, false);
assert.equal(glazeResolutionDevelopmentContract.automaticFallbackExecutionAllowed, false);

const requiredScenarioIds = [
  'resolution.provider-snapshot-authority',
  'resolution.context-composition',
  'resolution.navigation-capability',
  'resolution.action-capability',
  'resolution.control-state',
  'resolution.optical-accepted-state',
  'resolution.privacy-safe-diagnostics',
  'resolution.conflict-fails-closed',
  'resolution.no-automatic-execution',
  'resolution.offline-local-fallback'
];
const scenarioIds = new Set(conformance.scenarios.map(item => item.id));
for (const id of requiredScenarioIds) assert.ok(scenarioIds.has(id), `Missing resolution scenario: ${id}`);
assert.equal(conformance.scenarios.length, 10);
assert.ok(conformance.scenarios.every(item => item.machineCovered === true));
assert.equal(conformance.promotionBoundary.machineCoverageAloneQualifiesReleaseCandidate, false);
assert.equal(conformance.promotionBoundary.machineCoverageAloneQualifiesStable, false);
assert.equal(conformance.promotionBoundary.privacyReviewRequired, true);

console.log('GLAZE UI 1.5.0-dev.1 unified context/capability resolution verification: PASS');
console.log('Provider snapshot + application intent -> accepted presentation: verified');
console.log('Composition/navigation/actions/controls/optics/diagnostics: unified');
console.log('Provider conflicts: fail closed without inferred precedence');
console.log('Automatic navigation/permission/consequential/fallback execution: disabled');
console.log('Stable baseline preserved: 1.4.1');
