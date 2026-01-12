import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from pymongo import MongoClient

# MongoDB Setup - change URI and DB/Collection names as needed
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["employee_management"]
employees_col = db["employees"]
attendance_col = db["attendance"]

# Hardcoded credentials (for demo)
VALID_USERNAME = "srinithi"
VALID_PASSWORD = "srinithi249"

# Global variables
employees = []

def load_employees():
    employees.clear()
    tree.delete(*tree.get_children())
    for emp in employees_col.find():
        emp_record = {
            "name": emp.get("name", ""),
            "role": emp.get("role", ""),
            "phone": emp.get("phone", ""),
            "gender": emp.get("gender", ""),
            "salary": emp.get("salary", "")
        }
        employees.append(emp_record)
        tree.insert("", tk.END, values=(emp_record["name"], emp_record["role"], emp_record["phone"], emp_record["gender"], emp_record["salary"]))

def save_employee_to_db(emp):
    # Check if employee already exists (by name+phone for uniqueness)
    existing = employees_col.find_one({"name": emp["name"], "phone": emp["phone"]})
    if existing:
        # Update existing
        employees_col.update_one({"_id": existing["_id"]}, {"$set": emp})
    else:
        # Insert new
        employees_col.insert_one(emp)

def delete_employee_from_db(emp):
    employees_col.delete_one({"name": emp["name"], "role": emp["role"], "phone": emp["phone"], "gender": emp["gender"], "salary": emp["salary"]})

def add_employee():
    emp = {
        "name": name_var.get().strip(),
        "role": role_var.get(),
        "phone": phone_var.get().strip(),
        "gender": gender_var.get(),
        "salary": salary_var.get().strip()
    }
    if not emp["name"] or not emp["role"]:
        messagebox.showwarning("Input Error", "Name and Role are required.")
        return
    employees.append(emp)
    tree.insert("", tk.END, values=(emp["name"], emp["role"], emp["phone"], emp["gender"], emp["salary"]))
    save_employee_to_db(emp)
    clear_fields()

def delete_employee():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select an employee to delete.")
        return
    for sel in selected:
        values = tree.item(sel)["values"]
        tree.delete(sel)
        # Remove from employees list
        employees[:] = [e for e in employees if list(e.values()) != list(values)]
        # Delete from DB
        emp_dict = {
            "name": values[0],
            "role": values[1],
            "phone": values[2],
            "gender": values[3],
            "salary": values[4]
        }
        delete_employee_from_db(emp_dict)
    clear_fields()

def update_employee():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select an employee to update.")
        return
    values = tree.item(selected[0])["values"]
    for emp in employees:
        if list(emp.values()) == list(values):
            emp["name"] = name_var.get().strip()
            emp["role"] = role_var.get()
            emp["phone"] = phone_var.get().strip()
            emp["gender"] = gender_var.get()
            emp["salary"] = salary_var.get().strip()
            break
    tree.item(selected[0], values=(name_var.get(), role_var.get(), phone_var.get(), gender_var.get(), salary_var.get()))
    save_employee_to_db(emp)
    clear_fields()

def search_employees():
    query = search_var.get().strip().lower()
    tree.delete(*tree.get_children())
    for emp in employees:
        if query in emp["name"].lower() or query in emp["role"].lower():
            tree.insert("", tk.END, values=(emp["name"], emp["role"], emp["phone"], emp["gender"], emp["salary"]))

def clear_fields():
    name_var.set("")
    role_var.set(role_dropdown['values'][0])
    phone_var.set("")
    gender_var.set(gender_dropdown['values'][0])
    salary_var.set("")

def on_select(event):
    selected = tree.selection()
    if selected:
        values = tree.item(selected[0])["values"]
        name_var.set(values[0])
        role_var.set(values[1])
        phone_var.set(values[2])
        gender_var.set(values[3])
        salary_var.set(values[4])

# === Attendance Functions ===

