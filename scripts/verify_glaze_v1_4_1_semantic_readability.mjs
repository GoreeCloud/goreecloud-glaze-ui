import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createGlazeOpticalEngineV141Candidate} from '../js/glaze-v1.4.1-optical-engine.candidate.mjs';

const contract = JSON.parse(fs.readFileSync('contracts/v1.4.1/semantic-readability.contract.json', 'utf8'));
const css = fs.readFileSync('css/glaze-v1.4.1.candidate.css', 'utf8');

function fakeTarget() {
  const properties = new Map();
  return {
    dataset: {},
    style: {
      setProperty(name, value) {
        properties.set(name, String(value));
      },
      getPropertyValue(name) {
        return properties.get(name) || '';
      }
    },
    properties
  };
}

function percentage(value) {
  assert.match(value, /^\d+(?:\.\d+)?%$/);
  return Number.parseFloat(value) / 100;
}

const requirements = contract.requirements;
const scenario = contract.failedScenario;
const engine = createGlazeOpticalEngineV141Candidate({
  signalAdapter: {resolve: () => ({})}
});

const resolved = engine.resolve(scenario);
assert.equal(resolved.mode, 'adaptive-optical');
assert.equal(resolved.appearance, 'light');
assert.ok(resolved.semanticProtection >= 0.5 && resolved.semanticProtection <= 1);
assert.ok(
  resolved.semanticSurfaceStrength >= requirements.lightAppearanceMinimumSemanticSurfaceStrength,
  `expected light semantic surface strength >= ${requirements.lightAppearanceMinimumSemanticSurfaceStrength}, got ${resolved.semanticSurfaceStrength}`
);

const target = fakeTarget();
const applied = engine.apply(target, scenario);
assert.equal(applied.appearance, 'light');
assert.equal(target.dataset.glazeOpticalV141Appearance, 'light');
assert.ok(
  percentage(target.style.getPropertyValue('--glz141-semantic-surface-strength')) >= requirements.lightAppearanceMinimumSemanticSurfaceStrength
);

const accessibleTarget = fakeTarget();
const accessible = engine.apply(accessibleTarget, {
  ...scenario,
  accessibility: {reducedTransparency: true}
});
assert.equal(accessible.mode, 'solid-accessible');
assert.equal(accessible.semanticSurfaceStrength, requirements.solidAccessibleSemanticSurfaceStrength);
assert.equal(accessibleTarget.dataset.glazeOpticalV141Appearance, 'light');
assert.equal(accessibleTarget.style.getPropertyValue('--glz141-semantic-surface-strength'), '100.00%');

const failedTarget = fakeTarget();
const failingEngine = createGlazeOpticalEngineV141Candidate({
  signalAdapter: {resolve() { throw new Error('synthetic adapter fault'); }}
});
const failed = failingEngine.apply(failedTarget, scenario);
assert.equal(failed.mode, 'solid-accessible');
assert.equal(failed.adapterStatus, 'failed-safe');
assert.equal(failed.semanticSurfaceStrength, requirements.adapterFailureSemanticSurfaceStrength);
assert.equal(failedTarget.style.getPropertyValue('--glz141-semantic-surface-strength'), '100.00%');

assert.match(css, /@import url\("\.\/glaze-v1\.4\.0\.css"\)/);
assert.match(css, /data-glaze-semantic-surface="protected"/);
assert.match(css, /--glz141-semantic-surface-strength/);
assert.match(css, /data-glaze-action="secondary"/);
assert.doesNotMatch(css, /https?:\/\//);

if (requirements.stableV140SourceMustRemainImmutable) {
  const stableEngineBlob = execFileSync('git', ['hash-object', 'js/glaze-v1.4-optical-engine.mjs'], {encoding: 'utf8'}).trim();
  const stableCssBlob = execFileSync('git', ['hash-object', 'css/glaze-v1.4.0.css'], {encoding: 'utf8'}).trim();
  assert.equal(stableEngineBlob, 'b3961d6d3534732367704715666803bd8cd27894');
  assert.equal(stableCssBlob, 'd48a9bc317090d152799769271de0fb4325494c4');
}

assert.equal(requirements.remoteContextRequired, false);
assert.equal(requirements.telemetryRequired, false);
assert.equal(requirements.humanReReviewRequired, true);
assert.equal(requirements.automaticHumanPassForbidden, true);

console.log('GLAZE UI V1.4.1 semantic readability hardening verified.');
console.log(`Failed human-review revision preserved: ${contract.failedHumanReviewRevision}`);
console.log('Machine verification does not satisfy the required human re-review.');
