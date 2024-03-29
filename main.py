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

#------------Menu History (GLOBAL) (for backtracking)----------------
MENU_HISTORY = []


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


def is_input_quit_or_back(input):
    if (input == 'q' or input == 'Q'):
        quit_program()
        return True
    elif (input == 'b' or input == 'B'):
        back()
        return True
    else:
        return False




#------------ALL SHIFTS (Create/update and display view)----------------
def view_all_shifts(startDateStr):
    MENU_HISTORY.append((view_all_shifts, startDateStr))
    startDate = datetime.strptime(startDateStr, '%Y-%m-%d') # str to date, to add time on
    endDate = startDate + timedelta(days=7)
    endDateStr = endDate.strftime('%Y-%m-%d')

    # get time off for this week:
    msg = ['M', endDateStr]
    socket.send_json(msg)       # through ZeroMQ
    requests = socket.recv_json()

    approvedTimeOff = {}  # {empID: [list of dates]}
    for request in requests:
        TOrequestID, TOempID, TOstartDate, TOendDate, TOreason, TOapprovingManager, TOapproved = request
        if TOapproved:
            if TOempID not in approvedTimeOff:
                approvedTimeOff[TOempID] = []
            start_date = datetime.strptime(TOstartDate, '%Y-%m-%d')
            end_date = datetime.strptime(TOendDate, '%Y-%m-%d')
            current_date = start_date
            while current_date <= end_date:
                approvedTimeOff[TOempID].append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)

    # open database
    connection = sqlite3.connect('employeeShifts.db')
    cursor = connection.cursor()
    
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
            print()
            view_all_shifts_UI(startDateStr)
            return

    # into message, fetch employee count
    cursor.execute("SELECT COUNT(DISTINCT empID) FROM empShifts")
    empCount = cursor.fetchone()[0]
    print(f"Displaying shifts for all {empCount} employees during the week of {startDateStr}")

    # Fetch all employees to initialize the table rows
    cursor.execute("SELECT empID, name FROM employees ORDER BY empID")
    allEmployees = cursor.fetchall()

    # setup table
    headers = ["Employee"] + generate_weekdays(startDateStr)
    table = PrettyTable(headers)
    employeeRows = {empID: [name] + ["-"] * 7 for empID, name in allEmployees}


    # process shift data
    currentEmpID = None
    rowData = []


    #connect rows to all empShifts rows between start abd end date (start date6)
    sqlQuery = """SELECT empID, shiftDate, startTime, endTime FROM empShifts 
                  WHERE shiftDate >= ? AND shiftDate <= ? 
                  ORDER BY empID, shiftDate, startTime"""
    cursor.execute(sqlQuery, (startDateStr, endDateStr))
    shiftsData = cursor.fetchall()
    # db remains open to use get_employeeName from their ID, otherwise could close here

    for empID, shiftDate, startTime, endTime in shiftsData:
        dayIndex = headers.index(generate_weekday(shiftDate))
        if empID in approvedTimeOff and shiftDate in approvedTimeOff[empID]:
            employeeRows[empID][dayIndex] = "Time Off"
        else:
            employeeRows[empID][dayIndex] = simplify_shiftTime(startTime, endTime)

    # Update rows for employees with time off but no shifts
    for empID, dates in approvedTimeOff.items():
        for date in dates:
            if date >= startDateStr and date <= endDateStr:
                dayIndex = headers.index(generate_weekday(date))
                employeeRows[empID][dayIndex] = "Time Off"

    # Add rows to the table
    for row in employeeRows.values():
        table.add_row(row)



    #close database
    connection.close()

    print(table)
    view_all_shifts_UI(startDateStr)
    return





#------------PERSONAL SHIFTS FUNCTION CALLER (call view_my_shifts after asking for who to search for)----------------
def view_my_shifts_caller(priorMondayDateStr, inputID=0):
    MENU_HISTORY.append((view_my_shifts_caller, priorMondayDateStr, inputID))
    inputID = input("Employee ID: ")
    is_input_quit_or_back(inputID)
    view_my_shifts(priorMondayDateStr, inputID)
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
            view_my_shifts_UI(startDateStr, empID)
            return
    

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
    return






