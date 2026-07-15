"""Clean fake_employee.csv and create one cleaned CSV file."""

import random
import pandas as pd

# File names
input_file = "fake_employee.csv"
output_file = "employee_data_cleaned_v3.csv"

# Using a seed makes the random values repeatable each time the script runs.
random.seed(42)

# Read the original CSV
df = pd.read_csv(input_file)

# Remove the extra index column and fields that will not be used
df = df.drop(
    columns=[
        "Unnamed: 0",
        "email",
        "phone_number",
        "address",
        "emergency_contacts",
    ],
    errors="ignore",
)

# Keep the original ID for reference, then create unique employee IDs
# for use in Neo4j relationships.
df = df.rename(columns={"employee_id": "original_employee_id"})
df["employee_id"] = [f"E{i:04d}" for i in range(1, len(df) + 1)]

# Clean titles and suffixes from names, then create first and last name columns
clean_name = df["name"].str.replace(
    r"^(Mr\.|Mrs\.|Ms\.|Miss|Dr\.)\s+|\s+(Jr\.|Sr\.|II|III|IV|MD|DDS)$",
    "",
    regex=True,
)
df["first_name"] = clean_name.str.split().str[0]
df["last_name"] = clean_name.str.split().str[-1]

# Convert date columns to dates
df["date_of_birth"] = pd.to_datetime(df["dates_of_birth"], errors="coerce")
df["hire_date"] = pd.to_datetime(df["hire_date"], errors="coerce")
today = pd.Timestamp.today().normalize()

# Calculate age
df["age"] = ((today - df["date_of_birth"]).dt.days // 365.25).astype("Int64")

# Create a termination date for terminated employees.
# The date is randomly selected between 30 days after hire and today.
def create_termination_date(row):
    if row["employee_status"] != "Terminated" or pd.isna(row["hire_date"]):
        return pd.NaT

    earliest_date = row["hire_date"] + pd.Timedelta(days=30)
    if earliest_date > today:
        earliest_date = row["hire_date"]

    available_days = (today - earliest_date).days
    random_days = random.randint(0, available_days)
    return earliest_date + pd.Timedelta(days=random_days)


df["termination_date"] = df.apply(create_termination_date, axis=1)

# Calculate service through the termination date for terminated employees.
# Active and on-leave employees are calculated through today.
service_end_date = df["termination_date"].fillna(today)
df["years_of_service"] = (
    (service_end_date - df["hire_date"]).dt.days / 365.25
).round(1)

# Replace the original manager numbers with real employee IDs.
# Employees are ranked within their own department. Non-terminated employees
# are placed first so terminated employees are not selected as managers.
# A manager always appears earlier in the ranking, which prevents circular
# reporting relationships.
df["manager_id"] = pd.NA

df["manager_eligible"] = df["employee_status"] != "Terminated"

for department, department_rows in df.groupby("department"):
    ranked_rows = department_rows.sort_values(
        by=[
            "manager_eligible",
            "salary",
            "performance_ratings",
            "hire_date",
        ],
        ascending=[False, False, False, True],
    )

    ranked_employee_ids = ranked_rows["employee_id"].tolist()

    for position, row_index in enumerate(ranked_rows.index):
        if position == 0:
            # Department head has no manager.
            continue

        # Each manager receives up to five direct reports.
        manager_position = (position - 1) // 5
        df.loc[row_index, "manager_id"] = ranked_employee_ids[manager_position]

df = df.drop(columns=["manager_eligible"])

# Standardize work hours as shift names
shift_names = {
    "9-5": "First Shift",
    "5-Sep": "First Shift",
    "8-Dec": "Second Shift",
    "Night Shift": "Third Shift",
}
df["work_shift"] = df["work_hours"].replace(shift_names)

# Replace the random skill values with department-based required skills
required_skills = {
    "HR": "Employee Relations | Recruiting | Performance Management",
    "Finance": "Financial Analysis | Budgeting | Excel",
    "IT": "Technical Support | SQL | Cybersecurity",
    "Engineering": "Technical Design | Project Management | Problem Solving",
    "Marketing": "Digital Marketing | Content Development | Market Research",
}

df["job_required_skills"] = df["department"].map(required_skills)

# Randomly give each employee one additional skill.
# Required skills for the employee's department are excluded so the skill is
# truly additional.
additional_skill_pool = [
    "Change Management",
    "Coaching",
    "Communication",
    "Conflict Resolution",
    "Customer Service",
    "Data Analysis",
    "Excel",
    "Leadership",
    "Negotiation",
    "Presentation Skills",
    "Process Improvement",
    "Project Management",
    "Public Speaking",
    "SQL",
    "Strategic Planning",
    "Technical Writing",
]


def choose_additional_skill(required_skill_text):
    required = set(required_skill_text.split(" | "))
    choices = [skill for skill in additional_skill_pool if skill not in required]
    return random.choice(choices)


df["additional_employee_skills"] = df["job_required_skills"].apply(
    choose_additional_skill
)
df["employee_skills"] = (
    df["job_required_skills"] + " | " + df["additional_employee_skills"]
)

# Replace the random certification values with department-based certifications
required_certifications = {
    "HR": "SHRM-CP",
    "Finance": "Financial Modeling Certification",
    "IT": "CompTIA A+",
    "Engineering": "Six Sigma Green Belt",
    "Marketing": "Google Analytics Certification",
}

df["job_required_certification"] = df["department"].map(required_certifications)
df["employee_certification"] = df["job_required_certification"].where(
    df.index % 2 == 0,
    "None",
)

# Replace the random benefit values with consistent benefit packages
benefit_packages = {
    "Full-time": "Medical | Dental | Vision | Retirement",
    "Part-time": "Medical | Retirement",
    "Contractor": "None",
}
df["benefits_enrollment_clean"] = df["employment_status"].map(benefit_packages)

# Replace random work-experience text with an estimated number of years
df["estimated_work_experience_years"] = (df["age"] - 22).clip(lower=0)

# Format date columns consistently
df["date_of_birth"] = df["date_of_birth"].dt.strftime("%Y-%m-%d")
df["hire_date"] = df["hire_date"].dt.strftime("%Y-%m-%d")
df["termination_date"] = df["termination_date"].dt.strftime("%Y-%m-%d")

# Remove original fields that were cleaned or replaced
df = df.drop(
    columns=[
        "name",
        "dates_of_birth",
        "work_hours",
        "skills",
        "certifications",
        "benefits_enrollment",
        "work_experience",
    ],
    errors="ignore",
)

# Use simpler column names
df = df.rename(
    columns={
        "job_titles": "job_title",
        "performance_ratings": "performance_rating",
        "city": "work_location",
    }
)

# Put important relationship and date fields near the beginning
first_columns = [
    "employee_id",
    "original_employee_id",
    "manager_id",
    "first_name",
    "last_name",
    "department",
    "job_title",
    "employee_status",
    "hire_date",
    "termination_date",
    "years_of_service",
]
other_columns = [column for column in df.columns if column not in first_columns]
df = df[first_columns + other_columns]

# Create one cleaned CSV file
df.to_csv(output_file, index=False)

print(f"Created {output_file}")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
