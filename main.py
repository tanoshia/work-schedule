import os
from datetime import datetime, timedelta
import sqlite3
from prettytable import PrettyTable

#------------MICROSERVICE CONNECTION (for time off handling)----------------
import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:5555')
print('connected to server')



#------------HELPER FUNCTIONS (for shift displays)----------------
def get_employeeName(empID, cursor): # assumes open db due to cursor parameter
    # Assumes employee table is named 'employees' with columns 'empID' and 'name'
    cursor.execute("SELECT name FROM employees WHERE empID = ?", (empID,))
    result = cursor.fetchone()
    if result: return result[0]
    else: None

# generate the formatted string for a single day
def generate_weekday(dateStr):
    dateObj = datetime.strptime(dateStr, '%Y-%m-%d')
    return dateObj.strftime('%a %m/%d')

# generate an array of formatted strings for a week starting at the input day
def generate_weekdays(startDateStr):
    startDate = datetime.strptime(startDateStr, '%Y-%m-%d')
    weekdays = []
    for i in range(7):
        day = startDate + timedelta(days=i)
        dayStr = day.strftime('%Y-%m-%d')
        weekdays.append(generate_weekday(dayStr))
    return weekdays

# simplify shift start and end time (e.g. 08:00-16:00 becomes 8am-4pm)
def simplify_shiftTime(startTimeStr, endTimeStr):
    # string to datetime
    startTimeObj = datetime.strptime(startTimeStr, '%H:%M')
    endTimeObj = datetime.strptime(endTimeStr, '%H:%M')

    def format_shiftTime(time_str): # 24hr to 12hr, strip leading 0, %I=12hr, %M=mins, %p=am/pm
        time_obj = datetime.strptime(time_str, '%H:%M')
        if time_obj.minute == 0:    # if mins are 0, format without minutes
            return time_obj.strftime('%I%p').lstrip('0').lower()
        else:                       # if mins not 0, format with minutes
            return time_obj.strftime('%I:%M%p').lstrip('0').lower()

    startTimeSimple = format_shiftTime(startTimeStr)
    endTimeSimple = format_shiftTime(endTimeStr)

    #return back as string
    return f"{startTimeSimple}-{endTimeSimple}"


#------------HELPER FUNCTIONS (for validating managers)----------------
def is_manager(empID):
    # open db
    connection = sqlite3.connect('employeeShifts.db')
    cursor = connection.cursor()
    
    # check if employee with the given empID is a manager in the position column
    cursor.execute("SELECT position FROM employees WHERE empID = ?", (empID,))
    result = cursor.fetchone()

    # close db
    connection.close() 
    
    if result and result[0] == 'Manager':
        return True
    else:
        return False


def is_correct_password(inputPassword):
    #omit for assignment so this can be tested by anyone for now
    return True






#------------ALL SHIFTS (Create/update and display view)----------------
def view_all_shifts(startDateStr):
    # open database
    connection = sqlite3.connect('employeeShifts.db')
    cursor = connection.cursor()

    # into message, fetch employee count
    cursor.execute("SELECT COUNT(DISTINCT empID) FROM empShifts")
    empCount = cursor.fetchone()[0]
    print(f"Displaying shifts for all {empCount} employees during the week of {startDateStr}")

    # get oldest shift date in db to validate input
    cursor.execute("SELECT MIN(shiftDate) FROM empShifts")
    oldestShiftDateTuple = cursor.fetchone()
    if oldestShiftDateTuple:
        oldestShiftDateStr = oldestShiftDateTuple[0] # change result from Tuple to string
    
         # convert startDate and oldestShiftDate to datetime objects to compare
        startDateObj = datetime.strptime(startDateStr, '%Y-%m-%d')
        oldestShiftDateObj = datetime.strptime(oldestShiftDateStr, '%Y-%m-%d')
        endDateObj = startDateObj + timedelta(days=6)
        endDateStr = endDateObj.strftime('%Y-%m-%d')

        if startDateObj < oldestShiftDateObj:
            print(f"No Shifts before this date! Earliest shift to view is {oldestShiftDateStr}")

    #connect rows to all empShifts rows between start abd end date (start date6)
    sqlQuery = "SELECT empID, shiftDate, startTime, endTime FROM empShifts WHERE shiftDate >= ? AND shiftDate <= ? ORDER BY empID, shiftDate, startTime"
    cursor.execute(sqlQuery, (startDateStr, endDateStr))
    shiftsData = cursor.fetchall()
    # db remains open to use get_employeeName from their ID, otherwise could close here


    headers = ["Employee"] + generate_weekdays(startDateStr)
    table = PrettyTable(headers)

    # process shift data
    currentEmpID = None
    rowData = []

    for empID, shiftDate, startTime, endTime in shiftsData: #dates as string
        if empID != currentEmpID:
            # if new employee, add the prior emp data to the table
            if currentEmpID is not None:
                table.add_row(rowData)
            
            # fetch employees name
            employeeName = get_employeeName(empID, cursor)
            currentEmpID = empID
            # start new row for new emp
            rowData = [employeeName] + ["-"] * 7  # initialize with placeholders

        # format shiftDate for matching headers
        shiftDateFormatted = generate_weekday(shiftDate)

        # find the day index, then update the row data
        dayIndex = headers.index(shiftDateFormatted)
        rowData[dayIndex] = simplify_shiftTime(startTime, endTime) # adds string '8am-4:30pm' for '08:00-16:30' to row at index

    # add the last emp data
    if rowData:
        table.add_row(rowData)

    #close database
    connection.close()

    print(table)
    view_all_shifts_UI(startDateStr)





