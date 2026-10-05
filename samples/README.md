# samples/ (git-ignored)

Put test images here **on the pod only**. They are never committed.

Rules:
- Adults only. Original characters, or real people who agreed.
- Full body, head to toe, feet visible. Long side ≥ 1024 px.
- Name them `<name>_front.png`, `<name>_back.png`, `<name>_left.png`, `<name>_right.png`.

Ideal starter set (input from the owner, needed by T12–T15):

| File | Purpose |
|------|---------|
| `a_front.png` | Clean A-pose, plain background, tight suit + boots + jacket |
| `b_front.png` | Different body shape, skirt or dress, heels |
| `c_front.png` | Painted/illustrated character (style test) |
| `bad_cropped_feet.png` | Must be rejected by s01_validate |
| `bad_crossed_arms.png` | Must produce a warning |
| `a_back.png` (M5) | Back view of character a |

AI image generators are a quick way to produce original, consistent A-pose
test characters.
