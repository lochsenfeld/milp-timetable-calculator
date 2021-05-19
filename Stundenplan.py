#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pulp import *
from tabulate import tabulate
import itertools

################## INPUT DATA ##################

# Tage
days_cleartext = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
days = range(len(days_cleartext))

# Slots
slots_cleartext = ["1.", "2.", "3.", "4.", "5.", "6."]
slots = range(len(slots_cleartext))

# Klassen
classes_cleartext = ["1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b", "Fö"]
classes = range(len(classes_cleartext))

# Fächer
categories_cleartext = ["Sonstiges", "Englisch", "Förder",
                        "Sport", "Schwimmen", "Religion", "Religion ††", "Sport +"]
categories = range(len(categories_cleartext))

category_shorttext = ["", " 'E'", " 'FÖ'",
                      " 'Sp'", " 'Schw'", " 'Rel'", " 'Rel'", " 'Sp'"]

# Lehrer
teachers_cleartext = ["Wa", "Ka", "SB", "Si", "KE",
                      "Ba", "Ma", "Oc", "Gr", "Kl", "Ku", "Him"]
teachers = range(len(teachers_cleartext))
remedial_teacher = 10
conference_day = 0
conference_slot = 5

#! fächer: sport [alle], schwimmen, englisch, religion [1./2. alle sonst nicht alle]
teacherCategories = [
    [0, 5, 3, 7], [0, 5, 3, 7], [0, 5, 3, 7, 4], [0, 5, 3, 7, 4],
    [0, 5, 3, 7, 4], [0, 5, 3, 7, 4], [0, 5, 6, 3, 7, 4], [0, 5, 3, 7, 4],
    [0, 5, 6, 3, 7], [0, 5, 3, 7], [0, 5, 3, 7], [0, 5, 1, 3, 7]
]
teacherCategories[remedial_teacher].append(2)

sport_slots = {
    1: [0, 1],
    2: [0, 1]
}

swim_slots = {
    1: [0, 1],
    3: [3, 4],
    4: [0, 1]
}

class_categories_raw = [
    [19, 2, 0, 4, 0, 1, 0, 0],
    [19, 2, 0, 4, 0, 1, 0, 0],
    [17, 2, 0, 4, 2, 1, 0, 0],
    [17, 2, 0, 4, 2, 1, 0, 0],
    [20, 2, 0, 0, 0, 0, 1, 2],
    [18, 2, 0, 0, 2, 0, 1, 2],
    [20, 2, 0, 0, 0, 0, 1, 2],
    [20, 2, 0, 0, 0, 0, 1, 2],
    [0, 0, 10, 0, 0, 0, 0, 0]
]

class_categories = {}
for clazz in classes:
    for category in categories:
        class_categories[(clazz, category)
                         ] = class_categories_raw[clazz][category]

teacherLessons = [
    18, 14, 14, 28,
    19, 22, 24, 24,
    27, 26, 28, 23
]

classTeachers = {
    0: (0,),
    1: (1, 2),
    2: (3,),
    3: (4,),
    4: (5,),
    5: (6,),
    6: (7,),
    7: (8,),
    8: (remedial_teacher,)
}

classTeacherNames = [", ".join(map(lambda x: teachers_cleartext[x],
                                   classTeachers[clazz])) for clazz in classes]

teacherCombinations = list(itertools.combinations(
    teachers, 1)) + list(itertools.combinations(teachers, 2))
teacherCategoryCombinations = []
for combination in teacherCombinations:
    _categories = list(set(itertools.chain.from_iterable(
        [teacherCategories[teacher] for teacher in combination])))
    for category in _categories:
        # förder nicht in doppelbesetzung
        if category == 2 and len(combination) == 2:
            continue
        # * religion nicht in doppelbesetzung
        if category == 5 and len(combination) == 2:
            continue
        # * religion nicht in doppelbesetzung
        if category == 6 and len(combination) == 2:
            continue
        # * schwimmen MUSS in doppelbesetzung
        if category == 4 and len(combination) == 1:
            continue
        # * sport KEINE doppelbesetzung
        if category == 3 and len(combination) == 2:
            continue
        # * sport KEINE doppelbesetzung
        if category == 7 and len(combination) == 2:
            continue
        teacherCategoryCombinations.append({
            "teachers": combination,
            "category": category
        })
