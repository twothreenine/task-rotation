#!/usr/bin/env python3
import ethercalc
import json
import logging
import pprint
import argparse
import sys
import inspect
import datetime
import random

pp = pprint.PrettyPrinter(indent=4)
config_path = '_credentials/config.json'
newly_listed_events = []
newly_assigned_events = []

def retrieve_name(var): # for logging purposes
        """
        Gets the name of var. Does it from the out most frame inner-wards.
        :param var: variable to get name from.
        :return: string
        """
        for fi in reversed(inspect.stack()):
            names = [var_name for var_name, var_val in fi.frame.f_locals.items() if var_val is var]
            if len(names) > 0:
                return names[0]

def read_config():
    with open(config_path) as json_file:
        return json.load(json_file)

def excel_date(date1):
    delta = date1 - datetime.date(1899, 12, 30)
    return int(delta.days)

class Event:
    def __init__(self, date, type_id, event_no, regular_date, persons_needed, assigned_persons=[], note="", empty_row=""):
        self.date = date
        self.type_id = type_id
        self.event_no = event_no
        self.regular_date = regular_date
        self.persons_needed = persons_needed
        self.empty_row = empty_row
        self.assigned_persons = assigned_persons
        self.note = note

class Participant:
    def __init__(self, name, capable, active, old_task_count, task_count=0):
        self.name = name
        self.capable = capable
        self.active = active
        self.old_task_count = old_task_count
        self.task_count = task_count

class Task:
    def __init__(self, type_id, start, end, interval_days, persons_needed, assign_for_days, list_for_days, hide_from_days):
        self.type_id = type_id
        self.start = start
        self.end = end
        self.interval_days = interval_days
        self.persons_needed = persons_needed
        self.assign_for_days = assign_for_days
        self.list_for_days = list_for_days
        self.hide_from_days = hide_from_days

def load_ethercalc(sheet): # returns one of multiple sheets as a nested python list; for the first sheet: sheet=1
    config = read_config()
    logging.debug("remote host: " + config["host"] + " remote page: " + config["page"] + "." + str(sheet))
    return ethercalc.EtherCalc(config["host"]).export(config["page"] + "." + str(sheet))

""" Experiments to handle nested python lists, not used anymore """

def get_cell(table, coord): # returns the value of a cell, called by spreadsheet coordinates, in a "table" as returned by load_ethercalc 
    x,y = ethercalc.ss_to_xy(coord)
    logging.debug("called cell "+coord+ " of table "+retrieve_name(table))
    return table[y][x]

def set_cell(table, coord, value): # updates the value of a cell, called by spreadsheet coordinates, in a "table" as returned by load_ethercalc, to a given value
    x,y = ethercalc.ss_to_xy(coord)
    logging.debug("updated cell "+coord+ " of table "+retrieve_name(table)+" from "+str(get_cell(table, coord))+" to "+str(value))
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
    e = load_ethercalc(sheet=4)
    pp.pprint(e)
    set_cell(e,"E3","test")
    pp.pprint(e)

def get_vertical_cells_demo():
    e = load_ethercalc(sheet=1)
    cells = get_vertical_cells(e,"A3",10)
    pp.pprint(cells)

""" New class-based approach """

def load_objects(): # converts rows of the sheets events, participants and tasks into python objects; usually the header consists of 2 rows which have to be ignored (pop)
    events = []
    participants = []
    tasks = []
    particiant_list = load_ethercalc(sheet=2)
    for i in range(2):
        particiant_list.pop(0)
    while particiant_list[-1][0] == "":
        particiant_list.pop(-1)
    event_list = load_ethercalc(sheet=1)
    for i in range(2):
        event_list.pop(0)
    while event_list[-1][0] == None:
        event_list.pop(-1)
    task_list = load_ethercalc(sheet=4)
    for i in range(2):
        task_list.pop(0)
    while task_list[-1][0] == None:
        task_list.pop(-1)
    for row in particiant_list:
        p = Participant(name=row[0], capable=True, active=True, old_task_count=row[3])
        if row[1]=="0": p.capable=False
        if row[2]=="0": p.active=False
        participants.append(p)
    for row in event_list:
        assigned_persons = []
        for cell in row[8:13]:
            if cell != "" and cell and row[0]:
                matched = False
                for p in participants:
                    if p.name == cell:
                        assigned_persons.append(p)
                        matched = True
                        break
                if not matched:
                    print("Could not find any match for '"+str(cell)+"', assigned for task on "+str(row[0]))
        e = Event(date=row[0], type_id=row[1], event_no=row[2], regular_date=row[3], persons_needed=int(row[6]), empty_row=row[7], assigned_persons=assigned_persons, note=row[13])
        events.append(e)
    for row in task_list:
        t = Task(type_id=row[0], start=row[2], end=row[3], interval_days=row[4], persons_needed=int(row[5]), assign_for_days=row[6], list_for_days=row[7], hide_from_days=row[8])
        tasks.append(t)
    return events, participants, tasks

