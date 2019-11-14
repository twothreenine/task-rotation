#!/usr/bin/env python3
import ethercalc
import json
import logging
import pprint
import datetime
import random
import babel.dates

pp = pprint.PrettyPrinter(indent=4)
config_path = '_credentials/config.json'
newly_listed_events = []
newly_assigned_events = []
default_language = "en"
task_group_name = "Task group"
recent_events_factor = 0.8
header_lines = 2

def read_config():
    with open(config_path) as json_file:
        return json.load(json_file)

config = read_config()

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

class Event:
    def __init__(self, date, task_type, event_no, regular_date, persons_needed, capable_persons_needed, assigned_persons=[], note="", assignment_errors=[], reminders_sent=False, check_ups_sent=False):
        self.date = date
        self.task_type = task_type
        self.event_no = event_no
        self.regular_date = regular_date
        self.persons_needed = persons_needed
        self.capable_persons_needed = capable_persons_needed
        self.assigned_persons = assigned_persons.copy()
        self.note = note
        self.assignment_errors = assignment_errors.copy()
        self.reminders_sent_before = reminders_sent
        self.reminders_sent = reminders_sent
        self.check_ups_sent_before = check_ups_sent
        self.check_ups_sent = check_ups_sent

class Participant:
    def __init__(self, name, capable, active, entry_date, old_task_count, language=None):
        self.name = name
        self.capable = capable
        self.active = active
        self.entry_date = entry_date
        self.active_until = False
        self.old_task_count = old_task_count
        self.task_count = 0
        self.task_count_per_days_since_entry = False
        self.language = language

class Task:
    def __init__(self, type_id, name, start, end, interval_days, persons_needed, capable_persons_needed, assign_for_days, list_for_days, hide_from_days, reminder_days_before, note):
        self.type_id = type_id
        self.name = name
        self.start = start
        self.end = end
        self.interval_days = interval_days
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

def load_ethercalc(sheet): # returns one of multiple sheets as a nested python list; for the first sheet: sheet=1
    logging.debug("remote host: " + config["host"] + " remote page: " + config["page"] + "." + str(sheet))
    return ethercalc.EtherCalc(config["host"]).export(config["page"] + "." + str(sheet))

""" Experiments to handle nested python lists, not used anymore """

def get_cell(table, coord): # returns the value of a cell, called by spreadsheet coordinates, in a "table" as returned by load_ethercalc 
    x,y = ethercalc.ss_to_xy(coord)
    # logging.debug("called cell "+coord+ " of table "+retrieve_name(table))
    return table[y][x]

def set_cell(table, coord, value): # updates the value of a cell, called by spreadsheet coordinates, in a "table" as returned by load_ethercalc, to a given value
    x,y = ethercalc.ss_to_xy(coord)
    # logging.debug("updated cell "+coord+ " of table "+retrieve_name(table)+" from "+str(get_cell(table, coord))+" to "+str(value))
    table[y][x] = value

def get_vertical_cells(table, coord, count): # returns a vertical range of cells as a list
    x,y = ethercalc.ss_to_xy(coord)
    cells = []
    for i in range(count):
        cells.append(table[y+i][x])
    return cells

def get_horizontal_cells(table, coord, count): # returns a horizontal range of cells as a list
    x,y = ethercalc.ss_to_xy(coord)
    cells = []
    for i in range(count):
        cells.append(table[y][x+i])
    return cells

def get_set_demo(): # demonstrates the methods get_cell and set_cell
    e = load_ethercalc(sheet=3)
    pp.pprint(e)
    set_cell(e,"E3","test")
    pp.pprint(e)

def get_vertical_cells_demo():
    e = load_ethercalc(sheet=1)
    cells = get_vertical_cells(e,"A3",10)
    pp.pprint(cells)

""" New class-based approach """

