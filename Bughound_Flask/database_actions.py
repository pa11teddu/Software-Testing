# database_actions.py

import pymysql
from datetime import datetime, timedelta

def authenticate_user_db(db_params, username):
    """
    Fetch a user's level and approval status based on the username.
    Returns the user record if the user exists and None if not.
    This function now focuses on user level and approval status only.
    """
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT userlevel, is_approved FROM employees WHERE username = %s", (username,))
            return cursor.fetchone()  # Returns None if no record is found
    finally:
        connection.close()

def approve_user_db(db_params, user_id):
    """
    Approve a user account by setting is_approved to 1.
    """
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE employees SET is_approved = 1 WHERE emp_id = %s", (user_id,))
            connection.commit()
    finally:
        connection.close()

def toggle_user_approval(db_params, user_id, new_status):
    """
    Toggle a user's approval status in the database.
    """
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE employees SET is_approved = %s WHERE emp_id = %s", (new_status, user_id))
            connection.commit()
    finally:
        connection.close()

def get_assigned_bugs(db_params, user_id):
    connection = pymysql.connect(**db_params)
    username = None
    try:
        # Establish connection and create a cursor
        with connection.cursor() as cursor:
            # Query to fetch the username corresponding to the user_id
            sql_get_username = "SELECT name FROM employees WHERE username = %s"
            cursor.execute(sql_get_username, (user_id,))
            result = cursor.fetchone()
            username = result['name']
            if username:
                sql_get_bugs = "SELECT * FROM bug WHERE assigned_to = %s"
                cursor.execute(sql_get_bugs, (username,))
                return cursor.fetchall()  # Returns a list of dicts representing bugs assigned to the username
            else:
                return []  # Return an empty list if no username is found
    finally:
        connection.close()


def register_employee_db(db_params, emp_name, emp_username, emp_password, emp_level):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO employees (name, username, userlevel, is_approved) VALUES (%s, %s, %s, %s)",
                (emp_name, emp_username, emp_level, "1")
            )
            connection.commit()
            return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        connection.close()

import pymysql

def fetch_programs(db_params):
    """Fetches programs from the database and returns them."""
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT prog_id, program, program_version, program_release FROM programs")
            programs = cursor.fetchall()
            return programs  # This will be a list of tuples or dicts depending on cursor configuration
    finally:
        connection.close()


def check_user_exists(db_params, username):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM employees WHERE username = %s', (username,))
            return cursor.fetchone()
    finally:
        connection.close()

def add_new_user(db_params, employee_name, username, level):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO employees (name, username, userlevel) VALUES (%s, %s, %s, %s)', 
                           (employee_name, username, level))
            connection.commit()
            return True
    except Exception as e:
        print(f"Error occurred: {e}")
        return False
    finally:
        connection.close()

def update_employee_details_db(db_params, details):
    try:
        with pymysql.connect(**db_params) as connection:
            with connection.cursor() as cursor:
                sql_update_query = """
                UPDATE employees 
                SET name=%s, username=%s, userlevel=%s 
                WHERE emp_id=%s
                """
                cursor.execute(sql_update_query, (
                    details['name'], 
                    details['username'], 
                    # details['password'], 
                    details['userlevel'], 
                    details['emp_id']
                ))
                connection.commit()
    except Exception as e:
        print(f"An error occurred: {str(e)}", "error")
        return False

def add_program_db(db_params, program_name, release, version):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            sql_insert = """
            INSERT INTO programs (program, program_release, program_version)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql_insert, (program_name, release, version))
            connection.commit()
    finally:
        connection.close()

def insert_program(db_params, program_name, release, version):
    db_connection = pymysql.connect(**db_params)
    try:
        with db_connection.cursor() as cursor:
            sql_insert = """
                INSERT INTO programs (program, program_release, program_version)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql_insert, (program_name, release, version))
            db_connection.commit()
            return True  # Indicate success
    except Exception as e:
        print(f"An error occurred: {e}")  # Better to use logging in production
        return False  # Indicate failure
    finally:
        db_connection.close()

import pymysql

# Function to execute the update operation for a program
def update_program_db(db_params, prog_id, program, release, version):
    db_connection = pymysql.connect(**db_params)
    try:
        with db_connection.cursor() as cursor:
            update_query = """
                UPDATE programs 
                SET program = %s, program_release = %s, program_version = %s 
                WHERE prog_id = %s
            """
            cursor.execute(update_query, (program, release, version, prog_id))
            db_connection.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db_connection.close()

def delete_employee_db(db_params, emp_id):
    db_connection = pymysql.connect(**db_params)
    try:
        with db_connection.cursor() as cursor:
            sql_query = "DELETE FROM employees WHERE emp_id = %s"
            cursor.execute(sql_query, (emp_id,))
            db_connection.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db_connection.close()

