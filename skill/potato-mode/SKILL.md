---
name: potato-mode
description: Keep Claude Code or Codex responsive on older, low-spec, memory-constrained, disk-constrained, or already-busy computers. Use when the user mentions low RAM, weak CPU, old laptop, potato PC, limited disk, freezes, overheating, out-of-memory kills, slow builds, too many workers, duplicate dev servers, or needing an AI coding agent to use fewer local resources.
---

# Potato Mode

Adapt local execution to the machine's current headroom. Reduce resource spikes without lowering code quality or skipping relevant verification.

## Start the mode

1. Say `Potato mode active.`
2. Resolve this skill's directory from the loaded `SKILL.md`.
3. Probe the current project volume and machine:

```bash
python3 <skill-dir>/scripts/potato.py probe --path <project-root>
```

On Windows, use `py -3` when `python3` is unavailable.

4. Use the reported tier and worker limit for this task. Treat a probe as a snapshot, not a hardware benchmark.
5. Inspect existing dev servers, test runners, watchers, and build processes before starting another long-lived process. Never kill an unrelated process automatically.

## Work by tier

### Critical

- Use one worker.
- Avoid broad builds, full test suites, local containers, and duplicate servers while a lighter path exists.
- Work in small checkpoints. Run the smallest useful verification after each checkpoint.
- Before a necessary heavy command, tell the user what may become slow or unresponsive and offer the lightest viable alternative.

### Constrained

- Use one worker for builds and tests.
- Prefer targeted tests, one package or workspace at a time, and existing caches.
- Run the full suite only at the end when it is relevant.

### Balanced

- Use no more than the reported worker limit.
- Start with focused checks, then broaden after they pass.
- Avoid simultaneous builds, test suites, and dev servers unless the task needs them.

### Roomy

- Respect the reported worker limit. Do not assume unlimited headroom.
- Parallelize independent lightweight checks, but avoid starting duplicate long-lived processes.

## Run resource-limited commands

Use the helper for commands that honor common worker environment variables:

```bash
python3 <skill-dir>/scripts/potato.py run --path <project-root> -- <command> [args...]
```

The wrapper sets conservative values for `MAKEFLAGS`, `CARGO_BUILD_JOBS`, `RAYON_NUM_THREADS`, `GOMAXPROCS`, and common test-worker variables. It does not impose operating-system limits or promise a command cannot exhaust memory.

## Execution rules

- Reuse existing lockfiles, dependencies, caches, and dev servers.
- Do not clear caches merely to free space. Identify their owner, size, and rebuild cost first.
- Avoid unnecessary dependency upgrades, clean builds, whole-repository formatting, and watch mode.
- Prefer streaming or chunked processing over loading large files or datasets at once.
- Prefer targeted searches and explicit paths over scanning generated directories.
- Do not run Docker, emulators, browser farms, local AI models, or multiple agents by default on a constrained tier.
- Do not silently weaken correctness checks. Explain when a full check is deferred, and leave the exact command for later.
- Re-probe after an out-of-memory kill, disk-full error, severe slowdown, thermal warning, or the user closes other heavy applications.
- Do not claim exact RAM, CPU, disk, temperature, or energy use unless measured.

## End the task

Report only what helps the user continue:

```text
Mode: <tier, worker limit>
Verified: <checks completed>
Deferred: <heavy check not run, or none>
Run later: <exact command, or none>
```

## Limits

This mode controls how the coding agent uses local tools. It cannot reduce the cloud model's compute use, fix failing hardware, read temperatures consistently across platforms, or guarantee that third-party commands respect worker settings.