#------------PERSONAL SHIFTS FUNCTION CALLER (call view_my_shifts after asking for who to search for)----------------
def view_my_shifts_caller(priorMondayDateStr, inputID=0):
    inputID = input("Employee ID: ")
    view_my_shifts(priorMondayDateStr, inputID)


#------------PERSONAL SHIFTS (Create/update and display view)----------------
def view_my_shifts(startDateStr, empID):

    earliestHour = 5 #int in 24hr
    latestHour = 23 #int in 24hr

    # open db
    connection = sqlite3.connect('employeeShifts.db')
    cursor = connection.cursor()

    # fetch employee count
    cursor.execute("SELECT COUNT(DISTINCT empID) FROM empShifts")
    empCount = cursor.fetchone()[0]
    if int(empID) > empCount:
        print(f"Employee ID too large! No employee found; Try again.")
        view_my_shifts_caller(startDateStr)
        return

    #get employee name from db
    employeeName = get_employeeName(empID, cursor)

    # into message, use fetched employee name
    print(f"Displaying shifts for {employeeName} during the week of {startDateStr}")

    # get oldest shift date in db to validate input
    cursor.execute("SELECT MIN(shiftDate) FROM empShifts")
    oldestShiftDateTuple = cursor.fetchone()
    if oldestShiftDateTuple:
        oldestShiftDateStr = oldestShiftDateTuple[0] # change result from Tuple to string
    
         # convert startDate and oldestShiftDate to datetime objects to compare
        startDateObj = datetime.strptime(startDateStr, '%Y-%m-%d')
        oldestShiftDateObj = datetime.strptime(oldestShiftDateStr, '%Y-%m-%d')
        endDateObj = startDateObj + timedelta(days=6)
        endDateStr = endDateObj.strftime('%Y-%m-%d')

        if startDateObj < oldestShiftDateObj:
            print(f"No Shifts before this date! Earliest shift to view is {oldestShiftDateStr}")
    

    #connect rows to all empShifts rows between start abd end date (start date+6)
    sqlQuery = "SELECT shiftDate, startTime, endTime FROM empShifts WHERE empID = ? AND shiftDate >= ? AND shiftDate <= ? ORDER BY shiftDate, startTime"
    cursor.execute(sqlQuery, (empID, startDateStr, endDateStr))
    shiftsData = cursor.fetchall()
    # close db
    connection.close() 


    headers = ["Hours"] + generate_weekdays(startDateStr)
    table = PrettyTable(headers)

    # process shift data
    hourIterator = earliestHour


    for hour in range(earliestHour, latestHour + 1):
        rowData = [""] * len(headers)
        rowData[0] = f"{hour % 12 if hour not in [0, 12] else 12}{'am' if hour < 12 else 'pm'}" # set left colum to 12hr time
        for i in range(1, len(rowData)):
            rowData[i] = '.'

        # if shift this hour
        for shiftDate, startTime, endTime in shiftsData:
            shiftStartHour = int(startTime.split(':')[0])
            shiftEndHour = int(endTime.split(':')[0])

            if shiftStartHour <= hour < shiftEndHour:
                dayIndex = headers.index(generate_weekday(shiftDate))
                rowData[dayIndex] = '########'

        # add the last hour data
        table.add_row(rowData)
    
    print(table)

    view_my_shifts_UI(startDateStr, empID)