#------------TIME OFF FUNCTION CALLER (call view_time_off after asking for who to search for and validating managers)----------------
def view_time_off_caller(priorMondayDateStr, listType='all', empID=None):    # 'all' or 'pending'
    # if no ID passed in, ask for one
    if empID:
        inputID = empID
    else:
        inputID = input("Employee ID: ")
    if (is_input_quit_or_back(inputID)):
        return
            
    
    # check if the PASSED IN ID is a manager
    if is_manager(empID):   # if the PASSED IN ID is a manager, they've already typed password, thus skip next
        inputLastStartDate = input("End Date (blank for no date cap)\n[YYYY-MM-DD]: ")
        view_all_time_off(priorMondayDateStr, inputID, listType, inputLastStartDate)
        return
    # check if the INPUT ID is a manager then ask for password if so
    if is_manager(inputID):
        # open db for manager validation and password check
        connection = sqlite3.connect('employeeShifts.db')
        cursor = connection.cursor()

        correctPassword = False
        while not correctPassword:
            print("Enter Manager Password (or q to quit)    **press any key (password is omit for assignment)**")
            inputPassword = input("Password: ")
            if (is_input_quit_or_back(inputPassword)):
                return
            else:
                correctPassword = is_correct_password(inputPassword)

        connection.close()  # close db

        # if password correct:
        inputLastStartDate = input("End Date (blank for no date cap)\n[YYYY-MM-DD]: ")
        view_all_time_off(priorMondayDateStr, inputID, listType, inputLastStartDate)
    else: 
        view_my_time_off(priorMondayDateStr, inputID)   # for non-managers
    
    return


#------------ALL TIME OFF VIEW (Manager)----------------
def view_all_time_off(priorMondayDateStr, mngrID, listType, lastStartDate=None):      # for managers
    MENU_HISTORY.append((view_all_time_off, priorMondayDateStr, mngrID, listType, lastStartDate))
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

    return


#------------MY TIME OFF VIEW (Employee)----------------
def view_my_time_off(priorMondayDateStr, empID):
    MENU_HISTORY.append((view_my_time_off, priorMondayDateStr, empID))
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
    return

#------------REQUEST NEW TIME OFF (Employee)----------------
def request_new_time_off(priorMondayDateStr, empID):
    inputStartDate  = input("Time Off Start Date [YYYY-MM-DD]: ")
    inputEndDate    = input("Time Off End Date   [YYYY-MM-DD]: ")
    inputReason     = input("Reason (optional): ")

    if (inputStartDate == 'q' or inputEndDate == 'q' or inputReason == 'q'):
        quit_program()
    elif (inputStartDate == 'b' or inputEndDate == 'b' or inputReason == 'b'):
        back()
        return
    elif (not inputStartDate or not inputEndDate):
        back()
        return
    
    msg = ['C', [empID, inputStartDate, inputEndDate, inputReason]]
    socket.send_json(msg)       # through ZeroMQ
    socket.recv_json()
    print("Saved! Time Off Requested.")

    view_my_time_off(priorMondayDateStr, empID)
    return
    
#------------UPDATE A TIME OFF (Manager)----------------
def update_time_off_status(priorMondayDateStr, mngrID, listType):
    MENU_HISTORY.append((update_time_off_status, priorMondayDateStr, mngrID, listType))
    print("Updating Shifts Status, type \'b\' to return back")
    c = 0
    reqID  = 0
    status = 0
    while reqID != 'b' and status != 'b':
        reqID  = input("reqID: ")
        if (reqID == 'b' or reqID == 'B'):
            back()
            return
        status  = input("Status (a/d): ")
        if (status == 'b' or status == 'B'):
            back()
            return
        if   status == 'a': status = True
        elif status == 'd': status = False
        else: print("Invalid status; type \'a\' for Approve or \'d\' for Deny")
        msg = ['U', [reqID, mngrID, status]]
        socket.send_json(msg)       # through ZeroMQ
        socket.recv_json()

        c+=1 # c++ :D
    print("Updated",c,"shifts","\n")
    view_all_time_off_UI(priorMondayDateStr, mngrID, listType)    # listType is 'all' or 'pending'
    return




#------------Message a manager       CALLER (checks if worker or manager, ----------------
def message_manager_caller(priorMondayDateStr):
    inputID = input("Employee ID: ")
    if (is_input_quit_or_back(inputID)):
        return

    # check if the INPUT ID is a manager
    if is_manager(inputID):
        # open db for password check
        connection = sqlite3.connect('employeeShifts.db')
        cursor = connection.cursor()

        correctPassword = False
        while not correctPassword:
            print("Enter Manager Password (or q to quit)    **press any key (password is omit for assignment)**")
            inputPassword = input("Password: ")
            if (is_input_quit_or_back(inputPassword)):
                return
            else:
                correctPassword = is_correct_password(inputPassword)

        connection.close()  # close db

    # if password correct or a non-manager
    message_manager(priorMondayDateStr, inputID)   # if manager, inputID (self) will be a manager
    return
    
