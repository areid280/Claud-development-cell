"""Lazy wrappers around third-party models (one module per model, written in T10–T15).

Rules:
- Import torch / model libraries inside functions, never at module top level.
- Every wrapper reads its entry via avatar_forge.core.config.selected_model(role)
  in pipeline code, or by name in trial scripts.
- Map model-specific labels/outputs to the canonical ones in config/pipeline.yaml.
"""
