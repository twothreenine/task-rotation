#!/usr/bin/env python3
import ethercalc
import json
import logging
import pprint
import datetime
import random
import os
import babel.dates
from foodsoft import FSConnector
import export

pp = pprint.PrettyPrinter(indent=4)
calc = {"host": "", "page": "", "name": ""}
events = []
participants = []
tasks = []
notes = []
newly_calculated_events = []
newly_listed_events = []
newly_assigned_events = []
events_with_newly_attached_note = []
default_language = "en"
task_group_name = "Task group"
recent_events_factor = 0.8
header_lines = 2
capable_after_task_count = 0
save_backup_before_for_sheet_nos = []
save_backup_after_for_sheet_nos = []

def read_config():
    config = {'foodsoft_url': os.environ['TR_FOODSOFT_URL'],'foodsoft_user': os.environ['TR_FOODSOFT_USER'],'foodsoft_password': os.environ['TR_FOODSOFT_PASS']}
    return config

config = read_config()

fsc = FSConnector(config['foodsoft_url'], config['foodsoft_user'], config['foodsoft_password'])


def semicolon_separated_list_from_python_list(any_list, attribute=None):
    csl = ""
    if any_list:
        my_list = any_list.copy()
        if attribute:
            csl = str(eval("my_list[0]."+attribute))
        else:
            csl = str(my_list[0])
        my_list.pop(0)
        for item in my_list:
            if attribute:
                csl += ";" + str(eval("item."+attribute))
            else:
                csl += ";" + str(item)
    return csl

def python_list_from_semicolon_separated_list(any_list, data_type="str", convert_none_from_str=False):
    new_list = []
    if any_list:
        if ";" in str(any_list):
            new_list = list(map(eval(data_type), any_list.split(";")))
        else:
            new_list = [eval(data_type+"(any_list)")]
    # if convert_none_from_str:
    #     for item in new_list:
    #         if item == "None":
    #             item = None
    #     pp.pprint(new_list)
    return new_list

def dict_str(any_dict):
    dict_str = ""
    if any_dict:
        my_list = [item for item in any_dict]
        dict_str += my_list[0]
        my_list.pop(0)
        for item in my_list:
            dict_str += ", " + item
    return dict_str

def excel_date(date1):
    delta = date1 - datetime.date(1899, 12, 30)
    return int(delta.days)

def read_date(date1):
    a = None
    if date1:
        try:
            a = int(date1)
            date = datetime.date.fromordinal(datetime.date(1899, 12, 30).toordinal() + int(a))
        except (ValueError, TypeError):
            date = date1
        except:
            raise
        return date

def read_weekdays(weekdays_str):
    weekdays = []
    if weekdays_str:
        weekdays_strs = weekdays_str.split(";")
        for string in weekdays_strs:
            if string == "monday":
                weekdays.extend([1])
            elif string == "tuesday":
                weekdays.extend([2])
            elif string == "wednesday":
                weekdays.extend([3])
            elif string == "thursday":
                weekdays.extend([4])
            elif string == "friday":
                weekdays.extend([5])
            elif string == "saturday":
                weekdays.extend([6])
            elif string == "sunday":
                weekdays.extend([7])
            else:
                print("Warning: Weekday filter '"+string+"' not recognized. Valid arguments are: monday, tuesday, wednesday, thursday, friday, saturday, sunday.")
    if weekdays == []:
        weekdays = [1, 2, 3, 4, 5, 6, 7]
    return weekdays

def save_backup(sheet_nos, note=""):
    folder = calc["name"] + " " + datetime.date.today().isoformat()
    tested_number = 1
    if os.path.exists("exported_sheets/"+folder+" "+note):
        tested_number += 1
        while os.path.exists("exported_sheets/"+folder+" ("+str(tested_number)+") "+note):
            tested_number += 1
        folder += " (" + str(tested_number) + ")"
    export.export(host=calc["host"], page=calc["page"], sheets=sheet_nos, folder=folder+" "+note)

class Event:
    def __init__(self, date, task_type, event_no, regular_date, persons_needed, capable_persons_needed, event_number_in_time_period, note_types, note_numbers_in_time_period, note_time_period_start_dates, hidden, assigned_persons=[], note="", assignment_errors=[], reminders_sent=False, check_ups_sent=False, time_period_start_date=None):
        self.date = date
        self.task_type = task_type
        self.event_no = event_no
        self.regular_date = regular_date
        self.persons_needed = persons_needed
        self.capable_persons_needed = capable_persons_needed
        self.assigned_persons = assigned_persons.copy()
        self.note = note
        self.assignment_errors = assignment_errors.copy()
        self.reminders_sent = reminders_sent
        self.reminders_sent_before = reminders_sent
        self.check_ups_sent = check_ups_sent
        self.check_ups_sent_before = check_ups_sent
        self.event_number_in_time_period = event_number_in_time_period
        self.time_period_start_date = time_period_start_date
        self.note_types = note_types
        self.note_numbers_in_time_period = note_numbers_in_time_period
        self.note_time_period_start_dates = note_time_period_start_dates
        self.hidden = hidden

class Participant:
    def __init__(self, name, capable, active, entry_date, old_task_count, language=None, contact_info=None):
        self.name = name
        self.capable = capable
        self.active = active
        self.entry_date = entry_date
        self.active_until = False
        self.old_task_count = old_task_count
        if capable:
            self.capable_before = True
        else:
            self.capable_before = False
        self.task_count = 0
        self.task_count_per_days_since_entry = False
        self.language = language
        self.contact_info = contact_info

class Task:
    def __init__(self, type_id, name, start, end, time_period_factor, time_period_mode, day_numbers_in_time_period, weekday_filter, persons_needed, capable_persons_needed, assign_for_days, list_for_days, hide_from_days, reminder_days_before, note):
        self.type_id = type_id
        self.name = name
        self.start = start
        self.end = end
        self.time_period_factor = time_period_factor
        self.time_period_mode = time_period_mode
        self.day_numbers_in_time_period = day_numbers_in_time_period
        self.weekday_filter = weekday_filter
        self.persons_needed = persons_needed
        self.capable_persons_needed = capable_persons_needed
        self.assign_for_days = assign_for_days
        self.list_for_days = list_for_days
        self.hide_from_days = hide_from_days
        self.reminder_days_before = reminder_days_before
        self.note = note

class AssignmentError:
    def __init__(self, error_type, assigned_person_no, error_message, assigned_person=""):
        self.error_type = error_type
        self.assigned_person_no = assigned_person_no
        self.assigned_person = assigned_person
        self.error_message = error_message

