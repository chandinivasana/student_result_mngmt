import sqlite3
import os
import getpass # For hiding password input

DATABASE_NAME = "student_results.db"

# --- User Data (for basic login - NOT SECURE FOR PRODUCTION) ---
ADMIN_CREDENTIALS = {"admin": "admin123"}
CURRENT_USER_ROLE = None # 'admin', 'student'
CURRENT_USER_ID = None   # student_id if role is 'student'

# --- Database Initialization ---
def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        class_section TEXT,
        password_hash TEXT -- For student login (store HASHED password in real app)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Subjects (
        subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT NOT NULL UNIQUE,
        max_marks INTEGER DEFAULT 100
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Marks (
        mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject_id INTEGER,
        marks_obtained INTEGER,
        FOREIGN KEY (student_id) REFERENCES Students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
        UNIQUE(student_id, subject_id)
    )''')
    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' initialized/checked successfully.")


# --- Login Functions ---
def login():
    global CURRENT_USER_ROLE, CURRENT_USER_ID
    print("\n--- Login ---")
    print("1. Admin Login")
    print("2. Student Login")
    choice = input("Choose login type (1-2): ").strip()

    if choice == '1':
        username = input("Admin Username: ").strip()
        password = getpass.getpass("Admin Password: ") # Hides input
        if ADMIN_CREDENTIALS.get(username) == password:
            CURRENT_USER_ROLE = "admin"
            CURRENT_USER_ID = None
            print("Admin login successful!")
            return True
        else:
            print("Invalid admin credentials.")
            return False
    elif choice == '2':
        try:
            student_id_str = input("Enter Student ID: ").strip()
            if not student_id_str.isdigit():
                print("Student ID must be a number.")
                return False
            student_id = int(student_id_str)
            
            student_data = get_student_by_id(student_id)
            if student_data:
                stored_password_hash = student_data[4] # Assuming password_hash is at index 4
                
                if stored_password_hash: 
                    password_attempt = getpass.getpass(f"Password for {student_data[1]} {student_data[2]}: ")
                    # In a real app: hash password_attempt and compare with stored_password_hash
                    if password_attempt == stored_password_hash: # Direct compare for demo
                        CURRENT_USER_ROLE = "student"
                        CURRENT_USER_ID = student_id
                        print(f"Student login successful! Welcome {student_data[1]}.")
                        return True
                    else:
                        print("Invalid password for student.")
                        return False
                else: 
                    print(f"No password set for student {student_id}. Logging in by ID (demo feature).")
                    CURRENT_USER_ROLE = "student"
                    CURRENT_USER_ID = student_id
                    return True 
            else:
                print(f"Student with ID {student_id} not found.")
                return False
        except ValueError:
            print("Invalid Student ID format. Please enter a number.")
            return False
    else:
        print("Invalid login choice.")
        return False

def logout():
    global CURRENT_USER_ROLE, CURRENT_USER_ID
    CURRENT_USER_ROLE = None
    CURRENT_USER_ID = None
    print("Logged out successfully.")

# --- Student Management Functions ---
def add_student(first_name, last_name, class_section, password=None):
    password_to_store = password # HASH THIS IN PRODUCTION!
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Students (first_name, last_name, class_section, password_hash) VALUES (?, ?, ?, ?)",
                       (first_name, last_name, class_section, password_to_store))
        conn.commit()
        student_id = cursor.lastrowid
        print(f"Student '{first_name} {last_name}' added successfully with ID: {student_id}.")
        return student_id
    except sqlite3.Error as e:
        print(f"Error adding student: {e}")
        return None
    finally:
        conn.close()

def view_all_students():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, first_name, last_name, class_section FROM Students ORDER BY student_id")
    students = cursor.fetchall()
    conn.close()
    if not students: print("No students found."); return []
    print("\n--- All Students ---")
    print("ID | First Name | Last Name  | Class/Section")
    print("---|------------|------------|---------------")
    for student in students:
        print(f"{student[0]:<3}| {student[1]:<10} | {student[2]:<10} | {student[3]}")
    print("-------------------------------------------")
    return students

def get_student_by_id(student_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, first_name, last_name, class_section, password_hash FROM Students WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()
    return student

def view_student_profile(student_id_to_view):
    student_data = get_student_by_id(student_id_to_view)
    if not student_data: print(f"Student with ID {student_id_to_view} not found."); return
    print(f"\n--- Student Profile: {student_data[1]} {student_data[2]} ---")
    print(f"Student ID:      {student_data[0]}")
    print(f"Name:            {student_data[1]} {student_data[2]}")
    print(f"Class/Section:   {student_data[3]}")
    print("\n--- Academic Record ---")
    view_student_marks(student_id_to_view, print_header=False)

def update_student_details(student_id_to_update):
    if CURRENT_USER_ROLE != "admin": print("Access Denied."); return
    student = get_student_by_id(student_id_to_update)
    if not student: print(f"Student with ID {student_id_to_update} not found."); return

    print(f"\nUpdating details for Student ID: {student[0]} - {student[1]} {student[2]}")
    new_first_name = input(f"New first name (current: {student[1]}, Enter to keep): ").strip() or student[1]
    new_last_name = input(f"New last name (current: {student[2]}, Enter to keep): ").strip() or student[2]
    new_class_section = input(f"New class/section (current: {student[3]}, Enter to keep): ").strip() or student[3]
    new_password = getpass.getpass(f"New password (Enter to keep current or leave blank): ").strip()
    password_to_update = student[4] if not new_password else new_password # HASH new_password!

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE Students SET first_name = ?, last_name = ?, class_section = ?, password_hash = ?
            WHERE student_id = ? ''',
            (new_first_name, new_last_name, new_class_section, password_to_update, student_id_to_update))
        conn.commit()
        if cursor.rowcount > 0: print("Student details updated successfully.")
        else: print("No changes made or student not found.")
    except sqlite3.Error as e: print(f"Error updating student details: {e}")
    finally: conn.close()