def message_manager(priorMondayDateStr, empID):
    MENU_HISTORY.append((priorMondayDateStr, empID))
    manager = is_manager(empID) # bool
    # open db
    connection = sqlite3.connect('employeeShifts.db')
    cursor = connection.cursor()

    cursor.execute("SELECT messageID, empID, mngrID, timestamp, messageBody FROM messages")
    messages = cursor.fetchall()
    rowData = []

    # if no ID passed in, ask for one
    if manager:   # for managers
        mngrID = empID

        # messageTable headers
        messageTable = PrettyTable(["messageID", "Employee", "Timestamp", "Message"])

        for message in messages:
            messageID, tableEmpID, tableMngrID, timestamp, messageBody = message
            if str(tableMngrID) == mngrID: # grab only messages for this manager
                mngrName = get_employeeName(tableEmpID, cursor)

                # add row to messageTable
                messageTable.add_row([messageID, mngrName, timestamp, messageBody])
        print(messageTable)      
    elif not manager:
        # show all messages for me (where empID = tableEmpID)
                # messageTable headers
        messageTable = PrettyTable(["messageID", "Manager", "Timestamp", "Message"])

        for message in messages:
            messageID, tableEmpID, tableMngrID, timestamp, messageBody = message
            if str(tableEmpID) == empID: # grab only messages for this worker
                empName = get_employeeName(tableEmpID, cursor)

                # add row to messageTable
                messageTable.add_row([messageID, empName, timestamp, messageBody])
        print(messageTable)      
    else:
        print("err: employeeID invalid?")
        return
    
    #IH reassure privacy
    print("(Messages can only be viewed by the recipient manager)")

    # prompt to send a reply  
    inputRecipient = ""
    inputMessage = ""
    print("Send Reply, (or \'b\' to return back | or \'q\' to quit)") # outside loop so all others can prompt for undo message send
    if manager: inputRecipient = input("Send to employeeID: ")
    elif not manager: inputRecipient = input("Send to managerID: ")
    if (is_input_quit_or_back(inputRecipient)):
        return
    while inputRecipient != 'q' and inputMessage != 'q':

        # below are now above and at bottom of loop to handle the 'undo' case
        inputMessage   = input("Message: ")
        if (is_input_quit_or_back(inputMessage)):
            continue
        theTimeNow = datetime.now().isoformat(' ', 'seconds')

        if manager:
            cursor.execute("""INSERT INTO messages (empID, mngrID, messageBody, timestamp) 
                VALUES (?, ?, ?, ?)""", (inputRecipient, mngrID, inputMessage, theTimeNow))
        elif not manager: 
            cursor.execute("""INSERT INTO messages (empID, mngrID, messageBody, timestamp) 
                VALUES (?, ?, ?, ?)""", (empID, inputRecipient, inputMessage, theTimeNow))

        # Get the last inserted messageID in case an undo is called
        lastMessageID = cursor.lastrowid
        connection.commit()    

        print("Message sent to",get_employeeName(inputRecipient, cursor))
        print("\nSend Another Message? (or \'b\' to return back | \'q\' to quit | \'u\' to unsend last message)")

        if manager: inputRecipient = input("Send to employeeID: ")
        elif not manager: inputRecipient = input("Send to managerID: ")
        if (is_input_quit_or_back(inputRecipient)):
            continue
        if inputRecipient  == 'u':  # 'undo' last message sent by deleting
            cursor.execute("DELETE FROM messages WHERE messageID = ?", (lastMessageID,))
            connection.commit()
            print("Message Unsent")
            print("\nSend Another Message? (or \'b\' to return back | \'q\' to quit)")
            inputRecipient = input("Send to ID: ")
            if (is_input_quit_or_back(inputRecipient)):
                continue
            
    connection.close()

    main_UI()
    return

#------------GO BACK (to previous screen(s))----------------
def back():
    global MENU_HISTORY
    if len(MENU_HISTORY) > 1:  # Check if there's a previous state to go back to
        current_call = MENU_HISTORY.pop()  # Remove the current state
        last_call = MENU_HISTORY[-1]  # Peek at the last state without removing it
        
        # If the last call is the same as the current, keep popping until a different one is found
        while len(MENU_HISTORY) > 1 and last_call[0] == current_call[0]:
            MENU_HISTORY.pop()  # Remove redundant last call
            last_call = MENU_HISTORY[-1]  # Peek again
        
        if len(MENU_HISTORY) > 1:
            # Pop the unique last call to act upon it
            unique_last_call = MENU_HISTORY.pop()
            function, *args = unique_last_call
            print("\n\tGoing back...\n\n")
            function(*args)  # Execute the unique function with its arguments
        else:
            print("No previous unique menu to return to.")
            MENU_HISTORY.append(current_call)  # Re-append the current call if there's nowhere else to go
    else:
        print("No previous menu to return to.")


#------------QUIT PROGRAM----------------
def quit_program():
    global MENU_HISTORY
    MENU_HISTORY = [main_UI]
    print("Quitting...\n")
    print("Have a Great Day!")
    return

