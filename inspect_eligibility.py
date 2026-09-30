import pandas as pd

file_path = r"C:\Users\diyac\Desktop\Scholarsync\scholarships_final.csv"

df = pd.read_csv(file_path)

columns = [
    "scholarship_name",
    "education_level",
    "course",
    "state",
    "category",
    "gender",
    "income_limit_inr",
    "academic_requirement",
    "eligibility_rules"
]

print(df[columns].to_string(index=False))