def delete_student(student_id_to_delete):
    if CURRENT_USER_ROLE != "admin": print("Access Denied."); return
    student = get_student_by_id(student_id_to_delete)
    if not student: print(f"Student with ID {student_id_to_delete} not found."); return

    confirm = input(f"Delete {student[1]} {student[2]} (ID: {student_id_to_delete})? (yes/no): ").lower()
    if confirm == 'yes':
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Students WHERE student_id = ?", (student_id_to_delete,))
            conn.commit()
            if cursor.rowcount > 0: print(f"Student ID {student_id_to_delete} deleted.")
            else: print("Student not found or already deleted.")
        except sqlite3.Error as e: print(f"Error deleting student: {e}")
        finally: conn.close()
    else: print("Deletion cancelled.")

# --- Subject Management Functions ---
def add_subject(subject_name, max_marks=100):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Subjects (subject_name, max_marks) VALUES (?, ?)", (subject_name, max_marks))
        conn.commit()
        print(f"Subject '{subject_name}' added with ID: {cursor.lastrowid}.")
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Error: Subject '{subject_name}' already exists.")
        cursor.execute("SELECT subject_id FROM Subjects WHERE subject_name = ?", (subject_name,))
        return cursor.fetchone()[0] if cursor.fetchone() else None
    except sqlite3.Error as e: print(f"Error adding subject: {e}"); return None
    finally: conn.close()

def view_all_subjects():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT subject_id, subject_name, max_marks FROM Subjects ORDER BY subject_id")
    subjects = cursor.fetchall()
    conn.close()
    if not subjects: print("No subjects found."); return []
    print("\n--- All Subjects ---")
    print("ID | Subject Name     | Max Marks")
    print("---|------------------|-----------")
    for sub in subjects: print(f"{sub[0]:<3}| {sub[1]:<16} | {sub[2]}")
    print("---------------------------------")
    return subjects

