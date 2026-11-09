# AGENTS.md

Instructions for coding agents working in this repository. Everything here was checked against the repo. Deeper context is linked at the end.

## Project

Magpie is a self-hosted media tracker for movies, TV shows, anime, manga, video games, books, comics and board games. It is a fork of [Yamtrack](https://github.com/FuzzyGrim/Yamtrack) that adds groups, public profiles, roulette, recommendations and a REST API. Stack: Django 5.2 on Python 3.12, Celery with Redis for background jobs, Tailwind CSS for styling, SQLite by default or PostgreSQL.

## Layout

The Django project lives in `src/`, where `manage.py` is. Tests live in each app's `tests/` directory.

- `config/`: settings (`settings.py`, `test_settings.py`), root URLs, Celery app, gunicorn config.
- `app/`: media tracking core: models, metadata providers, views, Home, statistics, roulette, recommendations.
- `users/`: accounts, public profiles and per-section visibility.
- `groups/`: shared group progress and discards.
- `lists/`: user lists and their items.
- `integrations/`: imports, exports and media-server webhooks.
- `api/`: REST API mounted at `/api/v1/`, serializers, token auth.
- `events/`: release calendar and notifications.
- `templates/`: Django templates, with per-app subfolders and `base.html`.
- `static/`: assets. `static/css/input.css` is the Tailwind source. `static/css/main.css` is the built stylesheet and is committed.
- `db/`: runtime SQLite database and uploads (`db/media/`). Never commit it.

At the repo root: `docs/` (Zensical site), `.github/workflows/`, `Dockerfile`, `docker-compose*.yml`, `Procfile`, `pyproject.toml` (dependencies, ruff, djlint), `openapi.yaml`.

## Setup

You need `uv`, Python 3.12 (`.python-version`), Redis (`redis:8-alpine` in the compose files), and the Tailwind CLI for CSS (`npm install -g tailwindcss @tailwindcss/cli`). Put local settings in a `.env` file at the repo root. See `docs/development.md` and `docs/env-variables.md`.

```bash
uv sync                          # Python dependencies from pyproject.toml
uv run pre-commit install        # git hooks
cd src && uv run manage.py migrate
```

## Commands

Commands come from `Procfile`, `docs/development.md` and `.github/workflows/`. Run Python commands from `src/` unless noted.

Run the app:

```bash
cd src && uv run manage.py runserver                 # http://localhost:8000
cd src && uv run celery -A config worker --beat --scheduler django --loglevel DEBUG
uvx honcho -e /dev/null start                        # web, worker and css together, from the root Procfile
```

Test:

```bash
cd src && uv run manage.py test --parallel           # full suite
cd src && uv run manage.py test app.tests --parallel # one app or module
uv run playwright install                            # once, for the browser tests
```

No environment variables are needed for tests. `manage.py` switches to `config.test_settings`, which uses fakeredis instead of Redis. The database is SQLite unless `DB_HOST` is set. CI (`app-tests.yml`) runs the full suite, every app included.

Lint and format (the `lint` group, as in `lint.yml`):

```bash
uv run ruff check src                                # add --fix to apply fixes
uv run ruff format --check src                       # drop --check to reformat
uv run pre-commit run --all-files                    # all hooks: migrations, uv lock, django-upgrade, ruff, djlint
```

Docs (the `docs` group, as in `build-docs.yml`):

```bash
uv sync --group docs
uv run zensical serve                                # live preview
uv run zensical build                                # one-off build into site/
```

CI publishes docs on push to `dev` with `uv run mike deploy --push <branch>`. Running that locally is not part of the normal workflow.

CSS: `src/static/css/input.css` imports Tailwind with `source("../../")`, so it scans `src/` for classes. After changing templates or styles, rebuild and commit `main.css`:

```bash
cd src && tailwindcss --input ./static/css/input.css --output ./static/css/main.css
cd src && tailwindcss --input ./static/css/input.css --output ./static/css/main.css --watch
```

`docs/development.md` names `tailwind.css` as the output. That is wrong. `templates/base.html` loads `css/main.css`.

Containers: `docker compose up -d` runs the published image from `docker-compose.yml`. `docker-compose.postgres.yml` adds PostgreSQL.

## Git

- `dev` is the default branch and the integration branch. There is no `release` branch on origin yet, although `build-docs.yml` and `codeql.yml` already reference it; it will be recreated for the first release.
- Branch from `dev` with a short name: `feat/…`, `fix/…`, `docs/…` or `spike/…` (`docs/BRANCHING.md`).
- No pull requests and no merge commits. Rebase the branch onto `dev`, validate, then run `git checkout dev && git merge --ff-only <branch>`. Never create worktrees under `/tmp`.
- Before merging, lint and format must pass, the tests for the touched apps must pass, and so must the full suite. The test count may go up, never down.
- Commit subjects use Conventional Commits with a lowercase scope, for example `feat(groups): …`, `fix(api): …`, `ci(docs): …`, `docs: …`, `chore: …`. 59 of the last 60 subjects on `dev` follow this.
- Release tags are `fork-v*`. They build the release image in `.github/workflows/docker-image.yml`. No `fork-v*` tag exists yet. Upstream `v*` tags are not fork releases.
- Do not commit, push or tag unless asked. Never push to the `upstream` remote.

## Rules

- Env vars: new variables use the `MAGPIE_` prefix. The `YAMTRACK_` to `MAGPIE_` rename is complete, and no `YAMTRACK_` remains in tracked files. Settings such as `SECRET`, `REDIS_URL`, `DB_*` and `DEBUG` are unprefixed and used by existing deployments, so do not rename them.
- Never commit `src/db/`. Only `src/db/db.sqlite3` and `src/db/media` are gitignored. Backups such as `db.sqlite3.bak-*` are not, so stage files by name and never use `git add -A`.
- A model change ships with its migration. Run `cd src && uv run manage.py makemigrations`. `makemigrations --check` must report no changes; the pre-commit `check-migrations` hook runs it.
- Keep the Yamtrack credit in `README.md` and the FuzzyGrim copyright in `zensical.toml`.
- Docs live in `docs/`. The top of `README.md` is included into `docs/index.md` by its markers `<!-- --8<-- [start:docs-index-intro] -->` through `[end:docs-index-intro]`, and `docs-index-body`. Keep those markers and their names. Renaming them drops the intro from the docs site.
- No AI attribution anywhere. Commits are authored by the maintainer alone. Do not add `Co-Authored-By`, `Signed-off-by` or `Generated-by` trailers. Do not mention any tool or model name, or any "generated with" footer, in commits, PR titles or descriptions, code comments, docs or changelogs.

## Further reading

- `docs/development.md`: setup, running and testing in detail.
- `docs/BRANCHING.md`: the branch and integration workflow used day to day.
- `docs/FORK-MAINTENANCE.md`: syncing with upstream Yamtrack. It says its procedure has not been dry-run.
- `docs/adr/`: product decisions, written in Spanish. `0001` covers scope and `0002` covers the groups UI.
- `docs/env-variables.md`: every environment variable.