def load_objects(event_sheet_no=1, participant_sheet_no=2, task_sheet_no=3, settings_sheet_no=4): # converts rows of the sheets events, participants and tasks into python objects; usually the header consists of 2 rows which have to be ignored (pop)
    settings_list = load_ethercalc(sheet=settings_sheet_no)
    for i in range(2):
        settings_list.pop(0)
    if settings_list[0][1]:
        global default_language
        default_language = settings_list[0][1]
    if settings_list[1][1]:
        global task_group_name
        task_group_name = settings_list[1][1]
    if settings_list[2][1]:
        global recent_events_factor
        recent_events_factor = settings_list[2][1]
        print("recent events factor = "+str(recent_events_factor))
    if settings_list[3][1]:
        global header_lines
        header_lines = int(settings_list[3][1])
        print("header lines = "+str(header_lines))
    events = []
    participants = []
    tasks = []
    particiant_list = load_ethercalc(sheet=participant_sheet_no)
    for i in range(2):
        particiant_list.pop(0)
    while particiant_list[-1][0] == "":
        particiant_list.pop(-1)
    event_list = load_ethercalc(sheet=event_sheet_no)
    for i in range(2):
        event_list.pop(0)
    while event_list and event_list[-1] and event_list[-1][0] == None:
        event_list.pop(-1)
    task_list = load_ethercalc(sheet=task_sheet_no)
    for i in range(2):
        task_list.pop(0)
    while task_list[-1][0] == None:
        task_list.pop(-1)
    for row in particiant_list:
        try:
            old_task_count = int(row[3])
        except TypeError:
            old_task_count = 0
        except:
            raise
        p = Participant(name=row[0], capable=True, active=True, entry_date=read_date(row[4]), old_task_count=old_task_count, language=row[6])
        if row[1]=="0": p.capable=False
        if row[2]=="0": p.active=False
        if row[4]!="": p.active_until=read_date(row[5])
        participants.append(p)
    for row in task_list:
        t = Task(type_id=row[0], name=row[1], start=read_date(row[2]), end=read_date(row[3]), interval_days=row[4], persons_needed=int(row[5]), capable_persons_needed=int(row[6]), assign_for_days=row[7], list_for_days=row[8], hide_from_days=row[9], reminder_days_before=row[10], note=row[11])
        tasks.append(t)
    for row in event_list:
        assigned_persons = []
        assignment_errors = []
        for cell in row[8:13]:
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
        if row[14] == "1": reminders_sent = True
        check_ups_sent = False
        if row[15] == "1": check_ups_sent = True
        e = Event(date=read_date(row[0]), task_type=task_type, event_no=row[2], regular_date=read_date(row[3]), persons_needed=int(row[6]), capable_persons_needed=int(row[7]), assigned_persons=assigned_persons, note=row[13], assignment_errors=assignment_errors, reminders_sent=reminders_sent, check_ups_sent=check_ups_sent)
        events.append(e)
    return events, participants, tasks

def assigned_persons_column_letter(person_count):
    if person_count == 0:
        column_letter="I"
    elif person_count == 1:
        column_letter="J"
    elif person_count == 2:
        column_letter="K"
    elif person_count == 3:
        column_letter="L"
    elif person_count == 4:
        column_letter="M"
    return column_letter

def update_ethercalc_assignments(events, ecalc, e_page, event_to_assign):
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

