# Escalations

Workers append an entry, set the task to `blocked` in STATUS.md, and tell the
human: "Escalation for T<id>. Switch to Opus and run /escalate."
Opus resolves the newest `open` entry.

Template:

```
## E-NNN — T<id> — <short title>   status: open
Trigger: <which AGENTS.md §4 rule>
What I tried:
1. <attempt> -> <result>
2. <attempt> -> <result>
Error / evidence: <last 40 lines, or file paths>
Files involved: <paths>
My best guess: <one sentence>

Resolution (Opus): <filled in by Opus>
```

---

## E-001 — T00 — Not running on the GPU pod   status: open
Trigger: §4 GPU / CUDA / environment problems; task card requires the RunPod pod ("owner input").
What I tried:
1. nvidia-smi, ls /workspace, which blender -> none exist (cloud container, not the pod)
2. pip install -e . then ruff + pytest -> ruff passes; pytest fails at conftest: PIL (Pillow) missing
Error / evidence: see tasks/M0/T00_install_and_verify.md ## Log
Files involved: tasks/M0/T00_install_and_verify.md, pyproject.toml (Pillow not installed by `pip install -e .`?)
My best guess: Owner must run T00 on the pod (setup_pod.sh); separately check whether Pillow is a missing dependency in pyproject.toml.

Worker note: trigger no longer applies. Owner ran T00 on the pod; all Verify items passed and
setup_pod.sh was fixed (silent exit under set -e). Pillow was installed by the pod run. Opus to confirm and close.

Resolution (Opus): 
