import random


def load_weights(weights_config):
    """Returns (course_weights: dict, unit_weights: dict) with .get(key, 1.0) semantics baked in via defaultdict-like access."""
    courses = weights_config.get("courses", {})
    units = weights_config.get("units", {})
    return courses, units


def build_weighted_pool(course_pool_questions, weights_config):
    """
    course_pool_questions: {course_slug: {unit_slug: [question_dict, ...]}}
    Returns a flat list of (question_dict, weight) tuples - one entry per question,
    weight = course_weight * unit_weight for whichever course/unit it belongs to.
    """
    course_weights, unit_weights = load_weights(weights_config)

    pool = []
    for course_slug, units in course_pool_questions.items():
        c_weight = course_weights.get(course_slug, 1.0)
        for unit_slug, questions in units.items():
            unit_key = f"{course_slug}|{unit_slug}"
            u_weight = unit_weights.get(unit_key, 1.0)
            weight = c_weight * u_weight
            for q in questions:
                pool.append((q, weight))
    return pool


def sample_without_replacement(pool, k):
    """
    pool: list of (item, weight) tuples
    Returns up to k items, weighted, without replacement.
    O(n*k) - fine for pool sizes in the low thousands and k=250.
    """
    items = [p[0] for p in pool]
    weights = [p[1] for p in pool]
    selected = []

    for _ in range(min(k, len(items))):
        if not items:
            break
        chosen = random.choices(items, weights=weights, k=1)[0]
        idx = items.index(chosen)
        selected.append(items.pop(idx))
        weights.pop(idx)

    return selected
