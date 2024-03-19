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
            # print("Leaving view_all_shifts")
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
    # print("Leaving view_all_shifts")
    return





#------------PERSONAL SHIFTS FUNCTION CALLER (call view_my_shifts after asking for who to search for)----------------
def view_my_shifts_caller(priorMondayDateStr, inputID=0):
    MENU_HISTORY.append((view_my_shifts_caller, priorMondayDateStr, inputID))
    inputID = input("Employee ID: ")
    if (inputID == 'q'):
        quit()
    elif (inputID == 'b'):
        back()
    view_my_shifts(priorMondayDateStr, inputID)
    # print("Leaving view_my_shifts_caller")
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
            # print("Leaving view_my_shifts")
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
    # print("Leaving view_my_shifts")
    return






#------------TIME OFF FUNCTION CALLER (call view_time_off after asking for who to search for and validating managers)----------------
def view_time_off_caller(priorMondayDateStr, listType='all', empID=None):    # 'all' or 'pending'
    # if no ID passed in, ask for one
    if empID:
        inputID = empID
    else:
        inputID = input("Employee ID: ")
        if (inputID == 'q'):
            quit()
        elif (inputID == 'b'):
            back()
            
    
    # check if the PASSED IN ID is a manager
    if is_manager(empID):   # if the PASSED IN ID is a manager, they've already typed password, thus skip next
        inputLastStartDate = input("End Date (blank for no date cap)\n[YYYY-MM-DD]: ")
        view_all_time_off(priorMondayDateStr, inputID, listType, inputLastStartDate)
        # print("Leaving view_time_off_caller")
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
    
    # print("Leaving view_time_off_caller")
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

    # print("Leaving view_all_time_off")
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
    # print("Leaving view_my_time_off")
    return

#------------REQUEST NEW TIME OFF (Employee)----------------
def request_new_time_off(priorMondayDateStr, empID):
    MENU_HISTORY.append((request_new_time_off, priorMondayDateStr, empID))
    inputStartDate  = input("Time Off Start Date [YYYY-MM-DD]: ")
    inputEndDate    = input("Time Off End Date   [YYYY-MM-DD]: ")
    inputReason     = input("Reason (optional): ")

    if (inputStartDate == 'q' or inputEndDate == 'q' or inputReason == 'q'):
        quit()
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
    # print("Leaving request_new_time_off")
    return
    
#------------UPDATE A TIME OFF (Manager)----------------
def update_time_off_status(priorMondayDateStr, mngrID, listType):
    MENU_HISTORY.append((update_time_off_status, priorMondayDateStr, mngrID, listType))
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
    view_all_time_off_UI(priorMondayDateStr, mngrID, listType)    # listType is 'all' or 'pending'
    # print("Leaving update_time_off_status")
    return




#------------Message a manager       CALLER (checks if worker or manager, ----------------
def message_manager_caller(priorMondayDateStr):
    inputID = input("Employee ID: ")
    if (inputID == 'q'):
        quit()
    elif (inputID == 'b'):
        back()

    # check if the INPUT ID is a manager
    if is_manager(inputID):
        # open db for password check
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

    # if password correct or a non-manager
    message_manager(priorMondayDateStr, inputID)   # if manager, inputID (self) will be a manager
    # print("Leaving message_manager_caller")
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
            print("mngr",tableMngrID, mngrID)
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
            print("emp",tableEmpID, empID)
            if str(tableEmpID) == empID: # grab only messages for this worker
                empName = get_employeeName(tableEmpID, cursor)
                print("empName",empName)

                # add row to messageTable
                messageTable.add_row([messageID, empName, timestamp, messageBody])
        print(messageTable)      
    else:
        print("err: employeeID invalid?")
        return
    

    # prompt to send a reply  
    inputRecipient = ""
    inputMessage = ""
    print("Send Reply,  or \'q\' to quit") # outside loop so all others can prompt for undo message send
    if manager: inputRecipient = input("Send to employeeID: ")
    elif not manager: inputRecipient = input("Send to managerID: ")
    while inputRecipient != 'q' and inputMessage != 'q':

        # below are now above and at bottom of loop to handle the 'undo' case
        # inputRecipient = input("Message to empID: ")
        # if inputRecipient  == 'q': continue
        
        inputMessage   = input("Message: ")
        if inputRecipient  == 'q': continue

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
        print("\nSend Another Message,  or \'q\' to quit,  or \'u\' to unsend last message")

        if manager: inputRecipient = input("Send to employeeID: ")
        elif not manager: inputRecipient = input("Send to managerID: ")
        if inputRecipient  == 'u':  # 'undo' last message sent by deleting
            cursor.execute("DELETE FROM messages WHERE messageID = ?", (lastMessageID,))
            connection.commit()
            print("Message Unsent")
            print("\nSend Another Message,  or \'q\' to quit")
            inputRecipient = input("Send to ID: ")
        if (inputRecipient == 'q'):
            quit()
        elif (inputRecipient == 'b'):
            back()
            return
            
    connection.close()

    main_UI()
    # print("Leaving message_manager")
    return

