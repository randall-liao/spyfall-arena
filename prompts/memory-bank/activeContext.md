# Active Context

## Current Focus
- Implementing Gitleaks for secret scanning.
- Configuring pre-commit hooks and CI pipelines.

## Recent Changes
- Added `pre-commit` as a dev dependency.
- Created `.pre-commit-config.yaml` with Gitleaks hook (v8.29.1).
- Added `.gitleaks.toml` with default rules.
- Created `scripts/setup-git-hooks.sh` for easy installation.
- Created `.github/workflows/gitleaks.yml` for CI verification.
- Updated `README.md` with security instructions.

## Active Decisions
- **Gitleaks Version:** Pinned to v8.29.1 (latest stable at implementation).
- **CI Provider:** GitHub Actions chosen as the primary CI platform.
- **Configuration:** Using default Gitleaks rules maintained in `.gitleaks.toml` in the repo root.
