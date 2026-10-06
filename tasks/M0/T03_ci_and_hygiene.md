# T03 — CI and repo hygiene
milestone: M0 · effort: low · depends: T01, T02
owner input: push `main` from the pod with a token (step 1). Repo is **public** by owner decision (D-004).

## Goal
Green CI on GitHub and no way to accidentally commit secrets, weights or real-person images.

## Read first
- .github/workflows/ci.yml
- .gitignore

## Do
1. **Owner step (workers must not handle tokens, AGENTS.md §4).** Ask the human to run on the pod,
   then wait for them to confirm:
   ```bash
   git checkout main
   git pull --no-rebase --no-edit origin main
   git merge --no-edit claude/next-task-card-lscp12
   git push origin main     # username: areid280, password: the fine-grained token
   ```
   Then ask the human for the result of the `ci` run on that commit (Actions tab link or
   screenshot). It must be green. If it is red, paste the failing step into the Log and escalate.
2. Check ignore rules work. Each of these must print the path (meaning "ignored"):
   ```bash
   git check-ignore -v jobs/x/manifest.json samples/a_front.png weights/m.safetensors \
     .env assets/garment_library/boots/mesh.fbx assets/body_base/body.fbx
   ```
   and these must print nothing (not ignored):
   ```bash
   git check-ignore samples/README.md assets/garment_library/README.md \
     assets/garment_library/index.example.yaml
   ```
3. Run the secret scan from ci.yml locally; expect no output:
   ```bash
   git grep -nIE "(BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})" -- . ':!.github/workflows/ci.yml'
   ```
   The repo is public (D-004), so treat any hit as an immediate escalation.
4. In `tasks/STATUS.md`, mark T03 done, commit on `main`, and ask the human to push `main` again.
   Then tell the human:
   "Gate G0 is due. Switch to Opus and run /gate G0."

## Must not
- Weaken the secret scan or the ignore rules.

## Verify
- CI green on the latest commit.
- Step 2 outputs match expectations.

## Done when
- [x] CI green
- [x] Ignore checks pass

GATE: G0

## Log

Opus pre-check (cloud copy, 2026-10-06): step 2 ignore checks match expectations; step 3 secret
scan printed nothing. Card rewritten for D-004 (public repo, direct push to main).

Worker verification (2026-10-06):
```text
$ git check-ignore -v jobs/x/manifest.json samples/a_front.png weights/m.safetensors .env assets/garment_library/boots/mesh.fbx assets/body_base/body.fbx
.gitignore:20:jobs/    jobs/x/manifest.json
.gitignore:29:samples/*    samples/a_front.png
.gitignore:21:weights/    weights/m.safetensors
.gitignore:13:.env    .env
.gitignore:33:assets/garment_library/*    assets/garment_library/boots/mesh.fbx
.gitignore:36:assets/body_base/*    assets/body_base/body.fbx

$ git check-ignore samples/README.md assets/garment_library/README.md assets/garment_library/index.example.yaml
[no output; none are ignored]

$ git grep -nIE "(BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})" -- . ':!.github/workflows/ci.yml'
[no output; no matches]
```
GitHub Actions `ci` run #3 on `main` succeeded for commit `1c1d939d43f3b4a638de87df47f22f559b049bbf`:
https://github.com/areid280/Claud-development-cell/actions/runs/37520099827
