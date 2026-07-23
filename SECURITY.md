# Security policy

## Supported versions

Security fixes are applied to the latest release.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose secrets, execute unintended commands, or overwrite files. Use GitHub's private vulnerability reporting for this repository.

Include the affected version, operating system, command, expected behavior, and a minimal reproduction with secrets removed.

## Security boundary

The helper reads coarse local resource information and runs only the command the user or coding agent explicitly supplies. It does not send telemetry, inspect file contents, enumerate unrelated processes, kill processes, delete caches, change system settings, or enforce operating-system resource limits.
