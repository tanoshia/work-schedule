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
    return

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
    print("Leaving view_all_shifts")
    return





#------------PERSONAL SHIFTS FUNCTION CALLER (call view_my_shifts after asking for who to search for)----------------
def view_my_shifts_caller(priorMondayDateStr, inputID=0):
    inputID = input("Employee ID: ")
    view_my_shifts(priorMondayDateStr, inputID)
    print("Leaving view_my_shifts_caller")
    return


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
    print("Leaving view_my_shifts")
    return



#------------TIME OFF FUNCTION CALLER (call view_time_off after asking for who to search for and validating managers)----------------
def view_time_off_caller(priorMondayDateStr, listType='all', empID=None):    # 'all' or 'pending'
    # if no ID passed in, ask for one
    if empID:
        inputID = empID
    else:
        inputID = input("Employee ID: ")
        
    
    # check if the PASSED IN ID is a manager
    if is_manager(empID):   # if the PASSED IN ID is a manager, they've already typed password, thus skip next
        inputLastStartDate = input("End Date (blank for no date cap)\n[YYYY-MM-DD]: ")
        view_all_time_off(priorMondayDateStr, inputID, listType, inputLastStartDate)
        return
    # check if the INPUT ID is a manager
    if is_manager(inputID):
        # open db for manager validation and password check
        connection = sqlite3.connect('employeeShifts.db')
        cursor = connection.cursor()

        correctPassword = False
        while not correctPassword:
            print("Enter Manager Password (or q to quit)    **press any key (password is omit for assignment)**")
            inputPassword = input("Password: ")
            if inputPassword == 'q':
                print("Quitting")
                return 0
            else:
                correctPassword = is_correct_password(inputPassword)

        connection.close()  # close db

        # if password correct:
        inputLastStartDate = input("End Date (blank for no date cap)\n[YYYY-MM-DD]: ")
        view_all_time_off(priorMondayDateStr, inputID, listType, inputLastStartDate)
    else: 
        view_my_time_off(priorMondayDateStr, inputID)   # for non-managers
    
    print("Leaving view_time_off_caller")
    return


#------------ALL TIME OFF VIEW (Manager)----------------
def view_all_time_off(priorMondayDateStr, mngrID, listType, lastStartDate=None):      # for managers
    if lastStartDate == None or len(lastStartDate) < 1:    # if no end date
        # get all employee's active time-off requests from microservice
        msg = ['M']
        socket.send_json(msg)       # through ZeroMQ
    else:       # if end date presented
        msg = ['M', lastStartDate]
        socket.send_json(msg)       # through ZeroMQ

    requests = socket.recv_json()

    # open db for adding manager name in place of their id
    connection = sqlite3.connect('employeeShifts.db')
    cursor = connection.cursor()

    if listType == 'all':
        # table headers
        table = PrettyTable(["reqID", "empID", "Start Date", "End Date", "Status", "Updated by", "Time Off Reason"])

        for request in requests:
            requestID, empID, startDate, endDate, reason, approvingManager, approved = request
            
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
            table.add_row([requestID, empID, startDate, endDate, status, approvingManager, reason])
    
        # end, resume to manager TO UI
        connection.close() 
        print(table)
        view_all_time_off_UI(priorMondayDateStr, mngrID, 'all', lastStartDate)    # 'all' or 'pending'
    elif listType == 'pending':
        # table headers
        pendingTable = PrettyTable(["reqID", "empID", "Start Date", "End Date", "Time Off Reason"])

        for request in requests:
            requestID, empID, startDate, endDate, reason, approvingManager, approved = request
            
            # determine the status based on 'approved' and 'approvingManager'
            if approved:
                status = "Approved"
            elif approvingManager == 0 or approvingManager is None:
                status = "Pending"
                # add row to table only if it is pending approval
                pendingTable.add_row([requestID, empID, startDate, endDate, reason])
            else:
                status = "Denied"
            # if the approving manager has a value
            if approvingManager is not None:
                approvingManager = get_employeeName(approvingManager, cursor)
                
        # end, resume to manager TO UI
        connection.close() 
        print(pendingTable)
        view_all_time_off_UI(priorMondayDateStr, mngrID, 'pending', lastStartDate)    # 'all' or 'pending'

    else:
        print("err: invalid listType")

    print("Leaving view_all_time_off")
    return


#------------MY TIME OFF VIEW (Employee)----------------
def view_my_time_off(priorMondayDateStr, empID):
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
        empIDNotUsed, startDate, endDate, reason, approvingManager, approved = request
        
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

    view_my_time_off_UI(priorMondayDateStr, empID)
    print("Leaving view_my_time_off")
    return

