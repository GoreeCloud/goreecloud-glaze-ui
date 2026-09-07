#!/usr/bin/env node
import {readdir, readFile} from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

import {evaluateQualificationReadiness} from '../js/glaze-v1.3-qualification.candidate.mjs';

const SHA40 = /^[0-9a-f]{40}$/;

function usage() {
  return `Usage: node scripts/evaluate_glaze_v1_3_qualification.mjs --source-revision <sha40> [options]\n\n` +
    `Options:\n` +
    `  --evidence-dir <path>   Evidence directory (default: evidence/v1.3)\n` +
    `  --evaluated-at <iso>    Evaluation time (default: current time)\n` +
    `  --require-ready         Exit 2 unless all six tracks are accepted\n` +
    `  --help                  Show this help\n`;
}

function parseArgs(argv) {
  const args = {evidenceDir: 'evidence/v1.3', evaluatedAt: new Date().toISOString(), requireReady: false};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === '--help') args.help = true;
    else if (token === '--require-ready') args.requireReady = true;
    else if (token === '--source-revision') args.sourceRevision = argv[++i];
    else if (token === '--evidence-dir') args.evidenceDir = argv[++i];
    else if (token === '--evaluated-at') args.evaluatedAt = argv[++i];
    else throw new Error(`unknown argument: ${token}`);
  }
  return args;
}

async function loadEvidence(directory) {
  const entries = (await readdir(directory, {withFileTypes: true}))
    .filter(entry => entry.isFile() && entry.name.endsWith('.json'))
    .map(entry => entry.name)
    .sort();
  const records = [];
  for (const name of entries) {
    const filePath = path.join(directory, name);
    try {
      records.push(JSON.parse(await readFile(filePath, 'utf8')));
    } catch (error) {
      throw new Error(`${filePath}: invalid JSON: ${error.message}`);
    }
  }
  return {entries, records};
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.error(error.message);
    console.error(usage());
    return 1;
  }
  if (args.help) {
    console.log(usage());
    return 0;
  }
  if (!SHA40.test(args.sourceRevision ?? '')) {
    console.error('--source-revision must be an exact lowercase 40-character Git SHA');
    return 1;
  }

  const {entries, records} = await loadEvidence(args.evidenceDir);
  const result = evaluateQualificationReadiness(records, {
    sourceRevision: args.sourceRevision,
    evaluatedAt: args.evaluatedAt
  });
  console.log(JSON.stringify({
    evidenceDirectory: args.evidenceDir,
    evidenceFiles: entries,
    result
  }, null, 2));

  if (args.requireReady && !result.qualificationGateSatisfied) return 2;
  return 0;
}

try {
  process.exitCode = await main();
} catch (error) {
  console.error(error.stack || error.message);
  process.exitCode = 1;
}
