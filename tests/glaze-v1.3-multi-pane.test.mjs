import assert from 'node:assert/strict';
import test from 'node:test';

import {
  applyPaneComposition,
  multiPaneCandidate,
  recomposePaneModel,
  resolvePaneComposition
} from '../js/glaze-v1.3-multi-pane.candidate.mjs';

test('unknown environment falls back to compact single-pane behavior', () => {
  const result = resolvePaneComposition({environment: 'unknown', secondaryTaskValue: true});
  assert.equal(result.environment, 'compact');
  assert.equal(result.composition, 'singlePane');
  assert.equal(result.rawViewportWidthAuthority, false);
});

test('medium adds a secondary pane only when product task value exists', () => {
  assert.equal(resolvePaneComposition({environment: 'medium'}).composition, 'singlePane');
  assert.equal(resolvePaneComposition({environment: 'medium', secondaryTaskValue: true}).composition, 'dualPane');
});

test('expanded and workspace can add an inspector when it has task value', () => {
  const expanded = resolvePaneComposition({
    environment: 'expanded',
    secondaryTaskValue: true,
    inspectorTaskValue: true,
    supportsPersistentSecondary: true,
    supportsInspector: true
  });
  const workspace = resolvePaneComposition({
    environment: 'workspace',
    secondaryTaskValue: true,
    inspectorTaskValue: true
  });
  assert.equal(expanded.composition, 'triplePane');
  assert.deepEqual(expanded.visiblePaneRoles, ['primary', 'secondary', 'inspector']);
  assert.equal(workspace.composition, 'triplePane');
});

test('larger environments do not manufacture empty decorative panes', () => {
  const result = resolvePaneComposition({environment: 'workspace'});
  assert.equal(result.composition, 'singlePane');
  assert.equal(result.informationGain, false);
});

test('folded posture forces single-pane continuity', () => {
  const result = resolvePaneComposition({
    environment: 'expanded',
    posture: 'folded',
    secondaryTaskValue: true,
    inspectorTaskValue: true
  });
  assert.equal(result.composition, 'singlePane');
  assert.equal(result.taskContinuityRequired, true);
});

test('half-open uses a hinge divider only with platform-declared safe regions', () => {
  const dualRegion = resolvePaneComposition({
    environment: 'medium',
    posture: 'half-open',
    secondaryTaskValue: true,
    availableRegions: [{id: 'a', safe: true}, {id: 'b', safe: true}]
  });
  const noRegions = resolvePaneComposition({
    environment: 'medium',
    posture: 'halfOpen',
    secondaryTaskValue: true
  });
  assert.equal(dualRegion.composition, 'dualRegionHinge');
  assert.equal(dualRegion.usesHingeAsStructuralDivider, true);
  assert.equal(dualRegion.platformUnsafeRegionsRequiredForHingeLayout, true);
  assert.equal(noRegions.composition, 'dualPane');
});

test('large text/reflow collapses triple-pane before reducing target size', () => {
  const result = resolvePaneComposition({
    environment: 'workspace',
    secondaryTaskValue: true,
    inspectorTaskValue: true,
    largeTextOrReflow: true,
    touchAssistance: true
  });
  assert.equal(result.composition, 'dualPane');
  assert.equal(result.accessibilityCollapsedPaneCount, true);
  assert.equal(result.minimumInteractiveTargetPx, 56);
});

test('accessibility can force single-pane even on workspace', () => {
  const result = resolvePaneComposition({
    environment: 'workspace',
    secondaryTaskValue: true,
    inspectorTaskValue: true,
    forceSinglePaneForAccessibility: true
  });
  assert.equal(result.composition, 'singlePane');
});

test('far-view remains conservative and only adds secondary context when useful', () => {
  assert.equal(resolvePaneComposition({environment: 'far-view'}).composition, 'singlePane');
  assert.equal(resolvePaneComposition({environment: 'farView', secondaryTaskValue: true}).composition, 'dualPane');
});

test('wearable always remains single-pane', () => {
  const result = resolvePaneComposition({environment: 'wearable', secondaryTaskValue: true, inspectorTaskValue: true});
  assert.equal(result.composition, 'singlePane');
});

test('recomposition preserves model state and defers non-visible panes rather than deleting them', () => {
  const panes = [
    {role: 'primary', id: 'editor', unsaved: true},
    {role: 'secondary', id: 'outline'},
    {role: 'inspector', id: 'properties'}
  ];
  const result = recomposePaneModel(panes, {
    environment: 'medium',
    secondaryTaskValue: true,
    inspectorTaskValue: true
  });
  assert.deepEqual(result.visiblePanes.map(pane => pane.id), ['editor', 'outline']);
  assert.deepEqual(result.deferredPanes.map(pane => pane.id), ['properties']);
  assert.equal(result.unsavedWorkPreserved, true);
  assert.equal(result.pageReloadRequired, false);
});

test('pane model requires exactly one semantic primary pane', () => {
  assert.throws(() => recomposePaneModel([{role: 'secondary'}], {environment: 'medium'}), /exactly one primary/);
  assert.throws(() => recomposePaneModel([{role: 'primary'}, {role: 'primary'}], {environment: 'medium'}), /exactly one primary/);
});

test('pane model rejects ungoverned pane roles', () => {
  assert.throws(() => recomposePaneModel([{role: 'primary'}, {role: 'advertising'}]), /governed semantic role/);
});

test('reduced motion and transparency are explicit fallback signals', () => {
  const result = resolvePaneComposition({
    environment: 'expanded',
    secondaryTaskValue: true,
    reducedMotion: true,
    reducedTransparency: true
  });
  assert.equal(result.immediateRecomposition, true);
  assert.equal(result.solidPaneFallbackAllowed, true);
});

test('applyPaneComposition writes semantic composition data without pixel pane widths', () => {
  const properties = new Map();
  const target = {
    dataset: {},
    style: {setProperty(name, value) { properties.set(name, value); }}
  };
  const result = applyPaneComposition(target, {
    environment: 'workspace',
    secondaryTaskValue: true,
    inspectorTaskValue: true
  });
  assert.equal(target.dataset.glazePaneV13, 'triplePane');
  assert.equal(target.dataset.glazePaneEnvironment, 'workspace');
  assert.equal(properties.get('--glz13-pane-count'), '3');
  assert.equal(properties.get('--glz13-pane-min-target'), '48px');
  assert.equal(result.rawViewportWidthAuthority, false);
});

test('candidate metadata preserves evidence boundaries', () => {
  assert.equal(multiPaneCandidate.releaseLifecycle, 'proposed');
  assert.equal(multiPaneCandidate.consumerEligible, false);
  assert.equal(multiPaneCandidate.rawViewportWidthAuthority, false);
  assert.equal(multiPaneCandidate.deviceIdentityInferenceAllowed, false);
  assert.equal(multiPaneCandidate.hardCodedHingeGeometryAllowed, false);
  assert.equal(multiPaneCandidate.accessibilityMayCollapsePaneCount, true);
  assert.equal(multiPaneCandidate.physicalFoldableAcceptanceEstablished, false);
  assert.equal(multiPaneCandidate.humanLargeScreenAcceptanceEstablished, false);
});