class Note:
    def __init__(self, type_id, task_types, start, end, event_numbers_in_time_period, time_period_factor, time_period_mode, weekday_filter, message):
        self.type_id = type_id
        if task_types:
            self.task_types = task_types.copy()
        else:
            self.task_types = []
        self.start = start
        self.end  = end
        self.event_numbers_in_time_period = event_numbers_in_time_period
        self.time_period_factor = time_period_factor
        self.time_period_mode = time_period_mode
        self.message = message
        self.weekday_filter = weekday_filter

def load_ethercalc(host=None, page=None, sheet=None, export_format="python"): # returns one of multiple sheets as a nested python list; for the first sheet: sheet=1
    if not host:
        host = calc["host"]
    if not page:
        page = calc["page"]
    if sheet:
        sheet_str = "." + str(sheet)
    else:
        sheet_str = ""
    logging.debug("remote host: " + host + " remote page: " + page + sheet_str)
    return ethercalc.EtherCalc(host).export(page + sheet_str, format=export_format)

def find_header_lines(settings_list):
    header_lines_row = 0
    for row in settings_list:
        try:
            row.index('header_lines')
            break
        except ValueError:
            header_lines_row += 1
        except:
            raise
    return int(settings_list[header_lines_row][2])

def load_objects(event_sheet_no=1, participant_sheet_no=2, task_sheet_no=3, notes_sheet_no=4, settings_sheet_no=5): # converts rows of the sheets events, participants and tasks into python objects; usually the header consists of 2 rows which have to be ignored (pop)
    settings_list = load_ethercalc(sheet=settings_sheet_no)
    header_lines = find_header_lines(settings_list=settings_list)
    print("header lines = "+str(header_lines))
    for i in range(header_lines):
        settings_list.pop(0)
    if settings_list[2][2]:
        global default_language
        default_language = settings_list[2][2]
    if settings_list[3][2]:
        global task_group_name
        task_group_name = settings_list[3][2]
    if settings_list[4][2]:
        global recent_events_factor
        recent_events_factor = settings_list[4][2]
        print("recent events factor = "+str(recent_events_factor))
    if settings_list[5][2]:
        global capable_after_task_count
        capable_after_task_count = int(settings_list[5][2])
        print("capable after task count = "+str(capable_after_task_count))
    if settings_list[6][2]:
        global save_backup_before_for_sheet_nos
        save_backup_before_for_sheet_nos = python_list_from_semicolon_separated_list(any_list=settings_list[6][2], convert_none_from_str=True)
    if settings_list[7][2]:
        global save_backup_after_for_sheet_nos
        save_backup_after_for_sheet_nos = python_list_from_semicolon_separated_list(any_list=settings_list[7][2], convert_none_from_str=True)

    global events
    global participants
    global tasks
    global notes
    participant_list = load_ethercalc(sheet=participant_sheet_no)
    for i in range(header_lines):
        participant_list.pop(0)
    while participant_list[-1][0] == "" or participant_list[-1][0] == None:
        participant_list.pop(-1)
    event_list = load_ethercalc(sheet=event_sheet_no)
    for i in range(header_lines):
        event_list.pop(0)
    while event_list and event_list[-1] and event_list[-1][0] == None:
        event_list.pop(-1)
    task_list = load_ethercalc(sheet=task_sheet_no)
    for i in range(header_lines):
        task_list.pop(0)
    while task_list[-1][0] == None:
        task_list.pop(-1)
    note_list = load_ethercalc(sheet=notes_sheet_no)
    for i in range(header_lines):
        note_list.pop(0)
    if note_list:
        while note_list[-1][0] == None:
            note_list.pop(-1)

    for row in participant_list:
        try:
            old_task_count = int(row[3])
        except TypeError:
            old_task_count = 0
        except:
            raise
        capable = True
        if row[1]=="0": capable=False
        active = True
        if row[2]=="0": active=False
        p = Participant(name=row[0], capable=capable, active=active, entry_date=read_date(row[4]), old_task_count=old_task_count, language=row[6], contact_info=row[7])
        if row[4]!="": p.active_until=read_date(row[5])
        participants.append(p)

    for row in task_list:
        day_numbers_in_time_period = python_list_from_semicolon_separated_list(any_list=row[6], data_type="int")
        t = Task(type_id=row[0], name=row[1], start=read_date(row[2]), end=read_date(row[3]), time_period_factor=row[4], time_period_mode=row[5], day_numbers_in_time_period=day_numbers_in_time_period, weekday_filter=read_weekdays(row[7]), persons_needed=int(row[8]), capable_persons_needed=int(row[9]), assign_for_days=row[10], list_for_days=row[11], hide_from_days=row[12], reminder_days_before=row[13], note=row[14])
        tasks.append(t)

    for row in note_list:
        task_types = []
        task_type_ids = python_list_from_semicolon_separated_list(any_list=row[1], data_type="int")
        for tt in task_type_ids:
            task_types.append(next((task for task in tasks if task.type_id == tt), None))
        if not task_type_ids:
            task_types = tasks.copy()
        event_numbers = python_list_from_semicolon_separated_list(any_list=row[6], data_type="int")
        n = Note(type_id=int(row[0]), task_types=task_types, start=read_date(row[2]), end=read_date(row[3]), time_period_factor=row[4], time_period_mode=row[5], event_numbers_in_time_period=event_numbers, weekday_filter=read_weekdays(row[7]), message=row[8])
        notes.append(n)

    for row in event_list:
        assigned_persons = []
        assignment_errors = []
        for cell in row[9:14]:
            if cell != "" and cell and row[0]:
                if "Error: " in cell:
                    error_start = cell.index("Error:")
                    person_name = ""
                    message_end = None
                    if error_start > 2:
                        person_name = cell[0:error_start-2]
                        message_end = -1
                    message = cell[error_start+6:message_end]
                    error = AssignmentError(error_type="Test", assigned_person_no=row.index(cell)+1, assigned_person=person_name, error_message=message)
                    assignment_errors.append(error)
                else:
                    matched_count = 0
                    matches = []
                    for p in participants:
                        if p.name == cell:
                            matched_count += 1
                            matches.append(p)
                    if matched_count == 1:
                        assigned_persons.append(matches[0])
                    elif matched_count == 0:
                        print("No matching participant found for '"+str(cell)+"', assigned for task on "+str(row[0]))
                        error = AssignmentError(error_type="No match", assigned_person_no=row.index(cell)+1, assigned_person=str(cell), error_message="No matching participant found")
                        assignment_errors.append(error)
                    elif matched_count > 1:
                        print(str(matched_count)+" matching participants found for '"+str(cell)+"', assigned for task on "+str(row[0]))
                        error = AssignmentError(error_type="Multiple matches", assigned_person_no=row.index(cell)+1, assigned_person=str(cell), error_message=str(matched_count)+" matching participants found")
                        assignment_errors.append(error)
                    else:
                        print("Match count error for '"+str(cell)+"', assigned for task on "+str(row[0])+": "+str(matched_count))
                        error = AssignmentError(error_type="Match count error", assigned_person_no=row.index(cell)+1, assigned_person=str(cell), error_message="Match count error: "+str(matched_count)+" matching participants found")
                        assignment_errors.append(error)
        task_type = next((task for task in tasks if task.type_id == row[1]), None)
        reminders_sent = False
        if row[15] == "1": reminders_sent = True
        check_ups_sent = False
        if row[16] == "1": check_ups_sent = True
        hidden = False
        if row[22] == "1": hidden = True
        note_types = []
        note_ids = python_list_from_semicolon_separated_list(any_list=row[19], data_type="int")
        for nt in note_ids:
            note_types.append(next((note for note in notes if note.type_id == nt), None))
        note_numbers_in_time_period = python_list_from_semicolon_separated_list(any_list=row[20], data_type="int")
        note_time_period_start_dates = []
        dates = python_list_from_semicolon_separated_list(any_list=row[21], data_type="str")
        for d in dates:
            note_time_period_start_dates.append(read_date(d))
        e = Event(date=read_date(row[0]), task_type=task_type, event_no=row[2], regular_date=read_date(row[3]), persons_needed=int(row[7]), capable_persons_needed=int(row[8]), assigned_persons=assigned_persons, event_number_in_time_period=int(row[17]), time_period_start_date=read_date(row[18]), note_types=note_types, note_numbers_in_time_period=note_numbers_in_time_period, note_time_period_start_dates=note_time_period_start_dates, hidden=hidden, note=row[14], assignment_errors=assignment_errors, reminders_sent=reminders_sent, check_ups_sent=check_ups_sent)
        events.append(e)

