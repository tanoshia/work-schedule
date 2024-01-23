import sqlite3

#define connection and cursor
connection = sqlite3.connect('employeeShifts.db')

cursor = connection.cursor()

#create shift table
command1 = """CREATE TABLE IF NOT EXISTS employees (
empID INTEGER PRIMARY KEY,
name TEXT,
position TEXT,
sickHours)"""

cursor.execute(command1)

#create employees table
command2 = """CREATE TABLE IF NOT EXISTS empShifts (
shiftID INTEGER PRIMARY KEY,
empID INTEGER,
shiftDate DATE,
startTime TIME,
endTime TIME,
FOREIGN KEY(empID) REFERENCES employees(empID))"""

cursor.execute(command2)

#add to employees SAMPLE DATA
cursor.execute("""INSERT INTO employees 
               (name, position) VALUES 
               ('Brett Vandenburg', 'Manager')""")
cursor.execute("""INSERT INTO employees 
               (name, position) VALUES 
               ('David Thoe', 'Manager')""")
cursor.execute("""INSERT INTO employees 
               (name, position) VALUES 
               ('Adam Marks', 'Worker')""")
cursor.execute("""INSERT INTO employees 
               (name, position) VALUES 
               ('Ethan Shaw', 'Manager')""")
connection.commit()

#add to empShifts SAMPLE DATA
cursor.execute("""INSERT INTO empShifts (empID, shiftDate, startTime, endTime) VALUES (23, '2024-01-24', '08:00', '16:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(9, '2024-01-22', '07:00', '15:00'),
(9, '2024-01-23', '07:00', '15:00'),
(9, '2024-01-24', '07:00', '15:00'),
(9, '2024-01-25', '06:00', '14:00'),
(9, '2024-01-26', '07:00', '15:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(31, '2024-01-24', '08:00', '16:00'),
(31, '2024-01-25', '07:00', '15:00'),
(31, '2024-01-26', '08:00', '16:00'),
(31, '2024-01-27', '07:00', '15:00'),
(31, '2024-01-28', '07:00', '15:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(67, '2024-01-24', '11:00', '18:00'),
(67, '2024-01-25', '11:00', '18:00'),
(67, '2024-01-26', '11:00', '18:00'),
(67, '2024-01-27', '11:00', '18:00'),
(67, '2024-01-28', '11:00', '18:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(23, '2024-01-22', '17:00', '21:00'),
(23, '2024-01-23', '14:00', '21:00'),
(23, '2024-01-26', '08:00', '16:00'),
(23, '2024-01-27', '07:00', '15:00'),
(23, '2024-01-28', '07:00', '15:00')""")

connection.commit()


#get results
cursor.execute("SELECT * FROM empShifts")
results = cursor.fetchall()
print(results)

connection.close()