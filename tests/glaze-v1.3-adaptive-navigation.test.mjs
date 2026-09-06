import assert from 'node:assert/strict';
import test from 'node:test';

import {
  adaptiveNavigationCandidate,
  applyNavigationPresentation,
  resolveNavigationPresentation,
  transformNavigationModel
} from '../js/glaze-v1.3-adaptive-navigation.candidate.mjs';

test('unknown environment falls back to reachable compact navigation', () => {
  const result = resolveNavigationPresentation({environment: 'unknown'});
  assert.equal(result.environment, 'compact');
  assert.equal(result.presentation, 'navigation-capsule');
  assert.equal(result.lowerReachabilityPreferred, true);
  assert.equal(result.rawViewportWidthAuthority, false);
});

test('environment transforms presentation without changing navigation semantics', () => {
  assert.equal(resolveNavigationPresentation({environment: 'compact'}).presentation, 'navigation-capsule');
  assert.equal(resolveNavigationPresentation({environment: 'medium'}).presentation, 'navigation-rail');
  assert.equal(resolveNavigationPresentation({environment: 'expanded'}).presentation, 'persistent-sidebar');
  assert.equal(resolveNavigationPresentation({environment: 'workspace'}).presentation, 'persistent-sidebar-plus-toolbar');
  assert.equal(resolveNavigationPresentation({environment: 'far-view'}).presentation, 'directional-focus-navigation');
  assert.equal(resolveNavigationPresentation({environment: 'wearable'}).presentation, 'shallow-list');
});

test('medium and expanded presentations respect declared sidebar capability', () => {
  assert.equal(
    resolveNavigationPresentation({environment: 'medium', prefersSidebar: true, supportsPersistentSidebar: true}).presentation,
    'adaptive-sidebar'
  );
  assert.equal(
    resolveNavigationPresentation({environment: 'expanded', supportsPersistentSidebar: false}).presentation,
    'navigation-rail'
  );
});

test('compact navigation is forced in-flow when accessibility or occlusion requires it', () => {
  for (const option of [
    {largeText: true},
    {reflow: true},
    {touchAssistance: true},
    {safeAreaObstructed: true},
    {keyboardOccluded: true},
    {visibleContentOccluded: true}
  ]) {
    const result = resolveNavigationPresentation({environment: 'compact', ...option});
    assert.equal(result.presentation, 'navigation-capsule-in-flow');
    assert.equal(result.detached, false);
    assert.equal(result.accessibilityForcedInFlow, true);
  }
});

test('target floors never shrink to preserve a detached capsule', () => {
  assert.equal(resolveNavigationPresentation({environment: 'compact'}).minimumTargetPx, 48);
  assert.equal(resolveNavigationPresentation({environment: 'compact', touchAssistance: true}).minimumTargetPx, 56);
  assert.equal(resolveNavigationPresentation({environment: 'compact', platformMinimumTargetPx: 60}).minimumTargetPx, 60);
});

test('far-view navigation requires directional focus and 56px minimum targets', () => {
  const result = resolveNavigationPresentation({environment: 'farView', inputModality: 'directional'});
  assert.equal(result.presentation, 'directional-focus-navigation');
  assert.equal(result.requiresDirectionalFocus, true);
  assert.equal(result.focusBeforeActivation, true);
  assert.equal(result.minimumTargetPx, 56);
});

test('wearable can use platform rotary presentation when rotary input is declared', () => {
  const result = resolveNavigationPresentation({environment: 'wearable', inputModality: 'rotary'});
  assert.equal(result.presentation, 'platform-rotary-or-swipe');
  assert.equal(result.environment, 'wearable');
});

test('compact model preserves destination order and moves overflow behind More without reordering', () => {
  const destinations = ['home', 'search', 'library', 'activity', 'settings', 'help'].map(id => ({id, label: id}));
  const result = transformNavigationModel(destinations, 'library', {environment: 'compact'});
  assert.deepEqual(result.destinations.map(item => item.id), ['home', 'search', 'library', 'activity', 'settings', 'help']);
  assert.deepEqual(result.primaryDestinations.map(item => item.id), ['home', 'search', 'library', 'activity', 'settings']);
  assert.deepEqual(result.overflowDestinations.map(item => item.id), ['help']);
  assert.equal(result.presentation.compactOverflowPresentation, 'more-destination');
  assert.equal(result.currentDestinationId, 'library');
  assert.equal(result.predictionReorderingAllowed, false);
});

test('presentation transform rejects a current destination absent from the semantic model', () => {
  assert.throws(
    () => transformNavigationModel([{id: 'home'}, {id: 'search'}], 'settings', {environment: 'medium'}),
    /Current destination must exist/
  );
});

test('destination ids must be stable and unique', () => {
  assert.throws(() => transformNavigationModel([{label: 'Missing'}], null), /stable id/);
  assert.throws(() => transformNavigationModel([{id: 'home'}, {id: 'home'}], 'home'), /must be unique/);
});

test('reduced motion transforms presentation immediately rather than becoming decorative motion', () => {
  const result = resolveNavigationPresentation({environment: 'expanded', reducedMotion: true});
  assert.equal(result.reducedMotionImmediateTransform, true);
});

test('applyNavigationPresentation writes governed semantic data and target floor', () => {
  const properties = new Map();
  const target = {
    dataset: {},
    style: {setProperty(name, value) { properties.set(name, value); }}
  };
  const result = applyNavigationPresentation(target, {environment: 'compact', touchAssistance: true});
  assert.equal(target.dataset.glazeNavigationV13, 'navigation-capsule-in-flow');
  assert.equal(target.dataset.glazeNavigationEnvironment, 'compact');
  assert.equal(target.dataset.glazeNavigationDetached, 'false');
  assert.equal(properties.get('--glz13-navigation-min-target'), '56px');
  assert.equal(properties.get('--glz13-navigation-placement'), 'lower-reachable-region');
  assert.equal(result.minimumTargetPx, 56);
});

test('candidate metadata preserves lifecycle and acceptance boundaries', () => {
  assert.equal(adaptiveNavigationCandidate.releaseLifecycle, 'proposed');
  assert.equal(adaptiveNavigationCandidate.consumerEligible, false);
  assert.equal(adaptiveNavigationCandidate.destinationOrderStable, true);
  assert.equal(adaptiveNavigationCandidate.predictionMayReorderPrimaryDestinations, false);
  assert.equal(adaptiveNavigationCandidate.rawViewportWidthAuthority, false);
  assert.equal(adaptiveNavigationCandidate.accessibilityMayForceInFlowPresentation, true);
  assert.equal(adaptiveNavigationCandidate.humanNavigationAcceptanceEstablished, false);
  assert.equal(adaptiveNavigationCandidate.physicalDeviceNavigationAcceptanceEstablished, false);
});