def assigned_persons_column_letter(person_count):
    if person_count == 0:
        column_letter="J"
    elif person_count == 1:
        column_letter="K"
    elif person_count == 2:
        column_letter="L"
    elif person_count == 3:
        column_letter="M"
    elif person_count == 4:
        column_letter="N"
    return column_letter

def update_ethercalc_assignments(ecalc, e_page, event_to_assign):
    global events
    person_count = 0
    if event_to_assign.assigned_persons:
        if len(event_to_assign.assigned_persons) > 5:
            assigned_persons_count = 5
            print("More than 5 persons to be assigned onto task on "+str(event_to_assign.date))
        else:
            assigned_persons_count = len(event_to_assign.assigned_persons)
        for a in range(assigned_persons_count):
            letter = assigned_persons_column_letter(person_count=person_count)
            if letter:
                ecalc.command(e_page, ["set "+letter+str(events.index(event_to_assign)+1+header_lines)+" text t "+event_to_assign.assigned_persons[person_count].name])
                person_count += 1
    for error in event_to_assign.assignment_errors:
        if person_count > 4:
            break
        letter = assigned_persons_column_letter(person_count=person_count)
        if letter:
            assigned_person_text = ""
            error_text_ending = ""
            if error.assigned_person != "":
                assigned_person_text = error.assigned_person+" ("
                error_text_ending = ")"
            error_text = assigned_person_text + "Error: " + error.error_message + error_text_ending
            ecalc.command(e_page, ["set "+letter+str(events.index(event_to_assign)+1+header_lines)+" text t "+error_text])
            person_count += 1

def update_ethercalc():
    # update participant.task_count if different and set participant.capable to True if False and task_count > old_task_count
    # update all events from the first newly listed event on; before that, update assigned persons for newly assigned events

    global events
    global participants

    logging.debug("update_ethercalc: " + calc["host"])
    e = ethercalc.EtherCalc(calc["host"])
    e_page = calc["page"]+".1"
    p_page = calc["page"]+".2"

    e.command(e_page, ["set B"+str(1+header_lines)+":W"+str(1+header_lines+len(events))+" readonly no"]) # unlocking cells in the events sheet

    # updating participants' task counts and capability
    for p in participants:
        if not p.task_count == p.old_task_count:
            e.command(p_page, ["set D"+str(participants.index(p) + 1 + header_lines)+" value n "+str(p.task_count)])
        if p.capable and not p.capable_before:
            e.command(p_page, ["set B"+str(participants.index(p) + 1 + header_lines)+" constant nl 1 TRUE"])
            print(p.name+"'s experience set to TRUE")

    # listing events
    if newly_listed_events:
        earliest_newly_listed_event = min(newly_listed_events, key=lambda x: x.date)
        events = sorted(events, key=lambda x: x.date)
        events_to_keep = [event for event in events if event.date < earliest_newly_listed_event.date]
        events_to_overwrite = [event for event in events if event not in events_to_keep]
        last_row = header_lines + 1
        for e_o in events_to_overwrite:
            row_int = int(events.index(e_o)+1+header_lines)
            last_row = row_int
            row = str(row_int)
            e.command(e_page, ["set "+row+" hide"]) # un-hide this row
            e.command(e_page, ["set A"+row+" constant nd "+str(excel_date(e_o.date))+" "+str(e_o.date)])
            e.command(e_page, ["set B"+row+" value n "+str(e_o.task_type.type_id)])
            e.command(e_page, ["set C"+row+" value n "+str(e_o.event_no)])
            e.command(e_page, ["set D"+row+" constant nd "+str(excel_date(e_o.regular_date))+" "+str(e_o.regular_date)])
            e.command(e_page, ["set G"+row+" text t "+str(e_o.task_type.name)])
            e.command(e_page, ["set H"+row+" value n "+str(e_o.persons_needed)])
            e.command(e_page, ["set I"+row+" value n "+str(e_o.capable_persons_needed)])
            e.command(e_page, ["set O"+row+" text t "+str(e_o.note)])
            e.command(e_page, ["set R"+row+" value n "+str(e_o.event_number_in_time_period)])
            if e_o.time_period_start_date:
                e.command(e_page, ["set S"+row+" constant nd "+str(excel_date(e_o.time_period_start_date))+" "+str(e_o.time_period_start_date)])
            else:
                e.command(e_page, ["set S"+row+" empty"])
            note_ids_str = semicolon_separated_list_from_python_list(any_list=e_o.note_types, attribute="type_id")
            e.command(e_page, ["set T"+row+" text t "+note_ids_str])
            note_numbers_str = semicolon_separated_list_from_python_list(any_list=e_o.note_numbers_in_time_period)
            e.command(e_page, ["set U"+row+" text t "+note_numbers_str])
            note_start_dates_excel_int = [excel_date(start_date) for start_date in e_o.note_time_period_start_dates]
            note_start_dates_str = semicolon_separated_list_from_python_list(any_list=note_start_dates_excel_int)
            e.command(e_page, ["set V"+row+" text t "+note_start_dates_str])
            if e_o.hidden:
                e.command(e_page, ["set W"+row+" constant nl 1 TRUE"])
            else:
                e.command(e_page, ["set W"+row+" empty"])

        e.command(e_page, ["filldown E"+str(header_lines+1)+":E"+str(last_row)+" all"])
        e.command(e_page, ["filldown F"+str(header_lines+1)+":F"+str(last_row)+" all"])

    # events_with_newly_attached_note
    for e_n in events_with_newly_attached_note:
        row = str(events.index(e_n)+1+header_lines)
        e.command(e_page, ["set O"+row+" text t "+str(e_n.note)])
        note_ids_str = semicolon_separated_list_from_python_list(any_list=e_n.note_types, attribute="type_id")
        e.command(e_page, ["set T"+row+" text t "+note_ids_str])
        note_numbers_str = semicolon_separated_list_from_python_list(any_list=e_n.note_numbers_in_time_period)
        e.command(e_page, ["set U"+row+" text t "+note_numbers_str])
        note_start_dates_excel_int = [excel_date(start_date) for start_date in e_n.note_time_period_start_dates]
        note_start_dates_str = semicolon_separated_list_from_python_list(any_list=note_start_dates_excel_int)
        e.command(e_page, ["set V"+row+" text t "+note_start_dates_str])

    # assigning events
    for e_a in newly_assigned_events:
        update_ethercalc_assignments(ecalc=e, e_page=e_page, event_to_assign=e_a)

    # events with assignment errors
    for e_e in [event for event in events if event.assignment_errors and event not in newly_assigned_events]:
        update_ethercalc_assignments(ecalc=e, e_page=e_page, event_to_assign=e_e)

    # formatting
    past_events = [event for event in events if event.date < datetime.date.today()]
    events_to_hide = [event for event in events if event.date < datetime.date.today() - datetime.timedelta(days=event.task_type.hide_from_days) or event.hidden == True]
    events_to_mark = [event for event in events if event.date >= datetime.date.today() and event.regular_date <= datetime.date.today() + datetime.timedelta(days=event.task_type.assign_for_days)]
    if events:
        e.command(e_page, ["set A"+str(1+header_lines)+":W"+str(header_lines+len(events))+" bgcolor rgb(255, 255, 255)"])
        e.command(e_page, ["set A"+str(1+header_lines)+":W"+str(header_lines+len(events))+" color rgb(0, 0, 0)"])
    if past_events:
        e.command(e_page, ["set A"+str(1+header_lines)+":W"+str(header_lines+len(past_events))+" color rgb(153, 153, 153)"])
    for event in events_to_hide:
        e.command(e_page, ["set "+str(1+header_lines+events.index(event))+" hide yes"])
    for event in events_to_mark:
        row = str(header_lines+events.index(event)+1)
        e.command(e_page, ["set A"+row+":W"+row+" bgcolor rgb(255, 255, 0)"])

