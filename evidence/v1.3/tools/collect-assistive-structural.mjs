import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';

const sourceSha = process.env.SOURCE_SHA;
const sourceTreeSha = process.env.SOURCE_TREE_SHA;
const referenceHtml = process.env.REFERENCE_HTML;
const referenceBlobSha = process.env.REFERENCE_HTML_BLOB_SHA;
const referenceManifestBlobSha = process.env.REFERENCE_MANIFEST_BLOB_SHA;
const evidenceSchemaBlobSha = process.env.EVIDENCE_SCHEMA_BLOB_SHA;
const chrome = process.env.CHROME;
const sourceDir = path.resolve('exact-source');
const outputDir = path.resolve('assistive-output');
fs.mkdirSync(outputDir, { recursive: true });

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function waitFor(url, attempts = 120) {
  for (let i = 0; i < attempts; i++) {
    try {
      const response = await fetch(url);
      if (response.ok) return response;
    } catch {}
    await sleep(100);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

const server = spawn('python3', ['-m', 'http.server', '8765', '--bind', '127.0.0.1'], {
  cwd: sourceDir,
  stdio: ['ignore', 'pipe', 'pipe']
});
const chromeProc = spawn(chrome, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--remote-debugging-port=9222', `--user-data-dir=${process.env.RUNNER_TEMP}/glaze-at-chrome`, 'about:blank'
], { stdio: ['ignore', 'pipe', 'pipe'] });
function stopChildren() {
  try { server.kill('SIGTERM'); } catch {}
  try { chromeProc.kill('SIGTERM'); } catch {}
}
process.on('exit', stopChildren);
process.on('SIGINT', () => { stopChildren(); process.exit(130); });
process.on('SIGTERM', () => { stopChildren(); process.exit(143); });

await waitFor(`http://127.0.0.1:8765/${referenceHtml}`);
const versionResponse = await waitFor('http://127.0.0.1:9222/json/version');
const browserVersionInfo = await versionResponse.json();

async function openPage() {
  const response = await fetch('http://127.0.0.1:9222/json/new?about%3Ablank', { method: 'PUT' });
  if (!response.ok) throw new Error(`CDP target creation failed: ${response.status}`);
  const target = await response.json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, { once: true });
    ws.addEventListener('error', reject, { once: true });
  });
  let nextId = 0;
  const pending = new Map();
  ws.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (!message.id) return;
    const waiter = pending.get(message.id);
    if (!waiter) return;
    pending.delete(message.id);
    if (message.error) waiter.reject(new Error(JSON.stringify(message.error)));
    else waiter.resolve(message.result);
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++nextId;
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return { ws, send, targetId: target.id };
}

async function evaluate(send, expression) {
  const result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(`Evaluation failed: ${JSON.stringify(result.exceptionDetails)}`);
  return result.result?.value;
}

async function waitForReferenceReady(send) {
  for (let i = 0; i < 120; i++) {
    const state = await evaluate(send, `(() => ({
      ready: document.readyState,
      status: document.querySelector('#reference-status')?.textContent || '',
      components: document.querySelectorAll('[data-signature-component]').length,
      scenes: document.querySelectorAll('[data-reference-scene]').length
    }))()`);
    if (state.ready === 'complete' && state.components === 5 && state.scenes === 8 && state.status.includes('initialized')) return state;
    await sleep(100);
  }
  throw new Error('Reference page did not reach governed initialized state.');
}

async function pressTab(send, reverse = false) {
  const modifiers = reverse ? 8 : 0;
  const key = { key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9, nativeVirtualKeyCode: 9, modifiers };
  await send('Input.dispatchKeyEvent', { type: 'keyDown', ...key });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', ...key });
  await sleep(35);
}

async function collectFocusSequence(send, reverse = false) {
  await evaluate(send, 'document.activeElement?.blur(); true');
  const sequence = [];
  const seen = new Set();
  for (let i = 0; i < 20; i++) {
    await pressTab(send, reverse);
    const item = await evaluate(send, `(() => {
      const el = document.activeElement;
      if (!el || el === document.body || el === document.documentElement) return null;
      const text = (el.innerText || el.textContent || '').replace(/\\s+/g,' ').trim();
      return {
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute('type'),
        role: el.getAttribute('role'),
        name: el.getAttribute('aria-label') || text || el.getAttribute('placeholder') || null,
        ariaCurrent: el.getAttribute('aria-current'),
        ariaExpanded: el.getAttribute('aria-expanded')
      };
    })()`);
    if (!item) break;
    const key = JSON.stringify(item);
    if (seen.has(key)) break;
    seen.add(key);
    sequence.push(item);
  }
  return sequence;
}