# TODO categoryLessons if teacherCategoryCombinations[lesson]["category"] == 5
# TODO teacherLessons if teacher in teacherCategoryCombinations[lesson]["teachers"]
lessons = range(len(teacherCategoryCombinations))

slot_combinations = {
    0: [0, 0, 0, 0, 0, 0],
    1: [1, 0, 0, 0, 0, 0],
    2: [0, 1, 0, 0, 0, 0],
    3: [0, 0, 1, 0, 0, 0],
    4: [0, 0, 0, 1, 0, 0],
    5: [0, 0, 0, 0, 1, 0],
    6: [0, 0, 0, 0, 0, 1],
    7: [1, 1, 0, 0, 0, 0],
    8: [0, 1, 1, 0, 0, 0],
    9: [0, 0, 1, 1, 0, 0],
    10: [0, 0, 0, 1, 1, 0],
    11: [0, 0, 0, 0, 1, 1],
    12: [1, 1, 1, 0, 0, 0],
    13: [0, 1, 1, 1, 0, 0],
    14: [0, 0, 1, 1, 1, 0],
    15: [0, 0, 0, 1, 1, 1],
    16: [1, 1, 1, 1, 0, 0],
    17: [0, 1, 1, 1, 1, 0],
    18: [0, 0, 1, 1, 1, 1],
    19: [1, 1, 1, 1, 1, 0],
    20: [0, 1, 1, 1, 1, 1],
    21: [1, 1, 1, 1, 1, 1],
}

last_slot_to_slot_combinations = {
    -1: (0,),
    0: (1,),
    1: (2, 7,),
    2: (3, 8, 12,),
    3: (4, 9, 13, 16,),
    4: (5, 10, 14, 17, 19,),
    5: (6, 11, 15, 18, 20, 21,),
}


school_end_slots = [-1, *slots]


n_slot_combinations = range(len(slot_combinations))

grade_levels = {
    0: (0, 1,),
    1: (2, 3,),
    2: (4, 5,),
    3: (6, 7,)
}

grade_levels_clear_text = {
    0: "erste",
    1: "zweite",
    2: "dritte",
    3: "vierte"
}

n_grade_levels = range(len(grade_levels))
################################################

##################  VARIABLES  ##########################
p_school_end_deviation = {
    (day, grade_level): LpVariable("Stundenabweichung der Stufe %s am %s" %
                                   (grade_levels_clear_text[grade_level], days_cleartext[day]), cat=LpInteger, lowBound=0)
    for grade_level in n_grade_levels
    for day in days
}

class_teached_by = {
    (clazz, teacher): LpVariable("Klasse %s wird in der Woche von %s unterrichtet"
                                 % (classes_cleartext[clazz],
                                    teachers_cleartext[teacher],
                                    ), cat=LpBinary)
    for clazz in classes
    for teacher in teachers
}

sport_teached_by = {
    (day, clazz, teacher): LpVariable("Am %s hat Klasse %s Sport mit %s"
                                      % (days_cleartext[day],
                                         classes_cleartext[clazz],
                                         teachers_cleartext[teacher]), cat=LpBinary)
    for day in days
    for clazz in classes
    for teacher in teachers
}

teacher_day_slot_combination = {
    (teacher, day, slot_combination): LpVariable("Am Tag %s hat Lehrer %s die Stunden-Kombination %s"
                                                 % (days_cleartext[day],
                                                    teachers_cleartext[teacher],
                                                    slot_combination,
                                                    ), cat=LpBinary)
    for day in days
    for teacher in teachers
    for slot_combination in n_slot_combinations
}

x = {
    (day, slot, clazz, lesson): LpVariable("Am %s in der %s Stunde wird in der Klasse %s %s von %s unterrichtet"
                                           % (days_cleartext[day],
                                              slots_cleartext[slot],
                                              classes_cleartext[clazz],
                                              teacherCategoryCombinations[lesson]["category"],
                                              teacherCategoryCombinations[lesson]["teachers"]
                                              ), cat=LpBinary)
    for day in days
    for slot in slots
    for clazz in classes
    for lesson in lessons
}

