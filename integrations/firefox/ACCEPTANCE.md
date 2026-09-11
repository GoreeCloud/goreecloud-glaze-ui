# Firefox Glaze UI Runtime Acceptance

## Status

Source validation is automated. Runtime acceptance remains **pending** until results are recorded for representative supported Firefox desktop lines.

A real Firefox Release workstation baseline has now been exercised on August 20, 2026. Firefox 154.0 Flatpak on Zorin OS 17.3 / GNOME / Wayland loads the canonical `userChrome.css`, remains functional across the tested browser surfaces, and has completed a successful canonical light-mode visual pass. It does **not** yet promote the Release track to accepted because dark appearance, accessibility modes, private browsing, warning/security surfaces, rollback, update compatibility, and ESR remain outstanding.

## Target Matrix

| Track | Target | Status | Notes |
| --- | --- | --- | --- |
| Firefox Release | Firefox 153 or newer current Release | In progress | Firefox 154.0 Flatpak on Zorin OS 17.3 / GNOME / Wayland has passed canonical light-mode browser-chrome testing across tabs, URL bar, suggestions, menus, normal browsing, and Firefox internal pages. Remaining dark/accessibility/security/rollback/update scenarios are still pending. |
| Firefox ESR | Firefox ESR 140 current security-supported point release | Pending | Validate long-lived ESR behavior separately from rapid Release. |

The matrix must be updated when Mozilla changes supported release lines. A version appearing here is a validation target, not a claim that GoreeCloud controls Mozilla's support lifecycle.

## Observed Firefox 154 Baseline — August 20, 2026

Environment observed directly during workstation testing:

- Firefox 154.0, Flatpak application ID `org.mozilla.firefox`, Flathub stable, system installation.
- Zorin OS 17.3 on Lenovo IdeaPad 3 15IIL05.
- GNOME-based Zorin desktop on Wayland.
- Active Firefox profile explicitly identified before modification.
- No pre-existing `chrome/` directory and no pre-existing legacy user-stylesheet preference were present before the test.
- Firefox was fully stopped before profile-level customization was created.

Observed functional results:

- Custom `userChrome.css` loading was visibly confirmed.
- Canonical Glaze UI 1.4 browser chrome was installed from `GoreeCloud/glaze-ui` main and exercised successfully in light appearance.
- Active and inactive tabs remained usable and distinguishable.
- Navigation buttons and the address bar remained usable.
- URL-bar focus, typing, and suggestions remained readable and functional.
- Bookmarks toolbar remained usable.
- Application menu, Firefox account/sync panel, extension-related panels, and Multi-Account Containers panel remained readable and functional.
- `about:preferences` and `about:addons` remained usable.
- Normal web content, including GoreeCloud, Wardveil Security, Projects, and ChatGPT pages, rendered without browser-chrome overlap or clipping.
- Native Firefox/site identity and security controls remained recognizable and were not cosmetically relabeled as GoreeCloud security state.

### Cache-isolation finding

During the canonical light-mode pass, `projects.goreecloud.com` initially showed partially stale presentation in the normal Firefox window while rendering correctly in a new Private Window and in another browser. A Firefox hard reload with `Ctrl+Shift+R` immediately restored the correct current site presentation. The incident is therefore recorded as stale cached frontend assets in the normal Firefox profile, not a Firefox Glaze `userChrome.css` regression and not a Projects source compatibility defect. No Projects source patch, Firefox permission change, extension removal, or profile-data reset was required.

Observed refinement conclusions:

- The canonical refinement correctly avoids treating the full navigation row as one oversized capsule; Glaze geometry is concentrated on functional controls.
- Selected-tab hierarchy is clearer while inactive tabs remain quiet.
- Firefox 154 expanded URL suggestions now integrate with the address field without a competing outer popup border.
- Bookmarks remain secondary to navigation chrome.
- Native Firefox identity, permission, certificate, account, private-browsing, download, update, and warning semantics must continue to remain authoritative.
- Dark appearance and Wayland fallback behavior still require target-workstation acceptance.

The screenshots used for this baseline were reviewed interactively and are not embedded in the repository. They establish light-mode runtime progress, not final Release acceptance.

## Required Scenarios

For each target track, record pass/fail evidence for light and dark appearance; tab strip and active/inactive tabs; URL/search focus, typing, selection, suggestions, and identity/security indicators; navigation and toolbar actions; bookmarks toolbar; application menu and transient panels; sidebar; downloads; private browsing; certificate, permission, download, update, and warning indicators; keyboard-only navigation and visible focus; increased contrast or forced-colors where the platform exposes it; reduced motion; 200% zoom/reflow where applicable; and rollback by removing the theme and optional `userChrome.css` without profile-data loss.

## Runtime Tooling

Build the deterministic local-test theme package first:

```text
python3 integrations/firefox/build_theme.py
```

The optional deeper chrome layer can be installed only into an explicitly supplied Firefox profile:

```text
python3 integrations/firefox/install_userchrome.py --profile /exact/firefox/profile --install
python3 integrations/firefox/install_userchrome.py --profile /exact/firefox/profile --verify
python3 integrations/firefox/install_userchrome.py --profile /exact/firefox/profile --remove
```

The installer never guesses a Firefox profile, never edits `prefs.js` or `user.js`, and retains a timestamped backup before replacing or removing an existing `userChrome.css`. Firefox preference `toolkit.legacyUserProfileCustomizations.stylesheets` must be enabled separately by the tester when the optional layer is used.

Create a privacy-preserving evidence record before manual scenario testing:

```text
python3 integrations/firefox/collect_acceptance.py \
  --track release \
  --theme-package integrations/firefox/dist/glaze-ui-firefox-0.2.0.xpi \
  --userchrome enabled \
  --desktop "Zorin GNOME / Wayland" \
  --output firefox-release-acceptance.md
```

Run the same process separately for ESR with `--track esr`. The evidence helper records environment and package metadata plus an unchecked scenario checklist; it does not read Firefox history, bookmarks, cookies, credentials, URLs, tabs, or profile contents.

## Acceptance Rules

A Firefox runtime is accepted only when all required scenarios pass or a documented material exception is approved. Cosmetic consistency must never override Firefox security, identity, permission, update, private-browsing, or warning behavior. `userChrome.css` failures are allowed to fall back to the supported theme layer rather than forcing unsafe browser-chrome overrides.

The supported Firefox theme and optional `userChrome.css` layer must be evaluated independently enough that a `userChrome.css` selector regression can be disabled without invalidating an otherwise safe supported-theme experience.

A site rendering defect that disappears after a cache-bypassing hard reload or only reproduces in a stale normal-window cache must be isolated from browser-chrome acceptance before source changes are made to the site or Firefox integration.

## Evidence Record

Record the exact Firefox version, operating system and desktop environment, Glaze UI repository commit, theme package SHA-256, whether `userChrome.css` was enabled, canonical `userChrome.css` SHA-256 when enabled, tested appearance/accessibility modes, failures and corrections, rollback result, and final acceptance decision.
