# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project scaffolding
- Backend API with FastAPI (health, entity, search, stats endpoints)
- SQLite + FTS5 database schema
- SvelteKit frontend with Tailwind CSS
- Docker Compose configuration
- GitHub Actions CI with TruffleHog secrets scanning
- Taskfile for development tasks
- Lefthook git hooks with pre-push secrets scanning
- File length limits check script

### Coming Soon
- Wikidata dump importer
- Write-through cache for API fallback
- Helm chart for Kubernetes deployment
