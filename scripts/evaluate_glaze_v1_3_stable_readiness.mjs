#!/usr/bin/env node
import {readdirSync, readFileSync} from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import {evaluateStableReadiness} from '../js/glaze-v1.3-stable-readiness.candidate.mjs';

function usage() {
  console.error('Usage: evaluate_glaze_v1_3_stable_readiness.mjs --candidate-source-revision <sha> --stable-source-revision <sha> --evidence-dir <dir> [--candidate-active] [--evaluated-at <iso>] [--require-ready]');
}
function fail(message, code=1) { console.error(`GLAZE UI V1.3 Stable readiness evaluation failed: ${message}`); process.exit(code); }
const args=process.argv.slice(2); const options={candidateActive:false};
for(let i=0;i<args.length;i++) {
  const arg=args[i];
  if(arg==='--candidate-source-revision') options.candidateSourceRevision=args[++i];
  else if(arg==='--stable-source-revision') options.stableSourceRevision=args[++i];
  else if(arg==='--evidence-dir') options.evidenceDir=args[++i];
  else if(arg==='--candidate-active') options.candidateActive=true;
  else if(arg==='--evaluated-at') options.evaluatedAt=args[++i];
  else if(arg==='--require-ready') options.requireReady=true;
  else { usage(); fail(`unknown argument ${arg}`); }
}
if(!/^[0-9a-f]{40}$/.test(options.candidateSourceRevision ?? '')) fail('candidate source revision must be an exact lowercase 40-character Git SHA');
if(!/^[0-9a-f]{40}$/.test(options.stableSourceRevision ?? '')) fail('Stable source revision must be an exact lowercase 40-character Git SHA');
if(!options.evidenceDir) fail('evidence directory is required');
let files; try { files=readdirSync(options.evidenceDir).filter(name=>name.endsWith('.json')).sort(); } catch(error) { fail(`cannot read evidence directory: ${error.message}`); }
const records=[]; for(const name of files) { try { records.push(JSON.parse(readFileSync(path.join(options.evidenceDir,name),'utf8'))); } catch(error) { fail(`${name}: invalid JSON: ${error.message}`); } }
const result=evaluateStableReadiness(records,{candidateSourceRevision:options.candidateSourceRevision,stableSourceRevision:options.stableSourceRevision,candidateActive:options.candidateActive,evaluatedAt:options.evaluatedAt});
console.log(JSON.stringify({schemaVersion:1,evidenceFiles:files,result},null,2));
if(options.requireReady && !result.stableGateSatisfied) process.exit(2);