def update_ethercalc(events, participants):
    # update participant.task_count if different and set participant.capable to True if False and task_count > old_task_count
    # update all events from the first newly listed event on; before that, update assigned persons for newly assigned events

    e = ethercalc.EtherCalc(config["host"])
    e_page = config["page"]+".1"
    p_page = config["page"]+".2"

    # updating participants' task counts and capability
    for p in participants:
        if not p.task_count == p.old_task_count:
            x = participants.index(p) + 1 + header_lines
            e.command(p_page, ["set D"+str(x)+" value n "+str(p.task_count)])
            if not p.capable and p.task_count > p.old_task_count:
                e.command(p_page, ["set B"+str(x)+" constant nl 1 TRUE"])

    # listing events
    if newly_listed_events:
        earliest_newly_listed_event = min(newly_listed_events, key=lambda x: x.date)
        events_to_keep = [event for event in events if event.date < earliest_newly_listed_event.date]
        events_to_overwrite = [event for event in events if event not in events_to_keep]
        for e_o in events_to_overwrite:
            e.command(e_page, ["set A"+str(events.index(e_o)+1+header_lines)+" constant nd "+str(excel_date(e_o.date))+" "+str(e_o.date)])
            e.command(e_page, ["set B"+str(events.index(e_o)+1+header_lines)+" value n "+str(e_o.task_type.type_id)])
            e.command(e_page, ["set C"+str(events.index(e_o)+1+header_lines)+" value n "+str(e_o.event_no)])
            e.command(e_page, ["set D"+str(events.index(e_o)+1+header_lines)+" constant nd "+str(excel_date(e_o.regular_date))+" "+str(e_o.regular_date)])
            e.command(e_page, ["copy E"+str(header_lines+1)+" formulas"])
            e.command(e_page, ["paste E"+str(events.index(e_o)+1+header_lines)+" formulas"])
            e.command(e_page, ["copy F"+str(header_lines+1)+" formulas"])
            e.command(e_page, ["paste F"+str(events.index(e_o)+1+header_lines)+" formulas"])
            e.command(e_page, ["set G"+str(events.index(e_o)+1+header_lines)+" value n "+str(e_o.persons_needed)])
            e.command(e_page, ["set H"+str(events.index(e_o)+1+header_lines)+" value n "+str(e_o.capable_persons_needed)])
            e.command(e_page, ["set N"+str(events.index(e_o)+1+header_lines)+" text t "+str(e_o.note)])

    # assigning events
    for e_a in newly_assigned_events:
        update_ethercalc_assignments(events=events, ecalc=e, e_page=e_page, event_to_assign=e_a)

    # events with assignment errors
    for e_e in [event for event in events if event.assignment_errors and event not in newly_assigned_events]:
        update_ethercalc_assignments(events=events, ecalc=e, e_page=e_page, event_to_assign=e_e)

    # events with reminders resp. check ups sent
    for e_r in [event for event in events if event.reminders_sent == True and event.reminders_sent_before == False]:
        e.command(e_page, ["set O"+str(events.index(e_r)+1+header_lines)+" constant nl 1 TRUE"])
    for e_c in [event for event in events if event.check_ups_sent == True and event.check_ups_sent_before == False]:
        e.command(e_page, ["set P"+str(events.index(e_c)+1+header_lines)+" constant nl 1 TRUE"])

    # formatting
    past_events = [event for event in events if event.date < datetime.date.today()]
    events_to_hide = [event for event in events if event.date < datetime.date.today() - datetime.timedelta(days=event.task_type.hide_from_days)]
    events_to_mark = [event for event in events if event.date >= datetime.date.today() and event.regular_date <= datetime.date.today() + datetime.timedelta(days=event.task_type.assign_for_days)]
    if events:
        e.command(e_page, ["set A"+str(1+header_lines)+":N"+str(header_lines+len(events))+" bgcolor rgb(255, 255, 255)"])
        # e.command(e_page, ["set "+str(1+header_lines)+":"+str(header_lines+len(events))+" hide"])
        e.command(e_page, ["set A"+str(1+header_lines)+":N"+str(header_lines+len(events))+" color rgb(0, 0, 0)"])
    if past_events:
        e.command(e_page, ["set A"+str(1+header_lines)+":N"+str(header_lines+len(past_events))+" color rgb(153, 153, 153)"])
    for event in events_to_hide:
        e.command(e_page, ["set "+str(1+header_lines+events.index(event))+" hide yes"])
    for event in events_to_mark:
        row = str(header_lines+events.index(event)+1)
        e.command(e_page, ["set A"+row+":N"+row+" bgcolor rgb(255, 255, 0)"])

def count_tasks(events, participants): # calculating how many tasks each participant has done
    past_events = [event for event in events if event.date < datetime.date.today()]
    for e in past_events:
        for a_p in e.assigned_persons:
            a_p.task_count += 1
            if not a_p.capable and a_p.task_count > a_p.old_task_count:
                a_p.capable = True
    for p in participants:
        delta = datetime.date.today() - p.entry_date
        p.task_count_per_days_since_entry = p.task_count / int(delta.days)

