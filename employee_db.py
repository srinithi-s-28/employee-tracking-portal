employees = []

def add_employee(emp):
    employees.append(emp)

def delete_employee(emp_name):
    global employees
    employees = [emp for emp in employees if emp['name'] != emp_name]

def get_employees():
    return employees

