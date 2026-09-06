#!/usr/bin/env python3
"""Validate bounded GLAZE UI V1.2 core token ownership."""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CONTRACT=ROOT/'contracts/v1.2/core-tokens.candidate.json';MANIFEST=ROOT/'tokens/glaze-v1.2-core.candidate.json';README=ROOT/'tokens/README.md';LIFECYCLE=ROOT/'registry/lifecycle.json';VERSION=ROOT/'VERSION';ART=ROOT/'artifacts';REPORT=ART/'glaze-v1.2-core-tokens-report.json'
EXPECTED={
'color':('color.opticalPalette','tokens/glaze-v1.2-optical-foundation.candidate.json','/opticalPalette','candidate-owned'),
'atmosphere':('atmosphere.auraFamilies','tokens/glaze-v1.2-optical-foundation.candidate.json','/auraFamilies','candidate-owned'),
'material':('material.appearance','tokens/glaze-v1.2-frosted-neutral.candidate.json','/materials','candidate-owned'),
'frost':('frost.levels','tokens/glaze-v1.2-optical-foundation.candidate.json','/frostLevels','candidate-owned'),
'blur':('blur.material','tokens/glaze-v1.2-frosted-neutral.candidate.json','/effects/blur','candidate-owned'),
'opacity':('opacity.material','tokens/glaze-v1.2-frosted-neutral.candidate.json','/materials','candidate-owned'),
'spacing':('spacing.scale','tokens/glaze-v1.2-spatial-foundation.candidate.json','/spacePx','candidate-owned'),
'density':('density.profiles','tokens/glaze-v1.2-spatial-foundation.candidate.json','/density','candidate-owned'),
'radius':('radius.roles','tokens/glaze-v1.2-geometry.candidate.json','/radiusPx','candidate-owned'),
'shadow':('shadow.roles','tokens/glaze-v1.2-depth.candidate.json','/depth','candidate-owned'),
'elevation':('elevation.roles','tokens/glaze-v1.2-depth.candidate.json','/depth','candidate-owned'),
'typography':('typography.roles','tokens/glaze-v1.2-typography.candidate.json','/roles','candidate-owned'),
'iconSize':('icon.sizes','tokens/glaze-v1.2-crystal-icons.candidate.json','/sizes','candidate-owned'),
'stroke':('icon.strokes','tokens/glaze-v1.2-crystal-icons.candidate.json','/strokeViewBox','candidate-owned'),
'motion':('motion.durations','tokens/glaze-v1.2-motion.candidate.json','/durationsMs','candidate-owned'),
'semanticColor':('semanticColor.roles','tokens/semantic-colors.json','/roles','inherited-semantic-contract'),
'state':('state.interaction','tokens/glaze-v1.2-states.candidate.json','/states','candidate-owned'),
'formFactor':('formFactor.compositionStates','tokens/glaze-v1.2-form-factor.candidate.json','/compositionStates','candidate-owned')}
UNESTABLISHED=set();RAW_VALUE=re.compile(r'#[0-9a-fA-F]{3,8}|rgba?\(|\b\d+(?:\.\d+)?(?:px|rem|em|ms)\b')
class ValidationError(RuntimeError):pass
def require(ok,msg):
    if not ok:raise ValidationError(msg)
def load(p):
    require(p.is_file(),f'missing {p.relative_to(ROOT)}');v=json.loads(p.read_text(encoding='utf-8'));require(isinstance(v,dict),f'expected object in {p.relative_to(ROOT)}');return v
def pointer(doc,p):
    require(p.startswith('/'),f'invalid JSON pointer {p!r}');cur=doc
    for raw in p[1:].split('/'):
        key=raw.replace('~1','/').replace('~0','~');require(isinstance(cur,dict) and key in cur,f'unresolved JSON pointer {p!r} at {key!r}');cur=cur[key]
    return cur
def validate_candidate(path,doc):
    require(doc.get('version')=='1.2.0-candidate',f'Candidate version drifted in {path.relative_to(ROOT)}');require(doc.get('lifecycle')=='candidate',f'Candidate lifecycle drifted in {path.relative_to(ROOT)}');require(doc.get('stableBaseline')=='1.1.0',f'Stable baseline drifted in {path.relative_to(ROOT)}');
    if 'consumerEligible' in doc:require(doc.get('consumerEligible') is False,f'Candidate consumer eligibility drifted in {path.relative_to(ROOT)}')
