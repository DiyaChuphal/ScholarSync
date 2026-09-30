import pandas as pd
import re


# ============================================================
# CONFIGURATION
# ============================================================

FILE_PATH = r"C:\Users\diyac\Desktop\Scholarsync\scholarships_standardized.csv"

df = pd.read_csv(FILE_PATH)


# ============================================================
# BASIC NORMALIZATION
# ============================================================

def normalize(value):

    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    value = value.replace("&", " and ")

    value = re.sub(r"[/|;]+", ",", value)

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def is_unknown(value):

    value = normalize(value)

    unknown_values = {
        "",
        "not specified",
        "not available",
        "na",
        "n a",
        "none",
        "null"
    }

    return value in unknown_values


def split_values(value):

    value = normalize(value)

    if is_unknown(value):
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ============================================================
# EDUCATION
# ============================================================

def education_match(student, scholarship):

    student = normalize(student)
    scholarship = normalize(scholarship)

    if is_unknown(scholarship):

        return "unknown", "Education level is not specified."

    # Exact / explicit representations
    if student == "undergraduate":

        if "undergraduate" in scholarship:
            return "match", "Undergraduate education is explicitly included."

        if "post matric to phd" in scholarship:
            return "match", "Scholarship covers post-matric to PhD."

        if "post matric" in scholarship:
            return "match", "Scholarship includes post-matric education."

        if "professional" in scholarship or "technical" in scholarship:
            return "match", "Scholarship includes professional/technical education."

    elif student == "postgraduate":

        if "postgraduate" in scholarship or "pg" in scholarship:
            return "match", "Postgraduate education is explicitly included."

        if "post matric to phd" in scholarship:
            return "match", "Scholarship covers post-matric to PhD."

    elif student == "phd":

        if "phd" in scholarship:
            return "match", "PhD education is explicitly included."

        if "post matric to phd" in scholarship:
            return "match", "Scholarship covers post-matric to PhD."

    elif student == "diploma":

        if "diploma" in scholarship:
            return "match", "Diploma education is explicitly included."

        if "iti" in scholarship or "technical" in scholarship:
            return "match", "Technical/ITI education is included."

    elif student == "school":

        if "school" in scholarship:
            return "match", "School education is explicitly included."

    elif student == "intermediate (class 11-12)":

        if "intermediate" in scholarship:
            return "match", "Intermediate education is explicitly included."

        if "class 11" in scholarship or "class 12" in scholarship:
            return "match", "Class 11/12 education is explicitly included."

        if "post matric" in scholarship:
            return "match", "Post-matric education is included."

    return "conflict", "Scholarship education level does not include the student's level."


# ============================================================
# STATE
# ============================================================

def state_match(student_state, scholarship_state):

    student = normalize(student_state)
    scholarship = normalize(scholarship_state)

    if is_unknown(scholarship):
        return "unknown", "Scholarship state eligibility is not specified."

    if "all india" in scholarship:
        return "match", "Scholarship is available across India."

    states = split_values(scholarship)

    if student in states:
        return "match", f"Scholarship explicitly includes {student_state}."

    return "conflict", f"Scholarship does not list {student_state}."


# ============================================================
# GENDER
# ============================================================

def gender_match(student_gender, scholarship_gender):

    student = normalize(student_gender)
    scholarship = normalize(scholarship_gender)

    if is_unknown(scholarship):
        return "unknown", "Gender eligibility is not specified."

    if scholarship == "all":
        return "match", "Scholarship is open to all genders."

    if student == scholarship:
        return "match", "Gender requirement matches."

    return "conflict", "Gender requirement does not match."


# ============================================================
# CATEGORY
# ============================================================

CATEGORY_ALIASES = {

    "general": {"general", "gen"},

    "sc": {"sc"},

    "st": {"st"},

    "obc": {"obc", "obc bc"},

    "ews": {"ews", "ebc"},

    "pwd": {"pwd", "pwd 40 disability"},

    "minority": {
        "minority",
        "muslim",
        "christian",
        "sikh",
        "jain",
        "buddhist",
        "parsi"
    }
}


def category_match(student_category, scholarship_category):

    student = normalize(student_category)
    scholarship = normalize(scholarship_category)

    if is_unknown(scholarship):
        return "unknown", "Category eligibility is not specified."

    scholarship_parts = set(split_values(scholarship))

    aliases = CATEGORY_ALIASES.get(student, {student})

    # Direct category matching
    if aliases.intersection(scholarship_parts):
        return "match", "Student category is explicitly included."

    # Handle combined textual category descriptions
    if student == "pwd" and "pwd" in scholarship:
        return "match", "PWD students are explicitly included."

    if student == "obc" and "obc" in scholarship:
        return "match", "OBC students are explicitly included."

    if student == "sc" and "sc" in scholarship:
        return "match", "SC students are explicitly included."

    if student == "st" and "st" in scholarship:
        return "match", "ST students are explicitly included."

    return "conflict", "Student category is not listed in the scholarship eligibility."


# ============================================================
# INCOME
# ============================================================

def parse_income_limit(value):

    if pd.isna(value):
        return None

    text = normalize(value)

    if is_unknown(text):
        return None

    # Remove commas
    text = text.replace(",", "")

    # Detect lakh
    lakh_match = re.search(
        r"(\d+(?:\.\d+)?)\s*lakh",
        text
    )

    if lakh_match:
        return float(lakh_match.group(1)) * 100000

    # Detect crore
    crore_match = re.search(
        r"(\d+(?:\.\d+)?)\s*crore",
        text
    )

    if crore_match:
        return float(crore_match.group(1)) * 10000000

    # Plain numeric values
    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        text
    )

    if numbers:

        values = [
            float(number)
            for number in numbers
        ]

        return max(values)

    return None


