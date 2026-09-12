import {
  opticalRuntimeCandidate,
  resolveOpticalRuntime
} from './glaze-v1.4-optical-runtime.candidate.mjs';

function rootOf(target) {
  if (!target) throw new TypeError('A V1.4 optical web target is required');
  return target.documentElement || target;
}

function onOff(value) {
  return value ? 'on' : 'off';
}

/**
 * Project an already-resolved V1.4 semantic optical state into a Web surface.
 *
 * This adapter is intentionally presentation-only. It does not sample pixels,
 * perform analytics, infer operational authority, or promote V1.4 lifecycle state.
 */
export function applyResolvedOpticalWebState(target, resolved) {
  const element = rootOf(target);
  if (!element.dataset || !element.style || typeof element.style.setProperty !== 'function') {
    throw new TypeError('V1.4 optical web target must expose dataset and style.setProperty');
  }
  if (!resolved?.accepted?.effects) {
    throw new TypeError('A resolved V1.4 semantic optical result is required');
  }

  const accepted = resolved.accepted;
  const effects = accepted.effects;

  element.dataset.glazeV14Renderer = 'web-candidate';
  element.dataset.glazeV14Material = accepted.materialRole;
  element.dataset.glazeV14Elevation = accepted.elevationRole;
  element.dataset.glazeV14Interaction = accepted.interactionState;
  element.dataset.glazeV14Appearance = accepted.appearanceMode;
  element.dataset.glazeV14Accessibility = accepted.accessibilityProfile;
  element.dataset.glazeV14Performance = accepted.performanceLevel;
  element.dataset.glazeV14Disposition = resolved.disposition;
  element.dataset.glazeV14Profile = resolved.effectiveOpticalProfile;
  element.dataset.glazeV14Rendering = accepted.renderingMode;
  element.dataset.glazeV14Environment = accepted.environmentalResponse.mode;
  element.dataset.glazeV14Translucency = onOff(effects.translucency);
  element.dataset.glazeV14BackdropBlur = onOff(effects.backdropBlur);
  element.dataset.glazeV14Reflection = onOff(effects.reflection);
  element.dataset.glazeV14Aura = onOff(effects.aura);
  element.dataset.glazeV14EdgeIllumination = onOff(effects.edgeIllumination);
  element.dataset.glazeV14MaterialMotion = onOff(effects.materialAwareMotion);
  element.dataset.glazeV14EnvironmentalSampling = onOff(effects.environmentalSampling);

  element.style.setProperty('--glz14-optical-profile', resolved.effectiveOpticalProfile);
  element.style.setProperty('--glz14-translucency-enabled', effects.translucency ? '1' : '0');
  element.style.setProperty('--glz14-backdrop-blur-enabled', effects.backdropBlur ? '1' : '0');
  element.style.setProperty('--glz14-environmental-sampling-enabled', effects.environmentalSampling ? '1' : '0');
  element.style.setProperty('--glz14-reflection-enabled', effects.reflection ? '1' : '0');
  element.style.setProperty('--glz14-aura-enabled', effects.aura ? '1' : '0');
  element.style.setProperty('--glz14-material-motion-enabled', effects.materialAwareMotion ? '1' : '0');

  return resolved;
}

export function applyOpticalWebRuntime(target, request = {}) {
  return applyResolvedOpticalWebState(target, resolveOpticalRuntime(request));
}

export function createOpticalWebAdapter({capabilityAdapter = null} = {}) {
  return Object.freeze({
    kind: 'glaze-v1.4-optical-web-adapter-candidate',
    stylesheet: 'css/glaze-v1.4-optical-runtime.candidate.css',
    telemetryRequired: false,
    analyticsRequired: false,
    environmentalSamplingImplemented: false,
    browserQualificationEstablished: false,
    nativeRendererParityEstablished: false,
    resolve(request = {}) {
      const declared = request.platformCapabilities ?? (
        typeof capabilityAdapter?.resolve === 'function' ? capabilityAdapter.resolve() : []
      );
      return resolveOpticalRuntime({...request, platformCapabilities: declared});
    },
    apply(target, request = {}) {
      return applyResolvedOpticalWebState(target, this.resolve(request));
    }
  });
}

export const opticalWebCandidate = Object.freeze({
  targetVersion: opticalRuntimeCandidate.targetVersion,
  releaseLifecycle: 'proposed',
  consumerEligible: false,
  lifecycleAuthority: false,
  semanticApiStability: 'candidate-not-frozen',
  stableSource: '1.3.0',
  renderer: 'web-candidate',
  telemetryRequired: false,
  analyticsRequired: false,
  environmentalSamplingImplemented: false,
  browserQualificationEstablished: false,
  assistiveTechnologyQualificationEstablished: false,
  physicalDeviceQualificationEstablished: false,
  productionPerformanceBudgetsEstablished: false,
  nativeRendererParityEstablished: false,
  establishesOperationalSecurityAuthority: false,
  establishesOperationalPrivacyAuthority: false,
  establishesIdentityAuthority: false,
  establishesRecoveryAuthority: false
});
