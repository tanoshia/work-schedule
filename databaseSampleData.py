import sqlite3
from datetime import datetime, timedelta

#define connection and cursor
connection = sqlite3.connect('employeeShifts.db')
cursor = connection.cursor()

#TEMP reset tables from prior initalizations, comment out to edit db
cursor.execute("DELETE FROM employees")
cursor.execute("DELETE FROM empShifts")
cursor.execute("DELETE FROM messages")


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
(1, '2024-03-11', '07:00', '15:00'),
(1, '2024-03-12', '07:00', '15:00'),
(1, '2024-03-13', '07:00', '15:00'),
(1, '2024-03-14', '06:00', '14:00'),
(1, '2024-03-15', '07:00', '15:00'),
(1, '2024-03-18', '07:00', '15:00'),
(1, '2024-03-20', '07:00', '15:00'),
(1, '2024-03-21', '06:00', '14:00'),
(1, '2024-03-22', '07:00', '15:00'),
(1, '2024-03-25', '07:00', '15:00'),
(1, '2024-03-26', '07:00', '15:00'),
(1, '2024-03-27', '07:00', '15:00'),
(1, '2024-03-28', '06:00', '14:00'),
(1, '2024-03-29', '07:00', '15:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(2, '2024-03-20', '08:00', '16:00'),
(2, '2024-03-21', '07:00', '15:00'),
(2, '2024-03-22', '08:00', '16:00'),
(2, '2024-03-23', '07:00', '15:00'),
(2, '2024-03-24', '07:00', '15:00'),
(2, '2024-03-27', '08:00', '16:00'),
(2, '2024-03-28', '07:00', '15:00'),
(2, '2024-03-29', '08:00', '16:00'),
(2, '2024-03-30', '07:00', '15:00'),
(2, '2024-03-31', '07:00', '15:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(3, '2024-03-18', '17:00', '21:30'),
(3, '2024-03-19', '08:00', '21:30'),
(3, '2024-03-21', '08:00', '16:00'),
(3, '2024-03-23', '07:00', '15:00'),
(3, '2024-03-24', '07:00', '15:00'),
(3, '2024-03-25', '17:00', '21:30'),
(3, '2024-03-26', '14:00', '21:30'),
(3, '2024-03-28', '08:00', '16:00'),
(3, '2024-03-30', '07:00', '15:00'),
(3, '2024-03-31', '07:00', '15:00')""")

cursor.execute("""INSERT INTO empShifts 
(empID, shiftDate, startTime, endTime) VALUES 
(4, '2024-03-18', '11:00', '18:00'),
(4, '2024-03-19', '11:00', '18:00'),
(4, '2024-03-22', '11:00', '18:00'),
(4, '2024-03-23', '11:00', '18:00'),
(4, '2024-03-24', '11:00', '18:00'),
(4, '2024-03-25', '11:00', '18:00'),
(4, '2024-03-26', '11:00', '18:00')""")

connection.commit()


#add to messages SAMPLE DATA
theTimeNow = datetime.now()  # Format as ISO8601 without microseconds
cursor.execute("""INSERT INTO messages (empID, mngrID, messageBody, timestamp) 
               VALUES (?, ?, ?, ?)""", (3, 1, "I'm sick so ima need a lot of time off", theTimeNow.isoformat(' ', 'seconds')))

print("Now",theTimeNow)
theTimeLater = theTimeNow + timedelta(hours=1, minutes=10, seconds=23)
print("Later",theTimeLater)
cursor.execute("""INSERT INTO messages (empID, mngrID, messageBody, timestamp) 
               VALUES (?, ?, ?, ?)""", (3, 1, "Sure thing bud", theTimeLater.isoformat(' ', 'seconds')))


connection.commit()


#get results
cursor.execute("SELECT * FROM empShifts")
results = cursor.fetchall()
print(results)

connection.close()