#------------DEFAULT CHOICE (to customize when invalid switcher input)----------------
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
    MENU_HISTORY.append((main_UI,))
    today = datetime.now()
    # calc todays weekday (0=Monday, 1=Tuesday...6=Sunday)
    daysToMonday = today.weekday()
    priorMondayDate = today - timedelta(days=daysToMonday)
    priorMondayDateStr = priorMondayDate.strftime('%Y-%m-%d')

    # handle the menu options
    def menu_option(inputChoice):
        switcher = {
            'a': lambda: about(),
            '1': lambda: view_all_shifts(priorMondayDateStr),
            '2': lambda: view_my_shifts_caller(priorMondayDateStr),
            '3': lambda: view_time_off_caller(priorMondayDateStr),
            'm': lambda: message_manager_caller(priorMondayDateStr),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Portable Schedule Viewer")
    print("0 | About                        | General information about this program!")
    print("1 | All Shifts                   | View shifts for all employees for the upcoming week")
    print("2 | My Shifts                    | View in detial and edit your upcoming shifts")
    print("3 | Time off                     | To see your upcoming time off requests and status")
    print("m | Message a manager            | For any questions or other requests")
    print("b | Back")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    return


#------------ALL SHIFTS MENU UI (display options available)----------------
def view_all_shifts_UI(priorMondayDateStr, empID=0):
    priorMondayDate = datetime.strptime(priorMondayDateStr, '%Y-%m-%d') # str to date, to add time on
    lastPriorMondayDate = priorMondayDate - timedelta(days=7)   # for view_all_prev_week
    nextPriorMondayDate = priorMondayDate + timedelta(days=7)   # for view_all_next_week

    priorMondayDateStr = priorMondayDate.strftime('%Y-%m-%d')

    # handle the menu options
    def menu_option(inputChoice):
        switcher = {
            '1': lambda: view_all_shifts(lastPriorMondayDate.strftime('%Y-%m-%d')),
            '2': lambda: view_all_shifts(nextPriorMondayDate.strftime('%Y-%m-%d')),
            '3': lambda: view_my_shifts_caller(priorMondayDateStr, empID),
            '4': lambda: view_time_off_caller(priorMondayDateStr),
            'm': lambda: message_manager_caller(priorMondayDateStr),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing all employee shifts")
    print("1 | <- Previous Week")
    print("2 | -> Next Week")
    print("3 | My Shifts                    | View in detial and edit your upcoming shifts")
    print("4 | Time off                     | To see your upcoming time off requests and status")
    print("m | Message a manager            | For any questions or other requests!")
    print("b | Back")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    return



#------------MY SHIFTS MENU UI (display options available)----------------
def view_my_shifts_UI(priorMondayDateStr, empID):
    priorMondayDate = datetime.strptime(priorMondayDateStr, '%Y-%m-%d') # str to date, to add time on
    lastPriorMondayDate = priorMondayDate - timedelta(days=7)   # for view_all_prev_week
    nextPriorMondayDate = priorMondayDate + timedelta(days=7)   # for view_all_next_week
    
    priorMondayDateStr = priorMondayDate.strftime('%Y-%m-%d')

    # handle the menu options
    def menu_option(inputChoice):
        switcher = {
            '1': lambda: view_my_shifts(lastPriorMondayDate.strftime('%Y-%m-%d'), empID), # bypassing caller as empID is known
            '2': lambda: view_my_shifts(nextPriorMondayDate.strftime('%Y-%m-%d'), empID), # bypassing caller as empID is known
            '3': lambda: view_all_shifts(priorMondayDateStr),
            '4': lambda: view_time_off_caller(priorMondayDateStr),
            'm': lambda: message_manager_caller(priorMondayDateStr),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing my shifts")
    print("1 | <- Previous Week")
    print("2 | -> Next Week") # add earliest shift but for this employee only
    print("3 | All Shifts                   | View shifts for all employees for the upcoming week")
    print("4 | Time off                     | To see your upcoming time off requests and status")
    print("m | Message a manager            | For any questions or other requests!")
    print("b | Back")
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
            'm': lambda: message_manager_caller(priorMondayDateStr),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing my time off")
    print("1 | Request New Time Off         | Submit a new request for time off with \'status\' pending manager approval")
    print("m | Message a manager            | For any questions or other requests!")
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
            '3': lambda: update_time_off_status(priorMondayDateStr, mngrID, listType),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing all time off")
    if listType == 'all':
        print("1 | All Time off         [Here!] | Recall this table to view it with/without an end date")
        print("2 | Pending Time off             | To see only future time off with status \'Pending\'")
    elif listType == 'pending':
        print("1 | All Time off                 | To see your upcoming time off requests and status")
        print("2 | Pending Time off     [Here!] | Recall this table to view it with/without an end date")
    print("3 | Appove/Deny a Request")
    print("b | Back")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    return



main_UI()