def open_attendance_window():
    if not employees:
        messagebox.showwarning("No Employees", "No employees available to mark attendance.")
        return

    att_win = tk.Toplevel(root)
    att_win.title("🗓️ Mark Attendance - " + datetime.date.today().strftime("%Y-%m-%d"))
    att_win.geometry("600x600")

    canvas = tk.Canvas(att_win)
    scrollbar = ttk.Scrollbar(att_win, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    tk.Label(scrollable_frame, text="Mark Attendance for each employee:", font=("Helvetica", 14, "bold")).pack(pady=10)

    attendance_vars = {}

    for idx, emp in enumerate(employees):
        frame = ttk.Frame(scrollable_frame)
        frame.pack(fill="x", pady=5, padx=10)

        name_label = ttk.Label(frame, text=emp["name"], width=25)
        name_label.pack(side="left")

        var = tk.StringVar(value="Present")
        attendance_vars[emp["name"]] = var

        present_rb = ttk.Radiobutton(frame, text="Present", variable=var, value="Present")
        present_rb.pack(side="left", padx=10)

        absent_rb = ttk.Radiobutton(frame, text="Absent", variable=var, value="Absent")
        absent_rb.pack(side="left", padx=10)

    def save_attendance():
        date_str = datetime.date.today().strftime("%Y-%m-%d")

        # Save attendance records to MongoDB (one document per employee per date)
        for name, status_var in attendance_vars.items():
            attendance_col.update_one(
                {"name": name, "date": date_str},
                {"$set": {"status": status_var.get()}},
                upsert=True
            )

        # Save summary
        present_count = sum(1 for v in attendance_vars.values() if v.get() == "Present")
        absent_count = sum(1 for v in attendance_vars.values() if v.get() == "Absent")

        attendance_summary = {
            "date": date_str,
            "present": present_count,
            "absent": absent_count,
            "total_employees": len(employees),
            "timestamp": datetime.datetime.now()
        }
        db.attendance_summary.update_one(
            {"date": date_str},
            {"$set": attendance_summary},
            upsert=True
        )

        messagebox.showinfo("Saved", f"Attendance saved for {date_str}")
        att_win.destroy()

    ttk.Button(att_win, text="💾 Save Attendance", command=save_attendance).pack(pady=20)

def show_attendance_summary():
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    summary = db.attendance_summary.find_one({"date": date_str})

    if not summary:
        messagebox.showinfo("No Data", f"No attendance data found for {date_str}. Please mark attendance first.")
        return

    summary_msg = (f"Attendance Summary for {date_str}:\n\n"
                   f"Present: {summary.get('present', 0)}\n"
                   f"Absent: {summary.get('absent', 0)}\n"
                   f"Total Employees: {summary.get('total_employees', 0)}")
    messagebox.showinfo("📊 Attendance Summary", summary_msg)

# === Main Application Window ===

def open_main_window():
    global root, name_var, role_var, phone_var, gender_var, salary_var, search_var, tree, role_dropdown, gender_dropdown, list_frame

    root = tk.Tk()
    root.title(" 👤Employee Tracking Portal")
    root.geometry("1000x650")
    root.configure(bg="#f5f5f5")

    tk.Label(root, text="👤Employee Tracking Portal", font=("Helvetica", 24, "bold"), bg="#f5f5f5", fg="#333").pack(pady=20)

    form_title = tk.Label(root, text="📝 Employee Form", font=("Helvetica", 16, "bold"), bg="#f5f5f5", anchor="w")
    form_title.pack(fill="x", padx=20)

    form_frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20, bd=1, relief=tk.SOLID)
    form_frame.pack(padx=20, pady=10, fill="x")

    button_frame = tk.Frame(root, bg="#f5f5f5")
    button_frame.pack(pady=10, fill="x")

    table_title = tk.Label(root, text="📋 Employee List", font=("Helvetica", 16, "bold"), bg="#f5f5f5", anchor="w")
    table_title.pack(fill="x", padx=20)
    table_frame = tk.Frame(root)
    table_frame.pack(padx=20, pady=10, fill="both", expand=True)

    # Variables
    name_var = tk.StringVar()
    role_var = tk.StringVar()
    phone_var = tk.StringVar()
    gender_var = tk.StringVar()
    salary_var = tk.StringVar()
    search_var = tk.StringVar()

    # Form Labels and Entries
    tk.Label(form_frame, text="Name:", font=("Helvetica", 12), bg="#ffffff").grid(row=0, column=0, sticky="w", pady=8)
    tk.Entry(form_frame, textvariable=name_var, font=("Helvetica", 11), width=30).grid(row=0, column=1, pady=8, sticky="w")

    tk.Label(form_frame, text="Role:", font=("Helvetica", 12), bg="#ffffff").grid(row=1, column=0, sticky="w", pady=8)
    role_options = [
        " ","Software Engineer", "Senior Software Engineer", "QA Engineer", "HR",
        "Manager", "Team Lead", "Product Owner", "Designer", "Intern", "Other"
    ]
    role_dropdown = ttk.Combobox(form_frame, textvariable=role_var, values=role_options, state="readonly", width=28)
    role_dropdown.grid(row=1, column=1, pady=8, sticky="w")
    role_dropdown.current(0)

    tk.Label(form_frame, text="Phone:", font=("Helvetica", 12), bg="#ffffff").grid(row=2, column=0, sticky="w", pady=8)
    tk.Entry(form_frame, textvariable=phone_var, font=("Helvetica", 10), width=30).grid(row=2, column=1, pady=8, sticky="w")

    tk.Label(form_frame, text="Gender:", font=("Helvetica", 12), bg="#ffffff").grid(row=3, column=0, sticky="w", pady=8)
    gender_options = [" ","Male", "Female", "Other"]
    gender_dropdown = ttk.Combobox(form_frame, textvariable=gender_var, values=gender_options, state="readonly", width=28)
    gender_dropdown.grid(row=3, column=1, pady=8, sticky="w")
    gender_dropdown.current(0)

    tk.Label(form_frame, text="Salary:", font=("Helvetica", 12), bg="#ffffff").grid(row=4, column=0, sticky="w", pady=8)
    tk.Entry(form_frame, textvariable=salary_var, font=("Helvetica", 10), width=30).grid(row=4, column=1, pady=8, sticky="w")
    # Search Bar
    tk.Label(form_frame, text="🔍 Search:", font=("Helvetica", 12), bg="#ffffff").grid(row=5, column=0, sticky="w", pady=8)
    search_entry = ttk.Entry(form_frame, textvariable=search_var, width=32)
    search_entry.grid(row=5, column=1, pady=8, sticky="w")
    tk.Button(form_frame, text="Search", command=search_employees).grid(row=5, column=2, padx=10, pady=8)

    # Buttons
    tk.Button(button_frame, text="➕ Add", bg="#4CAF50", fg="white", font=("Helvetica", 12), width=12, command=add_employee).grid(row=0, column=0, padx=10)
    tk.Button(button_frame, text="✏️ Update", bg="#2196F3", fg="white", font=("Helvetica", 12), width=12, command=update_employee).grid(row=0, column=1, padx=10)
    tk.Button(button_frame, text="🗑️ Delete", bg="#f44336", fg="white", font=("Helvetica", 12), width=12, command=delete_employee).grid(row=0, column=2, padx=10)
    tk.Button(button_frame, text="📅 Mark Attendance", bg="#9C27B0", fg="white", font=("Helvetica", 12), width=16, command=open_attendance_window).grid(row=0, column=3, padx=10)
    tk.Button(button_frame, text="📊 Show Summary", bg="#FF9800", fg="white", font=("Helvetica", 12), width=16, command=show_attendance_summary).grid(row=0, column=4, padx=10)
    


    # Employee Table (TreeView)
    columns = ("Name", "Role", "Phone", "Gender", "Salary")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor="center")
    tree.pack(fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", on_select)

    load_employees()
    root.mainloop()

# === Login Window ===

def open_login_window():
    login_win = tk.Tk()
    login_win.title("Login - Employee Tracking Portal")
    login_win.geometry("400x300")
    login_win.configure(bg="#f5f5f5")

    tk.Label(login_win, text="🔐 Login", font=("Helvetica", 20, "bold"), bg="#f5f5f5").pack(pady=30)

    tk.Label(login_win, text="Username:", font=("Helvetica", 14), bg="#6edeef").pack(pady=5)
    username_entry = ttk.Entry(login_win, font=("Helvetica", 10))
    username_entry.pack(pady=5)

    tk.Label(login_win, text="Password:", font=("Helvetica", 14), bg="#6ee9f2").pack(pady=5)
    password_entry = ttk.Entry(login_win, show="*", font=("Helvetica", 10))
    password_entry.pack(pady=5)

    def attempt_login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            messagebox.showinfo("Login Success", "Welcome to Employee Tracking Portal!")
            login_win.destroy()
            open_main_window()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    login_btn = ttk.Button(login_win, text="Login", command=attempt_login)
    login_btn.pack(pady=20)

    login_win.mainloop()

if __name__ == "__main__":
    open_login_window()