#------------TIME OFF FUNCTION CALLER (call view_time_off after asking for who to search for and validating managers)----------------
def view_time_off_caller(priorMondayDateStr, inputID=0):
    inputID = input("Employee ID: ")
    
    # open db
    connection = sqlite3.connect('employeeShifts.db')
    cursor = connection.cursor()

    # check manager numbers
    if is_manager(inputID):
        correctPassword = False
        while not correctPassword:
            print("Enter Manager Password (or q to quit)    **omit for assignment, any string will be correct**")
            inputPassword = input("Input: ")
            if inputPassword == 'q':
                print("Quitting")
                return 0
            else:
                correctPassword = is_correct_password(inputPassword)
        view_all_time_off(priorMondayDateStr, inputID)  # for managers
    else: 
        view_my_time_off(priorMondayDateStr, inputID)   # for non-managers

    # close db
    connection.close() 


#------------ALL TIME OFF VIEW (Manager)----------------
def view_all_time_off(priorMondayDateStr, mngrID):      # for managers
    # get an employee's active time-off requests from microservice
    msg = ['M']
    socket.send_json(msg)       # through ZeroMQ

    requests = socket.recv_json()

    # table headers
    table = PrettyTable(["reqID", "empID", "Start Date", "End Date", "Status", "Updated by", "Time Off Reason"])
    table = PrettyTable(["reqID", "empID", "Start Date", "End Date", "Status", "Time Off Reason"])
    pendingTable = PrettyTable(["reqID", "empID", "Start Date", "End Date", "Time Off Reason"])

    for request in requests:
        requestID, empID, startDate, endDate, reason, approvingManager, approved = request
        
        # determine the status based on 'approved' and 'approvingManager'
        if approved:
            status = "Approved"
        elif approvingManager == 0 or approvingManager is None:
            status = "Pending"
            pendingTable.add_row([requestID, empID, startDate, endDate, reason])
        else:
            status = "Denied"
        
        # add row to table
        table.add_row([requestID, empID, startDate, endDate, status, approvingManager, reason])
    
    print(table)
    print(pendingTable)

#------------MY TIME OFF VIEW (Employee)----------------
def view_my_time_off(startDateStr, empID):
    # get an employee's active time-off requests from microservice
    msg = ['E', empID]
    socket.send_json(msg)       # through ZeroMQ

    requests = socket.recv_json()

    # open db for adding manager name in place of their id
    connection = sqlite3.connect('employeeShifts.db')
    cursor = connection.cursor()
    
    # table headers
    table = PrettyTable(["Start Date", "End Date", "Status", "Updated by", "Time Off Reason"])

    for request in requests:
        empID, startDate, endDate, reason, approvingManager, approved = request
        
        # determine the status based on 'approved' and 'approvingManager'
        if approved:
            status = "Approved"
        elif approvingManager == 0 or approvingManager is None:
            status = "Pending"
        else:
            status = "Denied"
        # if the approving manager has a value
        if approvingManager is not None:
            approvingManager = get_employeeName(approvingManager, cursor)

        # add row to table
        table.add_row([startDate, endDate, status, approvingManager, reason])

    connection.close() 

    print(table)





#------------F----------------
def message_manager():

    return 0

#------------G----------------
def back():

    return 0

#------------H----------------
def quit_program():
    return

#------------I----------------
def default():
    print("Invalid choice.")



#------------------------------------------------------------------------------
#
#
#-----------------------------------Menus--------------------------------------
#
#
#------------------------------------------------------------------------------
    