def update_ethercalc(events, participants):
    # update participant.task_count if different and set participant.capable to True if False and task_count > old_task_count
    # update all events from the first newly listed event on; before that, update assigned persons for newly assigned events

    e = ethercalc.EtherCalc(read_config()["host"])
    e_page = read_config()["page"]+".1"
    p_page = read_config()["page"]+".2"
    header_lines = 2
    for p in participants:
        if not p.task_count == p.old_task_count:
            x = participants.index(p) + 1 + header_lines
            e.command(p_page, ["set D"+str(x)+" value n "+str(p.task_count)])
            if not p.capable and p.task_count > p.old_task_count:
                e.command(p_page, ["set B"+str(x)+" constant nl 1 TRUE"])

    if newly_listed_events:
        earliest_newly_listed_event = min(newly_listed_events, key=lambda x: x.date)
        events_to_keep = [event for event in events if event.date < earliest_newly_listed_event.date]
        events_to_overwrite = [event for event in events if event not in events_to_keep]
        for e_o in events_to_overwrite:
            e.command(e_page, ["set A"+str(events.index(e_o)+1+header_lines)+" value n "+str(e_o.date)])
            e.command(e_page, ["set B"+str(events.index(e_o)+1+header_lines)+" value n "+str(e_o.type_id)])
            e.command(e_page, ["set C"+str(events.index(e_o)+1+header_lines)+" value n "+str(e_o.event_no)])
            e.command(e_page, ["set D"+str(events.index(e_o)+1+header_lines)+" value n "+str(e_o.regular_date)])
            e.command(e_page, ["set G"+str(events.index(e_o)+1+header_lines)+" value n "+str(e_o.persons_needed)])
            e.command(e_page, ["set H"+str(events.index(e_o)+1+header_lines)+" text t "+str(e_o.empty_row)])
            e.command(e_page, ["set N"+str(events.index(e_o)+1+header_lines)+" text t "+str(e_o.note)])

    for e_a in newly_assigned_events:
        e.command(e_page, ["set I"+str(events.index(e_a)+1+header_lines)+" text t "+e_a.assigned_persons[0].name])
        if len(e_a.assigned_persons) > 1:
            e.command(e_page, ["set J"+str(events.index(e_a)+1+header_lines)+" text t "+e_a.assigned_persons[1].name])
        if len(e_a.assigned_persons) > 2:
            e.command(e_page, ["set K"+str(events.index(e_a)+1+header_lines)+" text t "+e_a.assigned_persons[2].name])
        if len(e_a.assigned_persons) > 3:
            e.command(e_page, ["set L"+str(events.index(e_a)+1+header_lines)+" text t "+e_a.assigned_persons[3].name])
        if len(e_a.assigned_persons) > 4:
            e.command(e_page, ["set M"+str(events.index(e_a)+1+header_lines)+" text t "+e_a.assigned_persons[4].name])

def count_tasks(events, participants): # calculating how many tasks each participant has done
    past_events = [event for event in events if event.date < excel_date(datetime.date.today())]
    for e in past_events:
        for a_p in e.assigned_persons:
            a_p.task_count += 1
            if not a_p.capable and a_p.task_count > a_p.old_task_count:
                a_p.capable = True

