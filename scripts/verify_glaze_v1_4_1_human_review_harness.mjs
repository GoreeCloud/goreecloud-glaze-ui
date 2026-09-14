#!/usr/bin/env node
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

async function text(relative) {
  return readFile(path.join(ROOT, relative), 'utf8');
}

async function json(relative) {
  return JSON.parse(await text(relative));
}

function sorted(values) {
  return [...values].sort();
}

async function main() {
  const contract = await json('contracts/v1.4.1/human-review-harness.contract.json');
  const humanContract = await json('contracts/v1.4.1/human-validation.contract.json');
  const lifecycle = await json('registry/lifecycle.json');
  const html = await text(contract.harness);

  assert.equal(contract.version, '1.4.1-candidate');
  assert.equal(contract.stableBaseline, '1.4.0');
  assert.equal(contract.authority, 'human-review-surface-only');
  assert.equal(contract.networkPolicy, 'repository-local-only');
  assert.equal(contract.simulatedFormFactorsArePhysicalEvidence, false);
  assert.equal(contract.automaticHumanAcceptance, false);
  assert.equal(contract.automaticPromotionEligibility, false);

  assert.equal(lifecycle.currentStable, '1.4.0');
  assert.equal(lifecycle.currentOfficial, '1.4.0');
  assert.equal(lifecycle.plannedNext, '1.4.1-candidate');
  assert.equal(lifecycle.activeCandidate, null);

  const canonicalIds = new Set(humanContract.requiredChecks.map(check => check.id));
  assert.equal(canonicalIds.size, 34, 'human-validation authority must still contain exactly 34 canonical checks');
  assert.ok(contract.reviewChecks.length > 0, 'review harness must scope at least one human check');
  assert.equal(new Set(contract.reviewChecks).size, contract.reviewChecks.length, 'review harness check IDs must be unique');
  for (const id of contract.reviewChecks) assert.ok(canonicalIds.has(id), `review harness check is not canonical: ${id}`);

  for (const id of contract.reviewChecks) {
    assert.ok(html.includes(id), `review harness must visibly enumerate ${id}`);
  }
  for (const scenario of contract.requiredScenarios) {
    const marker = scenario.replace(/^background-/, '').replace(/^appearance-/, '').replace(/^daypart-/, '').replace(/^depth-/, '');
    assert.ok(html.toLowerCase().includes(marker.split('-')[0]), `review harness appears to omit required scenario ${scenario}`);
  }
  for (const factor of contract.formFactorSimulations) {
    assert.ok(html.includes(`data-form-factor="${factor}"`), `review harness must include ${factor} simulation`);
  }

  assert.match(html, /Human review surface only — not acceptance evidence\./i);
  assert.match(html, /not physical-device evidence/i);
  assert.match(html, /Human result: PENDING/i);
  assert.match(html, /UNBOUND — review is not exact-revision evidence/i);
  assert.match(html, /\?revision=&lt;40-hex-sha&gt;/i);
  assert.match(html, /\.\.\/\.\.\/css\/glaze-v1\.4\.0\.css/);
  assert.match(html, /\.\.\/\.\.\/js\/glaze-v1\.4\.1\.candidate\.mjs/);
  assert.match(html, /createGlazeOpticalEngineV141Candidate/);
  assert.match(html, /adapterFailure/);
  assert.match(html, /throw new Error\('review-harness synthetic adapter fault'\)/);
  assert.match(html, /reducedTransparency/);
  assert.match(html, /increasedContrast/);
  assert.match(html, /forcedColors/);
  assert.match(html, /reducedMotion/);
  assert.match(html, /memoryTint/);
  assert.match(html, /semanticImportance/);

  const forbiddenRemotePatterns = [
    /https?:\/\//i,
    /src\s*=\s*["']\/\//i,
    /href\s*=\s*["']\/\//i,
    /fetch\s*\(/i,
    /XMLHttpRequest/i,
    /WebSocket/i,
    /sendBeacon/i,
    /navigator\.mediaDevices/i,
    /getUserMedia/i
  ];
  for (const pattern of forbiddenRemotePatterns) {
    assert.equal(pattern.test(html), false, `review harness violates local-only/no-telemetry boundary: ${pattern}`);
  }

  const forbiddenEvidenceControls = [
    /mark\s+passed/i,
    /accept\s+review/i,
    /promotionEligible\s*[:=]\s*true/i,
    /recordType\s*[:=]/i,
    /evidenceType\s*[:=]\s*["']human/i
  ];
  for (const pattern of forbiddenEvidenceControls) {
    assert.equal(pattern.test(html), false, `review harness must not create or imply human evidence: ${pattern}`);
  }

  assert.deepEqual(sorted(contract.reviewChecks), sorted([
    'optical.content-aware-frost',
    'optical.semantic-blur-protection',
    'optical.environment-tint',
    'optical.chromatic-depth',
    'optical.environmental-color-memory',
    'accessibility.reduced-transparency',
    'accessibility.increased-contrast',
    'accessibility.forced-colors',
    'accessibility.reduced-motion',
    'input.keyboard',
    'input.pointer',
    'polish.glass-quality',
    'polish.depth-warmth',
    'polish.visual-balance',
    'identity.goreecloud-recognition'
  ]));

  console.log(`GLAZE UI V1.4.1 human review harness: PASS (${contract.reviewChecks.length} scoped human checks).`);
  console.log('Boundary: this verifies only the review surface. No human observation, physical-device result, acceptance decision, or promotion eligibility is implied.');
}

main().catch(error => {
  console.error(`GLAZE UI V1.4.1 human review harness FAILED: ${error?.stack || error}`);
  process.exitCode = 1;
});