def update_ethercalc_messages_sent():
    e = ethercalc.EtherCalc(calc["host"])
    e_page = calc["page"]+".1"
    # events with reminders resp. check ups sent (moved to for loop above, e_o in events_to_overwrite)
    for e_r in [event for event in events if event.reminders_sent == True and event.reminders_sent_before == False]:
        e.command(e_page, ["set P"+str(events.index(e_r)+1+header_lines)+" constant nl 1 TRUE"])
    for e_c in [event for event in events if event.check_ups_sent == True and event.check_ups_sent_before == False]:
        e.command(e_page, ["set Q"+str(events.index(e_c)+1+header_lines)+" constant nl 1 TRUE"])

def relock_cells():
    e = ethercalc.EtherCalc(calc["host"])
    e_page = calc["page"]+".1"
    e.command(e_page, ["set B"+str(1+header_lines)+":F"+str(1+header_lines+len(events))+" readonly yes"]) # locking cells in the events sheet
    e.command(e_page, ["set P"+str(1+header_lines)+":V"+str(1+header_lines+len(events))+" readonly yes"]) # locking cells in the events sheet    if save_backup_after_for_sheet_nos:

def count_tasks(): # calculating how many tasks each participant has done
    global events
    global participants
    past_events = [event for event in events if event.date < datetime.date.today()]
    for e in past_events:
        for a_p in e.assigned_persons:
            a_p.task_count += 1
            if not a_p.capable and capable_after_task_count > 0 and a_p.task_count >= capable_after_task_count:
                a_p.capable = True
    for p in participants:
        delta = datetime.date.today() - p.entry_date
        p.task_count_per_days_since_entry = p.task_count / int(delta.days)

def choose_person(to_be_assigned_event, only_if_capable=False):
    possible_participants = []
    for p in participants:
        if p.active:
            if p.active_until:
                if p.active_until >= to_be_assigned_event.date:
                    possible_participants.append(p)
            else:
                possible_participants.append(p)
    if only_if_capable:
        possible_participants = [participant for participant in possible_participants if participant.capable]
    recent_events_count = recent_events_factor * len(possible_participants)
    recently_assigned_possible_participants = []
    assigned_events = sorted([event for event in events if event.assigned_persons], key=lambda x: x.date, reverse=True)
    for a_e in assigned_events:
        recent_events_count -= len(a_e.assigned_persons)
        if recent_events_count <= -1:
            break
        for ap in a_e.assigned_persons:
            recently_assigned_possible_participants.append(ap)
    favorable_participants = [participant for participant in possible_participants if participant not in recently_assigned_possible_participants and participant not in to_be_assigned_event.assigned_persons]
    if not favorable_participants:
        favorable_participants = [participant for participant in possible_participants if participant not in to_be_assigned_event.assigned_persons]
    if favorable_participants:
        lowest_task_count_ratio = min(favorable_participants, key=lambda p: p.task_count_per_days_since_entry).task_count_per_days_since_entry
        most_favorable_participants = [participant for participant in favorable_participants if participant.task_count_per_days_since_entry == lowest_task_count_ratio]
        person = random.choice(most_favorable_participants)
        print("Assigned "+person.name+" to task on "+str(to_be_assigned_event.date))
        to_be_assigned_event.assigned_persons.append(person)
    else:
        other_text = ""
        if to_be_assigned_event.assigned_persons:
            other_text = "other "
        capable_text = ""
        if only_if_capable:
            capable_text = "capable "
        assign_person_count = 1
        if to_be_assigned_event.assigned_persons:
            assign_person_count += len(to_be_assigned_event.assigned_persons) + 1
        print("Could not assign person "+str(assign_person_count)+" for task on "+str(to_be_assigned_event.date)+": No "+other_text+capable_text+"active participants!")
        error = AssignmentError(error_type="No "+capable_text+"active participants", assigned_person_no=assign_person_count, assigned_person="", error_message="No "+other_text+capable_text+"active participants")
        to_be_assigned_event.assignment_errors.append(error)

