import sqlite3
from prettytable import PrettyTable

# Connect to the SQLite database
connection = sqlite3.connect('employeeShifts.db')
cursor = connection.cursor()

# Function to print table data using PrettyTable
def print_table_data(cursor, table_name, sort_columns=None):
    query = f"SELECT * FROM {table_name}"
    if sort_columns:
        query += " ORDER BY " + ", ".join(sort_columns)

    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]

    table = PrettyTable()
    table.field_names = columns

    for row in rows:
        table.add_row(row)

    print(table)

# Printing the 'employees' table
print("Employees Table:")
print_table_data(cursor, "employees")

# Printing the 'empShifts' table sorted by shiftDate and then by startTime
print("\nEmployee Shifts Table (Sorted by shiftDate and startTime):")
print_table_data(cursor, "empShifts", ["shiftDate", "startTime"])

# Adding display for the 'messages' table
print("\nMessages Table:")
print_table_data(cursor, "messages", ["messageID"])  # Assuming sorting by messageID makes sense for your application


# Close the database connection
connection.close()