def delete_program_db(db_params, prog_id):
    db_connection = pymysql.connect(**db_params)
    try:
        with db_connection.cursor() as cursor:
            sql_query = "DELETE FROM programs WHERE prog_id = %s"
            cursor.execute(sql_query, (prog_id,))
            db_connection.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db_connection.close()

def add_area_db(db_params, area, prog_id):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            # Check if there are any programs
            cursor.execute("SELECT COUNT(*) FROM programs")
            result = cursor.fetchone()
            if result['COUNT(*)'] == 0:
                message = "Cannot add area - programs table is empty."
            else:
                # Insert new area
                cursor.execute(
                    "INSERT INTO areas (area, prog_id) VALUES (%s, %s)", (area, prog_id)
                )
                connection.commit()
                message = f"Area {area} was successfully added with ID {cursor.lastrowid}."
            return message
    finally:
        connection.close()

def update_area_db(db_params, area_id, area, prog_id):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE areas SET area=%s, prog_id=%s WHERE area_id=%s",
                (area, prog_id, area_id)
            )
            connection.commit()
            message = f"Area {area} was successfully updated."
            return message
    finally:
        connection.close()

def delete_area_db(db_params, area_id):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM areas WHERE area_id=%s", (area_id,))
            connection.commit()
            message = f"Area with id {area_id} was successfully deleted"
            return message
    finally:
        connection.close()

def fetch_all_bugs(db_params):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM bug WHERE is_deleted = 0')
            bugs = cursor.fetchall()
            cursor.execute('SELECT * FROM programs')
            programs = cursor.fetchall()
            cursor.execute('SELECT * FROM areas')
            areas = cursor.fetchall()
            cursor.execute('SELECT * FROM employees')
            employees = cursor.fetchall()
            return bugs, programs, areas, employees
    finally:
        connection.close()

def fetch_recovered_bugs(db_params):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM bug WHERE is_deleted = 1')
            bugs = cursor.fetchall()
            cursor.execute('SELECT * FROM programs')
            programs = cursor.fetchall()
            cursor.execute('SELECT * FROM areas')
            areas = cursor.fetchall()
            cursor.execute('SELECT * FROM employees')
            employees = cursor.fetchall()
            return bugs, programs, areas, employees
    finally:
        connection.close()

def mark_bug_as_deleted(db_params, bug_id):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            delete_query = """
                UPDATE bug
                SET is_deleted = 1, deleted_at = NOW()
                WHERE bug_id = %s
            """
            cursor.execute(delete_query, (bug_id,))
            connection.commit()
    finally:
        connection.close()

def update_bug_details(db_params, bug_details):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT prog_id FROM programs WHERE program=%s", (bug_details['program'],))
            prog_id = cursor.fetchone()['prog_id']
            cursor.execute("SELECT area_id FROM areas WHERE area=%s", (bug_details['functional_area'],))
            if bug_details['functional_area'] is not None:
                area_id = cursor.fetchone()['area_id']
            else:
                area_id = None
            cursor.execute("""
                UPDATE bug
                SET program=%s, report_type=%s, severity=%s, problem_summary=%s, reproducible=%s, problem=%s,
                    reported_by=%s, date_reported=%s, functional_area=%s, assigned_to=%s, comments=%s,
                    status=%s, priority=%s, resolution=%s, resolution_version=%s, resolution_by=%s,
                    date_resolved=%s, tested_by=%s, prog_id=%s, area_id=%s, attachment=%s, filename=%s, suggested_fix = %s
                WHERE bug_id=%s
            """, (
                bug_details['program'], bug_details['report_type'], bug_details['severity'],
                bug_details['problem_summary'], bug_details['reproducible'], bug_details['problem'],
                bug_details['reported_by'], bug_details['date_reported'], bug_details['functional_area'],
                bug_details['assigned_to'], bug_details['comments'], bug_details['status'],
                bug_details['priority'], bug_details['resolution'], bug_details['resolution_version'],
                bug_details['resolution_by'], bug_details['date_resolved'], bug_details['tested_by'],
                prog_id, area_id, bug_details['attachment'], bug_details['file_name'], bug_details['suggested_fix'], bug_details['bug_id']
            ))
            connection.commit()
            return "Bug with name {} was successfully updated.".format(bug_details['program'])
    finally:
        connection.close()