def filter_weekdays(start_date, day_number_in_time_period, weekday_filter):
    day_number = 0
    if day_number_in_time_period > 0:
        tested_date = start_date - datetime.timedelta(days=1)
        test_number_a = 0
        while day_number < day_number_in_time_period:
            if test_number_a == 500:
                print("While loop 1 in filter_weekdays ran 500 times")
            test_number_a += 1
            tested_date += datetime.timedelta(days=1)
            if tested_date.isoweekday() in weekday_filter:
                day_number += 1
    else:
        tested_date = start_date
        test_number_a = 0
        while day_number > day_number_in_time_period:
            if test_number_a == 500:
                print("While loop 2 in filter_weekdays ran 500 times")
            test_number_a += 1
            tested_date -= datetime.timedelta(days=1)
            if tested_date.isoweekday() in weekday_filter:
                day_number -= 1
    return tested_date

def calculate_month(month, year):
    while month > 12:
        year += 1
        month -=12
    return int(month), int(year)

def find_next_date(task, t_events, skip_event_numbers): # for an event to be listed
    last_date = t_events[-1].regular_date
    last_event_number_in_time_period = t_events[-1].event_number_in_time_period + skip_event_numbers
    last_first_event_in_time_period = t_events[(-1)*last_event_number_in_time_period]
    time_period_start_date = None
    if last_event_number_in_time_period < len(task.day_numbers_in_time_period):
        next_event_number_in_time_period = last_event_number_in_time_period + 1
    else:
        next_event_number_in_time_period = 1
    if task.time_period_mode == "day":
        if next_event_number_in_time_period == 1:
            next_date = last_first_event_in_time_period.regular_date + datetime.timedelta(days=task.time_period_factor)
        elif task.day_numbers_in_time_period[next_event_number_in_time_period-1] > 0:
            interval = task.day_numbers_in_time_period[next_event_number_in_time_period-1] - task.day_numbers_in_time_period[last_event_number_in_time_period-1]
            next_date = last_date + datetime.timedelta(days=interval)
        else:
            interval = task.time_period_factor + task.day_numbers_in_time_period[next_event_number_in_time_period-1] + 1 - task.day_numbers_in_time_period[last_event_number_in_time_period-1]
            next_date = last_date + datetime.timedelta(days=interval)
    else:
        if last_first_event_in_time_period.time_period_start_date:
            next_date_month = last_first_event_in_time_period.time_period_start_date.month
            next_date_year = last_first_event_in_time_period.time_period_start_date.year
        else:
            next_date_month = last_first_event_in_time_period.regular_date.month
            next_date_year = last_first_event_in_time_period.regular_date.year
        if task.time_period_mode == "month":
            if next_event_number_in_time_period == 1:
                next_date_month += task.time_period_factor
            after_next_date_month = next_date_month + task.time_period_factor
            if task.day_numbers_in_time_period[next_event_number_in_time_period-1] < 0:
                next_date_month += 1
            next_date_month, next_date_year = calculate_month(next_date_month, next_date_year)
            after_next_date_month, after_next_date_year = calculate_month(after_next_date_month, next_date_year)
        elif task.time_period_mode == "year":
            if next_event_number_in_time_period == 1:
                next_date_year += task.time_period_factor
                next_date_month = 1
            after_next_date_year = next_date_year + task.time_period_factor
            after_next_date_month = 1
            if task.day_numbers_in_time_period[next_event_number_in_time_period-1] < 0:
                next_date_year += 1
        else:
            print("Error: Task time period mode '"+task.time_period_mode+"' is not supported. (day, month, year)")
        start_date = datetime.date(year=int(next_date_year), month=int(next_date_month), day=1)
        after_next_start_date = datetime.date(year=int(after_next_date_year), month=int(after_next_date_month), day=1)
        if next_event_number_in_time_period == 1:
            time_period_start_date = start_date
        next_date = filter_weekdays(start_date=start_date, day_number_in_time_period=task.day_numbers_in_time_period[next_event_number_in_time_period-1], weekday_filter=task.weekday_filter)
        if next_date >= after_next_start_date:
            skip_event_numbers += 1
        else:
            skip_event_numbers = 0
    return next_date, next_event_number_in_time_period, time_period_start_date, skip_event_numbers

def find_next_event(note, all_concerned_events, skip_event_numbers): # for a note to be attached
    events_with_note = [event for event in events if note in event.note_types]
    events_to_be_skipped = 0
    
    latest_first_event = None
    if events_with_note:
        first_events = [event for event in events_with_note if event.note_numbers_in_time_period[event.note_types.index(note)] == 1]
        if first_events:
            latest_first_event = first_events[-1]

    if latest_first_event:
        last_start_date = latest_first_event.note_time_period_start_dates[latest_first_event.note_types.index(note)]
    else:
        last_start_date = note.start

    if note.time_period_mode == "day":
        next_start_date = last_start_date + datetime.timedelta(days=note.time_period_factor)
        after_next_start_date = next_start_date + datetime.timedelta(days=note.time_period_factor)
    elif note.time_period_mode == "month":
        next_start_date_month, next_start_date_year = calculate_month(year=last_start_date.year, month=last_start_date.month + note.time_period_factor)
        after_next_start_date_month, after_next_start_date_year = calculate_month(year=next_start_date_year, month=next_start_date_month + note.time_period_factor)
        next_start_date = datetime.date(year=next_start_date_year, month=next_start_date_month, day=1)
        after_next_start_date = datetime.date(year=after_next_start_date_year, month=after_next_start_date_month, day=1)
    elif note.time_period_mode == "year":
        next_start_date = datetime.date(year=int(last_start_date.year + note.time_period_factor), month=1, day=1)
        after_next_start_date = datetime.date(year=int(next_start_date.year + note.time_period_factor), month=1, day=1)
    else:
        print("Error: Note time period mode '"+note.time_period_mode+"' is not supported. (day, month, year)")

    if latest_first_event: # if events_with_note
        last_event = events_with_note[-1]
        last_note_number_in_time_period = last_event.note_numbers_in_time_period[last_event.note_types.index(note)]
    else:
        last_note_number_in_time_period = 0
        last_start_date = note.start

    if last_note_number_in_time_period < len(note.event_numbers_in_time_period):
        jump_to_next_time_period = False
    else:
        last_note_number_in_time_period = 0
        jump_to_next_time_period = True
    next_note_number_in_time_period = last_note_number_in_time_period + 1 + skip_event_numbers
    next_event_number_in_time_period = note.event_numbers_in_time_period[next_note_number_in_time_period-1]
    if jump_to_next_time_period:
        events_in_time_period = [event for event in all_concerned_events if event.date >= next_start_date and event.date < after_next_start_date]
    else:
        events_in_time_period = [event for event in all_concerned_events if event.date >= last_start_date and event.date < next_start_date]
    if len(events_in_time_period) >= abs(next_event_number_in_time_period):
        zero_based_difference = 1
        if next_event_number_in_time_period < 0:
            zero_based_difference = 0
        next_event = events_in_time_period[next_event_number_in_time_period - zero_based_difference]
        skip_event_numbers = 0
        if jump_to_next_time_period:
            note_time_period_start_date = next_start_date
        else:
            note_time_period_start_date = last_start_date
    else:
        next_event = None
        if jump_to_next_time_period:
            events_left_to_be_checked = [event for event in all_concerned_events if event.date >= after_next_start_date]
        else:
            events_left_to_be_checked = [event for event in all_concerned_events if event.date >= next_start_date]
        if events_left_to_be_checked:
            events_to_be_skipped = 1
        else:
            skip_event_numbers = 0 # if both next_event == None and skip_event_numbers == 0, the while loop searching for events for the note to be attached will stop
        note_time_period_start_date = None

    skip_event_numbers += events_to_be_skipped
    return next_event, next_note_number_in_time_period, note_time_period_start_date, skip_event_numbers

