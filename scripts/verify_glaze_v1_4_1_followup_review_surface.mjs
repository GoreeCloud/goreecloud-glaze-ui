import fs from 'node:fs';

const path = 'reference/v1.4.1/session-001-followup-review.html';
const text = fs.readFileSync(path, 'utf8');
const required = [
  'Human follow-up review surface — not acceptance evidence.',
  '../../css/glaze-v1.4.1.candidate.css',
  '../../js/glaze-v1.4.1.candidate.mjs',
  'Noisy / bright',
  'Deep night',
  'Accessible solid',
  'Reduced motion',
  'data-glaze-semantic-surface="protected"',
  'Human result: PENDING',
  'exact-revision human review requires',
  'semanticSurfaceStrength',
  'reducedMotion=${resolved.accessibility.reducedMotion}'
];
for (const marker of required) {
  if (!text.includes(marker)) throw new Error(`Missing required follow-up review marker: ${marker}`);
}
if (/https?:\/\//i.test(text)) throw new Error('Follow-up review surface must not load remote resources');
if (/mark(s|ed)? checks? passed|promotion eligible|acceptance evidence created/i.test(text)) {
  throw new Error('Follow-up surface must not claim human acceptance or promotion');
}
for (const scenario of ['noisy','night','accessible','reduced']) {
  if (!text.includes(`${scenario}: {`)) throw new Error(`Missing canonical scenario: ${scenario}`);
}
console.log('GLAZE UI V1.4.1 Session 001 follow-up review surface verified as local-only, exact-revision-bound, and non-evidence.');
