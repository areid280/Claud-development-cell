from __future__ import annotations

import os
from typing import Any

from PIL import Image

from avatar_forge.core.paths import weights_dir
from avatar_forge.models.base import ModelWrapper


class Rembg(ModelWrapper):
    role = "bg_remove"
    name = "rembg"

    def load(self) -> None:
        os.environ.setdefault("U2NET_HOME", str(weights_dir() / "rembg"))
        from rembg import new_session

        self.session: Any = new_session("u2net_human_seg")

    def predict(self, image: Image.Image) -> Image.Image:
        from rembg import remove

        return remove(image.convert("RGBA"), session=self.session).convert("RGBA")