#------------GO BACK (to previous screen(s))----------------
def back():
    global MENU_HISTORY
    if len(MENU_HISTORY) > 1:  # Ensure there's at least one previous state to go back to
        print("\n\tGoing back...\n\n")
        MENU_HISTORY.pop()  # Remove the current state
        last_call = MENU_HISTORY[-1]  # Look at the last item in the history without removing it
        
        function, *args = last_call  # Unpack the function and its arguments
        function(*args)  # Execute the function with its arguments
    else:
        print("No previous menu to return to.")


#------------QUIT PROGRAM----------------
def quit_program():
    global MENU_HISTORY
    MENU_HISTORY = [main_UI]
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
    lastWeek = today - timedelta(days=7)    # manual adjustment for debug
    nextWeek = today + timedelta(days=7)    # manual adjustment for debug
    nextNextWeek = today + timedelta(days=7)# manual adjustment for debug
    today = nextWeek                        # manual adjustment for debug
    nextWeek = nextNextWeek                 # manual adjustment for debug
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
            'm': lambda: message_manager_caller(priorMondayDateStr),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Schedule Viewer 9000")
    print("1 | All Shifts                   | View shifts for all employees for the upcoming week")
    print("2 | My Shifts                    | View in detial and edit your upcoming shifts")
    print("3 | Time off                     | To see your upcoming time off requests and status")
    print("m | Message a manager            | For any questions or other requests!")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    # print("Leaving main_UI")
    return


#------------ALL SHIFTS - PREV WEEK - MENU UI (view all shifts for the previous relative week)----------------
def view_all_prev_week():

    return 0



#------------ALL SHIFTS - NEXT WEEK - MENU UI (view all shifts for the next relative week)----------------
def view_all_next_week():

    return 0



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
            'q': lambda: quit_program
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing all employee shifts")
    print("1 | <- Previous Week")
    print("2 | -> Next Week")
    print("3 | My Shifts                    | View in detial and edit your upcoming shifts")
    print("4 | Time off                     | To see your upcoming time off requests and status")
    print("m | Message a manager            | For any questions or other requests!")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    # print("Leaving view_all_shifts_UI")
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
            'q': lambda: quit_program
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing my shifts")
    print("1 | <- Previous Week")
    print("2 | -> Next Week [WIP]") # add earliest shift but for this employee only
    print("3 | All Shifts                   | View shifts for all employees for the upcoming week")
    print("4 | Time off                     | To see your upcoming time off requests and status")
    print("m | Message a manager            | For any questions or other requests!")
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    # print("Leaving view_my_shifts_UI")
    return


#------------EDIT MY SHIFT MENU UI (display options available)----------------

#------------SWITCH SHIFTS MENU UI (display options available)----------------

#------------TIME OFF MENU UI EMPLOYEE (display options available)----------------
def view_my_time_off_UI(priorMondayDateStr, empID):
    # handle the menu options
    def menu_option(inputChoice):
        switcher = {
            '0': lambda: main_UI(),
            '1': lambda: request_new_time_off(priorMondayDateStr, empID),
            'm': lambda: message_manager_caller(priorMondayDateStr),
            'b': lambda: back(),
            'q': lambda: quit_program()
        }
        # get function from switcher dict
        return switcher.get(inputChoice, default)()

    print("Viewing my time off")
    print("0 | Home                         | Temp while I get back() working")
    print("1 | Request New Time Off         | Submit a new request for time off with \'status\' pending manager approval")
    print("m | Message a manager            | For any questions or other requests!")
    print("b | Back")
    print("q | Quit")  
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    # print("Leaving view_my_time_off_UI")
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
    print("b | Back [WIP]")
    print("q | Quit")
    inputChoice = input("Input: ")
    print("")

    menu_option(inputChoice)
    # print("Leaving view_all_time_off_UI")
    return



main_UI()