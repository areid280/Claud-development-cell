# 04 — Environment setup (human steps)

Everything here is done once by the project owner. Total time: about 45 minutes.

## A. On your Windows PC

1. Install **Git for Windows** and **VS Code**.
2. In VS Code, install these extensions: *GitHub Copilot*, *GitHub Copilot Chat*,
   *Remote - SSH*, *Python*.
3. Sign in to GitHub in VS Code (Accounts icon, bottom left).
4. Create an SSH key if you don't have one. In PowerShell:
   ```powershell
   ssh-keygen -t ed25519 -C "runpod"
   type $env:USERPROFILE\.ssh\id_ed25519.pub
   ```
   Copy the line that starts with `ssh-ed25519`. This is your **public** key.
   Never share the file without `.pub` (the private key) with anyone, including AI chats.
5. The code lives in the public repo `areid280/Claud-development-cell` (D-004). Cloning needs no
   login; pushing from the pod needs a fine-grained token (this repo only, Contents: read/write).

## B. Rent the GPU (RunPod)

1. Create a RunPod account and add about $10 credit.
2. **Settings → SSH Public Keys**: paste your public key from A4.
3. **Storage → New Network Volume** (D-005): about **100 GB**, in a datacenter that also
   offers **RTX 4090** pods. A volume only attaches to pods in its own datacenter.
4. **Pods → Deploy**, choosing that network volume (it mounts at `/workspace`):
   - GPU: **budget phase** (M0 to T11): the cheapest NVIDIA GPU in that datacenter.
     **Model phase** (T12 onward): **RTX 4090** or **A40** (≥ 24 GB). Not a 5090: it needs CUDA 12.8+/torch 2.7+,
     newer than the template (gate decision required).
   - Template: the official **RunPod PyTorch** template with **Python 3.11** and CUDA 12.x
     (e.g. `py3.11-cuda12.x`). **Always the same template**: the venv uses its torch.
   - Expose TCP port 22
5. When the pod is running, click **Connect** and copy the
   "SSH over exposed TCP" command. It looks like
   `ssh root@<ip> -p <port> -i ~/.ssh/id_ed25519`.

**Switching GPU:** terminate the pod (the network volume is kept), deploy a new pod with the
same template and volume, then follow §F.

**Stop or terminate the pod whenever you finish a session.** Only `/workspace` (the network
volume) survives, and it holds **data only** (D-006): weights, caches, downloads, `jobs/`, git
identity and token. The code checkout (`~/avatar-forge`), venv and Blender live on the pod's own
disk and are rebuilt by `setup_pod.sh`. **Commit and push before you terminate a pod**, or
uncommitted work is lost.

## C. Connect VS Code to the pod

1. In VS Code press `F1` → **Remote-SSH: Add New SSH Host…** → paste the SSH
   command from B4. Save to your user SSH config.
2. `F1` → **Remote-SSH: Connect to Host…** → pick the new host.
3. In the remote window, open a terminal and run:
   ```bash
   cd ~
   git clone https://github.com/areid280/Claud-development-cell.git avatar-forge
   cd avatar-forge
   bash scripts/setup_pod.sh
   ```
   (GitHub will ask you to sign in; use the browser flow or a fine-grained
   token with access to this one repo only.)
4. **File → Open Folder** → `/root/avatar-forge`.
5. Open Copilot Chat, choose **Agent** mode. You're ready for `/run-task`.

The pod's IP and port change each time you start it. Update the host entry in
`%USERPROFILE%\.ssh\config` when that happens.

## D. Getting results onto your PC for UE5

Easiest: in the VS Code Explorer (remote window), right-click
`jobs/<job_id>/s09_export/<job_id>` → **Download…** and save it on your PC.
Then run the UE5 import script (see `docs/03_UE5_INTEGRATION.md`).

## E. If something breaks

- `bash scripts/doctor.sh` prints a full environment report. Paste it into
  the task card log, or into an escalation.
- A pod that won't start: deploy a new one with the same volume.
- Never try to fix GPU drivers on the pod. Deploy a different pod or template instead.

## F. After every pod start (D-006)

1. RunPod → **Connect** → copy the new "SSH over exposed TCP" command; update `HostName` and
   `Port` in VS Code (`F1` → *Remote-SSH: Open SSH Configuration File…*), then connect.
2. On the pod (the clone is needed only on a **new** pod; a restarted pod still has it):
   ```bash
   [ -d ~/avatar-forge ] || git clone https://github.com/areid280/Claud-development-cell.git ~/avatar-forge
   cd ~/avatar-forge && git checkout claude/next-task-card-lscp12 && git pull
   bash scripts/setup_pod.sh      # a few minutes: Blender and pip come from the volume cache
   ```
3. Open a **new** terminal, then `bash scripts/doctor.sh`. In VS Code open `/root/avatar-forge`.

**One-time git setup** (stored on the volume, reused by every pod):
```bash
printf 'name=Your Name\nemail=you@example.com\n' > /workspace/git/identity
bash scripts/setup_pod.sh          # applies it
git push                           # first push asks for the token once; saved to /workspace/git/credentials
```
