import pandas as pd

file_path = r"C:\Users\diyac\Desktop\Scholarsync\scholarships_final.csv"

df = pd.read_csv(file_path)


# -----------------------------
# EDUCATION LEVEL
# -----------------------------

def clean_education(value):
    value = str(value).strip().lower()

    if value == "not specified":
        return "Not Specified"

    return value


df["education_level_std"] = df["education_level"].apply(clean_education)


# -----------------------------
# CATEGORY
# -----------------------------

def clean_category(value):
    value = str(value).strip().lower()

    if value == "not specified":
        return "Not Specified"

    return value


df["category_std"] = df["category"].apply(clean_category)


# -----------------------------
# GENDER
# -----------------------------

def clean_gender(value):
    value = str(value).strip().lower()

    if value in ["all", "all genders", "both"]:
        return "All"

    if value == "not specified":
        return "Not Specified"

    return value


df["gender_std"] = df["gender"].apply(clean_gender)


# -----------------------------
# SAVE
# -----------------------------

output_path = r"C:\Users\diyac\Desktop\Scholarsync\scholarships_standardized.csv"

df.to_csv(output_path, index=False)

print("Standardization completed!")
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Saved at:", output_path)

print("\nEducation values:")
print(df["education_level_std"].value_counts())

print("\nCategory values:")
print(df["category_std"].value_counts())

print("\nGender values:")
print(df["gender_std"].value_counts())