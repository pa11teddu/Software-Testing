from flask import render_template, request, redirect, session, url_for, flash
import pymysql
import requests
from werkzeug.utils import secure_filename
import os
from flask import send_from_directory
import pymysql.cursors
from io import BytesIO
from flask import send_file, abort
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from flask import Flask, request, Response
from app import app, db_params, RECAPTCHA_SECRET_KEY, job_scheduler
from flask import render_template, request, redirect, session, url_for, flash, send_file
from apscheduler.schedulers.background import BackgroundScheduler
from database_actions import *
from collections import defaultdict
from functools import wraps
from flask import session, redirect, url_for, flash




def recaptcha_is_valid(recaptcha_response):
    payload = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': recaptcha_response
    }
    
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
    result = response.json()
    
    return result.get('success', False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Checking user session for access...")
        if 'user_id' not in session:
            flash("You must be logged in to view this page.")
            return redirect(url_for('authenticate_user'))
        return f(*args, **kwargs)
    return decorated_function



@app.route('/submit', methods=['POST'])
def submit_form():
    recaptcha_response = request.form['g-recaptcha-response']
    success, error = recaptcha_is_valid(recaptcha_response)

    if success:
        return 'Form submitted successfully'
    else:
        return 'reCAPTCHA verification failed: ' + error

def purge_stale_marked_records():
    threshold_date = datetime.now() - timedelta(weeks=1)
    db_connection = pymysql.connect(**db_params)

    try:
        with db_connection.cursor() as cursor:
            purge_query = """
                DELETE FROM bug_tracking 
                WHERE marked_for_deletion = %s 
                AND deletion_date <= %s
            """
            cursor.execute(purge_query, (True, threshold_date))
            db_connection.commit()
    finally:
        db_connection.close()
    print("Stale marked records have been purged.")

job_scheduler = BackgroundScheduler()
job_scheduler.add_job(
    func=purge_stale_marked_records,
    trigger="cron", 
    day_of_week='mon-sun', 
    hour=2
)
job_scheduler.start()

@app.teardown_appcontext
def cease_scheduler(sender, *args, **kwargs):
    if job_scheduler.state:  
        job_scheduler.shutdown(wait=False)


def get_db_connection():
    return pymysql.connect(**db_params)

@app.route("/")
def home_page():
    return render_template("user_login_page.html")

@app.route('/', methods=['GET', 'POST'])
def authenticate_user():
    if request.method == 'POST':
        username = request.form.get('username', '')
        userlevel_requested = request.form.get('userlevel', '')
        captcha_response = request.form.get('g-recaptcha-response', '')

        if not recaptcha_is_valid(captcha_response):
            flash("Failed CAPTCHA check. Please attempt again.")
            return redirect(url_for('authenticate_user'))
        # Use the new function to get the user record
        user_record = authenticate_user_db(db_params, username)
        if user_record:
            if str(user_record['userlevel']) == userlevel_requested:
                    session['user_id'] = username
                    session['access_level'] = user_record['userlevel']
                    return redirect(url_for('control_panel'))
            else:
                flash("User level does not match or unauthorized access.")
                return redirect(url_for('authenticate_user'))
        else:
            flash("User does not exist.")
            return redirect(url_for('authenticate_user'))
    return render_template('login.html')




@app.route('/session_termination', methods=['GET'])
def session_termination():
    session.clear()  # Clears all data from the session
    flash("You have been successfully logged out.")
    return redirect('/')



@app.route('/control_panel', methods=['GET'])
@login_required
def control_panel():

    return render_template('control_panel.html', 
                           condition=session.get('access_level'), 
                           user_name=session.get('user_id'), 
                           access_level=session.get('access_level'))


@app.route('/register_employee', methods=['POST'])
@login_required
def register_employee():
    success = register_employee_db(db_params, request.form.get('name'), request.form.get('username'), 
                                   request.form.get('password'), request.form.get('userlevel'))
    if success:
        flash(f"New staff member {request.form.get('username')} successfully added.", "success")
    else:
        flash("Failed to add new staff member.", "error")
    return redirect(url_for('employee_controller'))

@app.route('/employee_controller')
@login_required
def employee_controller():
    employees = fetch_all_employees(db_params)
    return render_template('employee_controller.html', employees=employees, username=session.get('user_id'), userlevel=session.get('access_level'))

@app.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        if request.form['password'] != request.form['confirm_password']:
            flash('Passwords do not match. Please re-enter your password.', 'danger')
            return redirect(url_for('user_signup'))
        existing_user = check_user_exists(db_params, request.form['username'])
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('user_signup'))
        success = add_new_user(db_params, request.form['employee_name'],
                                request.form['username'], request.form['password'], request.form['level'])
        if success:
            flash('Account created successfully. You can now log in.', 'success')
            return redirect(url_for('authenticate_user'))
        else:
            flash('An error occurred during account creation. Please try again.', 'danger')
    return render_template('user_signup.html')
    


