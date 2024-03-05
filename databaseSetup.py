import sqlite3

#define connection and cursor
connection = sqlite3.connect('employeeShifts.db')
cursor = connection.cursor()

# reset db
cursor.execute("DROP TABLE IF EXISTS employees")
cursor.execute("DROP TABLE IF EXISTS empShifts")
cursor.execute("DROP TABLE IF EXISTS messages")
connection.commit()

cursor.execute("PRAGMA foreign_keys = ON;")

#create employees table
createEmployeesTable = """CREATE TABLE IF NOT EXISTS employees (
empID INTEGER PRIMARY KEY,
name VARCHAR(64),
position VARCHAR(64),
sickHours INTEGER)"""

cursor.execute(createEmployeesTable)

#create shift table
createEmpShiftsTable = """CREATE TABLE IF NOT EXISTS empShifts (
shiftID INTEGER PRIMARY KEY,
empID INTEGER,
shiftDate DATE,
startTime TIME,
endTime TIME,
FOREIGN KEY(empID) REFERENCES employees(empID))"""

cursor.execute(createEmpShiftsTable)

#create messages table
createMessagesTable = """CREATE TABLE IF NOT EXISTS messages (
messageID       INTEGER         NOT NULL        PRIMARY KEY,
empID           INTEGER         NOT NULL,
mngrID          INTEGER         NOT NULL,
timestamp       VARCHAR(255)    NOT NULL,
messageBody     VARCHAR(255)    NOT NULL,
FOREIGN KEY(empID) REFERENCES employees(empID),
FOREIGN KEY(mngrID) REFERENCES employees(empID))"""

cursor.execute(createMessagesTable)

connection.close()