def list_and_assign_events():
    global events
    global participants
    global tasks
    global notes
    global newly_calculated_events
    global newly_listed_events
    global newly_assigned_events
    global events_with_newly_attached_note
    to_be_assigned_events = []
    for t in tasks:
        t_events = sorted([event for event in events if event.task_type == t], key=lambda e: (e.regular_date))
        ended = False
        if t.end:
            if t.end < datetime.date.today():
                ended = True
        if not t_events and t.start <= datetime.date.today() + datetime.timedelta(days=t.list_for_days) and not ended:
            time_period_start_date = None
            if t.time_period_mode == "month" or t.time_period_mode == "year":
                time_period_start_date = t.start
            new_e = Event(date=t.start, task_type=t, event_no=1, regular_date=t.start, persons_needed=t.persons_needed, capable_persons_needed=t.capable_persons_needed, event_number_in_time_period=1, time_period_start_date=time_period_start_date, note_types=[], note_numbers_in_time_period=[], note_time_period_start_dates=[], hidden=False)
            t_events.append(new_e)
            events.append(new_e)
            newly_calculated_events.append(new_e)
        if t_events:
            list_until = datetime.date.today() + datetime.timedelta(days=t.list_for_days)
            concerning_notes = [note for note in notes if t in note.task_types and note.start <= list_until]
            calculate_until = list_until
            note_concerning = False
            for n in concerning_notes: # we need to calculate some events beyond list_for_days if there is a relevant note type, in order to be determine if a event is the last (or n to last) in a note time period
                if n.end:
                    if n.end <= list_until:
                        continue
                tested_date = n.start
                test_number_a = 0
                if n.time_period_mode == "day":
                    while tested_date <= list_until:
                        test_number_a += 1
                        if test_number_a == 500:
                            print("While loop 1 in list_and_assign_events() ran 500 times")
                        tested_date += datetime.timedelta(days=n.time_period_factor)
                elif n.time_period_mode == "month":
                    while tested_date <= list_until:
                        test_number_a += 1
                        if test_number_a == 500:
                            print("While loop 2 in list_and_assign_events() ran 500 times")
                        month, year = calculate_month(month=tested_date.month + n.time_period_factor, year=tested_date.year)
                        tested_date = datetime.date(year=year, month=month, day=1)
                elif n.time_period_mode == "year":
                    while tested_date <= list_until:
                        test_number_a += 1
                        if test_number_a == 500:
                            print("While loop 3 in list_and_assign_events() ran 500 times")
                        tested_date = datetime.date(year=int(tested_date.year+n.time_period_factor), month=1, day=1)
                else:
                    print("Error: Note time period mode '"+n.time_period_mode+"' is not supported. (day, month, year)")
                if tested_date > calculate_until:
                    calculate_until = tested_date
                    note_concerning = True

            skip_event_numbers = 0
            new_date, event_number_in_time_period, time_period_start_date, skip_event_numbers = find_next_date(task=t, t_events=t_events, skip_event_numbers=skip_event_numbers)
            test_number_b = 0
            while skip_event_numbers > 0:
                test_number_b += 1
                if test_number_b == 500:
                    print("While loop 4 in list_and_assign_events() ran 500 times")
                new_date, event_number_in_time_period, time_period_start_date, skip_event_numbers = find_next_date(task=t, t_events=t_events, skip_event_numbers=skip_event_numbers)
            test_number_b = 0
            while new_date < calculate_until:
                test_number_b += 1
                if test_number_b == 500:
                    print("While loop 5 in list_and_assign_events() ran 500 times")
                if t.end:
                    if new_date > t.end:
                        break
                new_e = Event(date=new_date, task_type=t, event_no=t_events[-1].event_no+1, regular_date=new_date, persons_needed=t.persons_needed, capable_persons_needed=t.capable_persons_needed, event_number_in_time_period=event_number_in_time_period, time_period_start_date=time_period_start_date, note_types=[], note_numbers_in_time_period=[], note_time_period_start_dates=[], hidden=False)
                t_events.append(new_e)
                events.append(new_e)
                newly_calculated_events.append(new_e)
                skip_event_numbers = 0
                new_date, event_number_in_time_period, time_period_start_date, skip_event_numbers = find_next_date(task=t, t_events=t_events, skip_event_numbers=skip_event_numbers)
                test_number_c = 0
                while skip_event_numbers > 0:
                    test_number_c += 1
                    if test_number_c == 500:
                        print("While loop 6 in list_and_assign_events() ran 500 times")
                    new_date, event_number_in_time_period, time_period_start_date, skip_event_numbers = find_next_date(task=t, t_events=t_events, skip_event_numbers=skip_event_numbers)

            additional_event_listing = False
            if new_date == list_until:
                if t.end:
                    if new_date <= t.end:
                        additional_event_listing = True
                else:
                    additional_event_listing = True

            if note_concerning or additional_event_listing: # in this case, we need to calculate one more event
                new_e = Event(date=new_date, task_type=t, event_no=t_events[-1].event_no+1, regular_date=new_date, persons_needed=t.persons_needed, capable_persons_needed=t.capable_persons_needed, event_number_in_time_period=event_number_in_time_period, time_period_start_date=time_period_start_date, note_types=[], note_numbers_in_time_period=[], note_time_period_start_dates=[], hidden=False)
                t_events.append(new_e)
                events.append(new_e)
                newly_calculated_events.append(new_e)

        for t_e in t_events:
            if t_e.date >= datetime.date.today() and t_e.regular_date <= datetime.date.today() + datetime.timedelta(days=t.assign_for_days) and t_e.assigned_persons==[] and t_e.persons_needed>0 and t_e.assignment_errors==[]:
                to_be_assigned_events.append(t_e)
                pp.pprint(t_e.date)

    events = sorted(events, key=lambda x: x.date)

    for n in notes:
        all_concerned_events = events.copy()
        if n.task_types:
            all_concerned_events = [event for event in all_concerned_events if event.task_type in n.task_types]
        skip_event_numbers = 0
        if all_concerned_events:
            next_event, note_number_in_time_period, note_time_period_start_date, skip_event_numbers = find_next_event(note=n, all_concerned_events=all_concerned_events, skip_event_numbers=skip_event_numbers)
            test_number_a = 0
            while skip_event_numbers > 0:
                test_number_a += 1
                if test_number_a == 500:
                    print("While loop 7 in list_and_assign_events() ran 500 times")
                next_event, note_number_in_time_period, note_time_period_start_date, skip_event_numbers = find_next_event(note=n, all_concerned_events=all_concerned_events, skip_event_numbers=skip_event_numbers)
            test_number_a = 0
            while next_event:
                test_number_a += 1
                if test_number_a == 50:
                    print("While loop 8 in list_and_assign_events() ran 50 times")
                    break
                if next_event.note and next_event.note != "":
                    next_event.note += "; "
                else:
                    next_event.note = ""
                next_event.note += n.message
                next_event.note_types.append(n)
                next_event.note_numbers_in_time_period.append(note_number_in_time_period)
                if next_event not in newly_calculated_events:
                    events_with_newly_attached_note.append(next_event)
                if note_time_period_start_date:
                    next_event.note_time_period_start_dates.append(note_time_period_start_date)
                skip_event_numbers = 0
                next_event, note_number_in_time_period, note_time_period_start_date, skip_event_numbers = find_next_event(note=n, all_concerned_events=all_concerned_events, skip_event_numbers=skip_event_numbers)
                test_number_b = 0
                while skip_event_numbers > 0:
                    test_number_b += 1
                    if test_number_b == 500:
                        print("While loop 9 in list_and_assign_events() ran 500 times")
                    next_event, note_number_in_time_period, note_time_period_start_date, skip_event_numbers = find_next_event(note=n, all_concerned_events=all_concerned_events, skip_event_numbers=skip_event_numbers)

    newly_listed_events = [event for event in newly_calculated_events if event.regular_date <= datetime.date.today() + datetime.timedelta(days=event.task_type.list_for_days)]
    newly_listed_events = sorted(newly_listed_events, key=lambda x: x.date)
    all_events = events.copy()
    events = [event for event in all_events if event.regular_date <= datetime.date.today() + datetime.timedelta(days=event.task_type.list_for_days)]
    events = sorted(events, key=lambda x: x.date)
    
    for to_be_assigned_event in to_be_assigned_events:
        for p in range(to_be_assigned_event.capable_persons_needed):
            choose_person(to_be_assigned_event=to_be_assigned_event, only_if_capable=True)
        for p in range(to_be_assigned_event.persons_needed - to_be_assigned_event.capable_persons_needed):
            choose_person(to_be_assigned_event=to_be_assigned_event)
        newly_assigned_events.append(to_be_assigned_event)

