# T04 — Network volume persistence check
milestone: M0 · effort: low · depends: G0
owner input: a budget pod deployed on the RunPod network volume (D-005, docs/04 §B); terminate and redeploy it in step 2

## Goal
Prove that `/workspace` survives a pod stop/start before M1 downloads model weights there.
G0 found the first pod had no persistent volume. D-005 moves all state to a network volume;
this card proves it survives the pod being terminated and replaced. A budget GPU (< 20 GB VRAM)
is expected here and is not an escalation.

## Read first
- docs/04_ENVIRONMENT.md §B and §F
- docs/05_DECISIONS.md D-005

## Do
1. **Before the stop**, on the pod:
   ```bash
   mount | grep -i workspace; df -h /workspace   # must show a mount that is NOT overlay
   date -u > /workspace/.persist_marker && cat /workspace/.persist_marker
   ```
   Paste the output into the Log.
2. **Owner:** in RunPod, **Terminate** the pod, then deploy a new budget pod with the same
   template and the same network volume. Reconnect VS Code (new IP/port: update
   `HostName`/`Port` via `F1` → *Remote-SSH: Open SSH Configuration File…*).
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
- Step 1 shows `/workspace` on its own mount (not `overlay`).
- The marker file prints the same timestamp on the new pod.
- `setup_pod.sh` does not download Blender or create a new venv (it may reinstall apt libraries).
- `doctor.sh` shows `cuda=True` and Blender 4.2.x (any VRAM size is fine here); `pytest -q` all pass.

## Done when
- [ ] Marker survived terminate + redeploy
- [ ] doctor + pytest outputs pasted in Log

## Escalate if
- `/workspace` is still `overlay`, or the marker or `/workspace/avatar-forge` is missing on the
  new pod (the network volume is not attached).
- The restarted pod has no GPU (`nvidia-smi` fails).

## Log
