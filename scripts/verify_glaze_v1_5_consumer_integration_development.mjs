import assert from 'node:assert/strict';
import fs from 'node:fs';
import {resolveGlazeInterface} from '../js/glaze-v1.5-resolution.dev.mjs';
import {glazeProviderDevelopmentContract} from '../js/glaze-v1.5-provider-registry.dev.mjs';

const profilesDocument = JSON.parse(fs.readFileSync(new URL('../contracts/v1.5/representative-consumers.dev.json', import.meta.url), 'utf8'));
const matrix = JSON.parse(fs.readFileSync(new URL('../conformance/v1.5-consumer-integration-development-matrix.json', import.meta.url), 'utf8'));

assert.equal(profilesDocument.version, '1.5.0-dev.1');
assert.equal(profilesDocument.lifecycle, 'development');
assert.equal(profilesDocument.stableConsumerTarget, '1.4.1');
assert.equal(profilesDocument.developmentOnly, true);
assert.equal(profilesDocument.consumerAcceptanceEstablished, false);
assert.equal(profilesDocument.productionAcceptanceEstablished, false);
assert.equal(profilesDocument.repositoryLocalAcceptanceRequired, true);
assert.equal(glazeProviderDevelopmentContract.privacyAuthorityMayOwnAuthorizationTruth, true);
assert.equal(matrix.consumerAcceptanceEstablished, false);
assert.equal(matrix.repositoryLocalAcceptanceRequired, true);
assert.equal(matrix.promotionBoundary.representativeProfilesChangeStableConsumerTarget, false);
assert.equal(matrix.promotionBoundary.sharedMachineCoverageEstablishesConsumerConformance, false);
assert.equal(matrix.promotionBoundary.sharedMachineCoverageQualifiesReleaseCandidate, false);
assert.equal(matrix.promotionBoundary.sharedMachineCoverageQualifiesStable, false);

const expectedRepositories = new Map([
  ['GoreeCloud Launcher', 'GoreeCloud/goreecloud-launcher'],
  ['GoreeCloud Manager', 'GoreeCloud/goreecloud-manager'],
  ['GoreeCloud Reader', 'GoreeCloud/goreecloud-reader'],
  ['GoreeCloud Security Center', 'GoreeCloud/goreecloud-wardveil'],
  ['GoreeCloud Privacy Center', 'GoreeCloud/goreecloud-privacy-shield']
]);
assert.equal(profilesDocument.profiles.length, expectedRepositories.size);

const resolved = new Map();
for (const profile of profilesDocument.profiles) {
  assert.equal(expectedRepositories.get(profile.name), profile.repository, `Unexpected repository mapping for ${profile.name}`);
  const result = resolveGlazeInterface(profile.input);
  resolved.set(profile.id, result);
  assert.equal(result.lifecycle, 'development');
  assert.equal(result.stableBaseline, '1.4.1');
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
  assert.equal(result.privacy.localFirst, true);
  assert.equal(result.privacy.telemetryRequired, false);
  assert.equal(result.privacy.remoteAnalysisRequired, false);
  assert.equal(result.diagnostics.authority.operationalAuthorityGranted, false);
  assert.equal(result.diagnostics.authority.securityStateManufactured, false);
  assert.equal(result.diagnostics.authority.privacyStateManufactured, false);
  assert.equal(result.diagnostics.privacy.rawContextIncluded, false);
  assert.equal(result.diagnostics.privacy.providerIdentityIncluded, false);
  assert.equal(result.diagnostics.privacy.telemetryRequired, false);
}

const launcher = resolved.get('goreecloud-launcher-handheld');
assert.equal(launcher.composition.paneMode, 'single-pane');
assert.equal(launcher.composition.controlDensity, 'comfortable');
assert.equal(launcher.composition.commandSurface, 'direct-controls');
assert.equal(launcher.navigation.acceptedCurrentId, 'home');
assert.equal(launcher.navigation.currentDestinationChanged, false);
assert.equal(launcher.actions.actions.find(action => action.id === 'launch-app').enabled, true);
assert.equal(launcher.actions.actions.find(action => action.id === 'search-goreecloud').enabled, true);
assert.equal(launcher.capabilities.byId['service.index-search'].provenance.authority, 'service');
assert.equal(launcher.diagnostics.capabilities.find(item => item.id === 'service.index-search').authority, 'service');
assert.equal(JSON.stringify(launcher.diagnostics).includes('goreecloud-index'), false);

const manager = resolved.get('goreecloud-manager-desktop');
assert.equal(manager.composition.paneMode, 'multi-pane');
assert.equal(manager.composition.controlDensity, 'dense');
assert.equal(manager.composition.materialPreference, 'high-clarity');
assert.equal(manager.composition.labelMode, 'explicit');
const managerDestination = manager.navigation.destinations.find(item => item.id === 'administration');
assert.equal(managerDestination.visible, true);
assert.equal(managerDestination.enabled, false);
assert.equal(managerDestination.state, 'restricted');
assert.equal(manager.navigation.acceptedCurrentId, 'administration');
assert.equal(manager.navigation.currentDestinationChanged, false);
const managerAdmin = manager.actions.actions.find(item => item.id === 'apply-administrative-change');
assert.equal(managerAdmin.enabled, false);
assert.equal(managerAdmin.state, 'restricted');
assert.equal(managerAdmin.consequential, true);
assert.equal(managerAdmin.automaticExecutionAllowed, false);

