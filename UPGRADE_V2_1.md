# Aanya Trend Hunter v2.1 — safe incremental upgrade

This is an **intermediate local upgrade**, not a production-ready public deployment.

## What changed
- Top **10** video candidates in a three-column visual gallery.
- Conservative Gen Z topic classifier; generic `trend`, `girl`, or `shorts` alone no longer qualify.
- Explicit exclusion of food, politics, AI influencer content.
- Ranking prioritizes observed public **views**, then topical evidence; at most two picks per category until the second pass.
- Saved archive no longer disappears when you change the dashboard filters.
- Optional `PUBLIC_MODE` and admin password gate for edits; not a replacement for production authentication.
- No database schema migrations or destructive operations.

## Preserve existing data
1. Close the running Streamlit app and stop collectors.
2. Back up the **entire existing project**, including hidden `.env`, `.venv`, and `data/trends.db` (also `trends.db-wal` and `trends.db-shm` if present).
3. Extract this ZIP **to a different folder**. Do NOT replace the whole project directory.
4. Copy only `app.py`, `collect.py`, `ranking.py` into your current project. Keep existing `config.py`, `database.py`, `collectors/`, `.env`, and `data/` unchanged.
5. In your already activated venv, run:
   ```powershell
   cd E:\Aanya\aanya-trend-hunter
   python collect.py --batch morning
   streamlit run app.py
   ```
6. Check the Discover and Saved pages. If anything breaks, restore the three backed-up files.

## Important limitations
- Title/description keyword matching cannot confirm the actual video's visual content or audio.
- YouTube search region is NOT the audience's location. Age/gender audience demographics are not publicly available.
- A video with high views is not necessarily a rising trend. Velocity requires repeated snapshots.
- Instagram is still manual reference mode; no fabricated Instagram trend feed.
- `PUBLIC_MODE=true` with `ADMIN_KEY` is a lightweight edit gate only, not robust production authentication.
- SQLite on Streamlit Community Cloud is ephemeral; persistent shared saves and scheduled data ingestion require a hosted database (next phase).
- Public Streamlit deployments must keep `.env` and API keys out of Git; use platform secrets.

## Next phase: public hosting with shared persistence
- Supabase free Postgres: migrate `videos`, `observations`, `saved`, and `external_reels` with additive schema.
- Streamlit Community Cloud: public, read-only visitor experience.
- Authenticated editor actions: implement server-side authorization before enabling writes.
- GitHub Actions: twice-daily scheduled collection into hosted Postgres; manage API quotas and secrets.
- Instagram: investigate authorized Meta API access and permitted free external sources. No promise of unrestricted Reels search.
