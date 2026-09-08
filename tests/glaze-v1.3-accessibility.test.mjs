import test from 'node:test';
import assert from 'node:assert/strict';

import {
  ACCESSIBILITY_RESOLUTION_ORDER,
  ACCESSIBILITY_TARGET_FLOORS,
  accessibilityResilienceCandidate,
  auditAccessibleNode,
  createAccessibilityResolver,
  resolveAccessibilityProfile,
  resolveResilientComposition
} from '../js/glaze-v1.3-accessibility.candidate.mjs';

test('preserves canonical accessibility precedence', () => {
  assert.deepEqual([...ACCESSIBILITY_RESOLUTION_ORDER], [
    'protected-semantic-meaning',
    'forced-colors',
    'reduced-motion',
    'reduced-transparency',
    'increased-contrast-and-show-boundaries',
    'large-text-and-touch-assistance',
    'material-clarity',
    'expression-and-accent'
  ]);
});

test('Forced Colors overrides custom material and semantic color mapping', () => {
  const profile = resolveAccessibilityProfile({forcedColors: true, materialClarity: 'clear'});
  assert.equal(profile.effectiveMaterialClarity, 'solid');
  assert.equal(profile.blurAllowed, false);
  assert.equal(profile.refractionAllowed, false);
  assert.equal(profile.customSemanticColorMapping, 'platform');
  assert.equal(profile.contextualAccentMayOverrideSemanticColor, false);
});

test('Reduced Transparency removes backdrop-dependent effects', () => {
  const profile = resolveAccessibilityProfile({reducedTransparency: true, materialClarity: 'balanced'});
  assert.equal(profile.effectiveMaterialClarity, 'solid');
  assert.equal(profile.blurAllowed, false);
  assert.equal(profile.distortionAllowed, false);
});

test('Reduced Motion preserves direct manipulation and semantic completion', () => {
  const profile = resolveAccessibilityProfile({reducedMotion: true}, {motionRole: 'spatial'});
  assert.equal(profile.motionRole, 'reduced');
  assert.equal(profile.nonessentialMotionMayBecomeImmediate, true);
  assert.equal(profile.directManipulationPreserved, true);
});

test('default and Touch Assistance target floors remain 48 and 56 pixels', () => {
  assert.equal(ACCESSIBILITY_TARGET_FLOORS.default, 48);
  assert.equal(resolveAccessibilityProfile().targetFloorPx, 48);
  assert.equal(resolveAccessibilityProfile({touchAssistance: true}).targetFloorPx, 56);
});

test('far-view uses the 56 pixel interaction floor', () => {
  assert.equal(resolveAccessibilityProfile({}, {farView: true}).targetFloorPx, 56);
});

test('200 percent text and compact density require reflow before shrinkage', () => {
  const profile = resolveAccessibilityProfile({largeText: true, textScalePercent: 200, density: 'compact'});
  const composition = resolveResilientComposition({}, profile);
  assert.equal(profile.reflowRequired, true);
  assert.equal(profile.effectiveDensity, 'standard-or-comfortable-as-needed');
  assert.equal(composition.collapsePaneCountBeforeOverflow, true);
  assert.equal(composition.shrinkInteractiveTargetsBeforeReflow, false);
  assert.equal(composition.clipCriticalTextBeforeReflow, false);
});

test('auditor rejects color-only state and missing semantics', () => {
  const profile = resolveAccessibilityProfile();
  const result = auditAccessibleNode({
    interactive: true,
    widthPx: 48,
    heightPx: 48,
    stateCommunicatedByColorOnly: true,
    focusIndicatorVisible: true
  }, profile);
  const codes = result.issues.map(item => item.code);
  assert.equal(result.pass, false);
  assert.ok(codes.includes('missing-accessible-name'));
  assert.ok(codes.includes('missing-semantic-role'));
  assert.ok(codes.includes('color-only-state'));
});

test('auditor enforces resolved target floor and visible focus', () => {
  const profile = resolveAccessibilityProfile({touchAssistance: true});
  const result = auditAccessibleNode({
    interactive: true,
    accessibleName: 'Open settings',
    role: 'button',
    widthPx: 48,
    heightPx: 48,
    focusIndicatorVisible: false
  }, profile);
  const codes = result.issues.map(item => item.code);
  assert.ok(codes.includes('undersized-target'));
  assert.ok(codes.includes('focus-not-visible'));
});

test('RTL mode requires logical navigation order', () => {
  const profile = resolveAccessibilityProfile({}, {direction: 'rtl'});
  const result = auditAccessibleNode({
    interactive: true,
    accessibleName: 'Next',
    role: 'button',
    widthPx: 48,
    heightPx: 48,
    focusIndicatorVisible: true,
    logicalOrderPreserved: false
  }, profile);
  assert.ok(result.issues.some(item => item.code === 'rtl-logical-order-broken'));
});

test('resilient recomposition preserves task state instead of reloading', () => {
  const profile = resolveAccessibilityProfile({textScalePercent: 200});
  const composition = resolveResilientComposition({availableWidthConstrained: true}, profile);
  assert.equal(composition.reloadRequired, false);
  assert.equal(composition.resetSelectionRequired, false);
  assert.equal(composition.resetDraftRequired, false);
  assert.equal(composition.resetFocusRequired, false);
  assert.ok(composition.preserve.includes('unsaved-work'));
  assert.ok(composition.preserve.includes('logical-focus-order'));
});

test('resolver remains local and machine-observable without claiming manual acceptance', () => {
  const resolver = createAccessibilityResolver({increasedContrast: true});
  const profile = resolver.resolve();
  assert.equal(profile.focusVisibility, 'strong');
  assert.equal(accessibilityResilienceCandidate.parallelAccessibilityAuthorityIntroduced, false);
  assert.equal(accessibilityResilienceCandidate.automatedEvidenceEstablishesHumanAcceptance, false);
  assert.equal(accessibilityResilienceCandidate.automatedEvidenceEstablishesAssistiveTechnologyAcceptance, false);
  assert.equal(accessibilityResilienceCandidate.automatedEvidenceEstablishesPhysicalDeviceAcceptance, false);
});
