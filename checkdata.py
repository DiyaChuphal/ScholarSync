import pandas as pd

file_path = r"C:\Users\diyac\Desktop\Scholarsync\data\raw\scholarships.csv"

df = pd.read_csv(file_path)

print("Number of rows:", len(df))
print("Number of columns:", len(df.columns))

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())

print("\nMissing values:")
print(df.isnull().sum())

print("\nDuplicate rows:")
print(df.duplicated().sum())
