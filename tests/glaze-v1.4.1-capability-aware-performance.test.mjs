import test from 'node:test';
import assert from 'node:assert/strict';

import {
  GLAZE_OPTICAL_PERFORMANCE_LEVELS,
  createGlazeOpticalEngineV141Candidate,
  createGlazeOpticalPerformanceGovernor,
  deriveGlazeOpticalPerformanceLevel
} from '../js/glaze-v1.4.1-optical-engine.candidate.mjs';

function target() {
  const properties = new Map();
  return {
    dataset: {},
    style: {
      setProperty(name, value) {
        properties.set(name, String(value));
      }
    },
    properties
  };
}

test('V1.4.1 exposes the canonical four optical performance levels', () => {
  assert.deepEqual(GLAZE_OPTICAL_PERFORMANCE_LEVELS, [
    'full-optical',
    'balanced-optical',
    'efficient-optical',
    'durable-optical'
  ]);
});

test('unconfigured performance authority preserves Full Optical behavior', () => {
  const engine = createGlazeOpticalEngineV141Candidate();
  const resolved = engine.resolve({
    appearance: 'dark',
    backgroundComplexity: 'moderate',
    backgroundLuminance: 'mid'
  });

  assert.equal(resolved.performance.requestedLevel, 'full-optical');
  assert.equal(resolved.performance.acceptedLevel, 'full-optical');
  assert.equal(resolved.performance.downgraded, false);
  assert.equal(resolved.performanceAdapterStatus, 'not-configured');
});

test('older-device Session 005 sample maps to Balanced Optical without model heuristics', () => {
  const derived = deriveGlazeOpticalPerformanceLevel({
    targetFrameMs: 11.18,
    p95FrameMs: 22.22,
    slowFrameShare: 0.128,
    degradation: 0,
    longTasks: 0
  });

  assert.equal(derived.capabilityLevel, 'balanced-optical');
  assert.ok(derived.pressure > 0);
});

test('low-cost Android Session 005 sample maps to Efficient Optical without model heuristics', () => {
  const derived = deriveGlazeOpticalPerformanceLevel({
    targetFrameMs: 11.12,
    p95FrameMs: 33.28,
    slowFrameShare: 0.21,
    degradation: 0,
    longTasks: 0
  });

  assert.equal(derived.capabilityLevel, 'efficient-optical');
  assert.ok(derived.pressure >= 0.4);
});

test('local governor is downgrade-only within a session and remains non-persistent', () => {
  const governor = createGlazeOpticalPerformanceGovernor();
  assert.equal(governor.localOnly, true);
  assert.equal(governor.persistent, false);
  assert.equal(governor.telemetryRequired, false);

  governor.observe({targetFrameMs: 11.12, p95FrameMs: 33.28, slowFrameShare: 0.21});
  assert.equal(governor.resolve().capabilityLevel, 'efficient-optical');

  // A later easy sample must not oscillate the material back up mid-session.
  governor.observe({targetFrameMs: 11.12, p95FrameMs: 11.5, slowFrameShare: 0});
  assert.equal(governor.resolve().capabilityLevel, 'efficient-optical');

  governor.reset();
  assert.equal(governor.resolve().capabilityLevel, 'full-optical');
});

test('performance adapter can accept a lower-cost tier and runtime exposes it truthfully', () => {
  const governor = createGlazeOpticalPerformanceGovernor();
  governor.observe({targetFrameMs: 11.12, p95FrameMs: 33.28, slowFrameShare: 0.21});
  const engine = createGlazeOpticalEngineV141Candidate({performanceAdapter: governor});
  const resolved = engine.resolve({appearance: 'dark'});

  assert.equal(resolved.performanceAdapterStatus, 'resolved');
  assert.equal(resolved.performance.requestedLevel, 'full-optical');
  assert.equal(resolved.performance.acceptedLevel, 'efficient-optical');
  assert.equal(resolved.performance.downgraded, true);
  assert.ok(resolved.blurScale < 0.35);
  assert.ok(resolved.performance.samplingScale <= 0.15);
  assert.ok(resolved.performance.reflectionScale <= 0.15);
});

test('apply writes accepted tier and bounded cost controls to the target', () => {
  const governor = createGlazeOpticalPerformanceGovernor();
  governor.observe({targetFrameMs: 11.12, p95FrameMs: 33.28, slowFrameShare: 0.21});
  const engine = createGlazeOpticalEngineV141Candidate({performanceAdapter: governor});
  const root = target();
  const resolved = engine.apply(root, {appearance: 'light'});

  assert.equal(root.dataset.glazeOpticalV141Performance, 'efficient-optical');
  assert.equal(root.dataset.glazeOpticalV141PerformanceAdapter, 'resolved');
  assert.equal(root.properties.get('--glz14-blur-scale'), String(resolved.blurScale));
  assert.equal(root.properties.get('--glz141-sampling-scale'), '0.15');
  assert.equal(root.properties.get('--glz141-reflection-scale'), '0.15');
});

test('accessibility solid authority always resolves to Durable Optical with zero blur', () => {
  const engine = createGlazeOpticalEngineV141Candidate({
    performanceAdapter: {
      resolve() {
        return {requestedLevel: 'full-optical', capabilityLevel: 'full-optical'};
      }
    }
  });
  const resolved = engine.resolve({
    accessibility: {reducedTransparency: true}
  });

  assert.equal(resolved.mode, 'solid-accessible');
  assert.equal(resolved.performance.acceptedLevel, 'durable-optical');
  assert.equal(resolved.blurScale, 0);
  assert.equal(resolved.semanticSurfaceStrength, 1);
});

test('failed configured performance adapter degrades conservatively instead of claiming Full', () => {
  const engine = createGlazeOpticalEngineV141Candidate({
    performanceAdapter: {
      resolve() {
        throw new Error('adapter failed');
      }
    }
  });
  const resolved = engine.resolve({appearance: 'dark'});

  assert.equal(resolved.performanceAdapterStatus, 'failed-safe');
  assert.equal(resolved.performance.acceptedLevel, 'balanced-optical');
  assert.equal(resolved.performance.downgraded, true);
  assert.ok(resolved.performance.downgradeReasons.includes('performance-adapter-failed-safe'));
});