def choose_person(participants, events, to_be_assigned_event, only_if_capable=False):
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
            print(ap.name+" added to recently_assigned_possible_participants")
    favorable_participants = [participant for participant in possible_participants if participant not in recently_assigned_possible_participants and participant not in to_be_assigned_event.assigned_persons]
    if not favorable_participants:
        favorable_participants = [participant for participant in possible_participants if participant not in to_be_assigned_event.assigned_persons]
    if favorable_participants:
        lowest_task_count_ratio = min(favorable_participants, key=lambda p: p.task_count_per_days_since_entry).task_count_per_days_since_entry
        most_favorable_participants = [participant for participant in favorable_participants if participant.task_count_per_days_since_entry == lowest_task_count_ratio]
        person = random.choice(most_favorable_participants)
        print("Test: Assigned "+person.name+" to task on "+str(to_be_assigned_event.date))
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

def list_and_assign_events(events, participants, tasks):
    to_be_assigned_events = []
    for t in tasks:
        t_events = sorted([event for event in events if event.task_type == t], key=lambda e: (e.regular_date))
        ended = False
        if t.end:
            if t.end < datetime.date.today():
                ended = True
        if not t_events and t.start <= datetime.date.today() + datetime.timedelta(days=t.list_for_days) and not ended:
            new_e = Event(date=t.start, task_type=t, event_no=1, regular_date=t.start, persons_needed=t.persons_needed, capable_persons_needed=t.capable_persons_needed)
            t_events.append(new_e)
            events.append(new_e)
            newly_listed_events.append(new_e)
        if t_events:
            while t_events[-1].regular_date <= datetime.date.today() + datetime.timedelta(days=t.list_for_days) - datetime.timedelta(days=t.interval_days):
                new_date = t_events[-1].regular_date + datetime.timedelta(days=t.interval_days)
                if t.end:
                    if new_date > t.end:
                        break
                new_e = Event(date=new_date, task_type=t, event_no=t_events[-1].event_no+1, regular_date=new_date, persons_needed=t.persons_needed, capable_persons_needed=t.capable_persons_needed)
                
                t_events.append(new_e)
                events.append(new_e)
                newly_listed_events.append(new_e)
        for t_e in t_events:
            if t_e.date >= datetime.date.today() and t_e.regular_date <= datetime.date.today() + datetime.timedelta(days=t.assign_for_days) and t_e.assigned_persons==[] and t_e.persons_needed>0 and t_e.assignment_errors==[]:
                to_be_assigned_events.append(t_e)
    
    for to_be_assigned_event in to_be_assigned_events:
        for p in range(to_be_assigned_event.capable_persons_needed):
            choose_person(participants=participants, events=events, to_be_assigned_event=to_be_assigned_event, only_if_capable=True)
        for p in range(to_be_assigned_event.persons_needed - to_be_assigned_event.capable_persons_needed):
            choose_person(participants=participants, events=events, to_be_assigned_event=to_be_assigned_event)
        newly_assigned_events.append(to_be_assigned_event)

    events = sorted(events, key=lambda x: x.date)

    for event in newly_assigned_events: # for testing
        print("Task on "+str(event.date))
        for ap in event.assigned_persons:
            print(ap.name)

    # c = e.cells(read_config()["page"]+".1","A23")
    # pp.pprint(c["bgcolor"])
    # c2 = e.cells(read_config()["page"]+".1","A24")
    # pp.pprint(c2["bgcolor"])
    # e.command(page, ["set A23 color rgb(136, 136, 136)",
    #                  "set A23 bgcolor"])
    # e.command(page, ["set A23 color",
    #                  "set A23 bgcolor rgb(255, 255, 0)"])

def read_message_strings(participant):
    if participant.language:
        language = participant.language
    else:
        language = default_language
    if language != 'en' and language != 'de_AT':
        print("Locales for "+str(language)+" not registered, using en instead.")
        language = 'en'
    with open('locales/'+language+'.json', encoding='utf-8') as json_file:
        return json.load(json_file), language

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
    message = strings['check_up_title'].format(task_name=event.task_type.name)
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

