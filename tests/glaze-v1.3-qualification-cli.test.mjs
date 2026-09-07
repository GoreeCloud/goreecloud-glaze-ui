import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CLI = path.join(ROOT, 'scripts/evaluate_glaze_v1_3_qualification.mjs');
const SOURCE = 'a'.repeat(40);
const WORKSTREAMS = [
  'human-optical-and-icon-collision-qualification',
  'manual-assistive-technology-qualification',
  'physical-device-native-platform-qualification',
  'physical-device-production-performance-qualification',
  'native-personalization-adapter-qualification',
  'stable-activation-and-source-namespace-cleanup'
];
const REVIEW_MODE = {
  'human-optical-and-icon-collision-qualification': 'human',
  'manual-assistive-technology-qualification': 'human',
  'physical-device-native-platform-qualification': 'combined',
  'physical-device-production-performance-qualification': 'combined',
  'native-personalization-adapter-qualification': 'combined',
  'stable-activation-and-source-namespace-cleanup': 'combined'
};

function run(args) {
  return spawnSync(process.execPath, [CLI, ...args], {encoding: 'utf8'});
}

function passedRecord(id) {
  return {
    schema_version: 1,
    workstream_id: id,
    target: {product: 'GLAZE UI V1.3', target_version: '1.3.0-candidate', source_revision: SOURCE},
    status: 'passed',
    observed_at: '2026-09-06T18:00:00Z',
    valid_until: null,
    review_authority: {mode: REVIEW_MODE[id], authority: 'authorized qualification review'},
    evidence_references: [`evidence/${id}/primary`, `evidence/${id}/review`],
    issues: [],
    disposition: {accepted_for_lifecycle_gate: true, notes: 'qualification gate only'}
  };
}

test('CLI reports blocked without treating expected missing evidence as an execution error', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'glaze-q-empty-'));
  try {
    const result = run(['--source-revision', SOURCE, '--evidence-dir', dir, '--evaluated-at', '2026-09-06T19:00:00Z']);
    assert.equal(result.status, 0, result.stderr);
    const payload = JSON.parse(result.stdout);
    assert.equal(payload.result.state, 'blocked');
    assert.equal(payload.result.acceptedWorkstreamCount, 0);
    assert.equal(payload.evidenceFiles.length, 0);
  } finally {
    rmSync(dir, {recursive: true, force: true});
  }
});

test('CLI require-ready mode fails closed with exit 2 when qualification is blocked', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'glaze-q-blocked-'));
  try {
    const result = run(['--source-revision', SOURCE, '--evidence-dir', dir, '--require-ready']);
    assert.equal(result.status, 2);
    assert.equal(JSON.parse(result.stdout).result.qualificationGateSatisfied, false);
  } finally {
    rmSync(dir, {recursive: true, force: true});
  }
});

test('CLI require-ready mode succeeds only with all six accepted records for the supplied revision', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'glaze-q-ready-'));
  try {
    for (const id of WORKSTREAMS) writeFileSync(path.join(dir, `${id}.json`), JSON.stringify(passedRecord(id)));
    const result = run([
      '--source-revision', SOURCE,
      '--evidence-dir', dir,
      '--evaluated-at', '2026-09-06T19:00:00Z',
      '--require-ready'
    ]);
    assert.equal(result.status, 0, result.stderr);
    const payload = JSON.parse(result.stdout);
    assert.equal(payload.result.state, 'ready-for-governed-candidate-promotion-review');
    assert.equal(payload.result.acceptedWorkstreamCount, 6);
    assert.equal(payload.result.lifecyclePromotionGranted, false);
    assert.equal(payload.result.candidateActivated, false);
  } finally {
    rmSync(dir, {recursive: true, force: true});
  }
});

test('CLI rejects malformed source revision before evidence evaluation', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'glaze-q-sha-'));
  try {
    const result = run(['--source-revision', 'not-a-sha', '--evidence-dir', dir]);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /40-character Git SHA/);
  } finally {
    rmSync(dir, {recursive: true, force: true});
  }
});