def read_message_strings(participant):
    if participant.language:
        language = participant.language
    else:
        language = default_language
    if not os.path.exists('locales/'+language):
        print("Locales for "+str(language)+" not found, using en instead.")
        language = 'en'
    with open('locales/'+language+'/locales.json', encoding='utf-8') as json_file:
        return json.load(json_file), language

def days_ago(strings, event):
    number_of_days_difference = (datetime.date.today() - event.date).days
    if number_of_days_difference == 0:
        days_ago = strings['today']
    elif number_of_days_difference == 1:
        days_ago = strings['yesterday']
    elif number_of_days_difference > 1:
        days_ago = strings['x days ago'].format(number_of_days_difference=number_of_days_difference)
    else:
        days_ago = "error: Task's date higher than today's date"
    return days_ago

def in_days(strings, event):
    number_of_days_difference = event.date - datetime.date.today()
    if number_of_days_difference.days == 0:
        in_days = strings['today']+","
    elif number_of_days_difference.days == 1:
        in_days = strings['tomorrow']+","
    elif number_of_days_difference.days > 1 and number_of_days_difference.days < 7:
        in_days = strings['next']
    elif number_of_days_difference.days >= 7:
        in_days = strings['on']
    else:
        in_days = "error: Today's date higher than task's date"
    return in_days

def day_days(strings, number_of_days):
    if number_of_days == 1:
        return strings['day']
    elif number_of_days > 1 or number_of_days == 0:
        return strings['days']
    else:
        return 'error: Negative number of days set for sending reminder'

def assignment_notification_title(participant, event):
    strings, language = read_message_strings(participant)
    message = strings['assignment_notification_title'].format(task_name=event.task_type.name, event_date=babel.dates.format_date(event.date, locale=language))
    return message

def reminder_title(participant, event):
    strings, language = read_message_strings(participant)
    message = strings['reminder_title'].format(task_name=event.task_type.name, event_date=babel.dates.format_date(event.date, locale=language))
    return message

def check_up_title(participant, event):
    strings, language = read_message_strings(participant)
    message = strings['check_up_title'].format(task_name=event.task_type.name, days_ago=days_ago(strings, event))
    return message

def other_assigned_persons_str(p, e, strings):
    persons = [participant for participant in e.assigned_persons if participant != p]
    if not persons:
        return ""
    else:
        if len(persons) == 1:
            other_assigned_persons_list = persons[0].name
        elif len(persons) == 2:
            other_assigned_persons_list = persons[0].name + strings['and'] + persons[1].name
        else:
            other_assigned_persons_list = persons[0].name
            middle_persons = persons.copy()
            middle_persons.pop(0)
            middle_persons.pop(-1)
            for o_p in middle_persons:
                other_assigned_persons_list += ", " + o_p.name
            other_assigned_persons_list += strings['oxford_comma'] + strings['and'] + persons[-1].name
        return strings['other_assigned_persons'].format(other_assigned_persons_list=other_assigned_persons_list)

