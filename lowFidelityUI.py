import os
from prettytable import PrettyTable

print("\nAll Shifts view")

totalTable = PrettyTable()
totalTable.field_names = ["Employee", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
totalTable.add_row(["Brett Vandenburg", "7am-3pm", "7am-3pm", "7am-3pm", "6am-2pm", "7am-3pm", ".", "."])
totalTable.add_row(["David Thoe", ".", ".", "8am-4pm", "7am-3pm", "8am-4pm", "7am-3pm", "7am-3pm"])
totalTable.add_row(["Adam Marks", ".", ".", "11am-6pm", "11am-6pm", "11am-6pm", "11am-6pm", "11am-6pm"])
totalTable.add_row(["Ethan Shaw", "5pm-9pm", "2pm-9pm", ".", ".", "8am-4pm", "7am-3pm", "7am-3pm"])
print(totalTable)

print("1 : View My Shifts")
print("2 : Edit My Shifts")
print("1 : Time off")
print("q : Quit")
print("Input: ")


print("\nMy Shifts view")

selfTable = PrettyTable()
selfTable.field_names = ["Ethan Shaw", "Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
selfTable.add_rows(
    [
      ["Day in", "5pm", "2pm", ".", ".", "8am", "7am", "7am"],
     ["Day out", "9pm", "9pm", ".", ".", "4pm", "3pm", "3pm"],
        [" 5am", ".", ".", ".", ".", ".", ".", "."],
        [" 6am", ".", ".", ".", ".", ".", ".", "."],
        [" 7am", ".", ".", ".", ".", "#", "#", "#"],
        [" 8am", ".", ".", ".", ".", "#", "#", "#"],
        [" 9am", ".", ".", ".", ".", "#", "#", "#"],
        ["10am", ".", ".", ".", ".", "#", "#", "#"],
        ["11am", ".", ".", ".", ".", "#", "#", "#"],
        ["12pm", ".", ".", ".", ".", "#", "#", "#"],
        [" 1pm", ".", ".", ".", ".", "#", "#", "#"],
        [" 2pm", ".", "#", ".", ".", "#", "#", "#"],
        [" 3pm", ".", "#", ".", ".", "#", "#", "#"],
        [" 4pm", ".", "#", ".", ".", "#", ".", "."],
        [" 5pm", "#", "#", ".", ".", ".", ".", "."],
        [" 6pm", "#", "#", ".", ".", ".", ".", "."],
        [" 7pm", "#", "#", ".", ".", ".", ".", "."],
        [" 8pm", "#", "#", ".", ".", ".", ".", "."],
        [" 9pm", "#", "#", ".", ".", ".", ".", "."],
        ["10pm", "#", "#", ".", ".", ".", ".", "."],
    ])
print(selfTable)

print("1 | View All Shifts")
print("2 | Edit My Shifts")
print("3 | View Time off (+Pending)")
print("4 | Request Time off")
print("m | Message a manager")
print("b | Back")
print("q | Quit")
print("Input: ")


print("\nEdit Shifts Selector")

print("1 | Mon : 5pm-9pm :") 
print("2 | Tue : 2pm-9pm : closing with Kim")
print("3 | Wed : none")
print("4 | Thu : none")
print("5 | Fri : 8pm-4pm : clean machine 7B")
print("6 | Sat : 7pm-3pm :")
print("7 | Sun : 7pm-3pm :")
print("b | Back")
print("q | Quit")
print("Shift # to edit: ")


print("\nEdit Shifts Choice")

print("1 | Edit description (personal note per shift)")
print("2 | Request switch")
print("3 | Call in sick (will message manager)")
print("4 | Request new shift (if any shifts open)")
print("m | Message a manager")
print("b | Back (without saving)")
print("q | Quit (without saving)")


print("\nSwitch Shifts Choice")

print("Your Last Name            :")
print("Switchee Last Name        :")
print("Switchee Shift Day        :")
print("Switchee Shift Start time :")
print("m | Message a manager")
print("b | Back (without saving)")
print("q | Quit (without saving)")


print("\nRequest Time Off")

print("Time Off Start Date  :")
print("Time Off End Date    :")
print("Reason (optional)    :")
print("m | Message a manager")
print("b | Back (without saving)")
print("q | Quit (without saving)")



print("\n[Manager] Time Off Requests This Quarter")

timeOffTable = PrettyTable()
timeOffTable.field_names = ["Num", "Employee", "Start Date", "End Date", "Status"]
timeOffTable.add_rows(
    [
     ["1", "Adam Marks", "1/23/23", "1/23/23", "Pending"],
     ["2", "Ethan Shaw", "2/13/23", "2/15/23", "Approved"],
     ["3", "David Thoe", "2/31/23", "5/01/23", "Denied"],
     ["3", "David Thoe", "2/31/23", "3/01/23", "Pending"],
    ])
print(timeOffTable)
print("Time Off to Approve (\"1,3,4\") : ")
print("Time Off to Deny (\"1,3,4\")    : ")
