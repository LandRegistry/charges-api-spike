##DEFAULT DIR IS ROOT OF HOST_DATA

import logging
import psycopg2
from flask import Flask, render_template, request, url_for, json, redirect, session, g, flash
from flask.ext.login import login_user, logout_user, current_user, login_required, UserMixin
from app import app, lm

#Login Imports
from forms import LoginForm
from config import LDAPSRV
import ldap

##IMPORT FOR UTF-8 SUPPORT
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

#local modules
import controller
import database_utils
import utils
from User import User, ldap_validate
import os


# -*- coding: utf-8 -*-


log_event = logging.getLogger('log_event')
log_error = logging.getLogger('log_error')


@app.before_request
def log_request():
    """
    Logs each incoming request
    """
    log_event.info(request)
    if request.form:
        log_event.info(request.form)
######################################################
#""" LOGIN REQUIREMENTS """#


@lm.user_loader
def load_user(id):
    auto_db_user = controller.get_user_from_RACF(id)

    (auto_db_user_id, auto_db_user_racf, auto_db_user_real_name, auto_db_user_location,
     auto_db_user_admin, auto_db_user_active) = auto_db_user[0]

    u = User(uid=auto_db_user_id, id=auto_db_user_racf, realname=auto_db_user_real_name,
             location=auto_db_user_location, admin=auto_db_user_admin)
    return u


@app.before_request
def before_request():
    g.user = current_user


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#######################################################

# region Basic Functions


"""
BASIC FUNCTIONS
These function do not take arguments
Typically used for navigation and blank forms
"""


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if not g.user is None:
        if form.validate_on_submit():
            if ldap_validate(name=form.username.data, passwd=form.password.data):

                # get full user details from database
                db_user = controller.get_user_from_RACF(form.username.data)

                if db_user != []:
                    # User found on database

                    # correlate to named tuple
                    (db_user_id, db_user_racf, db_user_real_name, db_user_location, db_user_admin, db_user_active) \
                        = db_user[0]

                    if db_user_active:
                        u = User(uid=db_user_id, id=db_user_racf, realname=db_user_real_name, location=db_user_location,
                                 admin=db_user_admin)
                        login_user(u)
                        log_event.info(db_user_real_name + " Logged in")
                        login_date = controller.get_current_date()
                        login_time = controller.get_current_time()
                        controller.set_login_date_time(login_date, login_time, u.id)

                        return redirect(request.args.get('next') or url_for('index'))

                    else:
                        flash('Login was unsuccessful - User not authorised to access HOFM')
                        log_event.info("Login was unsuccessful - User not authorised to access HOFM")
                else:
                    flash('Login was unsuccessful - User not found on HOFM')
                    log_event.info("Login was unsuccessful - User not found on HOFM")
            else:
                flash('Login was unsuccessful - ADS failure')

    server_name = (os.environ['HOFM_HOST']).upper()

    if "DB31" in server_name:
        connected_server = "DB31 - Test"
    elif "AP21" in server_name:
        connected_server = "AP21 - LDev"
    elif "AP11" in server_name:
        connected_server = "AP11 - Assurance"
    elif "AP01" in server_name:
        connected_server = "AP01 - Live"

    return render_template('login.html', title='Sign In', form=form, connected_server=connected_server)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    """
    Returns starting page html with database status
    :return: html
    """

    error_message = ""

    database_connection_status = ""
    try:
        database_connection_status = controller.get_database_connection_status()
    except Exception as e:
        error_message = e

    return render_template("index.html",
                           database_connection_status=database_connection_status,
                           message_error=error_message)


@app.route('/search')
@login_required
def search_page():
    """
    Returns a page with controls used to build search criteria and start search.
    For example, data, title, file umber.
    :return: html
    """

    return render_template("search.html")


@app.route('/createrecord')
@login_required
def create_record():
    """
    Returns a page with controls used to specify file information and create a file record.
    :return: html
    """

    record_template = controller.create_record_template()
    return render_template("createrecord.html",
                           list_of_series_subjects=record_template['list_of_series_subjects'],
                           list_of_series_years=record_template['list_of_series_years'],
                           list_of_offices=record_template['list_of_offices'])


@app.route('/subjects')
@login_required
def show_subjects():
    """
    Returns a page with a list of all subjects
    :return: html
    """

    searched_date = controller.get_current_date()
    searched_time = controller.get_current_time()

    list_of_subjects = controller.show_all_subjects()

    return render_template("subjects.html",
                           searched_date=searched_date,
                           searched_time=searched_time,
                           search_results=list_of_subjects['records_data'],
                           count_results=len(list_of_subjects['records_data']))