const reader = resolved.get('goreecloud-reader-offline');
assert.equal(reader.composition.paneMode, 'multi-pane');
assert.equal(reader.composition.materialPreference, 'quiet');
assert.equal(reader.composition.motionPreference, 'reduced');
assert.equal(reader.composition.connectivityPresentation, 'offline');
const readerSyncDestination = reader.navigation.destinations.find(item => item.id === 'sync');
assert.equal(readerSyncDestination.visible, true);
assert.equal(readerSyncDestination.enabled, false);
assert.equal(readerSyncDestination.state, 'offline');
assert.equal(reader.navigation.acceptedCurrentId, 'sync');
assert.equal(reader.navigation.currentDestinationChanged, false);
const continueReading = reader.actions.actions.find(item => item.id === 'continue-reading');
const syncLibrary = reader.actions.actions.find(item => item.id === 'sync-library');
assert.equal(continueReading.enabled, true);
assert.equal(continueReading.contextuallyRelevant, true);
assert.equal(syncLibrary.enabled, false);
assert.equal(syncLibrary.state, 'offline');
assert.equal(syncLibrary.suggestedFallbackActionId, 'continue-reading');
assert.equal(syncLibrary.automaticExecutionAllowed, false);
assert.equal(reader.actions.fallbackExecutionAutomatic, false);

const wardveil = resolved.get('wardveil-security-center');
assert.equal(wardveil.capabilities.byId['authorization.quarantine'].provenance.authority, 'security');
const quarantine = wardveil.actions.actions.find(item => item.id === 'quarantine-item');
assert.equal(quarantine.enabled, false);
assert.equal(quarantine.state, 'restricted');
assert.equal(quarantine.consequential, true);
assert.equal(quarantine.destructive, true);
assert.equal(quarantine.automaticExecutionAllowed, false);
const quarantineDiagnostic = wardveil.diagnostics.capabilities.find(item => item.id === 'authorization.quarantine');
assert.equal(quarantineDiagnostic.authority, 'security');
assert.equal(quarantineDiagnostic.providerIdentityIncluded, false);
assert.equal(JSON.stringify(wardveil.diagnostics).includes('wardveil-security'), false);

const privacy = resolved.get('goreecloud-privacy-center');
assert.equal(privacy.capabilities.byId['authorization.data-use'].provenance.authority, 'privacy');
const dataUseDestination = privacy.navigation.destinations.find(item => item.id === 'data-use');
assert.equal(dataUseDestination.visible, true);
assert.equal(dataUseDestination.enabled, false);
assert.equal(dataUseDestination.state, 'permission-required');
assert.equal(privacy.navigation.acceptedCurrentId, 'data-use');
const authorizeDataUse = privacy.actions.actions.find(item => item.id === 'authorize-data-use');
assert.equal(authorizeDataUse.enabled, false);
assert.equal(authorizeDataUse.state, 'permission-required');
assert.equal(authorizeDataUse.recoveryAction.kind, 'request-permission');
assert.equal(authorizeDataUse.recoveryAction.userInitiated, true);
assert.equal(authorizeDataUse.recoveryAction.automaticExecutionAllowed, false);
assert.equal(privacy.actions.permissionRequestedAutomatically, false);
const privacyDiagnostic = privacy.diagnostics.capabilities.find(item => item.id === 'authorization.data-use');
assert.equal(privacyDiagnostic.authority, 'privacy');
assert.equal(privacyDiagnostic.providerIdentityIncluded, false);
assert.equal(JSON.stringify(privacy.diagnostics).includes('privacy-shield'), false);

const requiredScenarioIds = [
  'consumer.launcher.compact-touch-composition',
  'consumer.launcher.local-core-offline',
  'consumer.launcher.index-authority-preserved',
  'consumer.manager.desktop-critical-composition',
  'consumer.manager.restricted-admin-visible',
  'consumer.manager.no-automatic-admin-execution',
  'consumer.reader.reading-composition',
  'consumer.reader.offline-local-fallback',
  'consumer.reader.navigation-continuity',
  'consumer.wardveil.security-authority-preserved',
  'consumer.wardveil.restricted-quarantine-no-auto-execution',
  'consumer.privacy-shield.authorization-authority-preserved',
  'consumer.privacy-shield.permission-recovery-user-initiated',
  'consumer.integration.shared-evidence-not-consumer-acceptance'
];
const scenarioIds = new Set(matrix.scenarios.map(scenario => scenario.id));
for (const scenarioId of requiredScenarioIds) {
  assert.ok(scenarioIds.has(scenarioId), `Missing representative consumer scenario: ${scenarioId}`);
}
assert.equal(matrix.scenarios.length, 14);

console.log('GLAZE UI 1.5.0-dev.1 representative consumer integration verification: PASS');
console.log('Representative consumers: Launcher, Manager, Reader, Security Center, Privacy Center');
console.log('Representative consumer scenarios: 14');
console.log('Stable consumer target remains: 1.4.1');
console.log('Repository-local consumer acceptance established: false');
