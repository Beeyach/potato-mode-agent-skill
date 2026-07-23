# Potato Mode

**A resource-aware Agent Skill for Claude Code and OpenAI Codex on older, low-spec, memory-constrained, disk-constrained, or already-busy computers.**

Potato Mode changes how a coding agent uses your machine. It checks current headroom, chooses a conservative worker limit, runs focused checks before broad ones, reuses caches and dev servers, and warns before work likely to make the computer unresponsive.

It does not make code quality optional. If a full check is too heavy right now, the agent says what it deferred and leaves the exact command to run later.

## What it changes

- Measures available memory, free disk, visible CPU threads, and current one-minute load.
- Classifies the machine as `critical`, `constrained`, `balanced`, or `roomy`.
- Gives the agent a safe worker limit for the current conditions.
- Passes that limit to Make, Cargo, Rayon, Go, pytest-xdist, and uv when using the included wrapper.
- Starts with targeted tests and builds before widening the scope.
- Reuses installed dependencies, caches, and existing dev servers.
- Avoids duplicate watchers, containers, emulators, browser farms, and concurrent heavy jobs.
- Rechecks the machine after an out-of-memory kill, disk-full error, or severe slowdown.

## What it will not do

- Kill unrelated processes.
- Delete caches automatically.
- Pretend every command obeys worker environment variables.
- Guarantee a third-party build cannot run out of memory.
- Reduce cloud-model compute use or repair failing hardware.

## Example

```text
/potato-mode

Potato mode active.

Potato tier: constrained
Worker limit: 1
Memory: 2860 MiB available
Disk free: 9112 MiB

I’ll run the affected package’s tests first, reuse the current dev server,
and leave the full browser suite until the end.
```

In Codex, mention it with `$potato-mode` or let the description trigger it automatically.

## Install

Python 3.10 or newer is required for the bundled local probe.

### Interactive installer

Clone the repository and run:

```bash
python3 install.py
```

On Windows, use:

```powershell
py -3 install.py
```

Choose Claude Code, Codex, or both. The installer uses the current personal skill locations:

- Claude Code: `~/.claude/skills/potato-mode`
- Codex: `~/.agents/skills/potato-mode`

### Project-only install

```bash
python3 install.py --target claude --scope project --project /path/to/repo
python3 install.py --target codex --scope project --project /path/to/repo
```

Project locations:

- Claude Code: `<repo>/.claude/skills/potato-mode`
- Codex: `<repo>/.agents/skills/potato-mode`

### Manual install

Copy the entire `skill/potato-mode` directory into one of the locations above. Keep `SKILL.md` and `scripts/potato.py` together.

## Use the probe directly

```bash
python3 skill/potato-mode/scripts/potato.py probe --path .
python3 skill/potato-mode/scripts/potato.py probe --path . --json
```

Run a cooperative command with the recommended worker limit:

```bash
python3 skill/potato-mode/scripts/potato.py run --path . -- npm test
```

The wrapper uses environment variables. It is not an operating-system sandbox or hard resource limit.

## Why this exists

AI coding instructions often assume spare RAM, fast storage, many CPU cores, multiple parallel agents, a fresh dependency install, and room for several dev servers. Those defaults are painful on older laptops, shared machines, containers, small virtual machines, and computers already doing other work.

Potato Mode makes the agent inspect the machine it actually has before choosing how aggressively to work.

## Search terms this project covers

Low RAM Claude Code, Codex on old laptop, low-spec AI coding, reduce Claude Code CPU usage, reduce Codex memory usage, resource-aware coding agent, limit build workers, prevent AI coding freezes, coding agent for weak PC, vibe coding on low-end hardware.

## Contributing

Hardware and build tools vary. Contributions are welcome for new platform probes, package managers, build systems, resource-failure fixtures, and tested thresholds. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