slot_used = {
    (day, slot, clazz): LpVariable("Am Tag %s in der Klasse %s wird in der %s Stunde unterrichtet"
                                   % (days_cleartext[day],
                                      classes_cleartext[clazz],
                                      slots_cleartext[slot],
                                      ), cat=LpBinary)
    for day in days
    for slot in slots
    for clazz in classes
}

teacher_school_end = {
    (teacher, day, school_end_slot): LpVariable("Am %s hat %s ab Slot %s frei"
                                                % (days_cleartext[day], teachers_cleartext[teacher], school_end_slot), cat=LpBinary)
    for day in days
    for teacher in teachers
    for school_end_slot in school_end_slots
}

same_day_school_end = {
    (day, school_end_slot): LpVariable("Am %s haben alle ab der %s Stunde schluss" % (days_cleartext[day], school_end_slot), cat=LpBinary,)
    for day in days
    for school_end_slot in school_end_slots
}

teacher_day_ogs = {
    (teacher, day): LpVariable("%s hat am %s OGS" % (teachers_cleartext[teacher], days_cleartext[day]), cat=LpBinary)
    for teacher in teachers
    for day in days
}

#########################################################

problem = LpProblem("Stundenplan", sense=LpMaximize)

##################  CONSTRAINTS  ########################
# * Jede Klasse hat genau n stunden aus kategorie c pro Woche
for clazz in classes:
    for category in categories:
        problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)]
                                    for day in days
                                    for slot in slots
                                    for lesson in lessons
                                    if teacherCategoryCombinations[lesson]["category"] == category
                                    ) == class_categories[clazz, category])
for lesson in lessons:
    if teacherCategoryCombinations[lesson]["category"] != 3:
        continue
    for day in days:
        for slot in slots:
            for clazz in classes[:4]:
                problem.addConstraint(x[(day, slot, clazz, lesson)] == sport_teached_by[(
                    day, clazz, teacherCategoryCombinations[lesson]["teachers"][0])])


# * Jede klasse hat im slot 0 jeden tages unterricht
for day in days:
    for clazz in classes[:-1]:
        problem.addConstraint(
            lpSum(x[(day, 0, clazz, lesson)] for lesson in lessons) == 1)

# * Jeder Lehrer darf an jedem Tag in jedem Slot nur eine Klasse unterrichten
for teacher in teachers:
    for day in days:
        for slot in slots:
            problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)]
                                        for clazz in classes
                                        for lesson in lessons
                                        if teacher in teacherCategoryCombinations[lesson]["teachers"]
                                        ) == lpSum(
                teacher_day_slot_combination[(teacher, day, combination)] * slot_combinations[combination][slot] for
                combination in n_slot_combinations))

# * An jedem Tag hat jede Klasse maximal eine Stunde englisch
for day in days:
    for clazz in classes[:-1]:
        problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)]
                              for slot in slots for lesson in lessons if teacherCategoryCombinations[lesson]["category"] == 1) <= 1)

# * An jedem Tag hat jede Klasse maximal eine Stunde religion
for day in days:
    for clazz in classes[:-1]:
        problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)]
                              for slot in slots for lesson in lessons if teacherCategoryCombinations[lesson]["category"] == 5) <= 1)

for day in days:
    for clazz in classes[:-1]:
        problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)]
                              for slot in slots for lesson in lessons if teacherCategoryCombinations[lesson]["category"] == 6) <= 1)

# * Für jeden Slot darf nur eine Combination ausgewählt sein
for day in days:
    for slot in slots:
        for clazz in classes:
            problem.addConstraint(
                lpSum(x[(day, slot, clazz, lesson)] for lesson in lessons) == 1 * slot_used[(day, slot, clazz)])

# * Jeder Lehrer darf nur eine bestimmte Stundenzahl pro Woche unterrichten
for teacher in teachers:
    problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)]
                                for day in days
                                for slot in slots
                                for clazz in classes
                                for lesson in lessons
                                if teacher in teacherCategoryCombinations[lesson]["teachers"]
                                )
                          + lpSum(teacher_day_ogs[(teacher, day)]
                                  for day in days)
                          == teacherLessons[teacher])

