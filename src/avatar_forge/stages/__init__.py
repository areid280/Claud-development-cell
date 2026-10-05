"""Pipeline stages, in run order. Each module exposes `run(ctx) -> StageResult`."""

STAGE_ORDER: tuple[str, ...] = (
    "s00_ingest",
    "s01_validate",
    "s02_prepare",
    "s03_parse",
    "s04_body_fit",
    "s05_body_params",
    "s06_garments",
    "s07_texture",
    "s08_assemble",
    "s09_export",
)
