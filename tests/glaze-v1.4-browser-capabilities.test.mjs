import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

import {
  browserCapabilityCandidate,
  createBrowserOpticalCapabilityAdapter,
  detectBrowserOpticalCapabilities
} from '../js/glaze-v1.4-browser-capabilities.candidate.mjs';

const ROOT = new URL('../', import.meta.url);
const ADAPTER_URL = new URL('js/glaze-v1.4-browser-capabilities.candidate.mjs', ROOT);
const HARNESS_HTML_URL = new URL('reference/glaze-v1.4-browser-qualification.candidate.html', ROOT);
const HARNESS_JS_URL = new URL('reference/glaze-v1.4-browser-qualification.candidate.mjs', ROOT);

function makeEnvironment({supports = [], media = {}, webAnimations = false} = {}) {
  const supportSet = new Set(supports.map(([property, value]) => `${property}\u0000${value}`));
  const Element = function Element() {};
  if (webAnimations) Element.prototype.animate = function animate() {};
  return {
    CSS: {
      supports(property, value) {
        return supportSet.has(`${property}\u0000${value}`);
      }
    },
    matchMedia(query) {
      return {matches: media[query] === true};
    },
    Element
  };
}

const FULL_CSS_SUPPORT = [
  ['background-color', 'rgba(255, 255, 255, 0.5)'],
  ['backdrop-filter', 'blur(1px)'],
  ['opacity', '0.5'],
  ['transition-property', 'opacity'],
  ['background-image', 'radial-gradient(circle, transparent, black)'],
  ['filter', 'blur(1px)'],
  ['background-image', 'linear-gradient(white, black)'],
  ['box-shadow', '0 0 0 1px currentColor'],
  ['box-shadow', '0 1px 3px rgba(0, 0, 0, 0.2)']
];

test('browser capability detection fails closed when feature evidence is unavailable', () => {
  const snapshot = detectBrowserOpticalCapabilities({});
  assert.deepEqual(snapshot.capabilities, []);
  assert.equal(snapshot.recommendedAccessibilityProfile, 'standard');
  assert.equal(snapshot.recommendedAppearanceMode, 'light');
  assert.equal(snapshot.qualification.browserMatrixEstablished, false);
  assert.equal(snapshot.privacy.telemetryUsed, false);
  assert.equal(snapshot.privacy.screenCaptureUsed, false);
});

test('browser capability detection declares only bounded local feature evidence', () => {
  const snapshot = detectBrowserOpticalCapabilities(makeEnvironment({
    supports: FULL_CSS_SUPPORT,
    webAnimations: true
  }));

  for (const capability of [
    'translucency',
    'backdrop-blur',
    'dynamic-opacity',
    'adaptive-frost',
    'aura',
    'edge-illumination',
    'material-aware-motion',
    'connected-transformation',
    'shadow-diffusion'
  ]) {
    assert.ok(snapshot.capabilities.includes(capability), `missing ${capability}`);
  }

  for (const capability of ['environmental-sampling', 'reflection', 'hdr-aware-luminance']) {
    assert.equal(snapshot.capabilities.includes(capability), false, `${capability} must fail closed`);
    assert.ok(snapshot.neverAutoDeclared.includes(capability));
  }
});

test('webkit backdrop-filter support is accepted as bounded backdrop evidence', () => {
  const snapshot = detectBrowserOpticalCapabilities(makeEnvironment({
    supports: [
      ['background-color', 'rgba(255, 255, 255, 0.5)'],
      ['-webkit-backdrop-filter', 'blur(1px)'],
      ['opacity', '0.5'],
      ['transition-property', 'opacity']
    ]
  }));

  assert.ok(snapshot.capabilities.includes('backdrop-blur'));
  assert.ok(snapshot.capabilities.includes('adaptive-frost'));
});

