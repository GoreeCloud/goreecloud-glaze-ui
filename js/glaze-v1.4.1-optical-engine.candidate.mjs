import {
  applyGlazeOptics,
  resolveGlazeOptics,
  glazeOpticalEngineV14
} from './glaze-v1.4-optical-engine.mjs';

function asObject(value) {
  return value && typeof value === 'object' ? value : {};
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

function decorateResult(resolved, adapterStatus) {
  return Object.freeze({
    ...resolved,
    adapterStatus,
    adapterFailureMode: adapterStatus === 'failed-safe' ? 'solid-accessible' : null
  });
}

function targetRoot(target) {
  return target?.documentElement || target;
}

/**
 * GLAZE UI V1.4.1 Candidate optical-engine hardening.
 *
 * This wrapper preserves the V1.4.0 resolver as the optical authority and adds
 * an explicit fail-safe boundary around consumer signal adapters. It does not
 * collect context, telemetry, analytics, camera data, or remote state.
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
    resolve(overrides = {}) {
      const {adapterState, inputs} = stateAndInputs(overrides);
      return decorateResult(resolveGlazeOptics(inputs), adapterState.status);
    },
    apply(target, overrides = {}) {
      const {adapterState, inputs} = stateAndInputs(overrides);
      const resolved = applyGlazeOptics(target, inputs);
      const element = targetRoot(target);
      // Expose only bounded status, never the thrown error/message/stack.
      element.dataset.glazeOpticalV141Adapter = adapterState.status;
      return decorateResult(resolved, adapterState.status);
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
  maxMemoryTintInfluence: glazeOpticalEngineV14.maxMemoryTintInfluence,
  humanAcceptanceAutomatic: false,
  patchPromotionAutomatic: false
});
