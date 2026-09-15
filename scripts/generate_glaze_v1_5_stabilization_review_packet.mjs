#!/usr/bin/env node
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname, resolve} from 'node:path';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const CONTRACT = resolve(ROOT, 'contracts/v1.5/stabilization-review.dev.json');
const HEX40 = /^[0-9a-f]{40}$/;
const NOTICE = 'Pre-review planning packet only. This file is not human, assistive-technology, device, privacy, performance, platform, consumer, Release Candidate, Stable, deployment, or production acceptance evidence. Review outcomes and evidence references must be recorded only after real review of the exact source revision.';

export class StabilizationReviewPacketError extends Error {}

function req(condition, message) {
  if (!condition) throw new StabilizationReviewPacketError(message);
}

function text(value, label) {
  req(typeof value === 'string' && value.trim().length > 0, `${label} is required`);
  return value.trim();
}

function unique(values) {
  return [...new Set(values.map(value => value.trim()).filter(Boolean))];
}

function readContract() {
  const contract = JSON.parse(readFileSync(CONTRACT, 'utf8'));
  req(contract.schemaVersion === 1, 'stabilization review contract schema must remain version 1');
  req(contract.contractVersion === '1.5.0-dev.1', 'stabilization review contract must remain bound to 1.5.0-dev.1');
  req(contract.glazeUiVersion === '1.5.0-dev.1', 'stabilization review contract Glaze version mismatch');
  req(contract.releaseLifecycle === 'Development', 'stabilization review contract lifecycle must remain Development');
  req(contract.stableBaseline === '1.4.1', 'stabilization review contract Stable baseline must remain 1.4.1');
  req(contract.authority === 'review-planning-only', 'stabilization review contract authority must remain review-planning-only');
  req(contract.promotionEligible === false, 'stabilization review contract must never be promotion eligible');
  req(contract.consumerEligible === false, 'stabilization review contract must not establish consumer eligibility');
  req(contract.releaseCandidate === false, 'stabilization review contract must not establish Release Candidate status');
  req(contract.stable === false, 'stabilization review contract must not establish Stable status');
  req(Array.isArray(contract.requiredEvidenceAreas) && contract.requiredEvidenceAreas.length === 6, 'stabilization review contract must contain exactly six required evidence areas');
  req(contract.requiredEvidenceAreas.every(area => Array.isArray(area.checks) && area.checks.length === 3), 'each stabilization review evidence area must contain exactly three checks');
  return contract;
}

export function buildStabilizationReviewPacket(options) {
  const contract = readContract();
  const sourceRevision = text(options.sourceRevision, 'source revision');
  req(HEX40.test(sourceRevision), 'source revision must be exactly 40 lowercase hexadecimal characters');

  const checks = contract.requiredEvidenceAreas.flatMap(area => area.checks.map(check => ({
    id: check.id,
    area: area.id,
    areaLabel: area.label,
    description: check.description,
    status: 'pending',
    finding: null,
    limitations: [],
    evidenceRefs: []
  })));

  return {
    schemaVersion: 1,
    packetType: 'glaze-v1.5-stabilization-review-packet',
    glazeUiVersion: contract.glazeUiVersion,
    releaseLifecycle: contract.releaseLifecycle,
    stableBaseline: contract.stableBaseline,
    repository: contract.repository,
    authority: 'pre-review-planning-only',
    sourceRevision,
    build: {
      artifact: text(options.artifact, 'artifact'),
      buildIdentifier: text(options.buildIdentifier, 'build identifier')
    },
    environment: {
      platform: text(options.platform, 'platform'),
      osVersion: text(options.osVersion, 'OS version'),
      runtime: text(options.runtime, 'runtime'),
      device: text(options.device, 'device/environment'),
      formFactor: text(options.formFactor, 'form factor'),
      display: text(options.display, 'display context'),
      inputModalities: unique(options.inputModalities ?? []),
      assistiveTechnologies: unique(options.assistiveTechnologies ?? [])
    },
    checks,
    promotionEligible: false,
    consumerEligible: false,
    releaseCandidate: false,
    stable: false,
    deploymentAccepted: false,
    productionAccepted: false,
    notice: NOTICE
  };
}

