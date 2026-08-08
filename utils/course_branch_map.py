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

    # Replace the placeholder "midwifery": { ... } block in
# utils/course_branch_map.py with this.
#
# Grouping logic mirrors nursing's: same-subject courses recurring across
# years collapse into one branch name. A few branches here have no nursing
# equivalent since they're midwifery-specific (Midwifery Practice, Infant
# Care, Complicated Midwifery, etc.) -- these are new, not reused nursing
# names, so double check they read well as exam-category labels before
# this goes live.

    "midwifery": {
    # Foundation of Nursing
        "BMP110": "Foundation of Nursing",
        "BMP120": "Foundation of Nursing",

    # Anatomy and Physiology
        "BMP111": "Anatomy and Physiology",
        "BMP121": "Anatomy and Physiology",
        "BMP210": "Anatomy and Physiology",

    # Standalone first-year sciences/support courses
        "BMP112": "Applied Physics",
        "BMP113": "Applied Chemistry",
        "BMP115": "Use of English",
        "BMP116": "Microbiology",

    # Behavioral Science
        "BMP114": "Behavioral Science",
        "BMP122": "Behavioral Science",

    # Primary Health Care
        "BMP117": "Primary Health Care",
        "BMP126": "Primary Health Care",

        "BMP118": "Nutrition and Dietetics",
        "BMP119": "Hospital-Based Clinical Practice",
        "BMP123": "Nursing Informatics",  # ICT course, matches nursing's branch name

    # Pharmacology
        "BMP124": "Pharmacology",
        "BMP213": "Pharmacology",

        # Medical Surgical Nursing
        "BMP125": "Medical Surgical Nursing",
        "BMP216": "Medical Surgical Nursing",

    # Seminar in Midwifery Practice
        "BMP127": "Seminar in Midwifery Practice",
        "BMP217": "Seminar in Midwifery Practice",
        "BMP226": "Seminar in Midwifery Practice",
        "BMP313": "Seminar in Midwifery Practice",
        "BMP322": "Seminar in Midwifery Practice",

        # Midwifery Practice (core hospital-based clinical courses)
        "BMP211": "Midwifery Practice",
        "BMP212": "Midwifery Practice",
        "BMP218": "Midwifery Practice",
        "BMP315": "Midwifery Practice",
        "BMP324": "Midwifery Practice",

    # Infant Care
        "BMP214": "Infant Care",
        "BMP220": "Infant Care",

    # Community Midwifery
        "BMP215": "Community Midwifery",
        "BMP227": "Community Midwifery",
        "BMP316": "Community Midwifery",
        "BMP323": "Community Midwifery",

    # Complicated Midwifery
        "BMP221": "Complicated Midwifery",
        "BMP311": "Complicated Midwifery",

        "BMP222": "Child Health",
        "BMP223": "Mental Health Nursing",  # matches nursing's branch name
        "BMP224": "Family Planning",

    # Research
        "BMP225": "Research and Statistics",  # matches nursing's branch name
        "BMP314": "Research Project",  # kept separate -- capstone, not methods coursework

    # Reproductive Health
        "BMP310": "Reproductive Health",
        "BMP320": "Reproductive Health",

        "BMP312": "Management and Teaching",  # matches nursing's branch name
        "BMP321": "Expectant Family Care Project",
    },



def get_course_branch_map(program):
    """Returns the course_id -> course_name map for the given program.
    Unknown programs get an empty map, which build_pages.py's
    build_context_lookup() already falls back gracefully from (uses the
    curriculum's own course_name as-is when a course_id isn't found here)."""
    return COURSE_BRANCH_MAPS.get(program, {})


def get_course_id_from_topic_id(topic_id):
    """e.g. 'GNS321_U4_T6' -> 'GNS321' - program-agnostic, pure string parsing."""
    return topic_id.split("_")[0]