# * Alle Klassenstufen haben paarweise gleichzeitig schluss (1a+1b gleichzeitig!) => kann muss aber nicht
for grade_level in n_grade_levels:
    for day in days:
        for clazz in grade_levels[grade_level][:-1]:
            problem.addConstraint((lpSum(x[(day, slot, clazz, lesson)]
                                         for lesson in lessons
                                         for slot in slots)-lpSum(
                x[(day, slot, clazz+1, lesson)]
                for lesson in lessons
                for slot in slots)) == p_school_end_deviation[(day, grade_level)])

# * Keine FREISTUNDEN
for day in days:
    for clazz in classes[:-1]:
        for slot in slots[:-1]:
            problem.addConstraint(
                slot_used[(day, slot, clazz)] - slot_used[(day, slot + 1, clazz)] >= 0)

# * Alle Lehrer haben mindestens einmal die Woche gleichzeitig Schluss => muss (am besten Montags)
for teacher in teachers:
    for day in days:
        for school_end_slot in school_end_slots:
            problem.addConstraint(teacher_school_end[(
                teacher, day, school_end_slot)] ==
                lpSum(teacher_day_slot_combination[(teacher, day, slot_combination)] for slot_combination in last_slot_to_slot_combinations[school_end_slot]))

for day in days:
    for school_end_slot in school_end_slots:
        problem.addConstraint((lpSum(teacher_school_end[(teacher, day, school_end_slot)] for teacher in teachers) - (len(
            teachers)-lpSum(teacher_school_end[(teacher, day, -1)]for teacher in teachers)))*-1 <= 13*(1-same_day_school_end[(day, school_end_slot)]))

for day in days:
    problem.addConstraint(lpSum(same_day_school_end[(
        day, school_end_slot)] for school_end_slot in school_end_slots) <= 1)

# * am Konferenztag hat niemand frei
problem.addConstraint(lpSum(teacher_school_end[(
    teacher, conference_day, -1)] for teacher in teachers) == 0)

# * Alle Klassen haben nach der 5. Stunde Schluss am Konferenztag
problem.addConstraint(same_day_school_end[(
    conference_day, conference_slot-1)] == 1)

# * Freitags 5 Stunden
problem.addConstraint(same_day_school_end[(4, 4)] == 1)

# nicht zwingend aber höchst wünschenswert
# * keine SPRINGSTUNDEN
for teacher in teachers:
    for day in days:
        problem.addConstraint(lpSum(teacher_day_slot_combination[(
            teacher, day, slot_combination)] for slot_combination in n_slot_combinations) == 1)

# * Minimum 4h / Tag
for day in days:
    for clazz in classes[:-1]:
        problem.addConstraint(
            lpSum(slot_used[(day, slot, clazz)] for slot in slots) >= 4)

for clazz in classes:
    for teacher in teachers:
        problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)]
                                    for day in days
                                    for slot in slots
                                    for lesson in lessons
                                    if teacher in teacherCategoryCombinations[lesson]["teachers"]
                                    ) <= 29 * class_teached_by[(clazz, teacher)])

# nicht zwingend aber höchst wünschenswert (möglichst nicht 1./2.)
# # * Jede Klasse hat maximal drei Lehrkräfte (frisst unnormal viel Zeit)
for clazz in classes:
    for teacher in classTeachers[clazz]:
        problem.addConstraint(class_teached_by[(clazz, teacher)] == 1)
    # for category in categories:
    #     if class_categories[(clazz, category)] == 0:
    #         continue
    #     teachers_for_category = []
    #     for teacher in teachers:
    #         if not category in teacherCategories[teacher]:
    #             continue
    #         teachers_for_category.append(teacher)
    #     # if len(teachers_for_category) == 1:
    #     #     problem.addConstraint(
    #     #         class_teached_by[(clazz, teachers_for_category[0])] == 1)
    #     #     continue
    #     problem.addConstraint(lpSum(class_teached_by[(clazz, _teacher)] for _teacher in teachers_for_category)>=1)


for clazz in classes:
    problem.addConstraint(
        lpSum(class_teached_by[(clazz, teacher)] for teacher in teachers) <= 3)


# * Die Klassenleitung hat mindestens 2 Stunden pro Tag in seiner Klasse
for clazz in classes:
    for day in days:
        problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)]
                                    for lesson in lessons
                                    for slot in slots
                                    for teacher in teacherCategoryCombinations[lesson]["teachers"]
                                    if teacher in classTeachers[clazz]) >= 2)

