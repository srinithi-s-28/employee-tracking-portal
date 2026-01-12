attendance_records = {}

def mark_attendance(emp_name):
    from datetime import datetime
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    attendance_records[emp_name] = time_now
    return time_now

def get_attendance(emp_name):
    return attendance_records.get(emp_name, "Not marked")

def reset_attendance(emp_name):
    attendance_records.pop(emp_name, None)