def main():
    contract=load(CONTRACT);manifest=load(MANIFEST);lifecycle=load(LIFECYCLE);require(VERSION.read_text().strip()=='1.1.0','VERSION no longer preserves V1.1 Stable');require(lifecycle.get('currentStable')=='1.1.0' and lifecycle.get('currentOfficial')=='1.1.0','lifecycle no longer preserves V1.1 Stable/Official');v12=next((x for x in lifecycle.get('releases',[]) if x.get('version')=='1.2.0-candidate'),None);require(isinstance(v12,dict) and v12.get('status')=='candidate' and v12.get('consumerEligible') is False,'V1.2 lifecycle boundary drifted')
    for doc,name in ((contract,'contract'),(manifest,'manifest')):require(doc.get('version')=='1.2.0-candidate' and doc.get('lifecycle')=='candidate' and doc.get('consumerEligible') is False and doc.get('stableBaseline')=='1.1.0',f'core token {name} boundary drifted')
    for key in ('semanticRolesBeforeRawValues','singleOwnerPerFamily','compositionManifestDoesNotDuplicateRawValues','candidateDoesNotReplaceStable','unimplementedFamiliesRemainExplicitlyUnestablished','platformAdaptersMayMapButNotRedefineSemanticAuthority'):require(contract['principles'].get(key) is True,f'core token principle missing: {key}')
    aliases=manifest.get('aliases',{});families=contract.get('families',{});require(set(families)==set(EXPECTED)|UNESTABLISHED,f'core token family set drifted: {sorted(families)}');require(set(aliases)=={x[0] for x in EXPECTED.values()},f'core token alias set drifted: {sorted(aliases)}');require(not RAW_VALUE.search(json.dumps(aliases,sort_keys=True)),'core composition manifest copied raw token values');require(manifest.get('unestablished')=={},'resolved core token map retains stale unestablished family entries')
    sources={};resolved={}
    for family,(alias_name,source,p,status) in EXPECTED.items():
        item=families[family];alias=aliases[alias_name];require(item.get('status')==status and item.get('owner')==source and item.get('pointer')==p,f'ownership drifted for {family}');require(alias=={'source':source,'pointer':p},f'alias drifted for {family}');path=ROOT/source
        if source not in sources:
            sources[source]=load(path)
            if source.startswith('tokens/glaze-v1.2-'):validate_candidate(path,sources[source])
        require(pointer(sources[source],p) not in ({},[],None,''),f'alias resolved to empty authority for {family}');resolved[family]=f'{source}#{p}'
    semantic=sources['tokens/semantic-colors.json'];require(semantic.get('color_only_communication_allowed') is False and semantic.get('branding_may_override_semantics') is False,'semantic-color invariants drifted')
    state=sources['tokens/glaze-v1.2-states.candidate.json']['states'];require(state['hover']['overlayOpacity']==0.045 and state['pressed']['overlayOpacity']==0.095 and state['selected']['overlayOpacity']==0.12 and state['disabled']['opacity']==0.55,'state calibration drifted');require(state['focus']['widthPx']==3 and state['focus']['offsetPx']==2 and state['focus']['increasedContrastWidthPx']==4,'focus state calibration drifted');require(state['semantic']['colorOnlyMeaningProhibited'] is True and state['recovery']['authoritativeUnderlyingStateRequired'] is True,'state truth invariants drifted');require(families['state'].get('consumerClaimBlocked') is True,'state Candidate consumer boundary drifted')
    form=sources['tokens/glaze-v1.2-form-factor.candidate.json'];require(list(form['compositionStates'])==['compact','medium','expanded','largeFarView','wearable','spatial'],'form-factor composition-state authority drifted');require(form['adaptationRules']['platformAdapterOwnsCapabilitySelection'] is True and form['adaptationRules']['widthIsDeviceIdentity'] is False,'form-factor capability-selection invariants drifted');require(form['rules']['numericGuttersRemainSpatialTokenAuthority'] is True and form['rules']['densityRemainsSpatialTokenAuthority'] is True,'form-factor token authority duplicated spatial numeric ownership');require(families['formFactor'].get('consumerClaimBlocked') is True,'form-factor Candidate consumer boundary drifted')
    for family in UNESTABLISHED:
        item=families[family];mirror=manifest.get('unestablished',{}).get(family,{});require(item.get('owner') is None and item.get('pointer') is None and item.get('consumerClaimBlocked') is True,f'unestablished family incorrectly claims ownership: {family}');require(mirror.get('consumerClaimBlocked') is True,f'manifest unestablished boundary drifted: {family}')
    require(all(spec.get('source')!='tokens/states.json' for spec in aliases.values()),'unrelated lifecycle state tokens were imported as V1.2 authority')
    for key in ('aliasesResolveToExistingSources','aliasesContainNoCopiedRawValues','oneFamilyOneOwner','unestablishedFamiliesCannotBePresentedAsImplemented','semanticColorMeaningDoesNotAuthorizeHardCodedPigment','candidateCannotBecomeConsumerTargetByManifestPresence'):require(manifest['rules'].get(key) is True,f'manifest rule missing: {key}')
    readme=README.read_text(encoding='utf-8');
    for marker in ('V1.1 / `1.1.0`','glaze-v1.2-core.candidate.json','non-consumer-eligible','does not duplicate raw token values','glaze-v1.2-states.candidate.json','glaze-v1.2-form-factor.candidate.json','capability-class selection remains platform-adapter owned'):require(marker in readme,f'token authority documentation missing marker: {marker}')
    ART.mkdir(exist_ok=True);REPORT.write_text(json.dumps({'id':contract['id'],'version':contract['version'],'lifecycle':contract['lifecycle'],'stableBaseline':contract['stableBaseline'],'consumerEligible':contract['consumerEligible'],'resolvedFamilies':resolved,'unestablishedFamilies':sorted(UNESTABLISHED),'result':'pass'},indent=2,sort_keys=True)+'\n');print(f'GLAZE UI V1.2 core token authority validated: {len(resolved)} resolved families; {len(UNESTABLISHED)} explicitly unestablished');return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except ValidationError as e:print(f'GLAZE UI V1.2 core token authority validation failed: {e}');raise SystemExit(1)