def income_match(student_income, scholarship_income):

    if is_unknown(scholarship_income):

        return "unknown", "Income limit is not specified."

    limit = parse_income_limit(
        scholarship_income
    )

    if limit is None:

        return "unknown", "Income limit could not be reliably interpreted."

    if student_income <= limit:

        return (
            "match",
            f"Family income is within the stated limit of ₹{limit:,.0f}."
        )

    return (
        "conflict",
        f"Family income exceeds the stated limit of ₹{limit:,.0f}."
    )


# ============================================================
# COURSE
# ============================================================

def course_match(student_course, scholarship_course):

    student = normalize(student_course)
    scholarship = normalize(scholarship_course)

    if is_unknown(scholarship):

        return "unknown", "Course requirement is not specified."

    if not student:

        return "unknown", "Student course was not provided."

    scholarship_courses = split_values(
        scholarship
    )

    # Exact match
    if student in scholarship_courses:

        return "match", "Course is explicitly listed."

    # Known course aliases
    aliases = {

        "btech": {
            "btech",
            "b tech",
            "be",
            "engineering",
            "technical"
        },

        "mbbs": {
            "mbbs",
            "medicine",
            "medical"
        },

        "bcom": {
            "bcom",
            "commerce"
        },

        "bba": {
            "bba",
            "business administration"
        }
    }

    student_aliases = aliases.get(
        student,
        {student}
    )

    for course in scholarship_courses:

        if course in student_aliases:

            return (
                "match",
                "Course matches an explicitly listed course category."
            )

    # Broad "technical" scholarships
    if "technical" in scholarship:

        if any(
            keyword in student
            for keyword in [
                "engineering",
                "btech",
                "b tech",
                "technical"
            ]
        ):

            return (
                "match",
                "Scholarship explicitly covers technical education."
            )

    # DO NOT call it a conflict merely because
    # the course isn't mentioned.
    return (
        "unknown",
        "Scholarship has course restrictions that cannot be confirmed from the dataset."
    )


# ============================================================
# COMPLETE EVALUATION
# ============================================================

def evaluate(student, scholarship):

    education_status, education_reason = education_match(
        student["education"],
        scholarship["education_level"]
    )

    state_status, state_reason = state_match(
        student["state"],
        scholarship["state"]
    )

    category_status, category_reason = category_match(
        student["category"],
        scholarship["category"]
    )

    gender_status, gender_reason = gender_match(
        student["gender"],
        scholarship["gender"]
    )

    income_status, income_reason = income_match(
        student["income"],
        scholarship["income_limit"]
    )

    course_status, course_reason = course_match(
        student["course"],
        scholarship["course"]
    )

    checks = {
        "education": education_status,
        "state": state_status,
        "category": category_status,
        "gender": gender_status,
        "income": income_status,
        "course": course_status
    }

    reasons = {
        "education": education_reason,
        "state": state_reason,
        "category": category_reason,
        "gender": gender_reason,
        "income": income_reason,
        "course": course_reason
    }

    # ========================================================
    # DECISION LOGIC
    # ========================================================

    conflicts = [
        key
        for key, value in checks.items()
        if value == "conflict"
    ]

    unknowns = [
        key
        for key, value in checks.items()
        if value == "unknown"
    ]

    matches = [
        key
        for key, value in checks.items()
        if value == "match"
    ]

    # ANY confirmed conflict means do not recommend
    if conflicts:

        status = "Not Suitable"

    # No conflict but important information missing
    elif unknowns:

        status = "Needs Verification"

    # Every criterion is explicitly satisfied
    else:

        status = "Potentially Eligible"

    return {
        "status": status,
        "matches": matches,
        "unknowns": unknowns,
        "conflicts": conflicts,
        "reasons": reasons,
        "checks": checks
    }


# ============================================================
# FIND MATCHES
# ============================================================

def find_scholarships(
    education,
    course,
    state,
    category,
    gender,
    income
):

    student = {
        "education": education,
        "course": course,
        "state": state,
        "category": category,
        "gender": gender,
        "income": income
    }

    results = []

    for _, scholarship in df.iterrows():

        evaluation = evaluate(
            student,
            scholarship
        )

        # Never display confirmed conflicts
        if evaluation["status"] == "Not Suitable":
            continue

        result = scholarship.to_dict()

        result["status"] = evaluation["status"]

        result["matches"] = evaluation["matches"]

        result["unknowns"] = evaluation["unknowns"]

        result["conflicts"] = evaluation["conflicts"]

        result["reasons"] = evaluation["reasons"]

        result["checks"] = evaluation["checks"]

        # Number of explicitly matched criteria
        result["match_count"] = len(
            evaluation["matches"]
        )

        # Number of unknown criteria
        result["unknown_count"] = len(
            evaluation["unknowns"]
        )

        results.append(result)

    results_df = pd.DataFrame(results)

    if results_df.empty:
        return results_df

    # ========================================================
    # SORTING
    # ========================================================

    status_priority = {
        "Potentially Eligible": 0,
        "Needs Verification": 1
    }

    results_df["priority"] = (
        results_df["status"]
        .map(status_priority)
    )

    results_df = results_df.sort_values(
        by=[
            "priority",
            "match_count",
            "unknown_count"
        ],
        ascending=[
            True,
            False,
            True
        ]
    )

    results_df = results_df.drop(
        columns=["priority"]
    )

    return results_df