# * OGS => 3 Lehrer opfern jeweils eine Stunde die Woche für OGS (anschluss an die 6. Stunde 14-15uhr) keine springstunde
# genau drei mal ogs
problem.addConstraint(lpSum(
    teacher_day_ogs[(teacher, day)] for teacher in teachers for day in days) == 3)
# jeder lehrer maximal einmal ogs
for teacher in teachers:
    problem.addConstraint(
        lpSum(teacher_day_ogs[(teacher, day)] for day in days) <= 1)
# an jedem tag maxinmal einmal ogs
for day in days:
    problem.addConstraint(
        lpSum(teacher_day_ogs[(teacher, day)] for teacher in teachers) <= 1)

problem.addConstraint(lpSum(teacher_day_ogs[(
    teacher, 0)] for teacher in teachers) == 0)  # montags keine ogs

# im anschluss an die sechste klasse
for teacher in teachers:
    for day in days:
        problem.addConstraint(
            teacher_day_ogs[(teacher, day)] <= teacher_school_end[(teacher, day, 5)])

# * förder: 2 stunden 4-5 mal die woche migrationskinder; möglichst alle klassen unterricht (muss aber nicht); Ein Lehrer
for day in days:
    # zwei stunden am tag förderunterricht
    problem.addConstraint(
        lpSum(slot_used[(day, slot, 8)] for slot in slots) == 2)
    # förderunterricht nur in der 1.-4. Stunde
    problem.addConstraint(lpSum(slot_used[(day, 4, 8)]) == 0)
    # förderunterricht nur in der 1.-4. Stunde
    problem.addConstraint(lpSum(slot_used[(day, 5, 8)]) == 0)

# * religion am ende des tages => muss
# 1. und 2. Stufe
for day in days:
    for clazz in classes[:-1]:
        if clazz > 3:
            continue
        for slot in slots[:-1]:
            problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)] for lesson in lessons if teacherCategoryCombinations[lesson]["category"] == 5) <= 1 -
                                  slot_used[(day, slot+1, clazz)])
# 3. und 4. Stufe
for day in days:
    for clazz in classes[:-1]:
        if clazz <= 3:
            continue
        for slot in slots[:-1]:
            problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)] for lesson in lessons if teacherCategoryCombinations[lesson]["category"] == 6) <= 1 -
                                  slot_used[(day, slot+1, clazz)])

# * teils fixe sportzeiten (mehrere Klassen gleichzeitig => zwei hallen 3./4.)
# stufenweise zusammen
# ein lehrer
# doppelstunde

for clazz in classes[:-1]:
    if class_categories_raw[clazz][7] == 0:
        continue
    for day in days:
        for slot in slots:
            if day in sport_slots and slot in sport_slots[day]:
                continue
            for lesson in lessons:
                if teacherCategoryCombinations[lesson]["category"] == 7:
                    problem.addConstraint(x[(day, slot, clazz, lesson)] == 0)

