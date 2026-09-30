import pandas as pd

file_path = r"C:\Users\diyac\Desktop\Scholarsync\scholarships_final.csv"

df = pd.read_csv(file_path)

print("\n========== EDUCATION LEVEL ==========")
print(df["education_level"].value_counts().to_string())

print("\n========== COURSE ==========")
print(df["course"].value_counts().to_string())