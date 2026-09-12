import {
  createBrowserOpticalCapabilityAdapter
} from '../js/glaze-v1.4-browser-capabilities.candidate.mjs';
import {
  applyResolvedOpticalWebState,
  createOpticalWebAdapter
} from '../js/glaze-v1.4-optical-web.candidate.mjs';

const capabilityAdapter = createBrowserOpticalCapabilityAdapter({environment: globalThis});
const webAdapter = createOpticalWebAdapter({capabilityAdapter});

function replaceDefinitionList(target, entries) {
  target.replaceChildren();
  for (const [term, value] of entries) {
    const dt = document.createElement('dt');
    const dd = document.createElement('dd');
    dt.textContent = term;
    dd.textContent = value;
    target.append(dt, dd);
  }
}

function yesNo(value) {
  return value ? 'yes' : 'no';
}

function renderQualificationSnapshot() {
  const prepared = capabilityAdapter.prepareRequest({
    materialRole: 'glz.material.glaze',
    elevationRole: 'glz.elevation.raised',
    performanceLevel: 'balanced',
    environmentalResponse: {mode: 'static'}
  });
  const snapshot = prepared.snapshot;
  const resolved = webAdapter.resolve(prepared.request);

  const primarySurface = document.querySelector('[data-glz14-demo="primary"]');
  const solidSurface = document.querySelector('[data-glz14-demo="solid"]');
  applyResolvedOpticalWebState(primarySurface, resolved);

  const solidResolved = webAdapter.resolve({
    ...prepared.request,
    accessibilityProfile: 'reduced-transparency'
  });
  applyResolvedOpticalWebState(solidSurface, solidResolved);

  replaceDefinitionList(document.querySelector('#glz14-capability-list'), [
    ['Declared capabilities', snapshot.capabilities.length ? snapshot.capabilities.join(', ') : 'none'],
    ['Backdrop blur', yesNo(snapshot.evidence.backdropBlur)],
    ['Translucency', yesNo(snapshot.evidence.translucency)],
    ['Dynamic opacity', yesNo(snapshot.evidence.dynamicOpacity)],
    ['Web Animations API', yesNo(snapshot.evidence.webAnimations)],
    ['Never auto-declared', snapshot.neverAutoDeclared.join(', ')],
    ['Browser matrix qualified', yesNo(snapshot.qualification.browserMatrixEstablished)]
  ]);

  replaceDefinitionList(document.querySelector('#glz14-preference-list'), [
    ['Active accessibility preferences', snapshot.activeAccessibilityPreferences.length ? snapshot.activeAccessibilityPreferences.join(', ') : 'none detected'],
    ['Recommended candidate profile', snapshot.recommendedAccessibilityProfile],
    ['Recommended appearance', snapshot.recommendedAppearanceMode],
    ['Multiple preference policy needed', yesNo(prepared.consumerPolicyRequired)],
    ['Recommendation is qualification evidence', yesNo(snapshot.recommendationIsQualificationEvidence)]
  ]);

  document.querySelector('#glz14-resolution-output').textContent = JSON.stringify({
    candidate: true,
    localOnly: true,
    persisted: false,
    transmitted: false,
    requested: resolved.requested,
    accepted: resolved.accepted,
    disposition: resolved.disposition,
    reasons: resolved.reasons,
    fallbacks: resolved.fallbacks,
    effectiveOpticalProfile: resolved.effectiveOpticalProfile,
    privacy: snapshot.privacy,
    qualification: snapshot.qualification
  }, null, 2);
}

document.querySelector('#glz14-rerun').addEventListener('click', renderQualificationSnapshot);
renderQualificationSnapshot();