const { ws, send, targetId } = await openPage();
try {
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Accessibility.enable');
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false,
    screenWidth: 1440, screenHeight: 1000
  });
  await send('Page.navigate', {
    url: `http://127.0.0.1:8765/${referenceHtml}?exact-source=${sourceSha}&track=assistive-technology`
  });
  const initialized = await waitForReferenceReady(send);

  const domAudit = await evaluate(send, `(() => {
    const selector = 'a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])';
    const interactive = [...document.querySelectorAll(selector)].map((el,index) => {
      const r = el.getBoundingClientRect();
      const text = (el.innerText || el.textContent || '').replace(/\\s+/g,' ').trim();
      return {
        index,
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute('type'),
        role: el.getAttribute('role'),
        name: el.getAttribute('aria-label') || text || el.getAttribute('placeholder') || null,
        ariaCurrent: el.getAttribute('aria-current'),
        ariaExpanded: el.getAttribute('aria-expanded'),
        disabled: el.matches(':disabled'),
        tabIndex: el.tabIndex,
        rect: {x:r.x,y:r.y,width:r.width,height:r.height}
      };
    });
    const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
    const duplicateIds = [...new Set(ids.filter((id,i) => ids.indexOf(id) !== i))];
    const hiddenFocusable = [...document.querySelectorAll('[aria-hidden="true"]')].flatMap(hidden =>
      [...hidden.querySelectorAll(selector)].map(el => ({
        hiddenAncestor: hidden.className || hidden.id || hidden.tagName,
        focusable: el.className || el.id || el.tagName
      }))
    );
    return {
      lang: document.documentElement.lang,
      title: document.title,
      statusRole: document.querySelector('#reference-status')?.getAttribute('role'),
      statusLive: document.querySelector('#reference-status')?.getAttribute('aria-live'),
      interactive,
      duplicateIds,
      unlabeled: interactive.filter(x => !x.name),
      hiddenFocusable,
      componentCount: document.querySelectorAll('[data-signature-component]').length,
      sceneCount: document.querySelectorAll('[data-reference-scene]').length
    };
  })()`);

  const forwardFocus = await collectFocusSequence(send, false);
  const reverseFocus = await collectFocusSequence(send, true);

  const fullTree = await send('Accessibility.getFullAXTree');
  const simplifiedTree = (fullTree.nodes || []).map(node => ({
    nodeId: node.nodeId,
    ignored: Boolean(node.ignored),
    role: node.role?.value ?? null,
    name: node.name?.value ?? null,
    description: node.description?.value ?? null,
    value: node.value?.value ?? null,
    properties: Object.fromEntries((node.properties || []).map(p => [p.name, p.value?.value ?? null]))
  }));
  const relevantRoles = new Set(['button','searchbox','navigation','status','heading','article','main']);
  const relevantAxNodes = simplifiedTree.filter(node => relevantRoles.has(node.role));
  const unnamedInteractiveAx = simplifiedTree.filter(node =>
    ['button','searchbox','link','checkbox','radio','switch','combobox'].includes(node.role) && !node.ignored && !node.name
  );

  await send('Emulation.setDeviceMetricsOverride', {
    width: 390, height: 844, deviceScaleFactor: 1, mobile: true,
    screenWidth: 390, screenHeight: 844
  });
  await evaluate(send, "document.documentElement.style.fontSize='200%'; true");
  await sleep(120);
  const largeText = await evaluate(send, `(() => {
    const selector = 'a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])';
    const controls = [...document.querySelectorAll(selector)].map(el => {
      const r = el.getBoundingClientRect();
      const text = (el.innerText || el.textContent || '').replace(/\\s+/g,' ').trim();
      return {
        name: el.getAttribute('aria-label') || text || el.getAttribute('placeholder') || null,
        width:r.width,height:r.height,left:r.left,right:r.right,
        clippedInline:r.left < -0.5 || r.right > document.documentElement.clientWidth + 0.5
      };
    });
    return {
      method:'runtime root font-size 200% at 390 CSS px; supporting text-scale/reflow probe, not a manual browser-zoom session',
      viewport:{width:innerWidth,height:innerHeight},
      clientWidth:document.documentElement.clientWidth,
      scrollWidth:document.documentElement.scrollWidth,
      horizontalOverflow:document.documentElement.scrollWidth > document.documentElement.clientWidth,
      controls,
      clippedInteractiveControls:controls.filter(x => x.clippedInline)
    };
  })()`);

  const checks = {
    referenceInitialized: initialized.status.includes('initialized') && initialized.components === 5 && initialized.scenes === 8,
    documentLanguagePresent: Boolean(domAudit.lang),
    noDuplicateIds: domAudit.duplicateIds.length === 0,
    allFocusableControlsNamed: domAudit.unlabeled.length === 0,
    noFocusableDescendantsInsideAriaHidden: domAudit.hiddenFocusable.length === 0,
    axInteractiveNodesNamed: unnamedInteractiveAx.length === 0,
    keyboardForwardTraversalFoundAllFocusable: forwardFocus.length === domAudit.interactive.length,
    keyboardReverseTraversalFoundAllFocusable: reverseFocus.length === domAudit.interactive.length,
    largeTextNoHorizontalOverflow: !largeText.horizontalOverflow,
    largeTextNoClippedInteractiveControls: largeText.clippedInteractiveControls.length === 0,
    liveStatusSemanticsPresent: domAudit.statusRole === 'status' && domAudit.statusLive === 'polite'
  };
  const failedChecks = Object.entries(checks).filter(([,passed]) => !passed).map(([name]) => name);

  const report = {
    schemaVersion: 1,
    purpose: 'Automated structural accessibility review support for the manual Assistive Technology qualification track. This does not constitute a screen-reader, voice-control, switch-control, or human acceptance session.',
    source: {
      repository:'GoreeCloud/goreecloud-glaze-ui', revision:sourceSha, treeSha:sourceTreeSha,
      referencePath:referenceHtml, referenceBlobSha, referenceManifestBlobSha, evidenceSchemaBlobSha,
      servedFromCleanDetachedExactCheckout:true
    },
    evidenceHarness: {
      branch:process.env.GITHUB_REF_NAME || null, commit:process.env.GITHUB_SHA || null,
      workflow:process.env.GITHUB_WORKFLOW || null, runId:process.env.GITHUB_RUN_ID || null,
      runAttempt:process.env.GITHUB_RUN_ATTEMPT || null
    },
    environment: {
      runnerOs:process.env.RUNNER_OS || null, imageOs:process.env.ImageOS || null,
      imageVersion:process.env.ImageVersion || null, browser:browserVersionInfo.Browser || null,
      protocolVersion:browserVersionInfo['Protocol-Version'] || null
    },
    exactReferenceBoundary: {
      inheritedStableV12Css:true,
      v13SpecificNativePlatformSemanticsEstablished:false,
      manualScreenReaderSessionSupplied:false,
      manualVoiceControlSessionSupplied:false,
      manualSwitchControlSessionSupplied:false,
      lifecycleAcceptanceSupplied:false
    },
    observedAtUtc:new Date().toISOString(), initialized, domAudit,
    keyboard:{forwardFocus,reverseFocus},
    accessibilityTree:{relevantAxNodes,unnamedInteractiveAx,totalNodeCount:simplifiedTree.length},
    largeText, checks, failedChecks,
    manualReviewStillRequired:[
      'Screen-reader sessions for each claimed support-matrix platform/AT pairing',
      'Voice-control sessions for each claimed pairing',
      'Switch-control sessions for each claimed pairing',
      'Human confirmation of semantics, labels, state announcements, focus restoration, keyboard behavior, and large-text/zoom/reflow where applicable',
      'Inspectable issue/disposition references for any failures'
    ]
  };

  fs.writeFileSync(path.join(outputDir,'assistive-structural-report.json'), JSON.stringify(report,null,2)+'\n');
  fs.writeFileSync(path.join(outputDir,'accessibility-tree-relevant.json'), JSON.stringify(relevantAxNodes,null,2)+'\n');
  fs.writeFileSync(path.join(outputDir,'keyboard-navigation.json'), JSON.stringify(report.keyboard,null,2)+'\n');
  fs.writeFileSync(path.join(outputDir,'large-text-reflow.json'), JSON.stringify(largeText,null,2)+'\n');
  fs.writeFileSync(path.join(outputDir,'README.md'),
`# GLAZE UI V1.3 Assistive Technology Structural Support Packet\n\nFrozen source: \`${sourceSha}\`\n\nSource tree: \`${sourceTreeSha}\`\n\nReference: \`${referenceHtml}\`\n\nAutomated structural checks: ${Object.keys(checks).length}\n\nFailed automated checks: ${failedChecks.length ? failedChecks.join(', ') : 'none'}\n\nThis packet is supporting evidence only. It does **not** record manual screen-reader, voice-control, switch-control, or human lifecycle acceptance. The governed manual Assistive Technology worksheet remains incomplete until the claimed support matrix is exercised by an accepted human/combined authority.\n`);

  const files = fs.readdirSync(outputDir).filter(name => name !== 'SHA256SUMS.txt').sort();
  const sums = files.map(name => {
    const data = fs.readFileSync(path.join(outputDir,name));
    return `${crypto.createHash('sha256').update(data).digest('hex')}  ${name}`;
  }).join('\n') + '\n';
  fs.writeFileSync(path.join(outputDir,'SHA256SUMS.txt'), sums);

  if (failedChecks.length) {
    console.error(JSON.stringify({failedChecks},null,2));
    process.exitCode = 2;
  }
} finally {
  ws.close();
  try { await fetch(`http://127.0.0.1:9222/json/close/${targetId}`); } catch {}
  stopChildren();
}