#------------REQUEST NEW TIME OFF (Employee)----------------
def request_new_time_off(priorMondayDateStr, empID):
    inputStartDate  = input("Time Off Start Date [YYYY-MM-DD]: ")
    inputEndDate    = input("Time Off End Date   [YYYY-MM-DD]: ")
    inputReason     = input("Reason (optional): ")
    
    # msg = ['C', [3, '2024-05-01', '2024-05-03', 'reas lo']] test data
    msg = ['C', [empID, inputStartDate, inputEndDate, inputReason]]
    socket.send_json(msg)       # through ZeroMQ
    socket.recv_json()
    print("Saved! Time Off Requested.")

    view_my_time_off(priorMondayDateStr, empID)
    print("Leaving request_new_time_off")
    return
    
#------------UPDATE A TIME OFF (Manager)----------------
def update_time_off_status(priorMondayDateStr, mngrID):
    print("Updating Shifts Status, type \'q\' to quit")
    c = 0
    reqID  = 0
    status = 0
    while reqID != 'q' and status != 'q':
        reqID  = input("reqID: ")
        if reqID  == 'q': continue

        status  = input("Status (a/d): ")
        if status == 'q': continue

        if   status == 'a': status = True
        elif status == 'd': status = False
        else: print("Invalid status; type \'a\' for Approve or \'d\' for Deny")
        msg = ['U', [reqID, mngrID, status]]
        socket.send_json(msg)       # through ZeroMQ
        socket.recv_json()

        c+=1 # c++ :D
    print("Updated",c,"shifts","\n")
    view_all_time_off_UI(priorMondayDateStr, mngrID, 'pending')    # 'all' or 'pending'
    print("Leaving update_time_off_status")
    return

#------------F----------------
def message_manager():

    return 0

#------------G----------------
# def back():
 # relocated to end of file?
#     return 0

#------------QUIT PROGRAM----------------
def quit_program():
    return

#------------I----------------
def default():
    print("Invalid choice.")
    return


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
    print("3 | Time off                     | To see your upcoming time off requests and status")
    print("m | Message a manager [WIP]      | For any questions or other requests!")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    return


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
    print("4 | Time off                     | To see your upcoming time off requests and status")
    print("m | Message a manager [WIP]      | For any questions or other requests!")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    return


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
    print("4 | Time off                     | To see your upcoming time off requests and status")
    print("m | Message a manager [WIP]      | For any questions or other requests!")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    return


#------------EDIT MY SHIFT MENU UI (display options available)----------------

#------------SWITCH SHIFTS MENU UI (display options available)----------------

#------------TIME OFF MENU UI EMPLOYEE (display options available)----------------
def view_my_time_off_UI(priorMondayDateStr, empID):
    # handle the menu options
    def menu_option(inputChoice):
        switcher = {
            '1': lambda: request_new_time_off(priorMondayDateStr, empID),
            'm': lambda: message_manager(),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing Time Off")
    print("1 | Request New Time Off")
    print("m | Message a manager [WIP]      | For any questions or other requests!")
    print("b | Back")
    print("q | Quit")  
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    return

#------------TIME OFF MENU UI MANAGER (display options available)----------------
def view_all_time_off_UI(priorMondayDateStr, mngrID, listType='all', lastStartDate=None):
    # handle the menu options
    def menu_option(inputChoice):
        switcher = {
            '1': lambda: view_time_off_caller(priorMondayDateStr,'all', mngrID),
            '2': lambda: view_time_off_caller(priorMondayDateStr,'pending', mngrID),
            '3': lambda: update_time_off_status(priorMondayDateStr, mngrID),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing Time Off")
    if listType == 'all':
        print("1 | All Time off         [Here!] | Recall this table to view it with/without an end date")
        print("2 | Pending Time off             | To see only future time off with status \'Pending\'")
    elif listType == 'pending':
        print("1 | All Time off                 | To see your upcoming time off requests and status")
        print("2 | Pending Time off     [Here!] | Recall this table to view it with/without an end date")
    print("3 | Appove/Deny a Request")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    return


#------------MNGR TIME OFF MENU UI (display options available)----------------






#------------Function/Menu History (GLOBAL) (for backtracking)----------------
MENU_HISTORY = [main_UI]

def back():
    if MENU_HISTORY:
        print("Prev1", MENU_HISTORY)
        previous_menu = MENU_HISTORY.pop()  # Remove and return the last visited menu
        print("Prev1", previous_menu)
        previous_menu()  # Call the previous menu function


main_UI()