for sport_day in sport_slots:
    for sport_slot in sport_slots[sport_day]:
        problem.addConstraint(lpSum(x[(sport_day, sport_slot, clazz, lesson)]  # 2 klassen gleichzeitig sport
                              for clazz in classes[:-1]
                              for lesson in lessons
                              if teacherCategoryCombinations[lesson]["category"] == 7) == 2)
        problem.addConstraint(lpSum(x[(sport_day, sport_slot, 4, lesson)]  # dritte stufe hat gleichzeitig sport
                                    for lesson in lessons
                                    if teacherCategoryCombinations[lesson]["category"] == 7) == lpSum(
            x[(sport_day, sport_slot, 5, lesson)]
            for lesson in lessons
            if teacherCategoryCombinations[lesson]["category"] == 7))
        problem.addConstraint(lpSum(x[(sport_day, sport_slot, 6, lesson)]  # vierte stufe hat gleichzeitig sport
                                    for lesson in lessons
                                    if teacherCategoryCombinations[lesson]["category"] == 7) == lpSum(
            x[(sport_day, sport_slot, 7, lesson)]
            for lesson in lessons
            if teacherCategoryCombinations[lesson]["category"] == 7))
    # problem.addConstraint(lpSum(x[(sport_day, sport_slots[sport_day][0], 4, lesson)] for lesson in lessons if teacherCategoryCombinations[lesson]["category"]==7) == lpSum(x[(sport_day, sport_slots[sport_day][1], 4, lesson)] for lesson in lessons if teacherCategoryCombinations[lesson]["category"]==7))
    # problem.addConstraint(lpSum(x[(sport_day, sport_slots[sport_day][0], 6, lesson)] for lesson in lessons if teacherCategoryCombinations[lesson]["category"]==7) == lpSum(x[(sport_day, sport_slots[sport_day][1], 6, lesson)] for lesson in lessons if teacherCategoryCombinations[lesson]["category"]==7))
    for lesson in lessons:  # gleicher lehrer in doppelstunde
        if teacherCategoryCombinations[lesson]["category"] == 7:
            for clazz in classes[4:-1]:
                problem.addConstraint(x[(sport_day, sport_slots[sport_day][0], clazz, lesson)] == x[(
                    sport_day, sport_slots[sport_day][1], clazz, lesson)])

# * fixe schwimmzeiten muss Doppelstunde sein (selber lehrer)
for swim_day in swim_slots:
    for swim_slot in swim_slots[swim_day]:
        problem.addConstraint(lpSum(x[(swim_day, swim_slot, clazz, lesson)]  # 2 klassen gleichzeitig sport
                              for clazz in classes[:-1]
                              for lesson in lessons
                              if teacherCategoryCombinations[lesson]["category"] == 4) == 1)

for clazz in classes[:-1]:
    if class_categories_raw[clazz][4] == 0:
        continue
    for day in days:
        for slot in slots:
            if day in swim_slots and slot in swim_slots[day]:
                continue
            for lesson in lessons:
                if teacherCategoryCombinations[lesson]["category"] == 4:
                    problem.addConstraint(x[(day, slot, clazz, lesson)] == 0)

for swim_day in swim_slots:
    for lesson in lessons:  # gleicher lehrer in doppelstunde
        if teacherCategoryCombinations[lesson]["category"] == 4:
            for clazz in classes[:-1]:
                if class_categories_raw[clazz][4] == 0:
                    continue
                problem.addConstraint(x[(swim_day, swim_slots[swim_day][0], clazz, lesson)] == x[(
                    swim_day, swim_slots[swim_day][1], clazz, lesson)])

# * sport entweder doppelstunde oder einzel (1./2. klasse)


# maximal einen sport-lehrer pro tag
# for clazz in classes[:4]:
#     for day in days:
#         problem.addConstraint(
#             lpSum(sport_teached_by[(day, clazz, teacher)]
#              for teacher in teachers) <= 1)


# * maximal zwei stunden sport pro tag pro klasse
for clazz in classes[:4]:
    for day in days:
        problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)]
                              for slot in slots for lesson in lessons if teacherCategoryCombinations[lesson]["category"] == 3) <= 2)

# * sport in der 1. und 2. Klasse nicht gleichzeitig in mehreren Klassen möglich
for day in days:
    for slot in slots:
        problem.addConstraint(lpSum(x[(day, slot, clazz, lesson)] for clazz in classes[:4]
                              for lesson in lessons if teacherCategoryCombinations[lesson]["category"] == 3) <= 1)

# Nicht mehrere einzelstunden sport verteilt über den Tag
for clazz in classes[:4]:
    for day in days:
        for slot in [0, 2]:
            problem.addConstraint(
                (1 - lpSum(x[(day, slot, clazz, lesson)]
                 for lesson in lessons
                           if teacherCategoryCombinations[lesson]["category"] == 3)) * 20 >= lpSum(x[(day, slot_follow, clazz, lesson)]
                                                                                                   for slot_follow in slots[slot+2:]
                                                                                                   for lesson in lessons
                                                                                                   if teacherCategoryCombinations[lesson]["category"] == 3)
            )
        for slot in [1, 3]:
            problem.addConstraint(
                (1 - lpSum(x[(day, slot, clazz, lesson)]
                 for lesson in lessons
                           if teacherCategoryCombinations[lesson]["category"] == 3)) * 20 >= lpSum(
                    x[(day, slot_follow, clazz, lesson)]
                    for slot_follow in slots[slot+1:]
                    for lesson in lessons
                    if teacherCategoryCombinations[lesson]["category"] == 3)
            )