@app.route('/add_program', methods=['POST'])
@login_required
def add_program():
    if request.method == "POST":
        prog_name = request.form.get('program') + " "+ request.form.get('release') + " "+ request.form.get('version')
        add_program_db(db_params, prog_name, request.form.get('release'), request.form.get('version'))
        flash(f"New program '{request.form.get('program')}' added successfully.", "success")
        return redirect(url_for('manage_program'))

@app.route('/edit_program', methods=['POST', 'GET'])
@login_required
def edit_program():
    if request.method == "POST":
        name = request.form['program'] + " " + request.form['release'] + " " + request.form['version']
        update_program_db(db_params, request.form['prog_id'], name, 
                       request.form['release'], request.form['version'])
        flash(f"Program {request.form['program']} was updated successfully.")
        return redirect(url_for('manage_program'))


@app.route('/delete_employee/<string:emp_id>', methods=['GET'])
@login_required
def delete_employee(emp_id):
    delete_employee_db(db_params, emp_id)
    flash(f"Employee {emp_id} has been permanently deleted.", "success")
    return redirect(url_for('employee_controller'))

@app.route('/delete_program/<string:prog_id>', methods=['GET'])
@login_required
def delete_program(prog_id):
    delete_program_db(db_params, prog_id)
    flash(f"Program with id {prog_id} was successfully deleted", "success")
    return redirect(url_for('manage_program'))  


@app.route('/add_area', methods=['POST'])
@login_required
def add_area():
    if request.method == "POST":
        message = add_area_db(db_params, request.form['area'], request.form['prog_id'])
        flash(message)
        return redirect(url_for('area_controller'))

@app.route('/edit_employee', methods=['POST', 'GET'])
@login_required
def edit_employee():
    if request.method == "POST":
        employee_details = {
            'emp_id': request.form['emp_id'],
            'name': request.form['name'],
            'username': request.form['username'],
            # 'password': request.form['password'],
            'userlevel': request.form['userlevel']
        }
        update_employee_details_db(db_params, employee_details)
        flash(f"Updated details for {employee_details['name']}.", "success")
        return redirect(url_for('employee_controller'))

@app.route('/edit_area', methods=['POST', 'GET'])
@login_required
def edit_area():
    if request.method == "POST":
        message = update_area_db(db_params, request.form['area_id'], request.form['area'], request.form['prog_id'])
        flash(message)
        return redirect(url_for('area_controller'))  


@app.route('/delete_area/<string:id_data>', methods=['GET'])
@login_required
def delete_area(id_data):
    message = delete_area_db(db_params, id_data)
    flash(message)
    return redirect(url_for('area_controller'))

@app.route('/update_bug')
@login_required
def update_bug():
    bugs, programs, areas, employees = fetch_all_bugs(db_params)
    return render_template('update_bug.html', username=session.get('user_id'), userlevel=session.get('access_level'), bugs=bugs, 
                           programs=programs, report_types=app.config['REPORT_TYPE_OPTIONS'], severities=app.config['SEVERITY_LEVELS'], 
                           employees=employees, areas=areas, resolution=app.config['RESOLUTION_OPTIONS'], 
                           resolution_version=app.config['RESOLUTION_VERSION_OPTIONS'], priority=app.config['PRIORITY_LEVELS'], 
                           status=app.config['STATUS_OPTIONS'])

