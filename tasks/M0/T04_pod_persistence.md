# T04 — Network volume persistence check
milestone: M0 · effort: low · depends: G0
owner input: a budget pod on the RunPod network volume (D-005, D-006); terminate and redeploy it in step 3

## Goal
Prove the D-006 layout works: data on the network volume (`/workspace`) survives the pod being
terminated and replaced, and `setup_pod.sh` rebuilds code, venv and Blender on a fresh pod using
the volume caches. A budget GPU (< 20 GB VRAM) is expected here and is not an escalation.

## Read first
- docs/04_ENVIRONMENT.md §B and §F
- docs/05_DECISIONS.md D-005, D-006

## Do
1. On the first pod (repo at `~/avatar-forge`, `setup_pod.sh` already run):
   ```bash
   mount | grep -i workspace; df -h /workspace /
   date -u > /workspace/.persist_marker && cat /workspace/.persist_marker
   ls /workspace/downloads /workspace/git
   bash scripts/doctor.sh
   pytest -q
   ```
2. Set T04 to `doing` in STATUS.md, paste step 1 output into the Log, commit, and **push**
   (`git push`). Uncommitted work is lost in step 3.
3. **Owner:** terminate the pod; deploy a new budget pod with the same template and network
   volume; reconnect VS Code (docs/04 §F step 1).
4. On the new pod:
   ```bash
   cat /workspace/.persist_marker
   git clone https://github.com/areid280/Claud-development-cell.git ~/avatar-forge
   cd ~/avatar-forge && git checkout claude/next-task-card-lscp12
   time bash scripts/setup_pod.sh 2>&1 | tail -15
   ```
   Then open a new terminal:
   ```bash
   cd ~/avatar-forge && bash scripts/doctor.sh && pytest -q && git config --get user.name
   ```
5. Paste step 4 outputs into the Log (last 40 lines each). Set T04 `done`, commit `T04: <summary>`,
   and push.

## Must not
- Put the repo, venv or any executable on `/workspace`.
- Change any file under `src/` or `scripts/`.

## Verify
- Step 1: `/workspace` is `fuse.geesefs` (or another non-overlay mount).
- The marker prints the same timestamp on the new pod.
- `setup_pod.sh` on the new pod prints "Using cached Blender download" (no Blender download).
- `doctor.sh`: `cuda=True`, Blender 4.2.x (any VRAM size is fine here); `pytest -q` all pass;
  `git config --get user.name` prints the owner's name (identity restored from the volume).

## Done when
- [ ] Marker survived terminate + redeploy
- [ ] Rebuild used the cached Blender; doctor + pytest outputs pasted in Log

## Escalate if
- The marker or `/workspace/downloads/blender-*.tar.xz` is missing on the new pod.
- `setup_pod.sh` fails on the fresh pod.
- The new pod has no GPU (`nvidia-smi` fails).

## Log
