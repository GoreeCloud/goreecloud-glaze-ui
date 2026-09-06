import assert from 'node:assert/strict';
import test from 'node:test';

import {
  actionSafetyForSuggestion,
  applyContextualPresentation,
  contextualIntelligenceCandidate,
  dismissContextualSuggestion,
  normalizeContextSnapshot,
  rankOptionalSuggestions,
  resolveContextualPresentation
} from '../js/glaze-v1.3-contextual-intelligence.candidate.mjs';

const suggestions = [
  {id: 'a', label: 'Open recent item', provenance: 'local-history-adapter', relevance: 0.4},
  {id: 'b', label: 'Continue current task', provenance: 'task-adapter', relevance: 0.9},
  {id: 'c', label: 'Review source', provenance: 'source-adapter', relevance: 0.4}
];

test('context snapshot accepts only governed bounded signal families', () => {
  const result = normalizeContextSnapshot({
    signals: {
      'current-task': 'editing',
      'current-destination': 'library',
      'unapproved-signal': 'ignored',
      'selected-object-kind': 'document'
    }
  });
  assert.equal(result.contextAvailable, true);
  assert.equal(result.signals['current-task'], 'editing');
  assert.equal(result.signals['unapproved-signal'], undefined);
  assert.equal(result.rawPrivateActivityRetained, false);
  assert.equal(result.persisted, false);
});

test('missing context produces a context-neutral fallback', () => {
  const result = resolveContextualPresentation({suggestions});
  assert.equal(result.contextNeutralFallback, true);
  assert.equal(result.taskStateReset, false);
  assert.equal(result.pageReloadRequired, false);
});

test('optional suggestions rank by producer relevance with stable original-order ties', () => {
  const ranked = rankOptionalSuggestions(suggestions);
  assert.deepEqual(ranked.map(item => item.id), ['b', 'a', 'c']);
});

test('suggestions require stable id, visible label, and provenance', () => {
  assert.throws(() => rankOptionalSuggestions([{label: 'x', provenance: 'p'}]), /stable id/);
  assert.throws(() => rankOptionalSuggestions([{id: 'x', provenance: 'p'}]), /visible label/);
  assert.throws(() => rankOptionalSuggestions([{id: 'x', label: 'x'}]), /provenance/);
  assert.throws(() => rankOptionalSuggestions([{id: 'x', label: 'x', provenance: 'p'}, {id: 'x', label: 'y', provenance: 'q'}]), /must be unique/);
});

test('context never reorders primary navigation or redefines semantic truth', () => {
  const result = resolveContextualPresentation({
    context: {signals: {'current-destination': 'home'}},
    suggestions
  });
  assert.equal(result.primaryNavigationReordered, false);
  assert.equal(result.primaryNavigationInvented, false);
  assert.equal(result.semanticTruthRedefined, false);
  assert.equal(result.productIdentityErased, false);
});

test('context color remains below semantic, product identity, and user accent authorities', () => {
  const result = resolveContextualPresentation({context: {signals: {'local-environment-summary': 'calm'}}});
  assert.equal(result.contextColorAuthority, 'below-semantic-product-identity-and-user-accent');
});

test('dismissed suggestions leave the active interaction flow', () => {
  const result = resolveContextualPresentation({suggestions, dismissedSuggestionIds: ['b']});
  assert.deepEqual(result.activeSuggestions.map(item => item.id), ['a', 'c']);
  const dismissed = dismissContextualSuggestion(suggestions, 'b');
  assert.deepEqual(dismissed.map(item => item.id), ['a', 'c']);
});

test('non-dismissible suggestions cannot be removed through dismiss helper', () => {
  const locked = [{id: 'required', label: 'Required notice', provenance: 'system', relevance: 1, dismissible: false}];
  assert.throws(() => dismissContextualSuggestion(locked, 'required'), /not dismissible/);
});

test('consequential suggestions require confirmation and never auto-execute', () => {
  for (const suggestion of [
    {id: 'privacy', label: 'Review privacy setting', provenance: 'privacy-producer', consequential: true},
    {id: 'important', label: 'Review important change', provenance: 'item-producer', destructive: true}
  ]) {
    const result = actionSafetyForSuggestion(suggestion);
    assert.equal(result.confirmationRequired, true);
    assert.equal(result.automaticExecutionAllowed, false);
    assert.equal(result.generatedSuggestionIsSoleAuthority, false);
    assert.equal(result.producerTruthRemainsAuthoritative, true);
  }
});

test('ordinary optional suggestion remains non-automatic', () => {
  const result = actionSafetyForSuggestion({id: 'open', label: 'Open item', provenance: 'local'});
  assert.equal(result.confirmationRequired, false);
  assert.equal(result.automaticExecutionAllowed, false);
});

test('Reduced Motion keeps context changes immediate without removing provenance', () => {
  const result = resolveContextualPresentation({suggestions, reducedMotion: true});
  assert.equal(result.reducedMotionImmediateContextChange, true);
  assert.equal(result.largeTextKeepsProvenanceVisible, true);
});

test('applyContextualPresentation writes semantic state only', () => {
  const properties = new Map();
  const target = {
    dataset: {},
    style: {setProperty(name, value) { properties.set(name, value); }}
  };
  const result = applyContextualPresentation(target, {
    context: {signals: {'current-task': 'review'}},
    suggestions
  });
  assert.equal(target.dataset.glazeContextV13, 'contextual');
  assert.equal(target.dataset.glazeSuggestionCount, '3');
  assert.equal(properties.get('--glz13-context-provenance-visible'), '1');
  assert.equal(properties.get('--glz13-context-navigation-stable'), '1');
  assert.equal(result.generatedResultsAreSystemTruth, false);
});

test('candidate metadata preserves privacy, authority, and acceptance boundaries', () => {
  assert.equal(contextualIntelligenceCandidate.releaseLifecycle, 'proposed');
  assert.equal(contextualIntelligenceCandidate.consumerEligible, false);
  assert.equal(contextualIntelligenceCandidate.primaryNavigationReorderingAllowed, false);
  assert.equal(contextualIntelligenceCandidate.semanticTruthRedefinitionAllowed, false);
  assert.equal(contextualIntelligenceCandidate.automaticConsequentialExecutionAllowed, false);
  assert.equal(contextualIntelligenceCandidate.remoteInferenceRequired, false);
  assert.equal(contextualIntelligenceCandidate.telemetryRequired, false);
  assert.equal(contextualIntelligenceCandidate.runtimePersistenceRequired, false);
  assert.equal(contextualIntelligenceCandidate.humanIntelligenceAcceptanceEstablished, false);
});
