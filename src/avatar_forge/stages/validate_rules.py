from __future__ import annotations


def _person_score(person: dict) -> float:
    score = person.get("score")
    if isinstance(score, (int, float)):
        return float(score)
    return 0.0


def _keypoint_score(person: dict, name: str) -> float:
    keypoints = person.get("keypoints", {})
    values = keypoints.get(name, [0.0, 0.0, 0.0])
    if len(values) < 3:
        return 0.0
    return float(values[2])


def _confident_point(person: dict, name: str, min_score: float) -> list[float] | None:
    values = person.get("keypoints", {}).get(name)
    if not values or len(values) < 3 or float(values[2]) < min_score:
        return None
    return values


def _bbox_height(bbox: list[float]) -> float:
    return float(max(0.0, bbox[3] - bbox[1]))


def evaluate(
    persons: list[dict], image_size: tuple[int, int], cfg: dict
) -> tuple[str, list[str]]:
    width, height = image_size
    fails: list[str] = []
    warns: list[str] = []

    min_long_side = int(cfg.get("min_long_side_px", 0))
    long_side = max(width, height)
    if long_side < min_long_side:
        fails.append(
            "Image is too small "
            f"({width}x{height}). Use at least {min_long_side} px on the long side."
        )

    # Only confident detections count as people; faint detections of background clutter must
    # not trigger "more than one person" or the edge checks (Opus review of T20).
    min_score = float(cfg.get("keypoint_min_score", 0.0))
    persons = [person for person in persons if _person_score(person) >= min_score]
    if not persons:
        fails.append("No person found.")

    max_people = int(cfg.get("max_people", 1))
    if len(persons) > max_people:
        fails.append("More than one person found. Use one person per image.")

    required_keypoints = list(cfg.get("required_keypoints", []))
    for person in persons:
        missing = [
            key
            for key in required_keypoints
            if _keypoint_score(person, key) < min_score
        ]
        if missing:
            fails.append(
                f"Not visible: {', '.join(missing)}. Show the full body, head to toe."
            )

    for person in persons:
        bbox = person.get("bbox", [0.0, 0.0, 0.0, 0.0])
        if len(bbox) < 4:
            continue
        if bbox[3] >= height * (1.0 - 0.01):
            fails.append("Feet may be cut off at the bottom edge.")
        if bbox[1] <= height * 0.01:
            fails.append("Head may be cut off at the top edge.")

        person_height = _bbox_height(bbox)
        min_height_frac = float(cfg.get("min_person_height_frac", 0.0))
        if person_height / height < min_height_frac:
            fails.append("Person is too small in the frame.")

    if cfg.get("warn_crossed_arms", False):
        for person in persons:
            left_wrist = _confident_point(person, "left_wrist", min_score)
            right_wrist = _confident_point(person, "right_wrist", min_score)
            left_shoulder = _confident_point(person, "left_shoulder", min_score)
            right_shoulder = _confident_point(person, "right_shoulder", min_score)
            left_hip = _confident_point(person, "left_hip", min_score)
            right_hip = _confident_point(person, "right_hip", min_score)
            if not all(
                (
                    left_wrist,
                    right_wrist,
                    left_shoulder,
                    right_shoulder,
                    left_hip,
                    right_hip,
                )
            ):
                continue
            shoulder_x_min = min(float(left_shoulder[0]), float(right_shoulder[0]))
            shoulder_x_max = max(float(left_shoulder[0]), float(right_shoulder[0]))
            shoulder_y = (float(left_shoulder[1]) + float(right_shoulder[1])) / 2.0
            hip_y = (float(left_hip[1]) + float(right_hip[1])) / 2.0
            low_y = min(shoulder_y, hip_y)
            high_y = max(shoulder_y, hip_y)
            wrists_x = [float(left_wrist[0]), float(right_wrist[0])]
            wrists_y = [float(left_wrist[1]), float(right_wrist[1])]
            if all(shoulder_x_min <= x <= shoulder_x_max for x in wrists_x) and all(
                low_y <= y <= high_y for y in wrists_y
            ):
                warns.append("Arms look crossed; the torso and hands will be guessed.")

    if cfg.get("warn_wrists_inside_torso", False):
        for person in persons:
            wrists = [
                _confident_point(person, "left_wrist", min_score),
                _confident_point(person, "right_wrist", min_score),
            ]
            torso_points = [
                _confident_point(person, name, min_score)
                for name in ("left_shoulder", "right_shoulder", "left_hip", "right_hip")
            ]
            if not any(wrists) or not all(torso_points):
                continue
            xs = [p[0] for p in torso_points if p is not None]
            ys = [p[1] for p in torso_points if p is not None]
            torso_left = min(xs)
            torso_right = max(xs)
            torso_top = min(ys)
            torso_bottom = max(ys)
            if any(
                torso_left <= float(wrist[0]) <= torso_right
                and torso_top <= float(wrist[1]) <= torso_bottom
                for wrist in wrists
                if wrist is not None
            ):
                warns.append("An arm covers the torso; that area will be guessed.")

    if fails:
        return "fail", fails + warns
    if warns:
        return "warn", warns
    return "ok", []
