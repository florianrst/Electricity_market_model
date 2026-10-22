# Privacy definition (used by data-privacy-gate)

Private / must never be committed:
- `.env` and any `.env.*` except `.env.example` (API credentials: RTE, ENTSO-E, Meteo-France)
- `data/` contents (raw/interim/processed downloads), except `.gitkeep` files
- Trained model artifacts and experiment outputs
- Any hardcoded token, client id/secret, or bearer token in code, notebooks (including cell outputs) or configs

Checks:
- Verify the above paths are matched by `.gitignore` and not tracked (`git ls-files`).
- Grep tracked files and notebook outputs for token-like strings and `Authorization: Bearer`.
- Flag absolute home paths containing a real username in committed files.
