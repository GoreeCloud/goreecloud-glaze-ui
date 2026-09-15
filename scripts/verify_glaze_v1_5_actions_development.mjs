import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
  resolveGlazeActionPrioritization,
  summarizeGlazeActionPrioritization,
  glazeActionDevelopmentContract
} from '../js/glaze-v1.5-actions.dev.mjs';

const conformance = JSON.parse(fs.readFileSync(new URL('../conformance/v1.5-action-development-matrix.json', import.meta.url), 'utf8'));

const capabilities = [
  {id: 'application.compose', domain: 'application', state: 'available', provenance: {provider: 'app-runtime', authority: 'application'}},
  {id: 'service.cloud-save', domain: 'service', state: 'offline', provenance: {provider: 'sync-service', authority: 'service'}},
  {id: 'application.local-save', domain: 'application', state: 'available', provenance: {provider: 'app-runtime', authority: 'application'}},
  {id: 'authorization.camera', domain: 'authorization', state: 'permission-required', provenance: {provider: 'platform-permissions', authority: 'platform'}},
  {id: 'authorization.admin', domain: 'authorization', state: 'restricted', provenance: {provider: 'policy-engine', authority: 'policy'}},
  {id: 'device.cast', domain: 'device', state: 'unsupported', provenance: {provider: 'device-adapter', authority: 'platform'}},
  {id: 'service.search', domain: 'service', state: 'degraded', provenance: {provider: 'search-service', authority: 'service'}}
];

const actions = [
  {
    id: 'compose',
    label: 'Compose',
    primary: true,
    requiredCapabilities: ['application.compose'],
    relevance: [{domain: 'task', key: 'kind', values: ['composing']}]
  },
  {
    id: 'cloud-save',
    label: 'Save to cloud',
    primary: true,
    requiredCapabilities: ['service.cloud-save'],
    fallbackActionId: 'local-save',
    stateMessages: {offline: 'Cloud save is unavailable offline. Local save remains available.'}
  },
  {
    id: 'camera',
    label: 'Add photo',
    requiredCapabilities: ['authorization.camera'],
    recoveryActions: {
      'permission-required': {id: 'camera.permission', label: 'Review camera permission', kind: 'request-permission'}
    }
  },
  {
    id: 'admin',
    label: 'Administration',
    requiredCapabilities: ['authorization.admin']
  },
  {
    id: 'cast',
    label: 'Cast',
    requiredCapabilities: ['device.cast'],
    visibilityPolicy: 'omit-unsupported'
  },
  {
    id: 'local-save',
    label: 'Save locally',
    requiredCapabilities: ['application.local-save'],
    relevance: [{domain: 'connectivity', key: 'class', values: ['offline', 'constrained']}]
  },
  {
    id: 'search',
    label: 'Search',
    requiredCapabilities: ['service.search'],
    relevance: [{domain: 'task', key: 'kind', values: ['searching']}]
  },
  {id: 'help', label: 'Help'}
];

const result = resolveGlazeActionPrioritization({
  context: {task: {kind: 'searching'}, connectivity: {class: 'offline'}},
  capabilities,
  actions
});

assert.deepEqual(result.primaryActionIds, ['compose', 'cloud-save']);
assert.equal(result.primaryActionOrderStable, true);
assert.deepEqual(result.orderedActionIds.slice(0, 2), ['compose', 'cloud-save']);
assert.equal(result.actions.find(action => action.id === 'search').contextuallyRelevant, true);
assert.equal(result.actions.find(action => action.id === 'local-save').contextuallyRelevant, true);
assert.ok(result.orderedActionIds.indexOf('search') < result.orderedActionIds.indexOf('camera'));
assert.ok(result.orderedActionIds.indexOf('local-save') < result.orderedActionIds.indexOf('camera'));

const cloud = result.actions.find(action => action.id === 'cloud-save');
assert.equal(cloud.state, 'offline');
assert.equal(cloud.enabled, false);
assert.equal(cloud.suggestedFallbackActionId, 'local-save');
assert.match(cloud.explanation, /Local save remains available/);
assert.equal(cloud.automaticExecutionAllowed, false);

const camera = result.actions.find(action => action.id === 'camera');
assert.equal(camera.state, 'permission-required');
assert.equal(camera.recoveryAction.kind, 'request-permission');
assert.equal(camera.recoveryAction.userInitiated, true);
assert.equal(camera.recoveryAction.automaticExecutionAllowed, false);
assert.match(camera.explanation, /Permission is required/);

const admin = result.actions.find(action => action.id === 'admin');
assert.equal(admin.visible, true);
assert.equal(admin.state, 'restricted');
assert.equal(admin.enabled, false);
assert.match(admin.explanation, /restricted/i);

assert.equal(result.actions.some(action => action.id === 'cast'), false);

const search = result.actions.find(action => action.id === 'search');
assert.equal(search.state, 'degraded');
assert.equal(search.enabled, true);
assert.equal(search.degraded, true);
assert.match(search.explanation, /degraded/i);

assert.equal(result.automaticExecutionAllowed, false);
assert.equal(result.permissionRequestedAutomatically, false);
assert.equal(result.fallbackExecutionAutomatic, false);
assert.equal(result.explanationProviderIdentityIncluded, false);
assert.equal(result.rawContextIncludedInExplanation, false);

const summary = summarizeGlazeActionPrioritization(result);
assert.equal(summary.providerIdentityIncluded, false);
assert.equal(summary.rawContextIncluded, false);
assert.equal(JSON.stringify(summary).includes('sync-service'), false);
assert.equal(JSON.stringify(summary).includes('search-service'), false);
assert.equal(JSON.stringify(summary).includes('offline. Local'), false);

assert.equal(glazeActionDevelopmentContract.stablePrimaryActionOrdering, true);
assert.equal(glazeActionDevelopmentContract.contextualReorderingLimitedToNonPrimaryActions, true);
assert.equal(glazeActionDevelopmentContract.fallbackExecutionAutomatic, false);
assert.equal(glazeActionDevelopmentContract.automaticPermissionRequestAllowed, false);
assert.equal(glazeActionDevelopmentContract.automaticConsequentialExecutionAllowed, false);

const requiredScenarioIds = [
  'action.primary-order-stable',
  'action.contextual-prioritization',
  'action.permission-explanation',
  'action.restricted-visible',
  'action.unsupported-semantic-omit',
  'action.offline-fallback-local',
  'action.degraded-explanation',
  'action.no-automatic-execution'
];
const scenarioIds = new Set(conformance.scenarios.map(scenario => scenario.id));
for (const scenarioId of requiredScenarioIds) {
  assert.ok(scenarioIds.has(scenarioId), `Missing action conformance scenario: ${scenarioId}`);
}
assert.equal(conformance.scenarios.length, 8);

console.log('GLAZE UI 1.5.0-dev.1 adaptive action development verification: PASS');
console.log('Primary action ordering: stable');
console.log('Contextual prioritization boundary: non-primary actions only');
console.log('Unavailable/degraded explanation: verified');
console.log('Explicit local fallback suggestion: verified');
console.log('Automatic permission/consequential execution: disabled');
