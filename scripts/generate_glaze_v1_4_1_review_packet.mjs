#!/usr/bin/env node
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname, resolve} from 'node:path';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const CONTRACT = resolve(ROOT, 'contracts/v1.4.1/human-validation.contract.json');
const HEX40 = /^[0-9a-f]{40}$/;
const NOTICE = 'Pre-review planning packet only. This file is not human evidence, contains no reviewer authorization or review timestamp, cannot establish acceptance, and is never promotion eligible. A real human-validation record must be created after review under the separate V1.4.1 human-evidence protocol.';

class ReviewPacketError extends Error {}

function req(condition, message) {
  if (!condition) throw new ReviewPacketError(message);
}

function text(value, label) {
  req(typeof value === 'string' && value.trim().length > 0, `${label} is required`);
  return value.trim();
}

function unique(values) {
  return [...new Set(values.map(value => value.trim()).filter(Boolean))];
}

export function buildReviewPacket(options) {
  const contract = JSON.parse(readFileSync(CONTRACT, 'utf8'));
  const sourceRevision = text(options.sourceRevision, 'source revision');
  req(HEX40.test(sourceRevision), 'source revision must be exactly 40 lowercase hexadecimal characters');
  req(contract.version === '1.4.1-candidate', 'human-validation contract version must remain 1.4.1-candidate');
  req(contract.baselineVersion === '1.4.0', 'human-validation contract baseline must remain 1.4.0');
  req(contract.evidenceAuthority === 'human', 'human-validation contract must retain human evidence authority');
  req(Array.isArray(contract.requiredChecks) && contract.requiredChecks.length === 34, 'human-validation contract must contain exactly 34 required checks');

  return {
    schemaVersion: 1,
    packetType: 'glaze-v1.4.1-human-review-packet',
    glazeUiVersion: '1.4.1',
    baselineVersion: '1.4.0',
    repository: 'GoreeCloud/goreecloud-glaze-ui',
    authority: 'pre-review-planning-only',
    sourceRevision,
    build: {
      artifact: text(options.artifact, 'artifact'),
      buildIdentifier: text(options.buildIdentifier, 'build identifier')
    },
    environment: {
      platform: text(options.platform, 'platform'),
      osVersion: text(options.osVersion, 'OS version'),
      device: text(options.device, 'device/environment'),
      formFactor: text(options.formFactor, 'form factor'),
      display: text(options.display, 'display context'),
      inputModalities: unique(options.inputModalities ?? []),
      assistiveTechnologies: unique(options.assistiveTechnologies ?? [])
    },
    checks: contract.requiredChecks.map(check => ({
      id: check.id,
      category: check.category,
      description: check.description,
      status: 'pending',
      finding: null,
      limitations: [],
      evidenceRefs: []
    })),
    promotionEligible: false,
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
    else if (arg === '--device') args.device = argv[++index];
    else if (arg === '--form-factor') args.formFactor = argv[++index];
    else if (arg === '--display') args.display = argv[++index];
    else if (arg === '--input-modality') args.inputModalities.push(argv[++index]);
    else if (arg === '--assistive-technology') args.assistiveTechnologies.push(argv[++index]);
    else if (arg === '--output') args.output = argv[++index];
    else if (arg === '--force') args.force = true;
    else if (arg === '--self-test') args.selfTest = true;
    else throw new ReviewPacketError(`unknown argument ${arg}`);
  }
  return args;
}

function assertPacketIsPlanningOnly(packet) {
  req(packet.packetType === 'glaze-v1.4.1-human-review-packet', 'self-test packet type mismatch');
  req(packet.authority === 'pre-review-planning-only', 'self-test authority mismatch');
  req(packet.promotionEligible === false, 'review packet must never be promotion eligible');
  req(Array.isArray(packet.checks) && packet.checks.length === 34, 'review packet must contain all 34 checks');
  req(packet.checks.every(check => check.status === 'pending'), 'every generated check must be pending');
  req(packet.checks.every(check => check.finding === null), 'generated checks must not manufacture findings');
  req(packet.checks.every(check => check.limitations.length === 0 && check.evidenceRefs.length === 0), 'generated checks must not manufacture limitations or evidence references');
  req(!Object.hasOwn(packet, 'recordType'), 'review packet must not use the human evidence recordType');
  req(!Object.hasOwn(packet, 'evidenceType'), 'review packet must not claim human evidenceType');
  req(!Object.hasOwn(packet, 'sessions'), 'review packet must not manufacture review sessions');
  req(!Object.hasOwn(packet, 'reviewer'), 'review packet must not manufacture a reviewer');
  req(!Object.hasOwn(packet, 'reviewedAt'), 'review packet must not manufacture a review timestamp');
}

function selfTest() {
  const packet = buildReviewPacket({
    sourceRevision: 'a'.repeat(40),
    artifact: 'synthetic-review-build.apk',
    buildIdentifier: 'synthetic-review-build',
    platform: 'android',
    osVersion: 'synthetic-os',
    device: 'synthetic-device',
    formFactor: 'mobile',
    display: 'synthetic-display',
    inputModalities: ['touch', 'touch'],
    assistiveTechnologies: []
  });
  assertPacketIsPlanningOnly(packet);
  req(packet.environment.inputModalities.length === 1, 'duplicate input modalities must be normalized');
  console.log('GLAZE UI V1.4.1 human review packet generator self-test: PASS');
  console.log('Boundary: generated packets are planning artifacts only and cannot establish human acceptance.');
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.selfTest) {
    selfTest();
    return;
  }

  const packet = buildReviewPacket(args);
  assertPacketIsPlanningOnly(packet);
  const rendered = JSON.stringify(packet, null, 2) + '\n';

  if (args.output) {
    const output = resolve(process.cwd(), args.output);
    mkdirSync(dirname(output), {recursive: true});
    writeFileSync(output, rendered, {encoding: 'utf8', flag: args.force ? 'w' : 'wx'});
    console.log(`Created pending V1.4.1 human review packet: ${output}`);
    console.log('This planning packet is not human evidence and is not promotion eligible.');
  } else {
    process.stdout.write(rendered);
  }
}

const isDirect = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isDirect) {
  try {
    main();
  } catch (error) {
    if (error instanceof ReviewPacketError || error?.code === 'EEXIST') {
      console.error(`GLAZE UI V1.4.1 review packet generation failed: ${error.message}`);
      process.exit(1);
    }
    throw error;
  }
}
