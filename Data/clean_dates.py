import pandas as pd

file_path = r"C:\Users\diyac\Desktop\Scholarsync\scholarships_clean.csv"

df = pd.read_csv(file_path)

date_columns = [
    "opening_date",
    "closing_date",
    "verification_deadline"
]

for column in date_columns:
    df[column] = pd.to_datetime(
        df[column],
        format="%d-%m-%Y",
        errors="coerce"
    )

# Save the processed dataset
output_path = r"C:\Users\diyac\Desktop\Scholarsync\scholarships_final.csv"

df.to_csv(output_path, index=False)

print("Date conversion completed!")
print("Final dataset saved successfully.")
print("Location:", output_path)
print("Rows:", len(df))
print("Columns:", len(df.columns))