def get_subject_by_id(subject_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT subject_id, subject_name, max_marks FROM Subjects WHERE subject_id = ?", (subject_id,))
    subject = cursor.fetchone()
    conn.close()
    return subject

# --- Marks Management Functions ---
def add_marks(student_id, subject_id, marks_obtained):
    if CURRENT_USER_ROLE != "admin": print("Access Denied."); return None
    if get_student_by_id(student_id) is None: print(f"Error: Student ID {student_id} not found."); return None
    sub_details = get_subject_by_id(subject_id)
    if sub_details is None: print(f"Error: Subject ID {subject_id} not found."); return None
    max_m = sub_details[2]
    if not (0 <= marks_obtained <= max_m): print(f"Error: Marks ({marks_obtained}) must be 0-{max_m}."); return None

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO Marks (student_id, subject_id, marks_obtained) VALUES (?, ?, ?)",
                       (student_id, subject_id, marks_obtained))
        conn.commit()
        print(f"Marks {marks_obtained} for student {student_id}, subject {subject_id} recorded.")
        return cursor.lastrowid 
    except sqlite3.Error as e: print(f"Error adding/replacing marks: {e}"); return None
    finally: conn.close()

def view_student_marks(student_id, print_header=True):
    student = get_student_by_id(student_id)
    if not student:
        if print_header: print(f"Student with ID {student_id} not found.")
        return None, 0, 0

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.subject_name, m.marks_obtained, s.max_marks
        FROM Marks m JOIN Subjects s ON m.subject_id = s.subject_id
        WHERE m.student_id = ? ''', (student_id,))
    marks_data = cursor.fetchall()
    conn.close()

    if not marks_data:
        if print_header: print(f"No marks found for {student[1]} {student[2]} (ID: {student_id}).")
        return [], 0, 0

    if print_header:
        print(f"\n--- Marksheet for {student[1]} {student[2]} (ID: {student_id}, Class: {student[3]}) ---")
        print("Subject          | Marks Obtained | Max Marks")
        print("-----------------|----------------|-----------")

    total_obtained, total_max_marks = 0, 0
    for row in marks_data:
        if print_header: print(f"{row[0]:<16} | {row[1]:<14} | {row[2]}")
        total_obtained += row[1] if row[1] is not None else 0
        total_max_marks += row[2] if row[2] is not None else 0
    
    percentage = 0
    if print_header:
        print("-----------------|----------------|-----------")
        print(f"{'Total:':<16} | {total_obtained:<14} | {total_max_marks}")
        if total_max_marks > 0:
            percentage = (total_obtained / total_max_marks) * 100
            print(f"Percentage: {percentage:.2f}%")
        else: print("Percentage: N/A")
        print("-------------------------------------------")
    elif total_max_marks > 0: # Calculate percentage even if not printing header
        percentage = (total_obtained / total_max_marks) * 100
        
    return marks_data, total_obtained, percentage

# --- Reporting and Ranking Functions ---
def get_student_performance_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT st.student_id, st.first_name, st.last_name, st.class_section,
               COALESCE(SUM(m.marks_obtained), 0) as total_obtained,
               COALESCE(SUM(su.max_marks), 0) as total_max_marks
        FROM Students st
        LEFT JOIN Marks m ON st.student_id = m.student_id
        LEFT JOIN Subjects su ON m.subject_id = su.subject_id
        GROUP BY st.student_id, st.first_name, st.last_name, st.class_section
        ORDER BY st.student_id ''')
    perf_data = []
    for row in cursor.fetchall():
        perc = 0
        total_obt, total_max = row[4] or 0, row[5] or 0
        if total_max > 0: perc = (total_obt / total_max) * 100
        perf_data.append({
            "id": row[0], "first_name": row[1], "last_name": row[2], "class_section": row[3],
            "total_obtained": total_obt, "total_max_marks": total_max, "percentage": round(perc, 2)
        })
    conn.close()
    return perf_data

