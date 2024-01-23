import os
from datetime import datetime, timedelta
import sqlite3
from prettytable import PrettyTable



employeeList = ["Brett VanDenVurg", "David Thoe", "Adam Marks"]
for employee in employeeList:
    print(employee)


def get_employee_name(empID, cursor):
    # Assuming your employee table is named 'employees' with columns 'empID' and 'name'
    cursor.execute("SELECT name FROM employees WHERE empID = ?", (empID,))
    result = cursor.fetchone()
    return result[0] if result else None


def generate_weekdays(start_date):
    weekdays = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        weekdays.append(day.strftime('%a %m/%d'))
    return weekdays



# open database
connection = sqlite3.connect('employeeShifts.db')
cursor = connection.cursor()
#connect rows to all empShifts rows
cursor.execute("SELECT empID, shiftDate, startTime, endTime FROM empShifts ORDER BY empID, shiftDate")
shifts_data = cursor.fetchall()
# remains open to use get_employee_name from their ID

start_date = datetime.strptime('2024-01-22', '%Y-%m-%d') # first day of the week
headers = ["Employee"] + generate_weekdays(start_date)

table = PrettyTable(headers)

# process shift data
current_empID = None
row_data = []

for empID, shiftDate, startTime, endTime in shifts_data:
    if empID != current_empID:
        # if new employee, add the prior emp data to the table
        if current_empID is not None:
            table.add_row(row_data)
        
        employee_name = get_employee_name(empID, cursor)

        # start new row for new emp
        current_empID = empID
        row_data = [employee_name] + ["-"] * 7  # Initialize with placeholders

    # format shiftDate for matching headers
    shift_day_formatted = datetime.strptime(shiftDate, '%Y-%m-%d').strftime('%a %m/%d')

    # find the day index, then update the row data
    day_index = headers.index(shift_day_formatted)
    row_data[day_index] = f"{startTime}-{endTime}"

# add the last emp data
if row_data:
    table.add_row(row_data)

#close database
connection.close()


print(table)

connection.close()