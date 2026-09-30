import pandas as pd

file_path = r"C:\Users\diyac\Desktop\Scholarsync\scholarships_clean.csv"

df = pd.read_csv(file_path)

print("========== DATASET SUMMARY ==========")

print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

print("\n========== COLUMN INFORMATION ==========")
print(df.info())

print("\n========== SCHOLARSHIPS BY MINISTRY ==========")
print(df["ministry"].value_counts())

print("\n========== SCHOLARSHIPS BY EDUCATION LEVEL ==========")
print(df["education_level"].value_counts())

print("\n========== SCHOLARSHIPS BY GENDER ==========")
print(df["gender"].value_counts())

print("\n========== SCHOLARSHIPS BY STATE ==========")
print(df["state"].value_counts())

print("\n========== SCHOLARSHIPS BY SCHEME TYPE ==========")
print(df["scheme_type"].value_counts())

print("\n========== SCHOLARSHIPS BY CATEGORY ==========")
print(df["category"].value_counts())

print("\n========== ACADEMIC YEAR ==========")
print(df["academic_year"].value_counts())

print("\n========== CLOSING DATES ==========")
print(df["closing_date"].value_counts())

print("\n========== INCOME LIMIT ==========")
print(df["income_limit_inr"].describe())