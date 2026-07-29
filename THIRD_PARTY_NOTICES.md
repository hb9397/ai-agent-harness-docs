# Third-Party Notices

This repository includes adapted skills derived from MIT and Apache-2.0 sources.

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