def event_notes_str(e, strings):
    please_note = ""
    if e.task_type.note:
        please_note = strings['please_note'] + e.task_type.note + "\n"
    please_note_for_this_event = ""
    if e.note:
        event_notes_separated = python_list_from_semicolon_separated_list(any_list=e.note)
        if len(event_notes_separated) > 1:
            event_notes = ""
            for note in event_notes_separated:
                gap = ""
                if note[0] != " ":
                    gap = " "
                event_notes += "-" + gap + note + "\n"
            please_note_for_this_event = strings['please_note_for_this_event'] + "\n" + event_notes
        else:
            please_note_for_this_event = strings['please_note_for_this_event'] + e.note + "\n"
    return please_note, please_note_for_this_event

def assignment_notification_content(participant, event):
    strings, language = read_message_strings(participant)
    other_assigned_persons = other_assigned_persons_str(p=participant, e=event, strings=strings)
    please_note, please_note_for_this_event = event_notes_str(e=event, strings=strings)
    message = strings['hello'].format(participant_name=participant.name) + "\n" + "\n" + \
        strings['assignment_notification_text'].format(other_assigned_persons=other_assigned_persons, task_name=event.task_type.name, in_days=in_days(strings, event), event_date=babel.dates.format_date(event.date, format='full', locale=language), reminder_days_before=int(event.task_type.reminder_days_before), day_days=day_days(strings, int(event.task_type.reminder_days_before))) + "\n" + \
        strings['substitution_note'] + "\n" + \
        please_note + please_note_for_this_event + \
        "\n" + strings['bye'].format(task_group_name=task_group_name) + "\n" + \
        calc['host'] + "/=" + calc['page']
    return message

def reminder_content(participant, event):
    strings, language = read_message_strings(participant)
    other_assigned_persons = other_assigned_persons_str(p=participant, e=event, strings=strings)
    please_note, please_note_for_this_event = event_notes_str(e=event, strings=strings)
    message = strings['hello'].format(participant_name=participant.name) + "\n" + "\n" + \
        strings['reminder_text'].format(in_days=in_days(strings, event), other_assigned_persons=other_assigned_persons, task_name=event.task_type.name, event_date=babel.dates.format_date(event.date, format='full', locale=language)) + "\n" + \
        strings['substitution_note'] + "\n" + \
        please_note + please_note_for_this_event + \
        "\n" + strings['bye'].format(task_group_name=task_group_name) + "\n" + \
        calc['host'] + "/=" + calc['page']
    return message

def check_up_content(participant, event):
    strings, language = read_message_strings(participant)
    other_assigned_persons = other_assigned_persons_str(p=participant, e=event, strings=strings)
    message = strings['hello'].format(participant_name=participant.name) + "\n" + "\n" + \
        strings['check_up_text'].format(other_assigned_persons=other_assigned_persons, task_name=event.task_type.name, event_date=babel.dates.format_date(event.date, format='full', locale=language)) + "\n" + \
        "\n" + strings['bye'].format(task_group_name=task_group_name) + "\n" + \
        calc['host'] + "/=" + calc['page']
    return message

def send_assignment_notifications():
    for e in newly_assigned_events:
        for a_p in e.assigned_persons:
            if a_p.contact_info:
                title = assignment_notification_title(participant=a_p, event=e)
                content = assignment_notification_content(participant=a_p, event=e)
                fsc.sendMailToRecipients([int(a_p.contact_info)], {"subject":title, "body":content})

def send_reminders():
    global events
    events_to_be_reminded_of = [event for event in events if event.date >= datetime.date.today() and event.date <= datetime.date.today() + datetime.timedelta(days=event.task_type.reminder_days_before) and event.reminders_sent == False]
    for e in events_to_be_reminded_of:
        if e.assigned_persons:
            for a_p in e.assigned_persons:
                if a_p.contact_info:
                    title = reminder_title(participant=a_p, event=e)
                    content = reminder_content(participant=a_p, event=e)
                    fsc.sendMailToRecipients([int(a_p.contact_info)], {"subject":title, "body":content})
            e.reminders_sent = True

def send_check_ups():
    global events
    events_to_be_checked_up_on = [event for event in events if event.date < datetime.date.today() and event.check_ups_sent == False]
    for e in events_to_be_checked_up_on:
        if e.assigned_persons:
            for a_p in e.assigned_persons:
                if a_p.contact_info:
                    title = check_up_title(participant=a_p, event=e)
                    content = check_up_content(participant=a_p, event=e)
                    fsc.sendMailToRecipients([int(a_p.contact_info)], {"subject":title, "body":content})
            e.check_ups_sent = True

def reset_global_values():
    global calc
    calc = {}
    global events
    events = []
    global participants
    participants = []
    global tasks
    tasks = []
    global notes
    notes = []
    global newly_calculated_events
    newly_calculated_events = []
    global newly_listed_events
    newly_listed_events = []
    global newly_assigned_events
    newly_assigned_events = []
    global events_with_newly_attached_note
    events_with_newly_attached_note = []
    global default_language
    default_language = "en"
    global task_group_name
    task_group_name = "Task group"
    global recent_events_factor
    recent_events_factor = 0.8
    global header_lines
    header_lines = 2
    global capable_after_task_count
    capable_after_task_count = 0
    global save_backup_before_for_sheet_nos
    save_backup_before_for_sheet_nos = []
    global save_backup_after_for_sheet_nos
    save_backup_after_for_sheet_nos = []

def run_script_for_calc(calc_config):
    set_calc_data(calc_config)
    load_objects()
    if save_backup_before_for_sheet_nos:
        save_backup(sheet_nos=save_backup_before_for_sheet_nos, note="before")
    count_tasks()
    list_and_assign_events()
    update_ethercalc()
    send_assignment_notifications()
    send_reminders()
    send_check_ups()
    update_ethercalc_messages_sent()
    relock_cells()
    if save_backup_after_for_sheet_nos:
        save_backup(sheet_nos=save_backup_after_for_sheet_nos, note="after")
    reset_global_values()

def set_calc_data(config):
    global calc
    calc['host'] = config['host']
    calc['page'] = config['page']
    calc['name'] = config['name']
    return calc

def get_calc_configs():
    hosts = os.environ['TR_CALC_HOST'].split(';')
    pages = os.environ['TR_CALC_PAGE'].split(';')
    names = os.environ['TR_CALC_NAME'].split(';')
    if (len(hosts) == len(pages) == len(names)):
        return [dict(zip(('host','page','name'),(item,pages[i],names[i]))) for i,item in enumerate(hosts)]
    
    raise ValueError('Hosts, pages and names have to be the same sice')

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Enter Main()")

    calc_configs = get_calc_configs()
    for config in calc_configs:
        run_script_for_calc(config)

    fsc.logout()

if __name__== "__main__":
    main()