def rank_students(performance_data_list, sort_key="percentage"):
    if not performance_data_list: print("No performance data to rank."); return []
    ranked_list = sorted(performance_data_list, key=lambda x: x.get(sort_key, 0), reverse=True)
    print(f"\n--- Student Rankings (by {sort_key.replace('_', ' ').title()}) ---")
    print("Rank | ID | Name                | Class | Tot. Obt. | Tot. Max | Percentage")
    print("-----|----|---------------------|-------|-----------|----------|-----------")
    current_rank, last_score = 0, -1
    for i, stud in enumerate(ranked_list):
        score = stud.get(sort_key, 0)
        if score != last_score: current_rank, last_score = i + 1, score
        name = f"{stud['first_name']} {stud['last_name']}"
        print(f"{current_rank:<5}| {stud['id']:<2} | {name:<19} | {stud['class_section']:<5} | "
              f"{stud['total_obtained']:<9} | {stud['total_max_marks']:<8} | {stud['percentage']:.2f}%")
    print("--------------------------------------------------------------------------------")
    return ranked_list

def view_top_n_students(top_n=10, sort_key="percentage"):
    if CURRENT_USER_ROLE != "admin": print("Access Denied."); return
    perf_data = get_student_performance_data()
    if not perf_data: print("No student performance data."); return
    ranked = sorted(perf_data, key=lambda x: x.get(sort_key, 0), reverse=True)
    
    print(f"\n--- Top {top_n} Students (by {sort_key.replace('_', ' ').title()}) ---")
    if not ranked: print("No students to rank."); return
    print("Rank | ID | Name                | Class | Tot. Obt. | Tot. Max | Percentage")
    print("-----|----|---------------------|-------|-----------|----------|-----------")
    curr_rank, last_scr, disp_count = 0, -1, 0
    for i, stud in enumerate(ranked):
        if disp_count >= top_n: break
        score = stud.get(sort_key, 0)
        if score != last_scr: curr_rank, last_scr = i + 1, score
        name = f"{stud['first_name']} {stud['last_name']}"
        print(f"{curr_rank:<5}| {stud['id']:<2} | {name:<19} | {stud['class_section']:<5} | "
              f"{stud['total_obtained']:<9} | {stud['total_max_marks']:<8} | {stud['percentage']:.2f}%")
        disp_count += 1
    print("--------------------------------------------------------------------------------")
    if not disp_count: print(f"No students for top {top_n}.")

def view_failed_list(threshold=40.0):
    if CURRENT_USER_ROLE != "admin": print("Access Denied."); return
    perf_data = get_student_performance_data()
    if not perf_data: print("No student performance data."); return
    failed = [s for s in perf_data if s.get("percentage", 101) < threshold and s.get("total_max_marks",0) > 0]
    if not failed: print(f"No students below {threshold}%."); return

    print(f"\n--- Students Below {threshold}% Overall ---")
    print("ID | Name                | Class | Percentage")
    print("---|---------------------|-------|-----------")
    for stud in sorted(failed, key=lambda x: x.get("percentage", 101)):
        name = f"{stud['first_name']} {stud['last_name']}"
        print(f"{stud['id']:<2} | {name:<19} | {stud['class_section']:<5} | {stud['percentage']:.2f}%")
    print("-------------------------------------------")

# --- Search Functions ---
def search_students():
    if CURRENT_USER_ROLE != "admin": print("Access Denied."); return
    term = input("\nSearch Student (ID or Name part): ").strip().lower()
    if not term: print("Search term empty."); return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    query = """SELECT student_id, first_name, last_name, class_section FROM Students 
               WHERE CAST(student_id AS TEXT) = ? OR LOWER(first_name) LIKE ? OR LOWER(last_name) LIKE ?
               ORDER BY student_id"""
    cursor.execute(query, (term, f"%{term}%", f"%{term}%"))
    results = cursor.fetchall()
    conn.close()

    if not results: print(f"No students match '{term}'."); return
    print("\n--- Student Search Results ---")
    print("ID | First Name | Last Name  | Class/Section")
    print("---|------------|------------|---------------")
    for s in results: print(f"{s[0]:<3}| {s[1]:<10} | {s[2]:<10} | {s[3]}")
    print("-------------------------------------------")

