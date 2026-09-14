#!/usr/bin/env node
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

import {
  createGlazeOpticalEngine,
  glazeOpticalEngineV14
} from '../js/glaze-v1.4-optical-engine.mjs';
import {
  createGlazeOpticalEngineV141Candidate,
  glazeOpticalEngineV141Candidate
} from '../js/glaze-v1.4.1-optical-engine.candidate.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

async function json(relative) {
  return JSON.parse(await readFile(path.join(ROOT, relative), 'utf8'));
}

function gitBlobSha(relative) {
  return execFileSync('git', ['hash-object', relative], {
    cwd: ROOT,
    encoding: 'utf8'
  }).trim();
}

function fakeTarget() {
  const properties = new Map();
  return {
    dataset: {},
    style: {
      setProperty(name, value) {
        properties.set(name, value);
      }
    },
    properties
  };
}

function assertSolidAccessible(result) {
  assert.equal(result.mode, 'solid-accessible');
  assert.equal(result.blurScale, 0);
  assert.equal(result.semanticProtection, 1);
  assert.equal(result.memoryTint, null);
  assert.equal(result.decorativeTintAllowed, false);
  assert.equal(result.accessibility.forcedColors, true);
  assert.equal(result.accessibility.reducedTransparency, true);
}

async function main() {
  const lifecycle = await json('registry/lifecycle.json');
  const contract = await json('contracts/v1.4.1/optical-runtime-hardening.contract.json');

  assert.equal(lifecycle.currentStable, '1.4.0');
  assert.equal(lifecycle.currentOfficial, '1.4.0');
  assert.equal(lifecycle.plannedNext, '1.4.1-candidate');
  assert.equal(lifecycle.activeCandidate, null);

  assert.equal(glazeOpticalEngineV14.version, '1.4.0');
  assert.equal(glazeOpticalEngineV14.lifecycle, 'stable');
  assert.equal(glazeOpticalEngineV14.telemetryRequired, false);
  assert.equal(glazeOpticalEngineV14.remoteContextRequired, false);

  assert.equal(contract.version, '1.4.1-candidate');
  assert.equal(contract.stableBaseline, '1.4.0');
  assert.equal(contract.rules['v1.4.0StableSourceImmutable'], true);
  assert.equal(contract.rules.adapterResolveExceptionMayEscape, false);
  assert.equal(contract.rules.adapterFailureMode, 'solid-accessible');
  assert.equal(contract.rules.consumerOverridesMayDisableFailureFallback, false);
  assert.equal(contract.rules.adapterErrorObserverFailureMayEscape, false);
  assert.equal(contract.rules.telemetryRequired, false);
  assert.equal(contract.rules.remoteContextRequired, false);
  assert.equal(contract.rules.humanAcceptanceAutomatic, false);
  assert.equal(contract.rules.patchPromotionAutomatic, false);

  assert.equal(gitBlobSha(contract.stableEngine), contract.stableEngineBlobSha);
  assert.equal(gitBlobSha(contract.stableEntrypoint), contract.stableEntrypointBlobSha);

  assert.equal(glazeOpticalEngineV141Candidate.version, '1.4.1-candidate');
  assert.equal(glazeOpticalEngineV141Candidate.lifecycle, 'candidate-hardening');
  assert.equal(glazeOpticalEngineV141Candidate.stableBaseline, '1.4.0');
  assert.equal(glazeOpticalEngineV141Candidate.preservesStableEngineSource, true);
  assert.equal(glazeOpticalEngineV141Candidate.telemetryRequired, false);
  assert.equal(glazeOpticalEngineV141Candidate.remoteContextRequired, false);
  assert.equal(glazeOpticalEngineV141Candidate.adapterFailurePolicy, 'solid-accessible');
  assert.equal(glazeOpticalEngineV141Candidate.humanAcceptanceAutomatic, false);
  assert.equal(glazeOpticalEngineV141Candidate.patchPromotionAutomatic, false);

  const normal = createGlazeOpticalEngineV141Candidate({
    signalAdapter: {
      resolve() {
        return {
          backgroundComplexity: 'complex',
          backgroundLuminance: 'bright',
          appearance: 'dark',
          memoryTint: {css: 'rgb(12 34 56)', influence: 0.07}
        };
      }
    }
  }).resolve();
  assert.equal(normal.mode, 'adaptive-optical');
  assert.equal(normal.adapterStatus, 'resolved');
  assert.equal(normal.adapterFailureMode, null);
  assert.equal(normal.appearance, 'dark');
  assert.equal(normal.backgroundComplexity, 'complex');
  assert.equal(normal.memoryTint?.influence, 0.07);

  const malformed = createGlazeOpticalEngineV141Candidate({
    signalAdapter: {resolve: () => null}
  }).resolve();
  assert.equal(malformed.mode, 'adaptive-optical');
  assert.equal(malformed.adapterStatus, 'resolved');
  assert.equal(malformed.backgroundComplexity, 'unknown');

  const expectedError = new Error('private adapter detail must not reach DOM state');
  let observedError = null;
  let observerCount = 0;
  const failingEngine = createGlazeOpticalEngineV141Candidate({
    signalAdapter: {
      resolve() {
        throw expectedError;
      }
    },
    onAdapterError(error) {
      observerCount += 1;
      observedError = error;
    }
  });

  const failed = failingEngine.resolve({
    accessibility: {forcedColors: false, reducedTransparency: false},
    memoryTint: {css: 'rgb(255 0 0)', influence: 0.08},
    backgroundComplexity: 'complex'
  });
  assertSolidAccessible(failed);
  assert.equal(failed.adapterStatus, 'failed-safe');
  assert.equal(failed.adapterFailureMode, 'solid-accessible');
  assert.equal(observerCount, 1);
  assert.equal(observedError, expectedError);

  const observerFailure = createGlazeOpticalEngineV141Candidate({
    signalAdapter: {resolve: () => { throw new Error('adapter'); }},
    onAdapterError() {
      throw new Error('observer');
    }
  }).resolve();
  assertSolidAccessible(observerFailure);
  assert.equal(observerFailure.adapterStatus, 'failed-safe');

  const target = fakeTarget();
  const applied = failingEngine.apply(target, {
    accessibility: {forcedColors: false, reducedTransparency: false},
    memoryTint: {css: 'rgb(1 2 3)', influence: 0.08}
  });
  assertSolidAccessible(applied);
  assert.equal(target.dataset.glazeOpticalV14, 'solid-accessible');
  assert.equal(target.dataset.glazeOpticalV141Adapter, 'failed-safe');
  assert.equal(target.properties.get('--glz14-blur-scale'), '0');
  assert.equal(target.properties.get('--glz14-memory-tint'), 'transparent');
  assert.equal(target.properties.get('--glz14-memory-tint-influence'), '0');
  assert.equal(JSON.stringify(target.dataset).includes(expectedError.message), false);

  const noAdapter = createGlazeOpticalEngineV141Candidate().resolve({appearance: 'deep-dark'});
  assert.equal(noAdapter.mode, 'adaptive-optical');
  assert.equal(noAdapter.adapterStatus, 'not-configured');
  assert.equal(noAdapter.appearance, 'deep-dark');

  // Stable V1.4.0 behavior remains independently callable and is not rewritten
  // as V1.4.1 acceptance by the candidate wrapper.
  const stable = createGlazeOpticalEngine().resolve({appearance: 'dark'});
  assert.equal(stable.mode, 'adaptive-optical');
  assert.equal(stable.appearance, 'dark');
  assert.equal('adapterStatus' in stable, false);

  console.log('GLAZE UI V1.4.1 optical runtime hardening: PASS');
  console.log('Boundary: adapter faults fail safe to solid-accessible; V1.4.0 Stable blobs remain immutable; human V1.4.1 acceptance is not implied.');
}

main().catch((error) => {
  console.error(`GLAZE UI V1.4.1 optical runtime hardening FAILED: ${error?.stack || error}`);
  process.exitCode = 1;
});
