# Third-Party Notices

This repository includes adapted skills derived from MIT and Apache-2.0 sources.

The project itself is licensed under Apache-2.0; see `LICENSE` and `NOTICE`. The
components below keep their own upstream licenses, reproduced in full under
`licenses/` in the plugin archive.

## UI/UX Pro Max

- Source ID: `ui-ux-pro-max-runtime`
- Upstream: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- Accepted ref: `v2.13.0`
- Accepted commit: `4d140cf8ff6842de13213c7214eff3810371beb2`
- License: MIT, Copyright (c) 2024 Next Level Builder
- Adapted user skill: `skills/ui-ux-pro-max`
- Notice details: `maintainer/upstreams/provenance/ui-ux-pro-max/NOTICE.md`

The generated upstream skill tree is imported. `data/`, `references/` and
`scripts/` are preserved unchanged; `SKILL.md` is rewritten for platform-neutral
paths, project-scope confirmation, approval-gated persistence and public skill
handoff. The upstream generator, its TypeScript CLI and six sibling skills are
not imported.

## Motion Design

- Source ID: `lottiefiles-motion-design-runtime`
- Upstream: https://github.com/LottieFiles/motion-design-skill
- Accepted ref: `main`
- Accepted commit: `f9a8a041b85185ee4881b3471d3415e939aac772`
- License: MIT, Copyright (c) 2025 LottieFiles
- Adapted user skill: `skills/motion-design`
- Notice details: `maintainer/upstreams/provenance/lottiefiles-motion-design/NOTICE.md`

`director/`, `patterns/` and `reference/` are preserved unchanged; `SKILL.md` is
rewritten for purpose-first classification, optional motion, low motion density
on public, medical, financial and enterprise screens, mandatory reduced-motion
alternatives and evidence-backed layout-triggering properties.

The upstream reference material cites Material Design 3, Apple Human Interface
Guidelines and the Disney animation principles. Rights in that third-party
material remain with their respective owners; the upstream MIT grant does not
extend to rights the upstream author does not hold. Per-file assessments are
recorded in the notice file above.

## im-not-ai

- Upstream: https://github.com/epoko77-ai/im-not-ai
- Version: v2.3.0
- Commit: 82137e858763dadb99561f194c5c00465735017b
- License: MIT
- Local skill: `skills/humanize-korean`
- Notice details: `maintainer/upstreams/provenance/im-not-ai/NOTICE.md`

The local adaptation does not vendor the full upstream runtime. It keeps only harness-safe adapted guidance, local references, a deterministic guard script, and provenance records.

## Anthropic Skills

- Source ID: `anthropic-frontend-design`
- Upstream: https://github.com/anthropics/skills
- Accepted ref: `main`
- Accepted commit: `b29e7cf65e5cb78a5ac33d582270551bc74a14eb`
- License: Apache-2.0
- Adapted user skill: `skills/frontend-design`
- Adapted manager-only skill: `maintainer/skills/custom-skill-design`
- Notice details: `maintainer/upstreams/provenance/anthropic-skills/NOTICE.md`

The local files are translated, shortened and reorganized for this harness. `frontend-design`
adds project-scope routing and implementation verification. `custom-skill-design` adds the
manager repository, projection and plugin-release workflow. The manager skill is not included in
the user plugin.