def search_subjects():
    term = input("\nSearch Subject (Name part): ").strip().lower()
    if not term: print("Search term empty."); return
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    query = "SELECT subject_id, subject_name, max_marks FROM Subjects WHERE LOWER(subject_name) LIKE ? ORDER BY subject_id"
    cursor.execute(query, (f"%{term}%",))
    results = cursor.fetchall()
    conn.close()

    if not results: print(f"No subjects match '{term}'."); return
    print("\n--- Subject Search Results ---")
    print("ID | Subject Name     | Max Marks")
    print("---|------------------|-----------")
    for s in results: print(f"{s[0]:<3}| {s[1]:<16} | {s[2]}")
    print("---------------------------------")
# --- Menus ---
def admin_menu():
    while True:
        print("\n╔══════════════════════════════════════════════╗")
        print("║                Admin Dashboard                 ║")
        print("╠══════════════════════════════════════════════╣")
        print("║ Student Management:                          ║")
        print("║   1. Add New Student                         ║")
        print("║   2. View All Students                       ║")
        print("║   3. Update Student Details                  ║")
        print("║   4. Delete Student                          ║")
        print("║   5. View Specific Student Profile           ║")
        print("║   6. Search for Students                     ║")
        print("║----------------------------------------------║")
        print("║ Subject Management:                          ║")
        print("║   7. Add New Subject                         ║")
        print("║   8. View All Subjects                       ║")
        print("║   9. Search for Subjects                     ║")
        print("║----------------------------------------------║")
        print("║ Marks Management:                            ║")
        print("║  10. Add or Update Student Marks             ║")
        print("║  11. View Student Marksheet (by ID)          ║")
        print("║----------------------------------------------║")
        print("║ Reports:                                     ║")
        print("║  12. View Overall Student Rankings           ║")
        print("║  13. View Top N Performing Students          ║")
        print("║  14. View List of Students Below Threshold   ║")
        print("║----------------------------------------------║")
        print("║ System:                                      ║")
        print("║  15. Logout                                  ║")
        print("╚══════════════════════════════════════════════╝")

        choice = input("Admin choice (1-15): ").strip()
        try:
            if choice == '1': # Add Student
                fn = input("Enter student's first name: ").strip()
                ln = input("Enter student's last name: ").strip()
                cs = input("Enter student's class/section: ").strip()
                pwd = getpass.getpass("Set password for the student (optional, press Enter to skip): ").strip()
                if fn and ln and cs: # Ensure essential fields are not empty
                    add_student(fn, ln, cs, pwd if pwd else None)
                else:
                    print("Error: First name, last name, and class/section are required.")
            elif choice == '2': # View All Students
                view_all_students()
            elif choice == '3': # Update Student Details
                stud_id_str = input("Enter Student ID to update: ").strip()
                if stud_id_str.isdigit():
                    update_student_details(int(stud_id_str))
                else:
                    print("Invalid Student ID format.")
            elif choice == '4': # Delete Student
                stud_id_str = input("Enter Student ID to delete: ").strip()
                if stud_id_str.isdigit():
                    delete_student(int(stud_id_str))
                else:
                    print("Invalid Student ID format.")
            elif choice == '5': # View Specific Student Profile
                stud_id_str = input("Enter Student ID to view profile: ").strip()
                if stud_id_str.isdigit():
                    view_student_profile(int(stud_id_str))
                else:
                    print("Invalid Student ID format.")
            elif choice == '6': # Search for Students
                search_students()
            elif choice == '7': # Add New Subject
                sn = input("Enter subject name: ").strip()
                mm_str = input(f"Enter max marks for {sn} (default 100, press Enter for default): ").strip()
                if sn: # Ensure subject name is not empty
                    add_subject(sn, int(mm_str) if mm_str else 100)
                else:
                    print("Error: Subject name cannot be empty.")
            elif choice == '8': # View All Subjects
                view_all_subjects()
            elif choice == '9': # Search for Subjects
                search_subjects()
            elif choice == '10': # Add or Update Student Marks
                stud_id_str = input("Enter Student ID: ").strip()
                subj_id_str = input("Enter Subject ID: ").strip()
                mo_str = input("Enter marks obtained: ").strip()
                if stud_id_str.isdigit() and subj_id_str.isdigit() and mo_str.isdigit():
                    add_marks(int(stud_id_str), int(subj_id_str), int(mo_str))
                else:
                    print("Invalid input for IDs or marks. Please enter numbers.")
            elif choice == '11': # View Student Marksheet
                stud_id_str = input("Enter Student ID to view marksheet: ").strip()
                if stud_id_str.isdigit():
                    view_student_marks(int(stud_id_str))
                else:
                    print("Invalid Student ID format.")
            elif choice == '12': # View Overall Student Rankings
                data = get_student_performance_data()
                if data:
                    rc = input("Rank by (p)ercentage (default) or (t)otal marks? ").lower().strip()
                    rank_students(data, "total_obtained" if rc == 't' else "percentage")
                else:
                    print("No data available to generate rankings.")
            elif choice == '13': # View Top N Performing Students
                top_n_str = input("Enter N for Top N students (default 10): ").strip()
                top_n = int(top_n_str) if top_n_str.isdigit() else 10
                sc = input("Sort Top N by (p)ercentage (default) or (t)otal marks? ").lower().strip()
                view_top_n_students(top_n, "total_obtained" if sc == 't' else "percentage")
            elif choice == '14': # View List of Students Below Threshold
                th_str = input("Enter failing percentage threshold (default 40%): ").strip()
                threshold = float(th_str) if th_str else 40.0 # Add better validation for float
                view_failed_list(threshold)
            elif choice == '15': # Logout
                logout()
                break # Exit the admin menu loop
            else:
                print("Invalid choice. Please enter a number between 1 and 15.")
        except ValueError:
            print("Invalid input type. Please ensure you enter numbers where expected (e.g., for IDs, marks).")
        except Exception as e: # Catch any other unexpected errors during menu operation
            print(f"An unexpected error occurred in the admin menu: {e}")