@app.route('/about')
@login_required
def about_page():
    """
    Returns a page with information about the application.
    :return: html
    """

    return render_template("about.html")


@app.route('/contact')
@login_required
def contact_page():
    """
    Returns a page with information about who should be contacted for support
    :return: html
    """

    return render_template("contact.html")


@app.route('/noncomprecords')
@login_required
def show_records_with_noncompliant_numbering():
    """
    Returns a page with a list of file that do not match the standard format file numbering.
    :return: html
    """

    searched_date = controller.get_current_date()
    searched_time = controller.get_current_time()

    try:
        records_with_noncompliant_numbering = controller.show_records_with_noncompliant_numbering()
        return render_template('searchresults.html',
                               search_results=records_with_noncompliant_numbering['records_data'],
                               count_results=len(records_with_noncompliant_numbering['records_data']),
                               searched_date=searched_date,
                               searched_time=searched_time)
    except:
            return render_template("search.html",
                                   message_error="Error retrieving records with non-compliant numbering")


@app.route('/users')
@login_required
def show_latest_login_details():
    """
    Returns a page with a list of file that do not match the standard format file numbering.
    :return: html
    """

    searched_date = controller.get_current_date()
    searched_time = controller.get_current_time()

    login_details = controller.get_login_details()

    return render_template('users.html',
                           login_details=login_details,
                           searched_date=searched_date,
                           searched_time=searched_time)
    # except:
    #         return render_template("index.html",
    #                                message_error="Error retrieving latest login details")

# endregion


# region Advanced Functions


"""
ADVANCED FUNCTIONS
These functions take arguments
Typically used to handle populated forms
"""


@app.route('/record/<path:file_number>/<file_part>')
@login_required
def show_record(file_number, file_part):
    """
    Returns a page with the record of the file specified.
    :param file_number: The file series, e.g. AB/123/456/789
    :param file_part: The file series part, e.g. A, B, C
    :return: html
    """

    record = controller.show_record(file_number, file_part)
    update_token = "View"
    searched_date = controller.get_current_date()
    searched_time = controller.get_current_time()
    list_of_offices = controller.show_record_template()

    return render_template("showrecord.html",
                           show_record_data=record['show_record_data'],
                           show_movements_data=record['show_movements_data'],
                           now_date=record['now_date'],
                           now_time=record['now_time'],
                           update_token=update_token,
                           searched_date=searched_date,
                           searched_time=searched_time,
                           list_of_offices=list_of_offices['list_of_offices'])


@app.route('/searchresults/', methods=['POST'])
@login_required
def search_regmast():
    """
    Returns a page with a list of files that match the search criteria.
    :params: uses form data.
    :return: html
    """

    #Form Input and formatting
    file_status = request.form['file_status']
    file_number_code = request.form['file_number_code']
    file_number_1 = request.form['file_number_1']
    file_number_2 = request.form['file_number_2']
    file_number_3 = request.form['file_number_3']
    date_first = request.form['date_from']
    date_second = request.form['date_to']
    file_title = request.form['file_title']
    search_type = request.form['search_type']

    file_number_1 = database_utils.format_text_to_remove_escape_codes(file_number_1)
    file_number_2 = database_utils.format_text_to_remove_escape_codes(file_number_2)
    file_number_3 = database_utils.format_text_to_remove_escape_codes(file_number_3)
    file_title = database_utils.format_text_to_remove_escape_codes(file_title)

    records = controller.search_regmast(file_status, file_number_code,
                                        file_number_1, file_number_2, file_number_3,
                                        date_first, date_second, file_title, search_type)

    searched_date = controller.get_current_date()
    searched_time = controller.get_current_time()

    return render_template('searchresults.html',
                           search_results=records['search_results'],
                           count_results=records['count_results'],
                           search_error=records['search_error'],
                           new_search_clause=records['new_search_clause'],
                           parameter_dict=records['parameter_dict'],
                           searched_date=searched_date,
                           searched_time=searched_time)