def insert_bug(db_params, bug_details):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT prog_id FROM programs WHERE program=%s", (bug_details['program'],))
            prog_id = cursor.fetchone()['prog_id']
            cursor.execute("SELECT area_id FROM areas WHERE area=%s", (bug_details['functional_area'],))
            if bug_details['functional_area'] is not None:
                area_id = cursor.fetchone()['area_id']
            else:
                area_id = None
            cursor.execute("""
                INSERT INTO bug (program, report_type, severity, problem_summary, reproducible, problem,
                    reported_by, date_reported, functional_area, assigned_to, comments, status, priority,
                    resolution, resolution_version, resolution_by, date_resolved, tested_by, prog_id,
                    area_id, attachment, filename, suggested_fix)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s, %s, %s)
            """, (
                bug_details['program'], bug_details['report_type'], bug_details['severity'],
                bug_details['problem_summary'], bug_details['reproducible'], bug_details['problem'],
                bug_details['reported_by'], bug_details['date_reported'], bug_details['functional_area'],
                bug_details['assigned_to'], bug_details['comments'], bug_details['status'], bug_details['priority'],
                bug_details['resolution'], bug_details['resolution_version'], bug_details['resolution_by'],
                bug_details['date_resolved'], bug_details['tested_by'], prog_id, area_id, bug_details['attachment'], 
                bug_details['file_name'], bug_details['suggested_fix']))
            connection.commit()
            return cursor.lastrowid 
    finally:
        connection.close()

def fetch_all_programs(db_params):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT prog_id, program, program_release, program_version FROM programs ORDER BY program")
            programs = cursor.fetchall()
            return programs
    finally:
        connection.close()

def fetch_all_areas(db_params):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM areas ORDER BY area')
            areas = cursor.fetchall()
            return areas
    finally:
        connection.close()

def fetch_all_areas_prog(db_params):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT a.area_id, a.area, p.prog_id, p.program AS program FROM areas a JOIN programs p ON a.prog_id = p.prog_id ORDER BY a.prog_id")
            areas = cursor.fetchall()
            return areas
    finally:
        connection.close()



def fetch_attachment_by_filename(db_params, filename):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT attachment FROM bug WHERE filename = %s", (filename,))
            data = cursor.fetchone()
            return data['attachment'] if data else None
    finally:
        connection.close()

def recover_bug_by_id(db_params, id_data):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            update_query = """
                UPDATE bug
                SET is_deleted = 0, deleted_at = NULL
                WHERE bug_id = %s
            """
            cursor.execute(update_query, (id_data,))
            connection.commit()
            return cursor.rowcount  
    finally:
        connection.close()

def delete_bug_permanently(db_params, id_data):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            delete_query = "DELETE FROM bug WHERE bug_id = %s"
            cursor.execute(delete_query, (id_data,))
            connection.commit()
            return cursor.rowcount  
    except Exception as e:
        return None, str(e)
    finally:
        connection.close()

def recover_all_deleted_bugs(db_params):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            update_query = 'UPDATE bug SET is_deleted=0 WHERE is_deleted=1'
            cursor.execute(update_query)
            connection.commit()
            return cursor.rowcount, None  # Return the count and None for the error
    except Exception as e:
        return 0, str(e)  # Return 0 for the count and the error message
    finally:
        connection.close()


def delete_all_marked_bugs(db_params):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            delete_query = 'DELETE FROM bug WHERE is_deleted=1'
            cursor.execute(delete_query)
            connection.commit()
            return cursor.rowcount, None  # Ensure two values are returned
    except Exception as e:
        return 0, str(e)  # Return 0 and the error message
    finally:
        connection.close()


def fetch_all_bugs_db(db_params):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM bug")
            bugs = cursor.fetchall()
            return bugs
    finally:
        connection.close()

def perform_search(db_params, search_data):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            # Start with a base query that filters out deleted records
            query = "SELECT * FROM bug WHERE is_deleted = 0"
            params = []

            # Check if 'status' is provided and add to the query if so
            if 'status' in search_data and search_data['status']:
                query += " AND status = %s"
                params.append(search_data['status'])
            else:
                # Default to showing only 'Open' bugs if no status is specified
                query += " AND status = 'Open'"

            # Loop through each field in search_data to add to the query
            for field, value in search_data.items():
                if value and field != 'status':  # Skip 'status' as it's already handled
                    if field == 'report_date':  # Special handling for dates
                        query += f" AND DATE({field}) = %s"
                        params.append(value)
                    elif field in ['program', 'report_type', 'severity', 'problem_summary', 'reproducible', 'problem', 'reported_by', 'date_reported', 'functional_area', 'assigned_to', 'comments', 'priority', 'resolution', 'resolution_version', 'resolution_by', 'date_resolved', 'tested_by', 'attachment', 'file_name']:
                        query += f" AND {field} LIKE %s"
                        value = f"%{value}%"  # Adding wildcards around the value
                        params.append(value)
                    else:  # Direct match for other fields
                        query += f" AND {field} = %s"
                        params.append(value)

            query += " ORDER BY program"  # Ensure results are ordered by program
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        connection.close()



def fetch_all_employees(db_params):
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            sql = "SELECT emp_id, name, username, userlevel FROM employees"
            cursor.execute(sql)
            return cursor.fetchall()  # Returns a list of dictionaries where each dictionary represents an employee
    finally:
        connection.close()