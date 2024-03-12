import os
from datetime import datetime, timedelta
import sqlite3
from prettytable import PrettyTable

import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:5555')
print('\nconnected to server')

# clear data
socket.send_json(['CLEAR ALL DATA'])
print('Received reply [ %s ]' % socket.recv_json())

#------------Employee Create TO----------------
def create_time_off(empID, startDateStr, endDateStr, reason):
    msg = ['C', [empID, startDateStr, endDateStr, reason]]
    socket.send_json(msg)

    # reply
    message = socket.recv_json()

#------------Manager Update TO----------------
def update_time_off(requestID, approvingManager, approvalStatus):

    # get an employee's active time-off requests from microservice
    msg = ['U', [requestID, approvingManager, approvalStatus]]
    socket.send_json(msg)       # through ZeroMQ
    
    # reply
    results = socket.recv_json()


create_time_off(3, '2024-01-02', '2024-01-03', 'reason-Ethan-1')
create_time_off(3, '2024-04-11', '2024-04-14', 'reason-Ethan-2')
create_time_off(1, '2024-04-21', '2024-04-23', 'reason-Brett-1')
create_time_off(3, '2024-04-14', '2024-04-22', 'reason-Ethan-3')
create_time_off(3, '2024-05-11', '2024-06-12', 'deny-this-Ethan-4')
create_time_off(3, '2024-05-11', '2024-05-12', 'reason-Ethan-5')
create_time_off(1, '2024-03-19', '2024-03-19', 'Wedding') #shown in next week
create_time_off(4, '2024-03-28', '2024-03-31', 'Vacay') #shown in next week
create_time_off(3, '2024-06-13', '2024-06-15', 'reason-Ethan-6')
create_time_off(3, '2024-06-17', '2024-06-18', 'reason-Ethan-7')
update_time_off(4, 1, False)
update_time_off(7, 1, True)
update_time_off(8, 1, True)











def view_all_time_off():
    # get an employee's active time-off requests from microservice
    msg = ['M']
    socket.send_json(msg)       # through ZeroMQ
    requests = socket.recv_json()

    # table headers
    table = PrettyTable(["reqID", "empID", "Start Date", "End Date", "Status", "Manager", "Time Off Reason"])
    for request in requests:
        requestID, empID, startDate, endDate, reason, approvingManager, approved = request

        # determine the status based on 'approved' and 'approvingManager'
        if approved:
            status = "Approved"
        elif approvingManager == 0 or approvingManager is None:
            status = "Pending"
        else:
            status = "Denied"
        
        # add row to table
        table.add_row([requestID, empID, startDate, endDate, status, approvingManager, reason])
    
    print(table)

view_all_time_off()