@app.route('/update/', methods=['POST'])
@login_required
def update_record():
    """
    Copies current file details to  movement history (not all data).
    Updates current file details with new information provided.
    :param: uses form data.
    :return: html
    """

    #If variables are blank - no changes to be made (is this safe?)
    file_number = request.form['move_file_number']
    file_part = request.form['move_file_part']
    new_file_status = request.form['NewStatus']
    new_holder_name = request.form['NewHolder'].strip()
    new_holder_phone = request.form['NewPhone'].strip()
    new_holder_office = request.form['NewOffice']
    new_holder_room = request.form['NewRoom'].strip()
    new_movement_date = request.form['NewMoveDate']
    new_movement_time = request.form['NewMoveTime']
    try:
        new_movement_date_formatted = utils.to_date(new_movement_date)
    except:
        new_movement_date_formatted = new_movement_date

    new_movement_time_formatted = utils.to_time_string_with_seconds(new_movement_time)
    error_message = ""
    info_message = ""
    searched_date = controller.get_current_date()
    searched_time = controller.get_current_time()

    # validate incoming data
    validation_result = controller.validate_create_movement_data(new_file_status, new_holder_name, new_holder_phone,
                                                                 new_holder_room, new_movement_date_formatted,
                                                                 new_movement_time_formatted, file_number, file_part)
    # if invalid, return form with invalid data messages
    # if valid, continue with creation
    if not validation_result['valid']:
        error_message = validation_result['errors']
        #remove symbols that cause html textarea problems
        error_message = error_message.replace("'", "")
        error_message = error_message.replace("{", "")
        error_message = error_message.replace("}", "")
        error_message = error_message.replace("[", "")
        error_message = error_message.replace("]", "")

        record = controller.show_record(file_number, file_part)
        update_token = "View"

        searched_date = controller.get_current_date()
        searched_time = controller.get_current_time()
        list_of_offices = controller.show_record_template()

        return render_template("showrecord.html",
                               show_record_data=record['show_record_data'],
                               show_movements_data=record['show_movements_data'],
                               now_date=record['now_date'],
                               now_time=record['now_time'],
                               update_token=update_token,
                               searched_date=searched_date,
                               searched_time=searched_time,
                               list_of_offices=list_of_offices['list_of_offices'],
                               message_error=error_message)
    try:
        controller.create_new_movement(file_number, file_part, new_file_status,
                                       new_holder_name, new_holder_phone, new_holder_office,
                                       new_holder_room, new_movement_date_formatted, new_movement_time_formatted)
        info_message = "Movement Update Successful"
    except Exception as e:
        error_message = e

    record = controller.show_record(file_number, file_part)
    list_of_offices = controller.show_record_template()

    return render_template("showrecord.html",
                           show_record_data=record['show_record_data'],
                           show_movements_data=record['show_movements_data'],
                           now_date=record['now_date'],
                           now_time=record['now_time'],
                           searched_time=searched_time,
                           searched_date=searched_date,
                           message_info=info_message,
                           message_error=error_message,
                           list_of_offices=list_of_offices['list_of_offices'])


@app.route('/titleupdate/', methods=['POST'])
@login_required
def update_title():
    """
    Updates current file details with new information provided.
    :param: uses form data.
    :return: html
    """

    file_number = request.form['title_file_number']
    file_part = request.form['title_file_part']
    new_file_title = request.form['new_file_title'].strip()

    error_message = ""
    info_message = ""

    # validate incoming data
    validation_result = controller.validate_create_movement_title(new_file_title)
    # if invalid, return form with invalid data messages
    # if valid, continue with creation
    if not validation_result['valid']:
        error_message = validation_result['errors']
        #remove symbols that cause html textarea problems
        error_message = error_message.replace("'", "")
        error_message = error_message.replace("{", "")
        error_message = error_message.replace("}", "")
        error_message = error_message.replace("[", "")
        error_message = error_message.replace("]", "")

        record = controller.show_record(file_number, file_part)
        update_token = "View"

        searched_date = controller.get_current_date()
        searched_time = controller.get_current_time()
        list_of_offices = controller.show_record_template()

        return render_template("showrecord.html",
                               show_record_data=record['show_record_data'],
                               show_movements_data=record['show_movements_data'],
                               now_date=record['now_date'],
                               now_time=record['now_time'],
                               update_token=update_token,
                               searched_date=searched_date,
                               searched_time=searched_time,
                               list_of_offices=list_of_offices['list_of_offices'],
                               message_error=error_message)
    try:
        controller.update_file_title(file_number, file_part, new_file_title)
        info_message = "Title Update Successful"
    except Exception as e:
        error_message = e

    record = controller.show_record(file_number, file_part)
    update_token = "TitleOnly"

    searched_date = controller.get_current_date()
    searched_time = controller.get_current_time()

    return render_template("showrecord.html",
                           show_record_data=record['show_record_data'],
                           show_movements_data=record['show_movements_data'],
                           now_date=record['now_date'],
                           now_time=record['now_time'],
                           #user_notice=user_notice,
                           update_token=update_token,
                           searched_date=searched_date,
                           searched_time=searched_time,
                           message_info=info_message,
                           message_error=error_message)


