import {
  applyGlazeOptics,
  resolveGlazeOptics,
  glazeOpticalEngineV14
} from './glaze-v1.4-optical-engine.mjs';

const APPEARANCES = new Set(['light', 'dark', 'deep-dark']);

function asObject(value) {
  return value && typeof value === 'object' ? value : {};
}

function clamp(value, min = 0, max = 1) {
  const number = Number(value);
  if (!Number.isFinite(number)) return min;
  return Math.min(max, Math.max(min, number));
}

function notifyAdapterError(observer, error) {
  if (typeof observer !== 'function') return;
  try {
    observer(error);
  } catch {
    // Observation is non-authoritative. A failing observer must never defeat
    // the fail-safe optical fallback or escape into the consumer runtime.
  }
}

function readAdapter(signalAdapter, onAdapterError) {
  if (typeof signalAdapter?.resolve !== 'function') {
    return Object.freeze({status: 'not-configured', signals: Object.freeze({})});
  }

  try {
    return Object.freeze({
      status: 'resolved',
      signals: Object.freeze({...asObject(signalAdapter.resolve())})
    });
  } catch (error) {
    notifyAdapterError(onAdapterError, error);
    return Object.freeze({status: 'failed-safe', signals: Object.freeze({})});
  }
}

function composeInputs(adapterState, overrides) {
  const merged = {...adapterState.signals, ...asObject(overrides)};
  if (adapterState.status !== 'failed-safe') return merged;

  // An adapter exception means contextual/accessibility signal authority could
  // not be established. Fail closed into the existing V1.4 solid-accessible
  // mode. These forced flags are applied after consumer overrides so a caller
  // cannot accidentally or deliberately restore decorative optics after the
  // adapter fault.
  merged.accessibility = {
    ...asObject(merged.accessibility),
    forcedColors: true,
    reducedTransparency: true
  };
  merged.memoryTint = null;
  return merged;
}

function effectiveAppearance(resolved, inputs) {
  if (APPEARANCES.has(resolved.appearance)) return resolved.appearance;
  if (APPEARANCES.has(inputs.appearance)) return inputs.appearance;
  return 'light';
}

function semanticSurfaceStrength(resolved, appearance) {
  if (resolved.mode === 'solid-accessible') return 1;

  const protection = clamp(resolved.semanticProtection, 0.5, 1);
  if (appearance === 'light') return clamp(0.58 + protection * 0.34, 0.75, 0.94);
  if (appearance === 'deep-dark') return clamp(0.44 + protection * 0.30, 0.62, 0.82);
  return clamp(0.40 + protection * 0.30, 0.60, 0.80);
}

function decorateResult(resolved, adapterStatus, inputs) {
  const appearance = effectiveAppearance(resolved, inputs);
  return Object.freeze({
    ...resolved,
    appearance,
    semanticSurfaceStrength: semanticSurfaceStrength(resolved, appearance),
    adapterStatus,
    adapterFailureMode: adapterStatus === 'failed-safe' ? 'solid-accessible' : null
  });
}

function targetRoot(target) {
  return target?.documentElement || target;
}

function applyCandidatePresentation(element, resolved) {
  element.dataset.glazeOpticalV141Appearance = resolved.appearance;
  element.style.setProperty(
    '--glz141-semantic-surface-strength',
    `${(resolved.semanticSurfaceStrength * 100).toFixed(2)}%`
  );
}

/**
 * GLAZE UI V1.4.1 Candidate optical-engine hardening.
 *
 * This wrapper preserves the V1.4.0 resolver as the optical authority and adds
 * explicit fail-safe adapter handling plus bounded semantic readability
 * presentation state. It does not collect context, telemetry, analytics,
 * camera data, or remote state.
 */
export function createGlazeOpticalEngineV141Candidate(options = {}) {
  const input = asObject(options);
  const signalAdapter = input.signalAdapter ?? null;
  const onAdapterError = typeof input.onAdapterError === 'function' ? input.onAdapterError : null;

  function stateAndInputs(overrides = {}) {
    const adapterState = readAdapter(signalAdapter, onAdapterError);
    return Object.freeze({
      adapterState,
      inputs: composeInputs(adapterState, overrides)
    });
  }

  return Object.freeze({
    kind: 'glaze-optical-engine-v1.4.1-candidate',
    stableBaseline: '1.4.0',
    telemetryRequired: false,
    remoteContextRequired: false,
    adapterFailurePolicy: 'solid-accessible',
    semanticSurfaceProtection: true,
    resolve(overrides = {}) {
      const {adapterState, inputs} = stateAndInputs(overrides);
      return decorateResult(resolveGlazeOptics(inputs), adapterState.status, inputs);
    },
    apply(target, overrides = {}) {
      const {adapterState, inputs} = stateAndInputs(overrides);
      const stableResolved = applyGlazeOptics(target, inputs);
      const resolved = decorateResult(stableResolved, adapterState.status, inputs);
      const element = targetRoot(target);
      // Expose only bounded status/presentation state, never raw adapter error
      // details, messages, stacks, or untrusted context.
      element.dataset.glazeOpticalV141Adapter = adapterState.status;
      applyCandidatePresentation(element, resolved);
      return resolved;
    }
  });
}

export const glazeOpticalEngineV141Candidate = Object.freeze({
  version: '1.4.1-candidate',
  lifecycle: 'candidate-hardening',
  stableBaseline: glazeOpticalEngineV14.version,
  preservesStableEngineSource: true,
  telemetryRequired: false,
  remoteContextRequired: false,
  adapterFailurePolicy: 'solid-accessible',
  adapterFailureAllowsBlur: false,
  adapterFailureAllowsDecorativeTint: false,
  semanticSurfaceProtection: true,
  maxMemoryTintInfluence: glazeOpticalEngineV14.maxMemoryTintInfluence,
  humanAcceptanceAutomatic: false,
  patchPromotionAutomatic: false
});
