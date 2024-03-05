import sqlite3

#define connection and cursor
connection = sqlite3.connect('employeeShifts.db')
cursor = connection.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")

#TEMP reset tables from prior initalizations, comment out to edit db
cursor.execute("DELETE FROM employees")
cursor.execute("DELETE FROM empShifts")

#create employees table
createEmployeesTable = """CREATE TABLE IF NOT EXISTS employees (
empID INTEGER PRIMARY KEY,
name TEXT,
position TEXT,
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
createEmpShiftsTable = """CREATE TABLE IF NOT EXISTS messages (
messageID       INTEGER         NOT NULL        PRIMARY KEY,
empID           INTEGER         NOT NULL,
mngrID          INTEGER         NOT NULL,
messageBody     TEXT            NOT NULL,
FOREIGN KEY(empID) REFERENCES employees(empID),
FOREIGN KEY(mngrID) REFERENCES employees(empID))"""

cursor.execute(createEmpShiftsTable)

connection.close()