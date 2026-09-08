import test from 'node:test';
import assert from 'node:assert/strict';

import {
  HARDENING_STATE_PRIORITY,
  HARDENING_TARGET_FLOORS,
  accessibilityInteractionHardeningCandidate,
  auditInteractionPresentation,
  createInteractionHardeningResolver,
  resolveHardeningTargetFloor,
  resolveInteractionPresentation
} from '../js/glaze-v1.3.1-accessibility-interaction-hardening.candidate.mjs';

test('state priority keeps disabled and focus-visible ahead of decorative microstates', () => {
  assert.deepEqual([...HARDENING_STATE_PRIORITY], [
    'disabled',
    'focus-visible',
    'pressed',
    'hover',
    'current-or-selected',
    'rest'
  ]);
});

test('keyboard, remote, and assistive focus infer focus-visible without pointer noise', () => {
  for (const inputModality of ['keyboard', 'remote', 'assistive']) {
    const state = resolveInteractionPresentation({focused: true}, {}, {inputModality});
    assert.equal(state.focusVisible, true);
    assert.equal(state.focusIndicator, 'standard-focus-ring');
  }

  const pointer = resolveInteractionPresentation({focused: true}, {}, {inputModality: 'pointer'});
  assert.equal(pointer.focusVisible, false);
});

test('forced colors moves visible focus to platform highlight authority', () => {
  const state = resolveInteractionPresentation(
    {focused: true},
    {forcedColors: true},
    {inputModality: 'keyboard'}
  );
  assert.equal(state.focusIndicator, 'platform-highlight-outline');
  assert.equal(state.focusIndicatorDistinctFromSemanticState, true);
});

test('Reduced Motion removes nonessential hover and press transforms', () => {
  const hover = resolveInteractionPresentation(
    {hovered: true},
    {reducedMotion: true},
    {inputModality: 'pointer'}
  );
  assert.equal(hover.hoverVisualTreatmentAllowed, true);
  assert.equal(hover.hoverMotionAllowed, false);
  assert.equal(hover.transformTreatment, 'none');
  assert.equal(hover.transitionTreatment, 'immediate');

  const pressed = resolveInteractionPresentation(
    {pressed: true},
    {reducedMotion: true},
    {inputModality: 'pointer'}
  );
  assert.equal(pressed.pressMotionAllowed, false);
  assert.equal(pressed.transformTreatment, 'none');
  assert.equal(pressed.semanticActivationWaitsForAnimation, false);
});

test('disabled state wins and cannot activate, hover, or press', () => {
  const state = resolveInteractionPresentation(
    {disabled: true, focused: true, hovered: true, pressed: true},
    {},
    {inputModality: 'pointer'}
  );
  assert.equal(state.primaryState, 'disabled');
  assert.equal(state.activationAllowed, false);
  assert.equal(state.focusVisible, false);
  assert.equal(state.hoverMotionAllowed, false);
  assert.equal(state.pressMotionAllowed, false);
});

test('current state remains structural and distinct from focus', () => {
  const state = resolveInteractionPresentation(
    {current: true, focused: true},
    {},
    {inputModality: 'keyboard'}
  );
  assert.equal(state.primaryState, 'focus-visible');
  assert.equal(state.semanticStateIndicator, 'current');
  assert.equal(state.focusIndicatorDistinctFromSemanticState, true);
});

test('coarse-pointer and inherited accessibility floors never shrink below policy', () => {
  assert.equal(HARDENING_TARGET_FLOORS.default, 48);
  assert.equal(resolveHardeningTargetFloor({}, {}), 48);
  assert.equal(resolveHardeningTargetFloor({}, {coarsePointer: true}), 56);
  assert.equal(resolveHardeningTargetFloor({targetFloorPx: 64}, {coarsePointer: true}), 64);
});

test('auditor rejects hover-only affordance, activatable disabled state, and focus collisions', () => {
  const result = auditInteractionPresentation({
    interactive: true,
    disabled: true,
    activatable: true,
    hoverRequiredToDiscoverAction: true,
    focusIndicatorDistinctFromSemanticState: false,
    widthPx: 48,
    heightPx: 48
  });
  const codes = result.issues.map(issue => issue.code);
  assert.equal(result.pass, false);
  assert.ok(codes.includes('disabled-control-activatable'));
  assert.ok(codes.includes('hover-only-affordance'));
  assert.ok(codes.includes('focus-semantic-state-collision'));
});

test('auditor catches Reduced Motion transform leaks and Forced Colors focus authority drift', () => {
  const reduced = auditInteractionPresentation({
    interactive: true,
    widthPx: 48,
    heightPx: 48,
    nonessentialTransformEnabled: true
  }, {reducedMotion: true});
  assert.ok(reduced.issues.some(issue => issue.code === 'reduced-motion-transform-leak'));

  const forced = auditInteractionPresentation({
    interactive: true,
    focused: true,
    focusIndicatorVisible: true,
    usesPlatformFocusColor: false,
    widthPx: 48,
    heightPx: 48
  }, {forcedColors: true}, {inputModality: 'keyboard'});
  assert.ok(forced.issues.some(issue => issue.code === 'forced-colors-focus-authority'));
});

test('resolver stays local and carries no lifecycle or manual-acceptance authority', () => {
  const resolver = createInteractionHardeningResolver({increasedContrast: true}, {inputModality: 'keyboard'});
  const state = resolver.resolve({focused: true});
  assert.equal(state.focusIndicator, 'strong-focus-ring');
  assert.equal(accessibilityInteractionHardeningCandidate.lifecycleAuthority, false);
  assert.equal(accessibilityInteractionHardeningCandidate.consumerEligible, false);
  assert.equal(accessibilityInteractionHardeningCandidate.modifiesStableEntrypoint, false);
  assert.equal(accessibilityInteractionHardeningCandidate.manualAcceptanceEstablished, false);
});