function parseArgs(argv) {
  const args = {
    sourceRevision: null,
    artifact: null,
    buildIdentifier: null,
    platform: null,
    osVersion: null,
    runtime: null,
    device: null,
    formFactor: null,
    display: null,
    inputModalities: [],
    assistiveTechnologies: [],
    output: null,
    force: false,
    selfTest: false
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--source-revision') args.sourceRevision = argv[++index];
    else if (arg === '--artifact') args.artifact = argv[++index];
    else if (arg === '--build-id') args.buildIdentifier = argv[++index];
    else if (arg === '--platform') args.platform = argv[++index];
    else if (arg === '--os-version') args.osVersion = argv[++index];
    else if (arg === '--runtime') args.runtime = argv[++index];
    else if (arg === '--device') args.device = argv[++index];
    else if (arg === '--form-factor') args.formFactor = argv[++index];
    else if (arg === '--display') args.display = argv[++index];
    else if (arg === '--input-modality') args.inputModalities.push(argv[++index]);
    else if (arg === '--assistive-technology') args.assistiveTechnologies.push(argv[++index]);
    else if (arg === '--output') args.output = argv[++index];
    else if (arg === '--force') args.force = true;
    else if (arg === '--self-test') args.selfTest = true;
    else throw new StabilizationReviewPacketError(`unknown argument ${arg}`);
  }

  return args;
}

export function assertPacketIsPlanningOnly(packet) {
  req(packet.packetType === 'glaze-v1.5-stabilization-review-packet', 'packet type mismatch');
  req(packet.glazeUiVersion === '1.5.0-dev.1', 'packet Glaze version mismatch');
  req(packet.releaseLifecycle === 'Development', 'packet lifecycle must remain Development');
  req(packet.stableBaseline === '1.4.1', 'packet Stable baseline mismatch');
  req(packet.authority === 'pre-review-planning-only', 'packet authority mismatch');
  req(packet.promotionEligible === false, 'review packet must never be promotion eligible');
  req(packet.consumerEligible === false, 'review packet must never establish consumer eligibility');
  req(packet.releaseCandidate === false, 'review packet must never establish Release Candidate status');
  req(packet.stable === false, 'review packet must never establish Stable status');
  req(packet.deploymentAccepted === false, 'review packet must never establish deployment acceptance');
  req(packet.productionAccepted === false, 'review packet must never establish production acceptance');
  req(Array.isArray(packet.checks) && packet.checks.length === 18, 'review packet must contain all 18 stabilization checks');
  req(packet.checks.every(check => check.status === 'pending'), 'every generated check must be pending');
  req(packet.checks.every(check => check.finding === null), 'generated checks must not manufacture findings');
  req(packet.checks.every(check => check.limitations.length === 0 && check.evidenceRefs.length === 0), 'generated checks must not manufacture limitations or evidence references');
  req(!Object.hasOwn(packet, 'reviewer'), 'review packet must not manufacture a reviewer');
  req(!Object.hasOwn(packet, 'reviewedAt'), 'review packet must not manufacture a review timestamp');
  req(!Object.hasOwn(packet, 'approvedBy'), 'review packet must not manufacture approval');
  req(!Object.hasOwn(packet, 'releaseApproved'), 'review packet must not manufacture release approval');
}

function selfTest() {
  const packet = buildStabilizationReviewPacket({
    sourceRevision: 'a'.repeat(40),
    artifact: 'glaze-v1.5-review-build',
    buildIdentifier: 'glaze-v1.5-review-build',
    platform: 'web',
    osVersion: 'review-os',
    runtime: 'review-runtime',
    device: 'review-environment',
    formFactor: 'desktop',
    display: 'review-display',
    inputModalities: ['keyboard', 'pointer', 'keyboard'],
    assistiveTechnologies: ['screen-reader', 'screen-reader']
  });

  assertPacketIsPlanningOnly(packet);
  req(packet.environment.inputModalities.length === 2, 'duplicate input modalities must be normalized');
  req(packet.environment.assistiveTechnologies.length === 1, 'duplicate assistive technologies must be normalized');
  console.log('GLAZE UI V1.5 stabilization review packet generator self-test: PASS');
  console.log('Boundary: generated packets are planning artifacts only and cannot establish acceptance or lifecycle promotion.');
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.selfTest) {
    selfTest();
    return;
  }

  const packet = buildStabilizationReviewPacket(args);
  assertPacketIsPlanningOnly(packet);
  const rendered = `${JSON.stringify(packet, null, 2)}\n`;

  if (args.output) {
    const output = resolve(process.cwd(), args.output);
    mkdirSync(dirname(output), {recursive: true});
    writeFileSync(output, rendered, {encoding: 'utf8', flag: args.force ? 'w' : 'wx'});
    console.log(`Created pending V1.5 stabilization review packet: ${output}`);
    console.log('This planning packet is not acceptance evidence and is not promotion eligible.');
  } else {
    process.stdout.write(rendered);
  }
}

const isDirect = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isDirect) {
  try {
    main();
  } catch (error) {
    if (error instanceof StabilizationReviewPacketError || error?.code === 'EEXIST') {
      console.error(`GLAZE UI V1.5 stabilization review packet generation failed: ${error.message}`);
      process.exit(1);
    }
    throw error;
  }
}
