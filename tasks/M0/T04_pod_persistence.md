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

### Step 1 — first pod (2026-10-07)

```text
caabf492-6228-4ac4-b0df-2eddbf2b9bd8 on /workspace type fuse.geesefs (rw,nosuid,nodev,relatime,user_id=0,group_id=0,default_permissions,allow_other)
Filesystem                            Size  Used Avail Use% Mounted on
caabf492-6228-4ac4-b0df-2eddbf2b9bd8  1.0P     0  1.0P   0% /workspace
overlay                                20G  3.2G   17G  16% /
Wed Oct  7 20:11:29 UTC 2026
/workspace/downloads:
blender-4.2.3-linux-x64.tar.xz

/workspace/git:
credentials
identity
== system ==
Linux 90b460c94240 6.8.0-60-generic #63~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 22 19:00:15 UTC 2 x86_64 x86_64 x86_64 GNU/Linux
date: 2026-10-07T20:11:29Z

== gpu ==
NVIDIA A40, 46068 MiB, 570.195.03

== disk (/workspace = network volume, / = local) ==
Filesystem                            Size  Used Avail Use% Mounted on
caabf492-6228-4ac4-b0df-2eddbf2b9bd8  1.0P     0  1.0P   0% /workspace
overlay                                20G  3.2G   17G  16% /

== blender ==
Blender 4.2.3 LTS (hash 0e22e4fcea03 built 2024-10-14 23:31:34)

== python / avatar-forge ==
avatar-forge 0.0.1
python       3.11.10 (/opt/venv-af/bin/python)
repo root    /root/avatar-forge
jobs dir     /workspace/jobs
weights dir  /workspace/weights (exists: True)
torch        2.4.1+cu124  cuda=True  gpu=NVIDIA A40
blender      /opt/tools/blender/blender
disk free    1125899.9 GB
.......................                                                  [100%]
23 passed in 4.85s
```

### Step 4 — pod restart (2026-10-07; owner chose restart, not terminate/redeploy)

The marker is still present after restart:

```text
Wed Oct  7 20:11:29 UTC 2026
```

`bash scripts/setup_pod.sh` returned exit 0. Its final output included:

```text
Successfully installed avatar-forge-0.0.1
Blender 4.2.3 already installed at /opt/tools/blender

== done. Open a NEW terminal (or run: source /root/.avatar_forge_env), then: ==
   bash scripts/doctor.sh
```

In a fresh shell after sourcing `/root/.avatar_forge_env`:

```text
== gpu ==
NVIDIA A40, 46068 MiB, 570.195.03

== blender ==
Blender 4.2.3 LTS (hash 0e22e4fcea03 built 2024-10-14 23:31:34)

== python / avatar-forge ==
avatar-forge 0.0.1
python       3.11.10 (/opt/venv-af/bin/python)
repo root    /root/avatar-forge
jobs dir     /workspace/jobs
weights dir  /workspace/weights (exists: True)
torch        2.4.1+cu124  cuda=True  gpu=NVIDIA A40
blender      /opt/tools/blender/blender
disk free    1125899.9 GB
.......................                                                  [100%]
23 passed in 6.17s
Aaron Reid
```

Opus waiver 2026-10-07: terminate+redeploy and the cached-Blender path are deferred to the next fresh pod deploy (docs/04 §F). Persistence across restart and a from-scratch rebuild on a new pod (earlier today) are proven.