#------------MAIN MENU UI (greet and display options available)----------------
def main_UI():
    today = datetime.now()
    lastWeek = today - timedelta(days=7)
    nextWeek = today + timedelta(days=7)
    today = nextWeek #TEMP
    # calc todays weekday (0=Monday, 1=Tuesday...6=Sunday)
    daysToMonday = today.weekday()
    priorMondayDate = today - timedelta(days=daysToMonday)
    priorMondayDateStr = priorMondayDate.strftime('%Y-%m-%d')

    # handle the menu options
    def menu_option(inputChoice):
        switcher = {
            '1': lambda: view_all_shifts(priorMondayDateStr),
            '2': lambda: view_my_shifts_caller(priorMondayDateStr),
            '3': lambda: view_time_off_caller(priorMondayDateStr),
            'm': lambda: message_manager(),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Schedule Viewer 9000")
    print("1 | All Shifts                   | View shifts for all employees for the upcoming week")
    print("2 | My Shifts                    | View in detial and edit your upcoming shifts")
    print("3 | Time off (+Pending) [WIP]    | To see your upcoming time off requests and status")
    print("m | Message a manager [WIP]      | For any questions or other requests!")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")

    menu_option(inputChoice)




#------------ALL SHIFTS - PREV WEEK - MENU UI (view all shifts for the previous relative week)----------------
def view_all_prev_week():

    return 0

#------------ALL SHIFTS - NEXT WEEK - MENU UI (view all shifts for the next relative week)----------------
def view_all_next_week():

    return 0

#------------ALL SHIFTS MENU UI (display options available)----------------
def view_all_shifts_UI(priorMondayDateStr, empID=0):
    # handle the menu options
    def menu_option(inputChoice):
        switcher = {
            '1': lambda: view_all_prev_week,
            '2': lambda: view_all_next_week,
            '3': lambda: view_my_shifts_caller(priorMondayDateStr, empID),
            '4': lambda: view_time_off_caller(priorMondayDateStr),
            'm': lambda: message_manager,
            'b': lambda: back,
            'q': lambda: quit_program
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing all employee shifts")
    print("1 | <- Previous Week [WIP]")
    print("2 | -> Next Week [WIP]")
    print("3 | My Shifts                    | View in detial and edit your upcoming shifts")
    print("4 | Time off (+Pending) [WIP]    | To see your upcoming time off requests and status")
    print("m | Message a manager [WIP]      | For any questions or other requests!")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")

    menu_option(inputChoice)



#------------MY SHIFTS MENU UI (display options available)----------------
def view_my_shifts_UI(priorMondayDateStr, empID):
    # handle the menu options
    def menu_option(inputChoice):
        switcher = {
            '1': lambda: view_all_prev_week,
            '2': lambda: view_all_next_week,
            '3': lambda: view_all_shifts(priorMondayDateStr),
            '4': lambda: view_time_off_caller(priorMondayDateStr),
            'm': lambda: message_manager,
            'b': lambda: back,
            'q': lambda: quit_program
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing my shifts")
    print("1 | <- Previous Week [WIP]")
    print("2 | -> Next Week [WIP]")
    print("3 | All Shifts                   | View shifts for all employees for the upcoming week")
    print("4 | Time off (+Pending) [WIP]    | To see your upcoming time off requests and status")
    print("m | Message a manager [WIP]      | For any questions or other requests!")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")

    menu_option(inputChoice)




#------------EDIT MY SHIFT MENU UI (display options available)----------------

#------------SWITCH SHIFTS MENU UI (display options available)----------------

#------------TIME OFF MENU UI (display options available)----------------
def view_time_off_UI(priorMondayDateStr, empID):
    # handle the menu options
    def menu_option(inputChoice):
        switcher = {
            '1': lambda: view_all_shifts(priorMondayDateStr),
            '2': lambda: view_my_shifts_caller(priorMondayDateStr),
            '3': lambda: view_time_off_caller(priorMondayDateStr),
            'm': lambda: message_manager(),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing Time Off")
    print("1 | All Shifts                   | View shifts for all employees for the upcoming week")
    print("2 | My Shifts                    | View in detial and edit your upcoming shifts")
    print("3 | Time off (+Pending) [WIP]    | To see your upcoming time off requests and status")
    print("m | Message a manager [WIP]      | For any questions or other requests!")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")

    menu_option(inputChoice)




#------------MNGR TIME OFF MENU UI (display options available)----------------






main_UI()