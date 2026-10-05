# unreal/

Scripts that run **inside the Unreal Editor** on the owner's Windows PC.
See `docs/03_UE5_INTEGRATION.md` for how to install and run them.

- `import_character.py` — imports an export folder (T26, T38, T44).

Workers cannot test these on the pod. Every task that changes them must end
with "ask the owner to run it in UE5 and paste the Output Log", and the card
stays `doing` until the owner reports back.