# ... (The rest of your srms.py code: student_menu, main_application_loop, all other functions, if __name__ == "__main__":)


def student_menu():
    global CURRENT_USER_ID
    if CURRENT_USER_ID is None: print("Error: No student logged in."); return
    stud_data = get_student_by_id(CURRENT_USER_ID)
    if not stud_data: print("Error: Logged in student data not found."); logout(); return
    name = f"{stud_data[1]} {stud_data[2]}"

    while True:
        print(f"\n╔═══ Student Dashboard - {name[:15]:<15}═══╗")
        print(f"║ 1. View My Profile & Marksheet      ║")
        print(f"║ 2. Logout                           ║")
        print(f"╚═════════════════════════════════════╝")
        choice = input(f"{name}, your choice (1-2): ").strip()
        try:
            if choice == '1': view_student_profile(CURRENT_USER_ID)
            elif choice == '2': logout(); break
            else: print("Invalid choice.")
        except Exception as e: print(f"Student menu error: {e}")

def main_application_loop():
    if not os.path.exists(DATABASE_NAME):
        print("Database not found. Initializing..."); initialize_database()
    while True:
        if CURRENT_USER_ROLE is None:
            if not login():
                if input("Login failed. Retry? (y/n): ").lower() != 'y': print("Exiting."); break
                else: continue
        if CURRENT_USER_ROLE == "admin": admin_menu()
        elif CURRENT_USER_ROLE == "student": student_menu()
        if CURRENT_USER_ROLE is None and input("Return to login? (y/n): ").lower() != 'y':
             print("Exiting system."); break


if __name__ == "__main__":
    main_application_loop()