# NOTICE — Motion Design

- Upstream: https://github.com/LottieFiles/motion-design-skill
- Accepted ref: `main`
- Accepted commit: `f9a8a041b85185ee4881b3471d3415e939aac772`
- License: MIT
- Copyright: Copyright (c) 2025 LottieFiles
- License text: `maintainer/upstreams/provenance/lottiefiles-motion-design/LICENSE`
- License SHA-256: `9fc2e8685daa09e28d54b6afa8a38f168417c5735a3cd676c80c159785e93a80`

The upstream publishes no releases and no tags. A branch head commit is the only
available pin. The pinned commit was authored on 2026-05-18.

## Relationship group

| Source id | Mode | Local target | Packaged |
|---|---|---|---|
| `lottiefiles-motion-design-runtime` | `adapted` | `skills/motion-design` | yes |
| `lottiefiles-motion-design-principles` | `reference` | existing design and verification skills | no |

## Import scope

Imported: `skills/motion-design/SKILL.md`, `director/**` (8 files),
`patterns/**` (4 files), `reference/**` (4 files).

Not imported: repository `README.md` and `.gitignore`.

The upstream carries no executable code. The local skill stays
instruction-and-reference-only.

## Third-party material inside the upstream

The upstream top-level MIT license cannot grant rights the upstream author does
not hold. The following third-party references were reviewed per file.

| File | Cited material | Form | Assessment |
|---|---|---|---|
| `reference/timing-easing-tables.md` | Material Design 3 easing curves, Apple HIG easing and spring values | numeric parameter values in comparison tables | Functional and factual values rather than protected expression. Retained with attribution. Do not expand into copied prose or whole guideline tables. |
| `director/disney-principles.md` | Disney twelve principles of animation | concept names with upstream-authored explanation | Principle names are facts and the surrounding prose is the upstream author's MIT-licensed text. |
| `reference/quality-checklist.md` | Apple HIG | reference mention | No reproduction. |

## Local modification summary

The local `SKILL.md` is rewritten for this harness. It classifies motion purpose
first, allows skipping motion when a static screen is sufficient, prefers an
existing product motion language over new rules, defaults public, medical,
financial and enterprise screens to low motion density, and requires a
reduced-motion alternative. Upstream knowledge files are preserved; any local
change is recorded in `file-map.json`.