@app.route('/notesupdate/', methods=['POST'])
@login_required
def update_notes():
    """
    Updates current file details with new information provided.
    :param: uses form data.
    :return: html
    """

    file_number = request.form['notes_file_number']
    file_part = request.form['notes_file_part']
    new_file_notes = request.form['new_file_notes'].strip()

    error_message = ""
    info_message = ""

        # validate incoming data
    validation_result = controller.validate_create_movement_notes(new_file_notes)
    # if invalid, return form with invalid data messages
    # if valid, continue with creation
    if not validation_result['valid']:
        error_message = validation_result['errors']
        #remove symbols that cause html textarea problems
        error_message = error_message.replace("'", "")
        error_message = error_message.replace("{", "")
        error_message = error_message.replace("}", "")
        error_message = error_message.replace("[", "")
        error_message = error_message.replace("]", "")

        record = controller.show_record(file_number, file_part)
        update_token = "View"

        searched_date = controller.get_current_date()
        searched_time = controller.get_current_time()
        list_of_offices = controller.show_record_template()

        return render_template("showrecord.html",
                               show_record_data=record['show_record_data'],
                               show_movements_data=record['show_movements_data'],
                               now_date=record['now_date'],
                               now_time=record['now_time'],
                               update_token=update_token,
                               searched_date=searched_date,
                               searched_time=searched_time,
                               list_of_offices=list_of_offices['list_of_offices'],
                               message_error=error_message)
    try:
        controller.update_file_notes(file_number, file_part, new_file_notes)
        info_message = "Notes Update Successful"
    except Exception as e:
        error_message = e

    record = controller.show_record(file_number, file_part)
    update_token = "NotesOnly"

    searched_date = controller.get_current_date()
    searched_time = controller.get_current_time()

    return render_template("showrecord.html",
                           show_record_data=record['show_record_data'],
                           show_movements_data=record['show_movements_data'],
                           now_date=record['now_date'],
                           now_time=record['now_time'],
                           update_token=update_token,
                           searched_date=searched_date,
                           searched_time=searched_time,
                           message_info=info_message,
                           message_error=error_message)


@app.route('/creation/', methods=['POST'])
@login_required
def create_record_submit():
    """
    Create a new record of file information.
    :param: uses form data.
    :return: html
    """

    error_message = ""

    # get values from form
    file_title = request.form['input_create_title'].strip()
    file_number_code = request.form['input_file_number_code'].strip()
    file_number_1 = request.form['input_file_number_1']
    file_number_2 = request.form['input_file_number_2']
    file_number_3 = request.form['input_file_number_3']
    file_part = request.form['input_create_file_part']
    file_status = request.form['select_create_status']
    holder_name = request.form['input_create_holder'].strip()
    holder_phone = request.form['input_create_phone'].strip()
    holder_office = request.form['select_create_office']
    holder_room = request.form['input_create_room'].strip()
    file_notes = request.form['input_create_notes'].strip()

    file_part = file_part.upper()
    file_number_code = file_number_code.upper()

    # validate incoming data
    validation_result = controller.validate_create_record_data(file_title, file_number_code,
                                                               file_number_1, file_number_2, file_number_3,
                                                               file_part, file_status, holder_name, holder_phone,
                                                               holder_office, holder_room, file_notes)
    # if invalid, return form with invalid data messages
    # if valid, continue with creation
    if not validation_result['valid']:
        record_template = controller.create_record_template()
        error_message = validation_result['errors']
        #remove symbols that cause html textarea problems
        error_message = error_message.replace("'", "")
        error_message = error_message.replace("{", "")
        error_message = error_message.replace("}", "")
        error_message = error_message.replace("[", "")
        error_message = error_message.replace("]", "")
        return render_template("createrecord.html",
                               list_of_series_subjects=record_template['list_of_series_subjects'],
                               list_of_series_years=record_template['list_of_series_years'],
                               list_of_offices=record_template['list_of_offices'],
                               message_error=error_message,
                               request_form=request.form)
    # if valid
    #create full fnum
    #handle first part of file ID - spaces required
    create_file_number_complete = ""

    if file_number_code == "CE":
        create_file_number_complete = \
            file_number_code + '     ' + file_number_1 + '/' + file_number_2
    else:
        create_file_number_complete = \
            file_number_code + '    ' + file_number_1 + '/' + file_number_2
    #if file number 3 is used, add to full file number
    if file_number_3 != "":
        create_file_number_complete += '/' + file_number_3

    #Point into Controller
    searched_date = controller.get_current_date()
    searched_time = controller.get_current_time()
    #add to database
    #if successful, get exact details from database
    #otherwise, return to the form
    try:
        controller.create_new_record(file_title, create_file_number_complete, file_part, file_status,
                                     holder_name, holder_phone, holder_office, holder_room, file_notes)
        record = controller.show_record(create_file_number_complete, file_part)
        info_message = "File record creation successful"
        update_token = "NewRec"
        return render_template("showrecord.html",
                               show_record_data=record['show_record_data'],
                               show_movements_data=record['show_movements_data'],
                               now_date=record['now_date'],
                               now_time=record['now_time'],
                               update_token=update_token,
                               searched_date=searched_date,
                               searched_time=searched_time,
                               message_error=error_message,
                               message_info=info_message)
    except Exception as e:
        print e
        error_message = "File record creation failed" + error_message
        record_template = controller.create_record_template()
        return render_template("createrecord.html",
                               list_of_series_subjects=record_template['list_of_series_subjects'],
                               list_of_series_years=record_template['list_of_series_years'],
                               list_of_offices=record_template['list_of_offices'],
                               message_error=error_message,
                               request_form=request.form)


