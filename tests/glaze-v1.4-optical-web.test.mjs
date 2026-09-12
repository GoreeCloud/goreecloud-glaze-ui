import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

import {
  applyOpticalWebRuntime,
  createOpticalWebAdapter,
  opticalWebCandidate
} from '../js/glaze-v1.4-optical-web.candidate.mjs';

const ROOT = new URL('../', import.meta.url);
const CSS_URL = new URL('css/glaze-v1.4-optical-runtime.candidate.css', ROOT);
const TOKENS_URL = new URL('tokens/glaze-v1.4-optical-material.candidate.json', ROOT);

const BASE_CAPABILITIES = ['translucency', 'backdrop-blur', 'shadow-diffusion'];

function fakeTarget() {
  const properties = new Map();
  return {
    target: {
      dataset: {},
      style: {setProperty(name, value) { properties.set(name, value); }}
    },
    properties
  };
}

test('web adapter projects accepted semantic runtime state without raw optical values', () => {
  const {target, properties} = fakeTarget();
  const result = applyOpticalWebRuntime(target, {
    materialRole: 'glz.material.glaze',
    elevationRole: 'glz.elevation.raised',
    accessibilityProfile: 'standard',
    performanceLevel: 'balanced',
    platformCapabilities: BASE_CAPABILITIES
  });

  assert.equal(result.disposition, 'accepted');
  assert.equal(target.dataset.glazeV14Renderer, 'web-candidate');
  assert.equal(target.dataset.glazeV14Profile, 'standard');
  assert.equal(target.dataset.glazeV14Rendering, 'optical-glaze');
  assert.equal(target.dataset.glazeV14Accessibility, 'standard');
  assert.equal(target.dataset.glazeV14BackdropBlur, 'on');
  assert.equal(properties.get('--glz14-optical-profile'), 'standard');
  assert.equal(properties.has('--glz14-optical-depth'), false);
  assert.equal(properties.has('--glz14-refraction'), false);
});

test('web adapter preserves reduced-transparency solid fallback state', () => {
  const {target} = fakeTarget();
  const result = applyOpticalWebRuntime(target, {
    materialRole: 'glz.material.deepGlaze',
    accessibilityProfile: 'reduced-transparency',
    performanceLevel: 'full',
    platformCapabilities: BASE_CAPABILITIES
  });

  assert.equal(result.disposition, 'substituted');
  assert.equal(target.dataset.glazeV14Rendering, 'solid-semantic-surface');
  assert.equal(target.dataset.glazeV14Profile, 'solid-semantic-surface');
  assert.equal(target.dataset.glazeV14Translucency, 'off');
  assert.equal(target.dataset.glazeV14BackdropBlur, 'off');
});

test('web adapter metadata does not claim qualification or operational authority', () => {
  const adapter = createOpticalWebAdapter({
    capabilityAdapter: {resolve() { return BASE_CAPABILITIES; }}
  });
  const {target} = fakeTarget();
  const result = adapter.apply(target, {materialRole: 'glz.material.surface'});

  assert.equal(result.disposition, 'accepted');
  assert.equal(adapter.environmentalSamplingImplemented, false);
  assert.equal(adapter.browserQualificationEstablished, false);
  assert.equal(adapter.nativeRendererParityEstablished, false);
  assert.equal(adapter.telemetryRequired, false);
  assert.equal(adapter.analyticsRequired, false);
  assert.equal(opticalWebCandidate.establishesOperationalSecurityAuthority, false);
  assert.equal(opticalWebCandidate.establishesOperationalPrivacyAuthority, false);
  assert.equal(opticalWebCandidate.establishesIdentityAuthority, false);
  assert.equal(opticalWebCandidate.establishesRecoveryAuthority, false);
});

test('candidate stylesheet is isolated from the Stable entrypoint and imports Stable V1.3 locally', async () => {
  const css = await readFile(CSS_URL, 'utf8');
  assert.match(css, /@import url\("\.\/glaze-v1\.3\.0\.css"\);/);
  assert.doesNotMatch(css, /url\(["']?https?:\/\//i);
  assert.match(css, /\[data-glaze-v14-rendering="optical-glaze"\]/);
  assert.match(css, /\[data-glaze-v14-rendering="static-glaze"\]/);
  assert.match(css, /\[data-glaze-v14-rendering="solid-semantic-surface"\]/);
});

test('candidate stylesheet profile diagnostics match the governed optical token source', async () => {
  const [css, tokenText] = await Promise.all([
    readFile(CSS_URL, 'utf8'),
    readFile(TOKENS_URL, 'utf8')
  ]);
  const tokens = JSON.parse(tokenText);

  for (const [profileName, profile] of Object.entries(tokens.opticalProfiles)) {
    const selector = `[data-glaze-v14-profile="${profileName}"]`;
    const start = css.indexOf(selector);
    assert.notEqual(start, -1, `missing ${selector}`);
    const nextSelector = css.indexOf('\n[data-glaze-v14-', start + selector.length);
    const block = css.slice(start, nextSelector === -1 ? css.length : nextSelector);
    const expected = {
      '--glz14-optical-depth': profile.opticalDepth,
      '--glz14-diffusion': profile.diffusion,
      '--glz14-refraction': profile.refraction,
      '--glz14-color-bleed': profile.colorBleed,
      '--glz14-highlight-rim': profile.highlightRim,
      '--glz14-shadow-depth': profile.shadowDepth
    };
    for (const [name, value] of Object.entries(expected)) {
      const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      assert.match(block, new RegExp(`${escaped}:\\s*${Number(value).toFixed(2)};`));
    }
  }
});

test('candidate stylesheet solid fallback never uses backdrop processing', async () => {
  const css = await readFile(CSS_URL, 'utf8');
  const start = css.indexOf('[data-glaze-v14-rendering="solid-semantic-surface"]');
  assert.notEqual(start, -1);
  const block = css.slice(start, css.indexOf('/* Increased Contrast', start));
  assert.match(block, /backdrop-filter:\s*none;/);
  assert.match(block, /--glz14-render-blur:\s*0px;/);
});