@app.route('/show_recovered_bugs')
@login_required
def show_recovered_bugs():
    bugs, programs, areas, employees = fetch_recovered_bugs(db_params)
    return render_template('update_bug.html', username=session.get('user_id'), userlevel=session.get('access_level'),
                           bugs=bugs, programs=programs, report_types=app.config['REPORT_TYPE_OPTIONS'], 
                           severities=app.config['SEVERITY_LEVELS'],
                           employees=employees, areas=areas, resolution=app.config['RESOLUTION_OPTIONS'], 
                           resolution_version=app.config['RESOLUTION_VERSION_OPTIONS'],
                           priority=app.config['PRIORITY_LEVELS'], status=app.config['STATUS_OPTIONS'], showing_recovered=True)



@app.route('/delete_bug/<string:id_data>', methods=['GET'])
@login_required
def delete_bug(id_data):
    mark_bug_as_deleted(db_params, id_data)
    flash(f"Bug with id {id_data} was successfully marked as deleted.")
    return redirect(url_for('resulted_bugs'))

@app.route('/edit_bug', methods=['POST', 'GET'])
@login_required
def edit_bug():
    if request.method == "POST":
        bug_details = {
            'bug_id': request.form.get('bug_id'),
            'program': request.form.get('program'),
            'report_type': request.form.get('report_type'),
            'severity': request.form.get('severity'),
            'problem_summary': request.form.get('problem_summary'),
            'reproducible': request.form.get('reproducible'),
            'problem': request.form.get('problem'),
            'reported_by': request.form.get('reported_by'),
            'date_reported': request.form.get('date_reported'),
            'functional_area': request.form.get('functional_area'),
            'assigned_to': request.form.get('assigned_to'),
            'comments': request.form.get('comments'),
            'suggested_fix': request.form.get('suggested_fix'),
            'status': request.form.get('status'),
            'priority': request.form.get('priority'),
            'resolution': request.form.get('resolution'),
            'resolution_version': request.form.get('resolution_version'),
            'resolution_by': request.form.get('resolution_by'),
            'date_resolved': request.form.get('date_resolved'),
            'tested_by': request.form.get('tested_by'),
            'attachment': request.files["attachment"].read(),
            'file_name': request.files["attachment"].filename
        }
        message = update_bug_details(db_params, bug_details)
        flash(message)
        return redirect(url_for('resulted_bugs'))

@app.route('/modify_bug', methods=['POST', 'GET'])
@login_required
def modify_bug():
    if request.method == "POST":
        bug_details = {
            'bug_id': request.form.get('bug_id'),
            'program': request.form.get('program'),
            'report_type': request.form.get('report_type'),
            'severity': request.form.get('severity'),
            'problem_summary': request.form.get('problem_summary'),
            'reproducible': request.form.get('reproducible'),
            'problem': request.form.get('problem'),
            'reported_by': request.form.get('reported_by'),
            'date_reported': request.form.get('date_reported'),
            'functional_area': request.form.get('functional_area'),
            'assigned_to': request.form.get('assigned_to'),
            'comments': request.form.get('comments'),
             'suggested_fix': request.form.get('suggested_fix'),
            'status': request.form.get('status'),
            'priority': request.form.get('priority'),
            'resolution': request.form.get('resolution'),
            'resolution_version': request.form.get('resolution_version'),
            'resolution_by': request.form.get('resolution_by'),
            'date_resolved': request.form.get('date_resolved'),
            'tested_by': request.form.get('tested_by'),
            'attachment': request.files["attachment"].read(),
            'file_name': request.files["attachment"].filename
        }
        message = update_bug_details(db_params, bug_details)
        flash(message)
        return redirect(url_for('modify_bug'))

