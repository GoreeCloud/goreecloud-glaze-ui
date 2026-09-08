import assert from 'node:assert/strict';
import test from 'node:test';

import {
  applySystemShellPresentation,
  controlCenterCandidate,
  moveControlCenterModule,
  normalizeControlCenterModules,
  resetControlCenterModules,
  resizeControlCenterModule,
  resolveControlCenterPresentation,
  resolveSystemShell,
  systemShellCandidate
} from '../js/glaze-v1.3-system-shell.candidate.mjs';

const modules = [
  {id: 'network', type: 'connectivity-module', size: 'wide'},
  {id: 'brightness', type: 'slider', size: 'wide'},
  {id: 'media', type: 'media-module', size: 'expanded'}
];

test('system shell consumes adaptive navigation presentation', () => {
  const compact = resolveSystemShell({environment: 'compact', destinationCount: 4});
  const expanded = resolveSystemShell({environment: 'expanded', destinationCount: 4});
  assert.equal(compact.navigation.presentation, 'navigation-capsule');
  assert.equal(expanded.navigation.presentation, 'persistent-sidebar');
  assert.equal(compact.predictionMayReorderPrimaryNavigation, false);
});

test('large text can promote search into a dedicated view', () => {
  const result = resolveSystemShell({environment: 'workspace', largeText: true});
  assert.equal(result.searchPresentation, 'dedicated-view');
  assert.equal(result.searchScopeVisible, true);
});

test('critical system surfaces never depend on backdrop or context accent authority', () => {
  const result = resolveSystemShell({environment: 'expanded'});
  assert.equal(result.criticalSystemBackdropDependent, false);
  assert.equal(result.criticalStateProducerAuthoritative, true);
  assert.equal(result.criticalStateMayUseContextAccentAsAuthority, false);
});

test('reduced transparency and Forced Colors use solid or platform shell fallbacks', () => {
  const reduced = resolveSystemShell({environment: 'medium', reducedTransparency: true});
  const forced = resolveSystemShell({environment: 'medium', forcedColors: true});
  assert.equal(reduced.workspaceMaterial, 'solid-neutral');
  assert.equal(reduced.transientShellMaterial, 'solid-neutral');
  assert.equal(forced.criticalSystemMaterial, 'platform-forced-colors');
});

test('far-view and touch assistance retain 56px minimum targets', () => {
  assert.equal(resolveSystemShell({environment: 'farView'}).minimumTargetPx, 56);
  assert.equal(resolveSystemShell({environment: 'compact', touchAssistance: true}).minimumTargetPx, 56);
});

test('system shell does not use raw viewport width as authority', () => {
  const result = resolveSystemShell({environment: 'workspace'});
  assert.equal(result.rawViewportWidthAuthority, false);
  assert.equal(result.stableSpatialMemoryRequired, true);
  assert.equal(result.currentDestinationRequiresStructuralCue, true);
  assert.equal(result.currentDestinationMayDependOnColorAlone, false);
});

test('control center presentation adapts by semantic environment', () => {
  assert.equal(resolveControlCenterPresentation({environment: 'compact'}).presentation, 'in-flow-sheet-or-dedicated-panel');
  assert.equal(resolveControlCenterPresentation({environment: 'workspace'}).presentation, 'side-panel-or-overlay');
  assert.equal(resolveControlCenterPresentation({environment: 'far-view'}).presentation, 'focused-panel');
  assert.equal(resolveControlCenterPresentation({environment: 'wearable'}).presentation, 'shallow-system-controls');
});

test('control center parent material degrades before semantics or target size', () => {
  const result = resolveControlCenterPresentation({environment: 'expanded', reducedTransparency: true, touchAssistance: true});
  assert.equal(result.parentMaterial, 'solid-raised');
  assert.equal(result.minimumTargetPx, 56);
  assert.equal(result.nestedBackdropBlurAllowed, false);
});

test('control center module normalization requires stable unique ids and governed types', () => {
  assert.equal(normalizeControlCenterModules(modules).length, 3);
  assert.throws(() => normalizeControlCenterModules([{type: 'slider'}]), /stable id/);
  assert.throws(() => normalizeControlCenterModules([{id: 'x', type: 'unknown'}]), /ungoverned type/);
  assert.throws(() => normalizeControlCenterModules([{id: 'x', type: 'slider'}, {id: 'x', type: 'slider'}]), /must be unique/);
});

test('accessible reorder moves modules without changing semantic identity', () => {
  const moved = moveControlCenterModule(modules, 'media', 'start');
  assert.deepEqual(moved.map(module => module.id), ['media', 'network', 'brightness']);
  assert.equal(moved[0].type, 'media-module');
  const previous = moveControlCenterModule(modules, 'brightness', 'previous');
  assert.deepEqual(previous.map(module => module.id), ['brightness', 'network', 'media']);
});

test('resize preserves module id and semantic type', () => {
  const resized = resizeControlCenterModule(modules, 'network', 'compact');
  assert.equal(resized[0].id, 'network');
  assert.equal(resized[0].type, 'connectivity-module');
  assert.equal(resized[0].size, 'compact');
});

test('reset requires an exact permutation of current modules', () => {
  const reset = resetControlCenterModules(modules, ['brightness', 'media', 'network']);
  assert.deepEqual(reset.map(module => module.id), ['brightness', 'media', 'network']);
  assert.throws(() => resetControlCenterModules(modules, ['network', 'brightness']), /every current module id exactly once/);
});

test('control center runtime establishes no persistence or sync claim', () => {
  const result = resolveControlCenterPresentation({environment: 'expanded'});
  assert.equal(result.persistentStorageEstablished, false);
  assert.equal(result.crossDeviceSyncEstablished, false);
  assert.equal(result.keyboardEditingRequired, true);
  assert.equal(result.semanticAnnouncementsRequired, true);
});

test('applySystemShellPresentation writes semantic shell variables', () => {
  const properties = new Map();
  const target = {
    dataset: {},
    style: {setProperty(name, value) { properties.set(name, value); }}
  };
  const result = applySystemShellPresentation(target, {environment: 'compact', destinationCount: 4});
  assert.equal(target.dataset.glazeShellV13, 'compact');
  assert.equal(target.dataset.glazeShellNavigation, 'navigation-capsule');
  assert.equal(properties.get('--glz13-shell-min-target'), '48px');
  assert.equal(result.searchScopeVisible, true);
});

test('candidate metadata preserves lifecycle and acceptance boundaries', () => {
  assert.equal(systemShellCandidate.releaseLifecycle, 'proposed');
  assert.equal(systemShellCandidate.consumerEligible, false);
  assert.equal(systemShellCandidate.adaptiveNavigationOwnsPrimaryNavigationPresentation, true);
  assert.equal(systemShellCandidate.criticalDecisionsBackdropDependent, false);
  assert.equal(systemShellCandidate.fullNotificationCenterRuntimeEstablished, false);
  assert.equal(systemShellCandidate.nativeShellParityEstablished, false);
  assert.equal(controlCenterCandidate.dragIsSoleReorderMechanism, false);
  assert.equal(controlCenterCandidate.persistentStorageEstablished, false);
  assert.equal(controlCenterCandidate.crossDeviceSyncEstablished, false);
  assert.equal(controlCenterCandidate.physicalDeviceEditingAcceptanceEstablished, false);
});
