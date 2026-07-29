# im-not-ai adapted source snapshot

This directory records the storage-safe source basis accepted for the local `humanize-korean` skill.

The full upstream repository is not vendored. Phase 4 promotes only:

- a locally rewritten `skills/humanize-korean/SKILL.md`
- reduced local references under `skills/humanize-korean/references/`
- a deterministic local guard script under `skills/humanize-korean/scripts/`
- notice/license/provenance metadata under `maintainer/upstreams/provenance/im-not-ai/`

Accepted upstream:

- repository: https://github.com/epoko77-ai/im-not-ai
- tag: v2.3.0
- commit: 82137e858763dadb99561f194c5c00465735017b

Semantic adaptation note:

- Upstream v2.3.0 requires evidence-based, span-level edits and leaves text without
  a mapped finding unchanged.
- The local deterministic helper cannot decide the discourse role of
  `~를 통해`, `~에 의해`, or `결론적으로`.
- Those expressions are therefore reported as context-review diagnostics with
  possible rewrites; they are not unconditional string replacements.
- The agent, not the helper script, decides whether to preserve, delete, or
  rewrite a diagnosed span after checking its sentence and paragraph context.