#
# for clazz in classes[:4]:
#     for day in days:
#         for slot in sport_single_not:
#             problem.addConstraint(
#                 lpSum(x[(day, slot + 1, clazz, lesson)] for lesson in lessons if teacherCategoryCombinations[lesson]["category"] == 3) <= lpSum(x[(day, slot + 1, clazz, lesson)] for lesson in lessons if teacherCategoryCombinations[lesson]["category"] == 3) + 1
#             )

########################################################


#################  OBJECTIVE  ##################

# Maximize teacher hours in main class
problem.setObjective(
    lpSum(x[(day, slot, clazz, lesson)]
          for day in days
          for slot in slots
          for clazz in classes
          for lesson in lessons
          for teacher in teacherCategoryCombinations[lesson]["teachers"]
          if teacher in classTeachers[clazz]
          ) - lpSum(p_school_end_deviation[(day, grade_level)]
                    for grade_level in n_grade_levels
                    for day in days)
    + lpSum(x[(day, slot, clazz, lesson)]  # * gewichtung doppelbesetzungen => vorallem 1./2.
            for day in days
            for slot in slots
            for clazz in range(4)
            for lesson in lessons
            if len(teacherCategoryCombinations[lesson]["teachers"]) == 2
            ) * 100
    + lpSum(x[(day, slot, clazz, lesson)]  # * gewichtung doppelbesetzungen => vorallem 1./2.
            for day in days
            for slot in slots
            for clazz in range(4, 8)
            for lesson in lessons
            if len(teacherCategoryCombinations[lesson]["teachers"]) == 2
            ) * 1)
################################################
# The problem is solved using PuLP's choice of Solver
print("Constraints: %s" % (len(problem.constraints)))
problem.solve(GUROBI_CMD())

#################  OUTPUT  ##################

# The status of the solution is printed to the screen
print("Status:", LpStatus[problem.status])
if problem.status == LpStatusNotSolved:
    exit()

day_data = {}
for day in days:
    day_data[day] = []

for day in days:
    for slot in slots:
        slot_data = [slots_cleartext[slot]]
        day_data[day].append(slot_data)
        for clazz in classes:
            if sum(value(x[(day, slot, clazz, lesson)]) for lesson in lessons) == 0:
                slot_data.append("-")
                continue

            for lesson in lessons:
                if value(x[(day, slot, clazz, lesson)]) == 0:
                    continue
                slot_data.append(", ".join(list(map(
                    lambda x: teachers_cleartext[x], teacherCategoryCombinations[lesson]["teachers"]))) + category_shorttext[
                    teacherCategoryCombinations[lesson]["category"]])
    day_data[day].append(["7."])
    teacher_ogs_data = ["8."]
    for teacher in teachers:
        if value(teacher_day_ogs[(teacher, day)]) == 1:
            teacher_ogs_data.append("OGS von %s" %
                                    (teachers_cleartext[teacher]))
    day_data[day].append(teacher_ogs_data)

for day in days:
    print()
    print(days_cleartext[day] + ":")
    print(tabulate(day_data[day], headers=[
        "Stunde", *["%s - %s" % x for x in zip(classes_cleartext, classTeacherNames)]]))


category_clazz_data = []

for category in categories:
    _categories = [categories_cleartext[category]]
    for clazz in classes:
        hours = sum(value(x[(day, slot, clazz, lesson)])
                    for day in days for slot in slots for lesson in lessons if teacherCategoryCombinations[lesson]["category"] == category)
        _categories.append("%d" %
                           (hours))
    category_clazz_data.append(_categories)

print()
print(tabulate(category_clazz_data, headers=["Fach", *classes_cleartext]))


print()
for day in days:
    if sum(value(same_day_school_end[(day, school_end_slot)])for school_end_slot in school_end_slots) == 1:
        print("Gemeinsam Schluss am %s" % (days_cleartext[day]))

#############################################
# TODO persönliche präferenzen
# TODO lesson in lessons if xyz => in liste extrahieren
