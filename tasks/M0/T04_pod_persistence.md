# T04 — Pod restart persistence check
milestone: M0 · effort: low · depends: G0
owner input: stop and restart the pod in RunPod; reconnect VS Code (new IP/port)

## Goal
Prove that `/workspace` survives a pod stop/start before M1 downloads model weights there.
G0 found `df /workspace` reporting the `overlay` filesystem mounted on `/`, so it is not yet
proven that `/workspace` is a persistent volume.

## Read first
- docs/04_ENVIRONMENT.md §B and §F

## Do
1. **Before the stop**, on the pod:
   ```bash
   mount | grep -i workspace; df -h /workspace
   date -u > /workspace/.persist_marker && cat /workspace/.persist_marker
   ```
   Paste the output into the Log.
2. **Owner:** in RunPod, **Stop** the pod, then **Start** it again. Reconnect VS Code
   (new IP/port: update `HostName`/`Port` via `F1` → *Remote-SSH: Open SSH Configuration File…*).
3. **After the restart**, on the pod:
   ```bash
   cat /workspace/.persist_marker
   ls /workspace/avatar-forge /workspace/venv-af/bin/python /workspace/tools/blender/blender
   cd /workspace/avatar-forge && bash scripts/setup_pod.sh
   source ~/.avatar_forge_env
   bash scripts/doctor.sh
   pytest -q
   ```
4. Paste outputs into the Log (last 40 lines each). Set T04 `done` and commit `T04: <summary>`.

## Must not
- Delete or redeploy the pod yourself. Do not change any file under `src/` or `scripts/`.

## Verify
- The marker file prints the same timestamp after the restart.
- `setup_pod.sh` does not download Blender or create a new venv (it may reinstall apt libraries).
- `doctor.sh` shows `cuda=True` and Blender 4.2.x; `pytest -q` all pass.

## Done when
- [ ] Marker survived the restart
- [ ] doctor + pytest outputs pasted in Log

## Escalate if
- The marker or `/workspace/avatar-forge` is missing after the restart (no persistent volume:
  the owner must redeploy with a volume disk at `/workspace`).
- The restarted pod has no GPU (`nvidia-smi` fails).

## Log