def list_and_assign_events(events, participants, tasks):
    to_be_assigned_events = []
    for t in tasks:
        t_events = []
        for e in events:
            if e.type_id == t.type_id:
                t_events.append(e)
        t_events = sorted(t_events, key=lambda e: (e.regular_date))
        if not t_events:
            new_e = Event(date=t.start, type_id=t.type_id, event_no=1, regular_date=t.start, persons_needed=t.persons_needed)
            t_events.append(new_e)
            events.append(new_e)
            newly_listed_events.append(new_e)
        while t_events[-1].regular_date <= excel_date(datetime.date.today()) + t.list_for_days - t.interval_days:
            new_date = t_events[-1].regular_date + t.interval_days
            new_e = Event(date=new_date, type_id=t.type_id, event_no=t_events[-1].event_no+1, regular_date=new_date, persons_needed=t.persons_needed)
            t_events.append(new_e)
            events.append(new_e)
            newly_listed_events.append(new_e)
        for t_e in t_events:
            if t_e.date > excel_date(datetime.date.today()) and t_e.regular_date <= excel_date(datetime.date.today()) + t.assign_for_days and t_e.assigned_persons==[] and t_e.persons_needed>0:
                to_be_assigned_events.append(t_e)
    active_participants = [participant for participant in participants if participant.active]
    capable_active_participants = [participant for participant in active_participants if participant.capable]
    for e in to_be_assigned_events:
        recent_events_count = 0.8 * len(capable_active_participants)
        recently_assigned_capable_participants = []
        assigned_events = sorted([event for event in events if event.assigned_persons], key=lambda x: x.date, reverse=True)
        for a_e in assigned_events:
            recent_events_count -= len(a_e.assigned_persons)
            if recent_events_count < 0:
                break
            for ap in a_e.assigned_persons:
                recently_assigned_capable_participants.append(ap)
        favorable_participants = [participant for participant in capable_active_participants if participant not in recently_assigned_capable_participants]
        lowest_task_count = min(favorable_participants, key=lambda p: p.task_count).task_count
        most_favorable_participants = [participant for participant in favorable_participants if participant.task_count == lowest_task_count]
        if most_favorable_participants:
            e.assigned_persons.append(random.choice(most_favorable_participants))
        else:
            lowest_task_count = min(capable_active_participants, key=lambda p: p.task_count).task_count
            most_favorable_participants = [participant for participant in capable_active_participants if participant.task_count == lowest_task_count]
            if most_favorable_participants:
                e.assigned_persons.append(random.choice(most_favorable_participants))
            else:
                print("Could not assign person 1 for task on "+e.date+": No capable active participants!")
        for p in range(e.persons_needed - 1):
            recent_events_count = 0.8 * len(active_participants)
            recently_assigned_participants = []
            assigned_events = sorted([event for event in events if event.assigned_persons], key=lambda x: x.date, reverse=True)
            for a_e in assigned_events:
                recent_events_count -= len(a_e.assigned_persons)
                if recent_events_count < 0:
                    break
                for ap in a_e.assigned_persons:
                    recently_assigned_participants.append(ap)
            favorable_participants = [participant for participant in active_participants if participant not in recently_assigned_participants and participant not in e.assigned_persons]
            lowest_task_count = min(favorable_participants, key=lambda p: p.task_count).task_count
            most_favorable_participants = [participant for participant in favorable_participants if participant.task_count == lowest_task_count]
            if most_favorable_participants:
                e.assigned_persons.append(random.choice(most_favorable_participants))
            else:
                possible_participants = [participant for participant in active_participants if participant not in e.assigned_persons]
                lowest_task_count = min(possible_participants, key=lambda p: p.task_count).task_count
                most_favorable_participants = [participant for participant in possible_participants if participant.task_count == lowest_task_count]
                if most_favorable_participants:
                    e.assigned_persons.append(random.choice(most_favorable_participants))
                else:
                    print("Could not assign person for task on "+e.date+": No (other) active participants!")
        newly_assigned_events.append(e)

    events = sorted(events, key=lambda x: x.date)

    for e in newly_assigned_events: # for testing
        pp.pprint(e.date)
        for ap in e.assigned_persons:
            pp.pprint(ap.name)

    # c = e.cells(read_config()["page"]+".1","A23")
    # pp.pprint(c["bgcolor"])
    # c2 = e.cells(read_config()["page"]+".1","A24")
    # pp.pprint(c2["bgcolor"])
    # e.command(page, ["set A23 color rgb(136, 136, 136)",
    #                  "set A23 bgcolor"])
    # e.command(page, ["set A23 color",
    #                  "set A23 bgcolor rgb(255, 255, 0)"])

def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Enter Main()")

    events, participants, tasks = load_objects()
    count_tasks(events=events, participants=participants)
    list_and_assign_events(events=events, participants=participants, tasks=tasks)
    update_ethercalc(events=events, participants=participants)
  
if __name__== "__main__":
    main()