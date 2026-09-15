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

async function main() {
  const contract = await json('contracts/v1.5/human-review-harness.dev.json');
  const stabilization = await json('contracts/v1.5/stabilization-review.dev.json');
  const html = await text(contract.harness);

  assert.equal(contract.version, '1.5.0-dev.1');
  assert.equal(contract.lifecycle, 'Development');
  assert.equal(contract.stableBaseline, '1.4.1');
  assert.equal(contract.authority, 'human-review-surface-only');
  assert.equal(contract.networkPolicy, 'repository-local-only');
  assert.equal(contract.automaticHumanAcceptance, false);
  assert.equal(contract.automaticPromotionEligibility, false);
  assert.equal(contract.candidateRuntime, 'js/glaze-v1.5-resolution.dev.mjs');

  const canonicalCheckIds = new Set(
    stabilization.requiredEvidenceAreas.flatMap(area => area.checks.map(check => check.id))
  );
  assert.equal(canonicalCheckIds.size, 18, 'stabilization contract must retain exactly 18 canonical external review checks');
  assert.equal(new Set(contract.reviewChecks).size, contract.reviewChecks.length, 'review harness check IDs must be unique');
  for (const id of contract.reviewChecks) {
    assert.ok(canonicalCheckIds.has(id), `review harness references a non-canonical check: ${id}`);
    assert.ok(html.includes(id), `review harness must visibly enumerate canonical check ${id}`);
  }

  assert.deepEqual(contract.reviewChecks, [
    'human-usability-state-explanations',
    'human-usability-action-stability',
    'human-usability-task-continuity',
    'accessibility-keyboard-focus',
    'accessibility-semantic-announcement'
  ]);

  const scenarioMarkers = new Map([
    ['connectivity-online', '<option value="online">Online</option>'],
    ['connectivity-offline', '<option value="offline">Offline</option>'],
    ['authorization-permission-required', '<option value="permission-required">Permission required</option>'],
    ['authorization-available', '<option value="available">Available</option>'],
    ['policy-restricted', '<option value="restricted">Restricted</option>'],
    ['policy-available', "$('policy-state').value"],
    ['service-degraded', '<option value="degraded">Degraded</option>'],
    ['service-available', "$('search-state').value"],
    ['layout-compact', '<option value="compact">Compact</option>'],
    ['layout-expanded', '<option value="expanded">Expanded</option>'],
    ['reduced-motion-on', '<option value="true">On</option>'],
    ['reduced-motion-off', '<option value="false">Off</option>']
  ]);
  assert.deepEqual([...scenarioMarkers.keys()], contract.requiredScenarios, 'review scenario contract and verifier markers must stay aligned');
  for (const [scenario, marker] of scenarioMarkers) {
    assert.ok(html.includes(marker), `review harness appears to omit scenario ${scenario}`);
  }

  assert.match(html, /Human review surface only — not acceptance evidence\./i);
  assert.match(html, /Human result:<\/strong>\s*<span[^>]*>PENDING<\/span>/i);
  assert.match(html, /UNBOUND — review is not exact-revision evidence/i);
  assert.match(html, /\?revision=&lt;40-hex-sha&gt;/i);
  assert.match(html, /\.\.\/\.\.\/css\/glaze-v1\.4\.1\.css/);
  assert.match(html, /import\s*\{\s*resolveGlazeInterface\s*\}\s*from\s*['"]\.\.\/\.\.\/js\/glaze-v1\.5-resolution\.dev\.mjs['"]/);
  assert.match(html, /resolveGlazeInterface\s*\(/);
  assert.match(html, /id="task-text"/);
  assert.match(html, /id="focus-readout"/);
  assert.match(html, /role="status"/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /:focus-visible/);
  assert.match(html, /requestAnimationFrame\s*\(/);
  assert.match(html, /primaryActionIds/);
  assert.match(html, /primaryActionOrderStable/);
  assert.match(html, /taskStateReset/);
  assert.match(html, /pageReloadRequired/);
  assert.match(html, /automaticNavigationAllowed/);
  assert.match(html, /automaticPermissionRequestAllowed/);
  assert.match(html, /automaticConsequentialExecutionAllowed/);
  assert.match(html, /automaticFallbackExecutionAllowed/);

  const forbiddenRemotePatterns = [
    /<script[^>]+src\s*=\s*["']https?:\/\//i,
    /<link[^>]+href\s*=\s*["']https?:\/\//i,
    /<img[^>]+src\s*=\s*["']https?:\/\//i,
    /fetch\s*\(/i,
    /XMLHttpRequest/i,
    /WebSocket/i,
    /sendBeacon/i,
    /navigator\.mediaDevices/i,
    /getUserMedia/i
  ];
  for (const pattern of forbiddenRemotePatterns) {
    assert.equal(pattern.test(html), false, `review harness violates repository-local/no-telemetry boundary: ${pattern}`);
  }

  const forbiddenEvidenceControls = [
    /mark\s+passed/i,
    /accept\s+review/i,
    /promotionEligible\s*[:=]\s*true/i,
    /releaseCandidate\s*[:=]\s*true/i,
    /stable\s*[:=]\s*true/i,
    /recordType\s*[:=]/i,
    /evidenceType\s*[:=]\s*["']human/i
  ];
  for (const pattern of forbiddenEvidenceControls) {
    assert.equal(pattern.test(html), false, `review harness must not create or imply human evidence: ${pattern}`);
  }

  assert.equal(stabilization.releaseLifecycle, 'Development');
  assert.equal(stabilization.promotionEligible, false);
  assert.equal(stabilization.consumerEligible, false);
  assert.equal(stabilization.releaseCandidate, false);
  assert.equal(stabilization.stable, false);

  console.log(`GLAZE UI 1.5.0-dev.1 human review harness structural verification: PASS (${contract.reviewChecks.length} represented checks).`);
  console.log('Boundary: this verifies only the repository-local review surface and exact Development contract linkage.');
  console.log('No human observation, assistive-technology result, physical-device result, acceptance decision, or lifecycle promotion is implied.');
}

main().catch(error => {
  console.error(`GLAZE UI V1.5 human review harness FAILED: ${error?.stack || error}`);
  process.exitCode = 1;
});
