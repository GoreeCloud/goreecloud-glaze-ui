import test from 'node:test';
import assert from 'node:assert/strict';

import {
  SIGNATURE_COMPONENT_IDS,
  REFERENCE_SCENE_IDS,
  resolveSignatureComponent,
  resolveReferenceScene,
  validateReferenceManifest,
  componentExperienceCandidate
} from '../js/glaze-v1.3-component-experience.candidate.mjs';

const manifest = {
  signatureComponents: SIGNATURE_COMPONENT_IDS.map(id => ({id})),
  referenceScenes: REFERENCE_SCENE_IDS.map(id => ({id})),
  rules: {
    referenceSuiteCreatesNewTokenAuthority: false,
    referenceSuiteCreatesNewMaterialAuthority: false,
    personalizationMayChangeSemanticMeaning: false,
    accessibilityMayRecomposePresentation: true,
    durableReadingBackdropDependent: false,
    complete32ComponentCoverageClaimed: false
  }
};

test('preserves the five canonical Signature component identities', () => {
  assert.deepEqual([...SIGNATURE_COMPONENT_IDS], [
    'GlzCapsule', 'GlzMorphCard', 'GlzSmartRail', 'GlzAuroraSurface', 'GlzUniversalSearch'
  ]);
});

test('rejects ungoverned Signature identities', () => {
  assert.throws(() => resolveSignatureComponent('GlzMadeUp'), /Unknown Signature component/);
});

test('SmartRail delegates presentation to System Shell navigation', () => {
  const result = resolveSignatureComponent('GlzSmartRail', {environment: 'workspace', destinationCount: 5});
  assert.equal(result.presentation.presentation, result.shell.navigation.presentation);
  assert.equal(result.presentation.primaryNavigationOrderMayBePersonalized, false);
});

test('UniversalSearch retains scope and consequential-action boundaries', () => {
  const result = resolveSignatureComponent('GlzUniversalSearch', {environment: 'expanded'});
  assert.equal(result.presentation.scopeVisible, true);
  assert.equal(result.presentation.generatedResultsDistinctFromSystemTruth, true);
  assert.equal(result.presentation.destructiveActionRequiresConfirmation, true);
  assert.equal(result.presentation.nestedBackdropBlurAllowed, false);
});

test('Aurora atmosphere never becomes semantic authority and yields to transparency accessibility', () => {
  const ordinary = resolveSignatureComponent('GlzAuroraSurface', {
    environment: 'expanded',
    personalization: {expressionProfile: 'expressive'}
  });
  assert.equal(ordinary.presentation.semanticMeaningMayDependOnAtmosphere, false);
  const reduced = resolveSignatureComponent('GlzAuroraSurface', {
    environment: 'expanded',
    reducedTransparency: true,
    personalization: {expressionProfile: 'expressive'}
  });
  assert.equal(reduced.presentation.material, 'solid-neutral');
  assert.equal(reduced.presentation.atmosphereEnabled, false);
});

test('assisted and far-view targets remain at least 56px', () => {
  assert.equal(resolveSignatureComponent('GlzCapsule', {environment: 'compact', touchAssistance: true}).minimumInteractiveTargetPx, 56);
  assert.equal(resolveSignatureComponent('GlzCapsule', {environment: 'farView'}).minimumInteractiveTargetPx, 56);
});

test('preserves all eight canonical composition scenes', () => {
  assert.deepEqual([...REFERENCE_SCENE_IDS], [
    'home-dashboard', 'data-heavy-administration', 'settings', 'file-browser',
    'search', 'form', 'detail-inspector', 'media'
  ]);
});

test('workspace administration earns triple-pane composition through task value', () => {
  const result = resolveReferenceScene('data-heavy-administration', {environment: 'workspace'});
  assert.equal(result.pane.composition, 'triplePane');
  assert.deepEqual([...result.pane.visiblePaneRoles], ['primary', 'secondary', 'inspector']);
});

test('compact detail inspector collapses to single pane without losing continuity', () => {
  const result = resolveReferenceScene('detail-inspector', {environment: 'compact'});
  assert.equal(result.pane.composition, 'singlePane');
  assert.equal(result.currentTaskPreserved, true);
  assert.equal(result.selectionPreserved, true);
  assert.equal(result.typedInputPreserved, true);
  assert.equal(result.unsavedWorkPreserved, true);
  assert.equal(result.focusPreserved, true);
});

test('large text can reduce pane count before target loss', () => {
  const result = resolveReferenceScene('data-heavy-administration', {
    environment: 'workspace',
    largeTextOrReflow: true
  });
  assert.equal(result.pane.composition, 'dualPane');
  assert.equal(result.minimumInteractiveTargetPx >= 48, true);
  assert.equal(result.horizontalPageOverflowAllowedToPreserveComposition, false);
});

test('personalization changes expression without changing semantic identity', () => {
  const calm = resolveSignatureComponent('GlzMorphCard', {
    environment: 'expanded',
    personalization: {expressionProfile: 'calm', accentSeed: '#AA3377'}
  });
  const expressive = resolveSignatureComponent('GlzMorphCard', {
    environment: 'expanded',
    personalization: {expressionProfile: 'expressive', accentSeed: '#33AA77'}
  });
  assert.equal(calm.id, expressive.id);
  assert.equal(calm.semanticPurpose, expressive.semanticPurpose);
  assert.equal(calm.semanticIdentityPreserved, true);
  assert.equal(expressive.semanticIdentityPreserved, true);
});

test('reference manifest validation accepts the canonical bounded suite', () => {
  assert.deepEqual([...validateReferenceManifest(manifest)], []);
});

test('reference manifest validation fails closed on authority or coverage drift', () => {
  const unsafe = structuredClone(manifest);
  unsafe.rules.referenceSuiteCreatesNewTokenAuthority = true;
  unsafe.referenceScenes.pop();
  const errors = validateReferenceManifest(unsafe);
  assert.equal(errors.length >= 2, true);
});

test('candidate metadata keeps release and coverage boundaries explicit', () => {
  assert.equal(componentExperienceCandidate.releaseLifecycle, 'proposed');
  assert.equal(componentExperienceCandidate.consumerEligible, false);
  assert.equal(componentExperienceCandidate.complete32ComponentCoverageEstablished, false);
  assert.equal(componentExperienceCandidate.nativeComponentParityEstablished, false);
});
