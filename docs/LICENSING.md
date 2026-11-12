# Licensing and compatibility

This project is licensed under **Apache-2.0** (see `LICENSE`). This page records why that does not clash with the other software in the stack. It is a good-faith engineering summary, not legal advice. Licences below are from memory and must be re-checked when each dependency is added (tracked in Phase 1 CI via a licence report).

| Component | Licence | Relationship | Clash with Apache-2.0? |
|-----------|---------|--------------|------------------------|
| Jellyfin server | GPL-2.0 | Separate container, pulled by the user's Docker. We talk to it only over its HTTP API. We do not link, copy or redistribute its code or images. | No. Network API use between separate programs does not make ours a derivative work. |
| Jellyfin plugins (AniList, etc.) | mostly GPL | Installed by the user into their own Jellyfin, opt-in. Not shipped in this repo. | No, as long as we never vendor them. |
| `guessit` | LGPL-3.0 | Imported as an unmodified Python library dependency, installed from PyPI. | No. LGPL permits use by non-GPL code. We must not vendor or modify it without following LGPL terms. |
| FastAPI, Starlette, Pydantic, httpx, SQLAlchemy, Alembic, Jinja2, HTMX | MIT / BSD | Dependencies. | No. |
| TMDB API | Terms of use, not a code licence | User supplies their own key. Requires attribution and non-commercial use. | N/A. Attribution text will be shown in the UI and README. |
| AniList API | Terms of use | Same as above. | N/A. |

Rules for contributors:
- Do not copy GPL code into this repo.
- Do not commit Jellyfin or plugin binaries.
- New dependencies must be MIT, BSD, Apache-2.0, ISC, MPL-2.0, or LGPL used as an unmodified library. Anything else needs discussion first.
