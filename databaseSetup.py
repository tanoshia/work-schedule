import sqlite3

#define connection and cursor
connection = sqlite3.connect('employeeShifts.db')

cursor = connection.cursor()

#TEMP reset tables from prior initalizations, comment out to edit db
cursor.execute("DELETE FROM employees")
cursor.execute("DELETE FROM empShifts")

#create employees table
command1 = """CREATE TABLE IF NOT EXISTS employees (
empID INTEGER AUTO_INCREMENT PRIMARY KEY,
name TEXT,
position TEXT,
sickHours)"""

cursor.execute(command1)

#create shift table
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
               ('Ethan Shaw', 'Worker')""")
cursor.execute("""INSERT INTO employees 
               (name, position) VALUES 
               ('Adam Marks', 'Worker')""")
connection.commit()

#add to empShifts SAMPLE DATA
# cursor.execute("""INSERT INTO empShifts (empID, shiftDate, startTime, endTime) VALUES (23, '2024-01-24', '08:00', '16:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(1, '2024-03-04', '07:00', '15:00'),
(1, '2024-03-05', '07:00', '15:00'),
(1, '2024-03-06', '07:00', '15:00'),
(1, '2024-03-07', '06:00', '14:00'),
(1, '2024-03-08', '07:00', '15:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(2, '2024-03-06', '08:00', '16:00'),
(2, '2024-03-07', '07:00', '15:00'),
(2, '2024-03-08', '08:00', '16:00'),
(2, '2024-03-09', '07:00', '15:00'),
(2, '2024-03-10', '07:00', '15:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(3, '2024-03-04', '17:00', '21:30'),
(3, '2024-03-05', '14:00', '21:30'),
(3, '2024-03-07', '08:00', '16:00'),
(3, '2024-03-09', '07:00', '15:00'),
(3, '2024-03-10', '07:00', '15:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(4, '2024-03-04', '11:00', '18:00'),
(4, '2024-03-05', '11:00', '18:00'),
(4, '2024-03-08', '11:00', '18:00'),
(4, '2024-03-09', '11:00', '18:00'),
(4, '2024-03-10', '11:00', '18:00')""")

connection.commit()


#get results
cursor.execute("SELECT * FROM empShifts")
results = cursor.fetchall()
print(results)

connection.close()