@app.route('/add_bug', methods=['GET', 'POST'])
@login_required
def add_bug():
    if request.method == 'POST':
        status = request.form.get('status') or 'Open'
        file = request.files.get('attachment')
        file_path = None  # Default to None if no file is attached
        filename = None  # Default to None if no file is attached
        # Proceed only if a file is attached and has a filename
        if file and file.filename:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
            else:
                flash('Invalid file type.')
        bug_details = {
            'program': request.form.get('program'),
            'report_type': request.form.get('report_type'),
            'severity': request.form.get('severity'),
            'problem_summary': request.form.get('problem_summary'),
            'reproducible': request.form.get('reproducible'),
            'problem': request.form.get('problem'),
            'reported_by': request.form.get('reported_by'),
            'date_reported': request.form.get('date_reported'),
            'functional_area': request.form.get('functional_area'),
            'assigned_to': request.form.get('assigned_to'),
            'comments': request.form.get('comments'),
            'status': status,
            'suggested_fix': request.form.get('suggested_fix'),
            'priority': request.form.get('priority'),
            'resolution': request.form.get('resolution'),
            'resolution_version': request.form.get('resolution_version'),
            'resolution_by': request.form.get('resolution_by'),
            'date_resolved': request.form.get('date_resolved'),
            'tested_by': request.form.get('tested_by'),
            'attachment': file_path,
            'file_name': filename
        }
        bug_id = insert_bug(db_params, bug_details)

        flash(f"Bug with id {bug_id} was successfully added.")
        return redirect(url_for('add_bug'))
    connection = pymysql.connect(**db_params)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM programs ORDER BY program')
            programs = cursor.fetchall()
            
            cursor.execute('SELECT * FROM areas ORDER BY area')
            areas = cursor.fetchall()
            
            cursor.execute('SELECT * FROM employees')
            employees = cursor.fetchall()
    finally:
        connection.close()
    return render_template('add_bug.html', programs=programs, report_types=app.config['REPORT_TYPE_OPTIONS'], 
                           severities=app.config['SEVERITY_LEVELS'], employees=employees, areas=areas, 
                           resolution=app.config['RESOLUTION_OPTIONS'], resolution_version=app.config['RESOLUTION_VERSION_OPTIONS'], 
                           priority=app.config['PRIORITY_LEVELS'], status=app.config['STATUS_OPTIONS'], 
                           username=session.get('user_id'), userlevel=session.get('access_level'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


    

@app.route('/manage_program')
@login_required
def manage_program():
    programs = fetch_all_programs(db_params)
    return render_template('program_operations.html', program=programs, 
                           username=session.get('user_id'), userlevel=session.get('access_level'))

@app.route('/area_controller')
@login_required
def area_controller():
    areas = preprocess_areas(fetch_all_areas_prog(db_params))
    programs = fetch_all_programs(db_params)
    return render_template('area_controller.html', areas=areas, programs=programs, username=session.get('user_id'), userlevel=session.get('access_level'))

def preprocess_areas(areas):
    program_counts = defaultdict(int)
    for area in areas:
        program_counts[area['program']] += 1
    output = []
    seen_programs = set()
    for area in areas:
        if area['program'] in seen_programs:
            rowspan = 0
            show_program_name = False  # This flag indicates where to show the program name
        else:
            rowspan = program_counts[area['program']]
            seen_programs.add(area['program'])
            show_program_name = True
        area['rowspan'] = rowspan
        # Determine the middle row to display the program name
        area['show_program_name'] = show_program_name
        output.append(area)
    return output




@app.route('/update', methods=['POST', 'GET'])
@login_required
def update():
    return redirect(url_for('employee_controller'))

@app.route('/view_attachment/<filename>')
def view_attachment(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/recover_bug/<string:id_data>', methods=['GET'])
@login_required
def recover_bug(id_data):
    affected_rows = recover_bug_by_id(db_params, id_data)
    if affected_rows:
        flash(f"Bug with id {id_data} has been successfully recovered.", "success")
    else:
        flash("No bug found with that ID or it was not deleted.", "error")
    return redirect(url_for('update_bug'))

@app.route('/delete_permanently/<int:id_data>', methods=['POST', 'GET'])
@login_required
def delete_permanently(id_data):
    rows_deleted, error = delete_bug_permanently(db_params, id_data)
    if rows_deleted:
        flash('Bug deleted permanently.', 'success')
    else:
        error_message = 'An error occurred while deleting the bug.' if not error else error
        flash(error_message, 'danger')
    return redirect(url_for('show_recovered_bugs'))


@app.route('/recover_all_bugs', methods=['POST'])
@login_required
def recover_all_bugs():
    rows_updated, error = recover_all_deleted_bugs(db_params)  # Now both values will always be there
    if rows_updated:
        flash('All bugs recovered successfully.', 'success')
    else:
        error_message = 'An error occurred while recovering all bugs.' if not error else error
        flash(error_message, 'danger')
    return redirect(url_for('show_recovered_bugs'))


@app.route('/delete_all_bugs', methods=['POST'])
@login_required
def delete_all_bugs():
    rows_deleted, error = delete_all_marked_bugs(db_params)
    if rows_deleted:
        flash('All bugs deleted permanently.', 'success')
    else:
        error_message = 'An error occurred while deleting all bugs.' if not error else error
        flash(error_message, 'danger')
    return redirect(url_for('show_recovered_bugs'))


@app.route('/export_bugs_to_xml')
@login_required
def export_bugs_to_xml():
    bugs = fetch_all_bugs_db(db_params)
    root = ET.Element('Bugs')
    for bug in bugs:
        bug_element = ET.SubElement(root, 'Bug')
        for key, value in bug.items():
            element = ET.SubElement(bug_element, key)
            element.text = str(value)
    xml_string = ET.tostring(root, encoding='utf8', method='xml').decode()
    return Response(xml_string, mimetype='text/xml', headers={"Content-disposition": "attachment; filename=bugs.xml"})

@app.route('/export_programs_to_xml')
@login_required
def export_programs_to_xml():
    programs = fetch_all_programs(db_params)  # Ensure this fetches all needed program data
    root = ET.Element('Programs')
    for program in programs:
        program_element = ET.SubElement(root, 'Program')
        for key, value in program.items():
            element = ET.SubElement(program_element, key)
            element.text = str(value)
    xml_string = ET.tostring(root, encoding='utf8', method='xml').decode()
    return Response(xml_string, mimetype='text/xml', headers={"Content-disposition": "attachment; filename=programs.xml"})

@app.route('/export_areas_to_xml')
@login_required
def export_areas_to_xml():
    areas = fetch_all_areas(db_params)  # Ensure this fetches all needed area data
    root = ET.Element('Areas')
    for area in areas:
        area_element = ET.SubElement(root, 'Area')
        for key, value in area.items():
            element = ET.SubElement(area_element, key)
            element.text = str(value)
    xml_string = ET.tostring(root, encoding='utf8', method='xml').decode()
    return Response(xml_string, mimetype='text/xml', headers={"Content-disposition": "attachment; filename=areas.xml"})

@app.route('/export_employees_to_xml')
@login_required
def export_employees_to_xml():
    employees = fetch_all_employees(db_params)  # Ensure this fetches all needed employee data
    root = ET.Element('Employees')
    for employee in employees:
        employee_element = ET.SubElement(root, 'Employee')
        for key, value in employee.items():
            element = ET.SubElement(employee_element, key)
            element.text = str(value)
    xml_string = ET.tostring(root, encoding='utf8', method='xml').decode()
    return Response(xml_string, mimetype='text/xml', headers={"Content-disposition": "attachment; filename=employees.xml"})

@app.route('/export_employees_to_ascii')
@login_required
def export_employees_to_ascii():
    employees = fetch_all_employees(db_params)
    output = "EmployeeID, Name, Username, UserLevel\n"  # Header for the CSV format
    for employee in employees:
        # Extract only the necessary fields
        output += f"{employee['emp_id']}, {employee['name']}, {employee['username']}, {employee['userlevel']}\n"
    return Response(output, mimetype='text/plain', headers={"Content-disposition": "attachment; filename=employees.txt"})

@app.route('/export_areas_to_ascii')
@login_required
def export_areas_to_ascii():
    areas = fetch_all_areas(db_params)
    output = "AreaID, ProgramID, AreaName\n"
    for area in areas:
        output += f"{area['area_id']}, {area['prog_id']}, {area['area']}\n"
    return Response(output, mimetype='text/plain', headers={"Content-disposition": "attachment; filename=areas.txt"})

@app.route('/export_programs_to_ascii')
@login_required
def export_programs_to_ascii():
    programs = fetch_all_programs(db_params)
    output = "ProgramID, ProgramName, Release, Version\n"
    for program in programs:
        output += f"{program['prog_id']}, {program['program']}, {program['program_release']}, {program['program_version']}\n"
    return Response(output, mimetype='text/plain', headers={"Content-disposition": "attachment; filename=programs.txt"})


@app.route('/search_bugs', methods=['GET', 'POST'])
@login_required
def search_bugs():
    programs = fetch_all_programs(db_params)
    employees = fetch_all_employees(db_params)
    areas = fetch_all_areas(db_params)

    if request.method == 'POST':
        
        file = request.files.get('attachment')
        filename = secure_filename(file.filename) if file else None
        if file and allowed_file(file.filename):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        search_data = {
            'program': request.form.get('program'),
            'report_type': request.form.get('report_type'),
            'severity': request.form.get('severity'),
            'problem_summary': request.form.get('problem_summary'),
            'reproducible': request.form.get('reproducible'),
            'problem': request.form.get('problem'),
            'reported_by': request.form.get('reported_by'),
            'date_reported': request.form.get('date_reported'),
            'functional_area': request.form.get('functional_area'),
            'assigned_to': request.form.get('assigned_to'),
            'comments': request.form.get('comments'),
            'status': request.form.get('status'),
            'suggested_fix': request.form.get('suggested_fix'),
            'priority': request.form.get('priority'),
            'resolution': request.form.get('resolution'),
            'resolution_version': request.form.get('resolution_version'),
            'resolution_by': request.form.get('resolution_by'),
            'date_resolved': request.form.get('date_resolved'),
            'tested_by': request.form.get('tested_by'),
            'attachment': file_path if file else None,
            'file_name': filename if file else None
        }

        results = perform_search(db_params, search_data)
        session['search_results'] = results  # Store results in session or another form of temporary storage
        return redirect(url_for('resulted_bugs'))

    return render_template('bug_search.html', programs=programs, report_types=app.config['REPORT_TYPE_OPTIONS'], 
                           severities=app.config['SEVERITY_LEVELS'], employees=employees, areas=areas, 
                           resolution=app.config['RESOLUTION_OPTIONS'], resolution_version=app.config['RESOLUTION_VERSION_OPTIONS'], 
                           priority=app.config['PRIORITY_LEVELS'], status=app.config['STATUS_OPTIONS'], 
                           user_name=session.get('user_id'), access_level=session.get('access_level'))

@app.route('/resulted_bugs', methods=['GET', 'POST'])
@login_required
def resulted_bugs():
    file = request.files.get('attachment')
    filename = secure_filename(file.filename) if file else None
    if file and allowed_file(file.filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    programs = fetch_all_programs(db_params)
    employees = fetch_all_employees(db_params)
    areas = fetch_all_areas(db_params)
    search_criteria = {}
    search_data = {
            'program': request.form.get('program'),
            'report_type': request.form.get('report_type'),
            'severity': request.form.get('severity'),
            'problem_summary': request.form.get('problem_summary'),
            'reproducible': request.form.get('reproducible'),
            'problem': request.form.get('problem'),
            'reported_by': request.form.get('reported_by'),
            'date_reported': request.form.get('date_reported'),
            'functional_area': request.form.get('functional_area'),
            'assigned_to': request.form.get('assigned_to'),
            'comments': request.form.get('comments'),
            'suggested_fix': request.form.get('suggested_fix'),
            'status': request.form.get('status'),
            'priority': request.form.get('priority'),
            'resolution': request.form.get('resolution'),
            'resolution_version': request.form.get('resolution_version'),
            'resolution_by': request.form.get('resolution_by'),
            'date_resolved': request.form.get('date_resolved'),
            'tested_by': request.form.get('tested_by'),
            'attachment': file_path if file else None,
            'file_name': filename if file else None
        }
    criteria_descriptions = []
    for key, value in search_data.items():
        if value:
            criteria_descriptions.append(value)

    criteria_summary = ", ".join(criteria_descriptions) if criteria_descriptions else "All Bugs"

    results = perform_search(db_params, search_data)
    results_count = len(results)
    # flash("Bug Updated")
        # return redirect(url_for('resulted_bugs'))

    return render_template('search_results.html', areas = areas, results_count = results_count, results=results, programs=programs, employees=employees, 
                            user_name=session.get('user_id'), access_level=session.get('access_level'), 
                            report_types=app.config['REPORT_TYPE_OPTIONS'], 
                            severities=app.config['SEVERITY_LEVELS'], criteria_summary=criteria_summary,
                            resolution=app.config['RESOLUTION_OPTIONS'], resolution_version=app.config['RESOLUTION_VERSION_OPTIONS'], 
                            priority=app.config['PRIORITY_LEVELS'], status=app.config['STATUS_OPTIONS'])
    # return render_template('search_results.html', areas = areas, results_count = results_count, results=results, programs=programs, employees=employees, 
    #                         user_name=session.get('user_id'), access_level=session.get('access_level'), 
    #                         report_types=app.config['REPORT_TYPE_OPTIONS'], 
    #                         severities=app.config['SEVERITY_LEVELS'],
    #                         resolution=app.config['RESOLUTION_OPTIONS'], resolution_version=app.config['RESOLUTION_VERSION_OPTIONS'], 
    #                         priority=app.config['PRIORITY_LEVELS'], status=app.config['STATUS_OPTIONS'])


# @app.route('/search_bugs', methods=['GET', 'POST'])
# @login_required
# def search_bugs():
#     programs = fetch_all_programs(db_params)
#     employees = fetch_all_employees(db_params)
#     areas = fetch_all_areas(db_params)
#     if request.method == 'POST':
#         search_data = {
#             'program': request.form.get('program'),
#             'report_type': request.form.get('report_type'),
#             'severity': request.form.get('severity'),
#             # 'problem_summary': request.form.get('problem_summary'),
#             'reproducible': request.form.get('reproducible'),
#             # 'problem': request.form.get('problem'),
#             'reported_by': request.form.get('reported_by'),
#             'date_reported': request.form.get('date_reported'),
#             'functional_area': request.form.get('functional_area'),
#             'assigned_to': request.form.get('assigned_to'),
#             # 'comments': request.form.get('comments'),
#             'status': request.form.get('status'),
#             'priority': request.form.get('priority'),
#             'resolution': request.form.get('resolution'),
#             'resolution_version': request.form.get('resolution_version'),
#             'resolution_by': request.form.get('resolution_by'),
#             'date_resolved': request.form.get('date_resolved'),
#             'tested_by': request.form.get('tested_by'),
#             # 'attachment': request.files["attachment"].read(),
#             # 'file_name': request.files["attachment"].filename
#         }

#         return redirect(url_for('resulted_bugs'))
#         # results = perform_search(db_params, search_data)
#         # results_count = len(results)
#         # return render_template('search_results.html',areas = areas, results_count = results_count, results=results, programs=programs, employees=employees, 
#         #                        user_name=session.get('user_id'), access_level=session.get('access_level'), 
#         #                        report_types=app.config['REPORT_TYPE_OPTIONS'], 
#         #                    severities=app.config['SEVERITY_LEVELS'],
#         #                    resolution=app.config['RESOLUTION_OPTIONS'], resolution_version=app.config['RESOLUTION_VERSION_OPTIONS'], 
#         #                    priority=app.config['PRIORITY_LEVELS'], status=app.config['STATUS_OPTIONS'])
    
#     return render_template('bug_search.html', programs=programs, report_types=app.config['REPORT_TYPE_OPTIONS'], 
#                            severities=app.config['SEVERITY_LEVELS'], employees=employees, areas=areas, 
#                            resolution=app.config['RESOLUTION_OPTIONS'], resolution_version=app.config['RESOLUTION_VERSION_OPTIONS'], 
#                            priority=app.config['PRIORITY_LEVELS'], status=app.config['STATUS_OPTIONS'], 
#                            user_name=session.get('user_id'), access_level=session.get('access_level'))



# @app.route('/resulted_bugs', methods=['GET', 'POST'])
# @login_required
# def resulted_bugs():
#     programs = fetch_all_programs(db_params)
#     employees = fetch_all_employees(db_params)
#     areas = fetch_all_areas(db_params)
#     search_data = {
#             'program': request.form.get('program'),
#             'report_type': request.form.get('report_type'),
#             'severity': request.form.get('severity'),
#             # 'problem_summary': request.form.get('problem_summary'),
#             'reproducible': request.form.get('reproducible'),
#             # 'problem': request.form.get('problem'),
#             'reported_by': request.form.get('reported_by'),
#             'date_reported': request.form.get('date_reported'),
#             'functional_area': request.form.get('functional_area'),
#             'assigned_to': request.form.get('assigned_to'),
#             # 'comments': request.form.get('comments'),
#             'status': request.form.get('status'),
#             'priority': request.form.get('priority'),
#             'resolution': request.form.get('resolution'),
#             'resolution_version': request.form.get('resolution_version'),
#             'resolution_by': request.form.get('resolution_by'),
#             'date_resolved': request.form.get('date_resolved'),
#             'tested_by': request.form.get('tested_by'),
#             # 'attachment': request.files["attachment"].read(),
#             # 'file_name': request.files["attachment"].filename
#     }


#     results = perform_search(db_params, search_data)
#     results_count = len(results)
#     return render_template('search_results.html',areas = areas, results_count = results_count, results=results, programs=programs, employees=employees, 
#                                user_name=session.get('user_id'), access_level=session.get('access_level'), 
#                                report_types=app.config['REPORT_TYPE_OPTIONS'], 
#                            severities=app.config['SEVERITY_LEVELS'],
#                            resolution=app.config['RESOLUTION_OPTIONS'], resolution_version=app.config['RESOLUTION_VERSION_OPTIONS'], 
#                            priority=app.config['PRIORITY_LEVELS'], status=app.config['STATUS_OPTIONS'])


@app.route('/approve_user', methods=['POST'])
@login_required
def approve_user():
    emp_id = request.form['emp_id']
    if emp_id:
        approve_user_db(db_params, emp_id)
        flash(f'{emp_id} access has been approved.')
    return redirect(url_for('employee_controller'))  

@app.route('/toggle_approval', methods=['POST'])
@login_required
def toggle_approval():
    emp_id = request.form['emp_id']
    new_status = request.form['new_status']
    if emp_id and new_status is not None:
        toggle_user_approval(db_params, emp_id, new_status)
        action = "approved" if new_status == "1" else "revoked"
        flash(f'{emp_id} access has been {action}.')
    return redirect(url_for('employee_controller'))

@app.route('/assigned_bugs')
@login_required
def assigned_bugs():
    bugs = get_assigned_bugs(db_params, session.get('user_id'))
    return render_template('assigned_bugs.html', bugs=bugs, user_name=session.get('user_id'), 
                           access_level=session.get('access_level'))

if __name__ == "__main__":
    app.run(debug=True)