def assignment_notification_content(participant, event):
    strings, language = read_message_strings(participant)
    other_assigned_persons = other_assigned_persons_str(p=participant, e=event, strings=strings)
    message = strings['hello'].format(participant_name=participant.name) + "\n" + "\n" + \
        strings['assignment_notification_text'].format(other_assigned_persons=other_assigned_persons, task_name=event.task_type.name, event_date=babel.dates.format_date(event.date, format='full', locale=language), reminder_days_before=int(event.task_type.reminder_days_before)) + "\n" + \
        strings['substitution_note'] + "\n" + \
        "\n" + strings['bye'].format(task_group_name=task_group_name) + "\n" + \
        config['host'] + "/=" + config['page']
    return message

def reminder_content(participant, event):
    strings, language = read_message_strings(participant)
    other_assigned_persons = other_assigned_persons_str(p=participant, e=event, strings=strings)
    please_note = ""
    if event.task_type.note:
        please_note = strings['please_note'] + event.task_type.note + "\n"
    please_note_for_this_event = ""
    if event.note:
        please_note_for_this_event = strings['please_note_for_this_event'] + event.note + "\n"
    message = strings['hello'].format(participant_name=participant.name) + "\n" + "\n" + \
        strings['reminder_text'].format(other_assigned_persons=other_assigned_persons, task_name=event.task_type.name, event_date=babel.dates.format_date(event.date, format='full', locale=language)) + "\n" + \
        strings['substitution_note'] + "\n" + \
        please_note + please_note_for_this_event + \
        "\n" + strings['bye'].format(task_group_name=task_group_name) + "\n" + \
        config['host'] + "/=" + config['page']
    return message

def check_up_content(participant, event):
    strings, language = read_message_strings(participant)
    other_assigned_persons = other_assigned_persons_str(p=participant, e=event, strings=strings)
    message = strings['hello'].format(participant_name=participant.name) + "\n" + "\n" + \
        strings['check_up_text'].format(other_assigned_persons=other_assigned_persons, task_name=event.task_type.name) + "\n" + \
        "\n" + strings['bye'].format(task_group_name=task_group_name) + "\n" + \
        config['host'] + "/=" + config['page']
    return message

def send_assignment_notifications():
    for e in newly_assigned_events:
        for a_p in e.assigned_persons:
            print(assignment_notification_title(participant=a_p, event=e))
            print(assignment_notification_content(participant=a_p, event=e))

def send_reminders(events):
    events_to_be_reminded_of = [event for event in events if event.date >= datetime.date.today() and event.date <= datetime.date.today() + datetime.timedelta(days=event.task_type.reminder_days_before) and event.reminders_sent == False]
    for e in events_to_be_reminded_of:
        if e.assigned_persons:
            for a_p in e.assigned_persons:
                print(reminder_title(participant=a_p, event=e))
                print(reminder_content(participant=a_p, event=e))
            e.reminders_sent = True

def send_check_ups(events):
    events_to_be_checked_up_on = [event for event in events if event.date < datetime.date.today() and event.check_ups_sent == False]
    for e in events_to_be_checked_up_on:
        if e.assigned_persons:
            for a_p in e.assigned_persons:
                print(check_up_title(participant=a_p, event=e))
                print(check_up_content(participant=a_p, event=e))
            e.check_ups_sent = True

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Enter Main()")

    events, participants, tasks = load_objects()
    count_tasks(events=events, participants=participants)
    list_and_assign_events(events=events, participants=participants, tasks=tasks)
    send_assignment_notifications()
    send_reminders(events=events)
    send_check_ups(events=events)
    update_ethercalc(events=events, participants=participants)

    # events = []
    # for i in range(4):
    #     e = Event(date=0, task_type=0, event_no=0, regular_date=0, persons_needed=0, capable_persons_needed=0, assigned_persons=[], note=0, assignment_errors=[])
    #     events.append(e)
    # p1 = Participant(name=0, capable=0, active=0, old_task_count=0)
    # p2 = Participant(name=0, capable=0, active=0, old_task_count=0)
    # for e in events:
    #     e.assigned_persons.append(p1)
    #     e.assigned_persons.append(p2)
    # for e in events:
    #     pp.pprint(e.assigned_persons)

if __name__== "__main__":
    main()