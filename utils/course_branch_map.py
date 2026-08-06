COURSE_BRANCH_MAPS = {
    "nursing": {
        # Anatomy & Physiology
        "GNS111": "Anatomy and Physiology",
        "GNS121": "Anatomy and Physiology",
        "GNS211": "Anatomy and Physiology",

        # Foundation of Nursing
        "GNS112": "Foundation of Nursing",
        "GNS122": "Foundation of Nursing",
        "GNS212": "Foundation of Nursing",
        "GNS221": "Foundation of Nursing",

        # Nursing Informatics
        "GNS113": "Nursing Informatics",

        # Microbiology
        "GST114": "Microbiology",

        # Medical/Surgical Nursing
        "GNS123": "Medical Surgical Nursing",
        "GNS213": "Medical Surgical Nursing",
        "GNS222": "Medical Surgical Nursing",
        "GNS311": "Medical Surgical Nursing",
        "GNS321": "Medical Surgical Nursing",

        # Primary Health Care
        "GNS124": "Primary Health Care",
        "GNS214": "Primary Health Care",

        # Pharmacology
        "GNS125": "Pharmacology",
        "GNS215": "Pharmacology",
        "GNS223": "Pharmacology",

        # Reproductive Health
        "GNS216": "Reproductive Health",
        "GNS226": "Reproductive Health",
        "GNS312": "Reproductive Health",

        # Research & Statistics
        "GNS217": "Research and Statistics",
        "GNS224": "Research and Statistics",

        # Community Health Nursing
        "GNS225": "Community Health Nursing",
        "GNS313": "Community Health Nursing",

        # Nutrition
        "GNS227": "Nutrition and Dietetics",

        # Mental Health
        "GNS314": "Mental Health Nursing",

        # Emergency & Disaster
        "GNS315": "Emergency and Disaster Nursing",

        # Quality & Safety
        "GST319": "Quality Improvement and Patient Safety",

        # Home Healthcare
        "GNS324": "Home Healthcare Nursing",

        # Management & Teaching
        "GST321": "Management and Teaching",

        # Health Economics
        "GST322": "Health Economics",
    },

    "midwifery": {
        # To be filled in once the midwifery curriculum's course codes are finalized.
    },
}


def get_course_branch_map(program):
    """Returns the course_id -> course_name map for the given program.
    Unknown programs get an empty map, which build_pages.py's
    build_context_lookup() already falls back gracefully from (uses the
    curriculum's own course_name as-is when a course_id isn't found here)."""
    return COURSE_BRANCH_MAPS.get(program, {})


def get_course_id_from_topic_id(topic_id):
    """e.g. 'GNS321_U4_T6' -> 'GNS321' - program-agnostic, pure string parsing."""
    return topic_id.split("_")[0]
