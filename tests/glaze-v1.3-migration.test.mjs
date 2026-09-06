import test from 'node:test';
import assert from 'node:assert/strict';

import {
  MIGRATION_EVIDENCE_CATEGORIES,
  validateConsumerAdoptionRecord,
  evaluateConsumerMigration,
  migrationCandidate
} from '../js/glaze-v1.3-migration.candidate.mjs';

const CONSUMER_SHA = '1'.repeat(40);
const DESIGN_SHA = '2'.repeat(40);
const ROLLBACK_SHA = '3'.repeat(40);

function validRecord(overrides = {}) {
  const evidence = Object.fromEntries(MIGRATION_EVIDENCE_CATEGORIES.map(name => [name, {
    status: 'passed',
    consumerRevision: CONSUMER_SHA,
    repositoryLocal: true,
    platforms: ['web'],
    reference: `evidence/${name}.json`
  }]));
  return {
    schemaVersion: 1,
    consumerName: 'GoreeCloud Example',
    repository: 'GoreeCloud/goreecloud-example',
    consumerRevision: CONSUMER_SHA,
    designSystemVersion: '1.3.0',
    designSystemRevision: DESIGN_SHA,
    supportedPlatforms: ['web'],
    evidence,
    rollback: {
      lastKnownGoodRevision: ROLLBACK_SHA,
      verified: true,
      independentlyReversible: true
    },
    productionApproval: {
      approved: true,
      authority: 'consumer-release-owner',
      consumerRevision: CONSUMER_SHA
    },
    ...overrides
  };
}

const stableRelease = {
  version: '1.3.0',
  revision: DESIGN_SHA,
  lifecycle: 'stable',
  consumerEligible: true
};

test('canonical complete adoption record validates', () => {
  assert.deepEqual([...validateConsumerAdoptionRecord(validRecord())], []);
});

test('Proposed V1.3 remains evaluation-only even with complete consumer evidence', () => {
  const result = evaluateConsumerMigration(validRecord({designSystemVersion: '1.3.0-candidate'}), {
    version: '1.3.0-candidate',
    revision: DESIGN_SHA,
    lifecycle: 'proposed',
    consumerEligible: false
  });
  assert.equal(result.state, 'evaluation-only');
  assert.equal(result.productionEligible, false);
  assert.equal(result.conformanceGranted, false);
});

test('non-consumer-eligible Candidate remains evaluation-only', () => {
  const result = evaluateConsumerMigration(validRecord({designSystemVersion: '1.3.0-candidate'}), {
    version: '1.3.0-candidate',
    revision: DESIGN_SHA,
    lifecycle: 'candidate',
    consumerEligible: false
  });
  assert.equal(result.state, 'evaluation-only');
  assert.equal(result.productionEligible, false);
});

test('Stable release with exact complete record reaches eligibility only after independent acceptance', () => {
  const result = evaluateConsumerMigration(validRecord(), stableRelease);
  assert.equal(result.state, 'eligible-after-independent-acceptance');
  assert.equal(result.productionEligible, true);
  assert.equal(result.conformanceGranted, false);
  assert.deepEqual([...result.blockers], []);
});

test('complete technical evidence without production approval remains acceptance-pending', () => {
  const record = validRecord({
    productionApproval: {
      approved: false,
      authority: 'consumer-release-owner',
      consumerRevision: CONSUMER_SHA
    }
  });
  const result = evaluateConsumerMigration(record, stableRelease);
  assert.equal(result.state, 'ready-for-consumer-acceptance');
  assert.equal(result.productionEligible, false);
  assert.equal(result.conformanceGranted, false);
});

test('design-system revision mismatch fails closed', () => {
  const result = evaluateConsumerMigration(validRecord(), {...stableRelease, revision: '4'.repeat(40)});
  assert.equal(result.state, 'blocked');
  assert.equal(result.productionEligible, false);
  assert.match(result.blockers.join('\n'), /design-system revision/);
});

test('stale evidence fails closed', () => {
  const record = validRecord();
  record.evidence.accessibility = {...record.evidence.accessibility, status: 'stale'};
  const result = evaluateConsumerMigration(record, stableRelease);
  assert.equal(result.state, 'blocked');
  assert.match(result.blockers.join('\n'), /accessibility\.status/);
});

test('non-repository-local evidence fails closed', () => {
  const record = validRecord();
  record.evidence.performance = {...record.evidence.performance, repositoryLocal: false};
  const result = evaluateConsumerMigration(record, stableRelease);
  assert.equal(result.state, 'blocked');
  assert.match(result.blockers.join('\n'), /performance must be repository-local/);
});

test('evidence must reference the exact consumer revision', () => {
  const record = validRecord();
  record.evidence.interaction = {...record.evidence.interaction, consumerRevision: '5'.repeat(40)};
  const result = evaluateConsumerMigration(record, stableRelease);
  assert.equal(result.state, 'blocked');
  assert.match(result.blockers.join('\n'), /interaction must match the exact consumer revision/);
});

test('rollback must be verified and independently reversible', () => {
  const record = validRecord({
    rollback: {
      lastKnownGoodRevision: ROLLBACK_SHA,
      verified: false,
      independentlyReversible: false
    }
  });
  const result = evaluateConsumerMigration(record, stableRelease);
  assert.equal(result.state, 'blocked');
  assert.match(result.blockers.join('\n'), /rollback must be verified/);
  assert.match(result.blockers.join('\n'), /independently reversible/);
});

test('unsupported or duplicate platform declarations fail closed', () => {
  const record = validRecord({supportedPlatforms: ['web', 'web', 'car-dashboard']});
  const errors = validateConsumerAdoptionRecord(record);
  assert.match(errors.join('\n'), /duplicate supported platform web/);
  assert.match(errors.join('\n'), /unsupported platform kind car-dashboard/);
});

test('production approval must bind the exact consumer revision', () => {
  const record = validRecord({
    productionApproval: {
      approved: true,
      authority: 'consumer-release-owner',
      consumerRevision: '6'.repeat(40)
    }
  });
  const result = evaluateConsumerMigration(record, stableRelease);
  assert.equal(result.state, 'blocked');
  assert.match(result.blockers.join('\n'), /productionApproval must reference the exact consumer revision/);
});

test('not-applicable evidence is explicit and allowed when repository-local and revision-bound', () => {
  const record = validRecord();
  record.evidence.platformIntegration = {
    status: 'not-applicable',
    consumerRevision: CONSUMER_SHA,
    repositoryLocal: true,
    reference: 'evidence/platform-not-applicable.md'
  };
  assert.deepEqual([...validateConsumerAdoptionRecord(record)], []);
});

test('candidate metadata cannot mutate lifecycle, repositories, conformance, or production approval', () => {
  assert.equal(migrationCandidate.releaseLifecycle, 'proposed');
  assert.equal(migrationCandidate.consumerEligible, false);
  assert.equal(migrationCandidate.liveRequiredConsumerVersion, '1.2.0');
  assert.equal(migrationCandidate.canMutateConsumerRepository, false);
  assert.equal(migrationCandidate.canMutateLifecycle, false);
  assert.equal(migrationCandidate.canGrantConformance, false);
  assert.equal(migrationCandidate.canGrantProductionApproval, false);
  assert.equal(migrationCandidate.proposedEvaluationIsNonProductionOnly, true);
});
