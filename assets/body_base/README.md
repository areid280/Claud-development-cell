# Body base meshes

The pipeline needs a body mesh on the pod (Blender) that matches the
MetaHuman body in UE5, so garments fitted here also fit there.

How it gets here is decided by the gatekeeper at **G2** (task T32). Likely
route: the owner exports one or more MetaHuman bodies (A-pose, with skeleton)
from UE5 as FBX, and the pipeline morphs them to the measured body.

Check Epic's MetaHuman licence for exporting bodies to other tools before
doing this. Files here are not committed to git.
