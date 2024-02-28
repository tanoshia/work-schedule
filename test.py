import os
from datetime import datetime, timedelta
import sqlite3
from prettytable import PrettyTable

import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:5555')
print('\nconnected to server')


today = datetime.now()
lastWeek = today - timedelta(days=7)
nextWeek = today + timedelta(days=7)
today = nextWeek #TEMP
# calc todays weekday (0=Monday, 1=Tuesday...6=Sunday)
daysToMonday = today.weekday()
priorMondayDate = today - timedelta(days=daysToMonday)
priorMondayDateStr = priorMondayDate.strftime('%Y-%m-%d')

#------------Employee Create TO----------------
def create_time_off(empID, startDateStr, endDateStr, reason):
    msg = ['C', [empID, startDateStr, endDateStr, reason]]
    socket.send_json(msg)
    # reply
    message = socket.recv_json()
    print('Received reply [%s]' % (message))


#------------Employee View TO----------------
def view_my_time_off(startDateStr, empID):

    # get an employee's active time-off requests from microservice
    msg = ['E', empID]
    socket.send_json(msg)       # through ZeroMQ

    requests = socket.recv_json()

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
        
        # add row to table
        table.add_row([startDate, endDate, status, approvingManager, reason])
    
    print(table)



#------------Manager View TO----------------
def view_all_time_off():

    # get an employee's active time-off requests from microservice
    msg = ['M', '2024-05-01']
    socket.send_json(msg)       # through ZeroMQ

    requests = socket.recv_json()
    print("Received requests:", requests)

    # table headers
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
        table.add_row([requestID, empID, startDate, endDate, status, reason])
    
    print(table)
    print(pendingTable)



#------------Manager Update TO----------------
def update_time_off(requestID, approvingManager, approvalStatus):

    # get an employee's active time-off requests from microservice
    msg = ['U', [requestID, approvingManager, approvalStatus]]
    socket.send_json(msg)       # through ZeroMQ

    results = socket.recv_json()
    print('\nUpdate Time Off:')
    print(results)


create_time_off(3, '2024-04-11', '2024-04-14', 'reason-Ethan-1')
create_time_off(1, '2024-04-21', '2024-04-23', 'reason-Brett-1')
create_time_off(3, '2024-04-14', '2024-04-22', 'reason-Ethan-2')
create_time_off(3, '2024-05-11', '2024-06-12', 'reason-Ethan-3-D') #id 3? 4?
create_time_off(3, '2024-05-11', '2024-05-12', 'reason-Ethan-4')
create_time_off(3, '2024-06-13', '2024-06-15', 'reason-Ethan-5')
create_time_off(3, '2024-06-17', '2024-06-18', 'reason-Ethan-6')
print("All TO")
view_all_time_off()
print("MY TO")
view_my_time_off(priorMondayDateStr, 3)

print("\n*\n***********UPDATES***********\n*")
update_time_off(3, 1, False)

print("All TO")
view_all_time_off()
print("MY TO")
view_my_time_off(priorMondayDateStr, 3)









# clear data from table
socket.send_json(['CLEAR ALL DATA'])
print('Received reply [ %s ]' % socket.recv_json())



















# start_date = datetime.strptime('2024-01-22', '%Y-%m-%d') # first day of the week
# startTime = '08:15'
# endTime = '16:00'

# # simplify shift start and end time (e.g. 08:00-16:00 becomes 8am-4pm)
# def simplify_shiftTime(startTimeStr, endTimeStr):
#     # string to datetime
#     startTimeObj = datetime.strptime(startTimeStr, '%H:%M')
#     endTimeObj = datetime.strptime(endTimeStr, '%H:%M')

#     def formatShiftTime(time_str): # 24hr to 12hr, strip leading 0, %I=12hr, %M=mins, %p=am/pm
#         time_obj = datetime.strptime(time_str, '%H:%M')
#         if time_obj.minute == 0:    # if mins are 0, format without minutes
#             return time_obj.strftime('%I%p').lstrip('0').lower()
#         else:                       # if mins not 0, format with minutes
#             return time_obj.strftime('%I:%M%p').lstrip('0').lower()

#     startTimeSimple = formatShiftTime(startTimeStr)
#     endTimeSimple = formatShiftTime(endTimeStr)

#     #return back as string
#     return f"{startTimeSimple}-{endTimeSimple}"

# print(simplify_shiftTime(startTime, endTime))