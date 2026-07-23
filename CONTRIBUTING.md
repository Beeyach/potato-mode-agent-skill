# Contributing

Thank you for helping Potato Mode work on more machines and toolchains.

Useful contributions include:

- Resource probes for platforms the current helper cannot inspect.
- Build or test tools that respect worker environment variables.
- Fixtures for out-of-memory, disk-full, and overload failures.
- Threshold changes backed by measurements from real machines.
- Clearer instructions for Claude Code, Codex, and other Agent Skills clients.
- Accessibility and localization improvements.

## Before opening a pull request

1. Keep the helper dependency-free. Use the Python standard library.
2. Do not add code that kills processes, clears caches, or changes system settings automatically.
3. Add or update tests for behavior changes.
4. Run `python -m unittest discover -s tests -v`.
5. Run `python skill/potato-mode/scripts/potato.py probe --path .` on your platform.
6. Explain the machine, operating system, and failure or improvement you observed. Do not include usernames, tokens, private paths, or unrelated process details.

## Threshold changes

Resource tiers are intentionally conservative. A threshold pull request should include:

- The workload tested.
- Total and available memory.
- CPU thread count.
- Free disk space.
- Whether the machine remained responsive.
- The before-and-after tier or worker recommendation.

Synthetic data is welcome for tests. Label it as synthetic.