test('accessibility preferences are recorded independently with explicit recommendation limits', () => {
  const environment = makeEnvironment({
    media: {
      '(prefers-reduced-transparency: reduce)': true,
      '(prefers-reduced-motion: reduce)': true,
      '(forced-colors: active)': true,
      '(prefers-color-scheme: dark)': true
    }
  });
  const adapter = createBrowserOpticalCapabilityAdapter({environment});
  const prepared = adapter.prepareRequest({materialRole: 'glz.material.glaze'});
  const snapshot = prepared.snapshot;

  assert.deepEqual(snapshot.activeAccessibilityPreferences, [
    'reduced-transparency',
    'increased-contrast',
    'reduced-motion'
  ]);
  assert.equal(snapshot.recommendedAccessibilityProfile, 'reduced-transparency');
  assert.equal(snapshot.recommendedAppearanceMode, 'dark');
  assert.equal(snapshot.multipleAccessibilityPreferencesActive, true);
  assert.equal(prepared.consumerPolicyRequired, true);
  assert.equal(prepared.request.accessibilityProfile, 'reduced-transparency');
  assert.equal(snapshot.recommendationIsQualificationEvidence, false);
});

test('explicit consumer request values override browser recommendations', () => {
  const environment = makeEnvironment({
    supports: FULL_CSS_SUPPORT,
    media: {'(prefers-reduced-motion: reduce)': true}
  });
  const adapter = createBrowserOpticalCapabilityAdapter({environment});
  const prepared = adapter.prepareRequest({
    accessibilityProfile: 'standard',
    appearanceMode: 'deep-dark',
    platformCapabilities: ['translucency']
  });

  assert.equal(prepared.request.accessibilityProfile, 'standard');
  assert.equal(prepared.request.appearanceMode, 'deep-dark');
  assert.deepEqual(prepared.request.platformCapabilities, ['translucency']);
  assert.equal(Object.isFrozen(prepared.request), true);
  assert.equal(Object.isFrozen(prepared.snapshot), true);
});

test('candidate metadata never claims browser or production qualification', () => {
  assert.equal(browserCapabilityCandidate.consumerEligible, false);
  assert.equal(browserCapabilityCandidate.lifecycleAuthority, false);
  assert.equal(browserCapabilityCandidate.browserMatrixQualificationEstablished, false);
  assert.equal(browserCapabilityCandidate.assistiveTechnologyQualificationEstablished, false);
  assert.equal(browserCapabilityCandidate.physicalDeviceQualificationEstablished, false);
  assert.equal(browserCapabilityCandidate.productionPerformanceQualificationEstablished, false);
  assert.equal(browserCapabilityCandidate.environmentalSamplingAutoDeclared, false);
});

test('browser adapter and harness avoid identity, fingerprinting, capture, storage, and network APIs', async () => {
  const [adapter, harness] = await Promise.all([
    readFile(ADAPTER_URL, 'utf8'),
    readFile(HARNESS_JS_URL, 'utf8')
  ]);
  const source = `${adapter}\n${harness}`;
  for (const forbidden of [
    /\.userAgent\b/,
    /\.deviceMemory\b/,
    /\.hardwareConcurrency\b/,
    /getBattery\s*\(/,
    /getDisplayMedia\s*\(/,
    /getUserMedia\s*\(/,
    /localStorage\b/,
    /sessionStorage\b/,
    /fetch\s*\(/,
    /XMLHttpRequest\b/,
    /sendBeacon\b/,
    /WebSocket\b/
  ]) {
    assert.doesNotMatch(source, forbidden);
  }
});

test('qualification harness is local-only and labels itself as non-qualification evidence', async () => {
  const html = await readFile(HARNESS_HTML_URL, 'utf8');
  assert.match(html, /Candidate diagnostic only/);
  assert.match(html, /does not establish browser qualification/);
  assert.match(html, /glaze-v1\.4-optical-runtime\.candidate\.css/);
  assert.match(html, /glaze-v1\.4-browser-qualification\.candidate\.mjs/);
  assert.doesNotMatch(html, /https?:\/\//i);
  assert.doesNotMatch(html, /<iframe\b/i);
});