@app.route('/createsubject/', methods=['POST'])
@login_required
def create_subject():
    """
    Updates current file details with new information provided.
    :param: uses form data.
    :return: html
    """

    subject_type = "T"
    subject_code = request.form['new_subject_code']
    subject_description = request.form['new_subject_description']

    error_message = ""
    info_message = ""

    subject_description = database_utils.format_text_to_restore_escape_codes(subject_description)

    try:
        controller.create_new_subject(subject_type, subject_code, subject_description)
        info_message = "Subject Creation Complete"
    except Exception as e:
        error_message = e

    searched_date = controller.get_current_date()
    searched_time = controller.get_current_time()

    list_of_subjects = controller.show_all_subjects()

    return render_template("subjects.html",
                           searched_date=searched_date,
                           searched_time=searched_time,
                           search_results=list_of_subjects['records_data'],
                           count_results=len(list_of_subjects['records_data']),
                           message_info=info_message,
                           message_error=error_message)


# endregion


# region AJAX Functions
"""
AJAX FUNCTIONS
"""


@app.route('/getnextsequentialfilenumber/<file_number_code>/<file_number_1>/<file_number_2>/<file_number_3>')
@app.route('/creation/getnextsequentialfilenumber/<file_number_code>/<file_number_1>/<file_number_2>/<file_number_3>')
@login_required
def get_next_sequential_file(file_number_code, file_number_1, file_number_2="", file_number_3=""):
    """
    Returns the next number increment for the file series.
    :param file_number_code: CE, SUB, etc
    :param file_number_1: 123, 456, etc
    :param file_number_2: 123, 456, etc
    :param file_number_3: 123, 456, etc
    :return: JSON doc with file_number_1, file_number_2, file_number_3, file_part
    """
    file_number_code_stripped = file_number_code.strip()
    file_number_1_stripped = file_number_1.strip()
    file_number_2_stripped = file_number_2.strip()
    file_number_3_stripped = file_number_3.strip()
    if file_number_2 == "none":
        file_number_2_stripped = ""
    if file_number_3 == "none":
        file_number_3_stripped = ""
    next_sequential_number = controller.get_next_sequential_file_number(file_number_code_stripped,
                                                                        file_number_1_stripped,
                                                                        file_number_2_stripped,
                                                                        file_number_3_stripped)
    return json.dumps(next_sequential_number)


@app.route('/getnextsequentialsubject')
@login_required
def get_next_sequential_subject():
    next_sequential_subject = controller.get_next_sequential_subject()
    return json.dumps(next_sequential_subject)

# endregion

#Error Handling#
@app.errorhandler(404)
def not_found_error(error):

    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(error):
    log_event.error("INTERNAL SERVER ERROR")
    log_error.error("INTERNAL SERVER ERROR")
    log_error.error(error)
    
    print "**************INTERNAL SERVER ERROR************************"
    print error
    print "**************INTERNAL SERVER ERROR************************"

    return render_template("500.html",
                            error=error), 404