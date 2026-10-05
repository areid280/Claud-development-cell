# T03 — CI and repo hygiene
milestone: M0 · effort: low · depends: T01, T02
owner input: confirm the GitHub repo is **private**

## Goal
Green CI on GitHub and no way to accidentally commit secrets, weights or real-person images.

## Read first
- .github/workflows/ci.yml
- .gitignore

## Do
1. Push the current `main`. Open the repo's **Actions** tab (ask the owner
   for the link/screenshot if you can't see it) and confirm the `ci` run is green.
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
3. Run the secret scan from ci.yml locally; expect no output.
4. In `tasks/STATUS.md`, mark T03 done, then tell the human:
   "Gate G0 is due. Switch to Opus and run /gate G0."

## Must not
- Weaken the secret scan or the ignore rules.

## Verify
- CI green on the latest commit.
- Step 2 outputs match expectations.

## Done when
- [ ] CI green
- [ ] Ignore checks pass

GATE: G0

## Log
