import pandas as pd

df = pd.read_csv("employees.csv")

# See the shape — how many rows and columns?
print(df.shape)

# See the first 5 rows
print(df.head())

# See data types of each column
print(df.dtypes)

# Basic statistics
print(df.describe())


# Average salary by department
print(df.groupby("department")["salary"].mean())

# Top 3 highest paid employees
print(df.nlargest(3, "salary")[["name", "salary", "department"]])

exit()