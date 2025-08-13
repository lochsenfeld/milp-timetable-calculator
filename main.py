#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import itertools
from pulp import *
from tabulate import tabulate
from config import LESSONS_NONE, Days, Lessons, OgsSlots, Subjects
from input import CONFERENCE_DAY, CONFERENCE_LESSON, OGS_DAYS, SPORT_SLOTS, ClassLevels, Classes, Teachers

# Alle Kombinationen von Einzelunterricht und Doppelbesetzung
teacher_combinations = list(itertools.combinations(
    Teachers, 1)) + list(itertools.combinations(Teachers, 2))
teacher_subject_combinations = []
for combination in teacher_combinations:
    # Fächer die in dieser Kombination unterrichtet werden können
    _subjects = list(set(itertools.chain.from_iterable(
        map(lambda teacher: teacher.value.subjects, combination))))
    for subject in _subjects:
        # region Fächer Doppelbestzungen Constraints
        # * religion nicht in doppelbesetzung
        if subject == Subjects.Religion and len(combination) == 2:
            continue
        # * englisch nicht in doppelbesetzung
        if subject == Subjects.English and len(combination) == 2:
            continue
        # * sport nicht in doppelbesetzung
        if subject == Subjects.Sports and len(combination) == 2:
            continue
        # # * schwimmen muss in doppelbesetzung und beide müssen schwimmen unterrichten
        # if subject == Subjects.Swimming and len(combination) == 1:
        #     continue
        # if subject == Subjects.Swimming and len(combination) == 2:
        #     if Subjects.Swimming not in combination[0].value.subjects or Subjects.Swimming not in combination[1].value.subjects:
        #         continue
        # endregion
        # region Persönliche Präferenzen Doppelbesetzung
        # # * Si hat keine Doppelbesetzung mit Kl
        # if Teachers.Si in combination and Teachers.Kl in combination:
        #     continue
        # # * Wa hat keine Doppelbesetzung mit Kl
        # if Teachers.Wa in combination and Teachers.Kl in combination:
        #     continue
        # # * Ba hat keine Doppelbesetzung mit Kl
        # if Teachers.Ba in combination and Teachers.Kl in combination:
        #     continue
        # endregion
        # append combination as list and subjects
        teacher_subject_combinations.append({
            "teachers": list(combination),
            "subject": subject
        })
n_teacher_subject_combinations = range(len(teacher_subject_combinations))
# region subjectLessons
subject_lessons = {}
for subject in Subjects:
    _lessons = []
    for lesson in n_teacher_subject_combinations:
        if teacher_subject_combinations[lesson]["subject"] == subject:
            _lessons.append(lesson)
    subject_lessons[subject] = _lessons

# endregion

# region teacherToLessons
# zuordnung von Kombination zu lehrer
teacher_to_lessons = {}
for teacher in Teachers:
    _lessons = []
    for lesson in n_teacher_subject_combinations:
        if teacher in teacher_subject_combinations[lesson]["teachers"]:
            _lessons.append(lesson)
    teacher_to_lessons[teacher] = _lessons
# endregion

# region lesson combinations
# hier werden freistunden für lehrer ausgeschlossen
# lesson combination = Menge an zusammenhängenden Unterrichtsstunden für einen Lehrer an einem Tag
# define all possible lesson combinations for a teacher on a single day
# from 0 to 6 lessons
# should look like this:
# [0, 0, 0, 0, 0, 0],
# [1, 0, 0, 0, 0, 0],
# [0, 1, 0, 0, 0, 0],
# [0, 0, 1, 0, 0, 0],
# [0, 0, 0, 1, 0, 0],
# [0, 0, 0, 0, 1, 0],
# [0, 0, 0, 0, 0, 1],
# [1, 1, 0, 0, 0, 0],
# [0, 1, 1, 0, 0, 0],
# [0, 0, 1, 1, 0, 0],
# [0, 0, 0, 1, 1, 0],
# [0, 0, 0, 0, 1, 1],
# [1, 1, 1, 0, 0, 0],
# [0, 1, 1, 1, 0, 0],
# [0, 0, 1, 1, 1, 0],
# [0, 0, 0, 1, 1, 1],
# [1, 1, 1, 1, 0, 0],
# [0, 1, 1, 1, 1, 0],
# [0, 0, 1, 1, 1, 1],
# [1, 1, 1, 1, 1, 0],
# [0, 1, 1, 1, 1, 1],
# [1, 1, 1, 1, 1, 1],


def generate_combinations(length=6):
    result = []

    # Generiere alle möglichen Kombinationen
    for i in range(2**length):
        # Konvertiere die Zahl in eine binäre Darstellung und fülle mit Nullen auf
        binary = format(i, f'0{length}b')

        # Konvertiere den String in eine Liste von Integers
        combination = [int(bit) for bit in binary]

        # Überprüfe, ob die Kombination gültig ist (keine Lücken nach der ersten 1)
        first_one = binary.find('1')
        if first_one == -1 or '01' not in binary[first_one:]:
            result.append(combination)

    return result


# Generiere die Kombinationen
lesson_combinations = generate_combinations()
n_lesson_combinations = range(len(lesson_combinations))
# zuordnung wann eine kombination startet (erste 1 pro kombination)
lesson_combination_start_lessons = []
for lesson_combination in lesson_combinations:
    if 1 not in lesson_combination:
        lesson_combination_start_lessons.append(LESSONS_NONE)
    else:
        lesson_combination_start_lessons.append(
            Lessons.by_index(lesson_combination.index(1)))
# zuordnung wann eine kombination endet (letzte 1 pro kombination) als index
last_lesson_to_lesson_combination = {}
for i in range(len(lesson_combinations)):
    lesson_combination = lesson_combinations[i]
    last_lesson = LESSONS_NONE
    for j in range(len(lesson_combination)):
        if lesson_combination[j] == 1:
            last_lesson = j
    if last_lesson not in last_lesson_to_lesson_combination:
        last_lesson_to_lesson_combination[last_lesson] = []
    last_lesson_to_lesson_combination[last_lesson].append(i)
# endregion

# region school_end_lessons
# liste an möglichen endstunden einschließlich frei
school_end_lessons = [LESSONS_NONE] + list(Lessons)
# endregion

# region variables
# region penalties
p_school_end_deviation = {
    (day.index, classLevel.index): LpVariable("Stundenabweichung der Stufe %s am %s" %
                                              (classLevel.text, day.text), cat=LpInteger, lowBound=0)
    for classLevel in ClassLevels
    for day in Days
}

p_no_school_conference_day = LpVariable(
    "Keine Schule am Konferenz-Tag", cat=LpInteger, lowBound=0, upBound=Teachers.length())

p_two_hours_on_conference_day = {
    (teacher.index): LpVariable(
        "Zwei Stunden Schule am Konferenz-Tag von Lehrer %s"
        % (teacher.text), cat=LpInteger, lowBound=0, upBound=len(teacher_subject_combinations))
    for teacher in Teachers
}
# endregion

# region zu optimierende ziele
class_teached_by = {
    (clazz.index, teacher.index): LpVariable("Klasse %s wird in der Woche von %s unterrichtet"
                                             % (clazz.text,
                                                teacher.text,
                                                ), cat=LpBinary)
    for clazz in Classes
    for teacher in Teachers
}

teacher_day_lesson_combination = {
    (teacher.index, day.index, lesson_combination): LpVariable("Am %s hat Lehrer %s die Stunden-Kombination %s"
                                                               % (day.text,
                                                                  teacher.text,
                                                                  lesson_combination,
                                                                  ), cat=LpBinary)
    for day in Days
    for teacher in Teachers
    for lesson_combination in range(len(lesson_combinations))
}
# hauptproblem
x = {
    (day.index, lesson.index, clazz.index, teacher_subject_combination): LpVariable("Am %s in der %s Stunde wird in der Klasse %s %s von %s unterrichtet"
                                                                                    % (day.text,
                                                                                       lesson.text,
                                                                                       clazz.text,
                                                                                       teacher_subject_combinations[
                                                                                           teacher_subject_combination]["subject"].text,
                                                                                        ",".join(list(map(lambda t: t.text, teacher_subject_combinations[
                                                                                            teacher_subject_combination]["teachers"])))
                                                                                       ), cat=LpBinary)
    for day in Days
    for lesson in Lessons
    for clazz in Classes
    for teacher_subject_combination in n_teacher_subject_combinations
}

lesson_used = {
    (day.index, lesson.index, clazz.index): LpVariable("Am Tag %s in der Klasse %s wird in der %s Stunde unterrichtet"
                                                       % (day.text,
                                                          clazz.text,
                                                          lesson.text,
                                                          ), cat=LpBinary)
    for day in Days
    for lesson in Lessons
    for clazz in Classes
}

teacher_school_end = {
    (teacher.index, day.index, school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE): LpVariable("Am %s hat %s ab Stunde %s frei"
                                                                                                                           % (day.text, teacher.text, school_end_lesson.text if school_end_lesson != LESSONS_NONE else LESSONS_NONE), cat=LpBinary)
    for day in Days
    for teacher in Teachers
    for school_end_lesson in school_end_lessons
}
same_day_school_end = {
    (day.index, school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE): LpVariable("Am %s haben alle ab der %s Stunde schluss" % (day.text, school_end_lesson.text if school_end_lesson != LESSONS_NONE else LESSONS_NONE), cat=LpBinary,)
    for day in Days
    for school_end_lesson in school_end_lessons
}

teacher_day_ogs = {
    (teacher.index, day.index, ogs_slot.index): LpVariable("%s hat am %s in der %s OGS" % (teacher.text, day.text, ogs_slot.text), cat=LpBinary)
    for teacher in Teachers
    for day in Days
    for ogs_slot in OgsSlots
}

english_teached_by = {
    (clazz.index, teacher.index): LpVariable("In der %s wird Englisch von %s unterrichtet"
                                             % (clazz.text, teacher.text), cat=LpBinary)
    for clazz in list(filter(lambda clazz: Subjects.English in clazz.value.lessoncount, Classes))
    for teacher in list(filter(lambda teacher: Subjects.English in teacher.value.subjects, Teachers))
}
# endregion

problem = LpProblem("Stundenplan", sense=LpMaximize)
# endregion

# region persönliche constraints
# * Ma startet um 8 oder hat frei
for day in Days:
    problem.addConstraint(lpSum(x[(day.index, Lessons.First.index, clazz.index, lesson)]
                                for clazz in Classes
                                for lesson in teacher_to_lessons[Teachers.Ma]) +
                          teacher_school_end[(Teachers.Ma.index, day.index, LESSONS_NONE)] == 1)

# # * Si startet um 8 oder hat frei
# for day in Days:
#     problem.addConstraint(lpSum(x[(day.index, Lessons.First.index, clazz.index, lesson)]
#                                 for clazz in Classes
#                                 for lesson in teacher_to_lessons[Teachers.Si]) +
#                           teacher_school_end[(Teachers.Si.index, day.index, LESSONS_NONE)] == 1)
# endregion

# region default constraints
# * Jede Klasse hat genau n stunden aus fach c pro Woche
for clazz in Classes:
    for subject in list(filter(lambda s: s in clazz.value.lessoncount, list(Subjects))):
        # exakt x stunden
        if clazz.value.lessoncount[subject].min == clazz.value.lessoncount[subject].max:
            problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)]
                                        for day in Days
                                        for lesson in Lessons
                                        for combo in subject_lessons[subject]
                                        ) == clazz.value.lessoncount[subject].min)
        # zwischen x und y stunden eines fachs
        else:
            problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)]
                                        for day in Days
                                        for lesson in Lessons
                                        for combo in subject_lessons[subject]
                                        ) >= clazz.value.lessoncount[subject].min)
            problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)]
                                        for day in Days
                                        for lesson in Lessons
                                        for combo in subject_lessons[subject]
                                        ) <= clazz.value.lessoncount[subject].max)
# für alle fächer die nicht in der klasse unterrichtet werden, setze combination auf 0
for clazz in Classes:
    for combo in n_teacher_subject_combinations:
        if teacher_subject_combinations[combo]["subject"] not in clazz.value.lessoncount:
            for day in Days:
                for lesson in Lessons:
                    problem.addConstraint(
                        x[(day.index, lesson.index, clazz.index, combo)] == 0)

# Klassen haben stufenweise gleich viele Stunden
for clazz in [Classes.FirstA, Classes.SecondA, Classes.ThirdA, Classes.FourthA]:
    problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)]
                                for day in Days for lesson in Lessons for combo in n_teacher_subject_combinations) == lpSum(
        x[(day.index, lesson.index, clazz.index+1, combo)]for day in Days for lesson in Lessons for combo in n_teacher_subject_combinations))

# * Jede klasse hat in der ersten Stunde jeden tages unterricht
for day in Days:
    for clazz in Classes.but_remedial():
        problem.addConstraint(
            lpSum(x[(day.index, Lessons.First.index, clazz.index, combo)] for combo in n_teacher_subject_combinations) == 1)

# * Jeder Lehrer darf an jedem Tag in jeder Stunde nur eine Klasse unterrichten
for teacher in Teachers:
    for day in Days:
        for lesson in Lessons:
            problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)]
                                        for clazz in Classes
                                        for combo in n_teacher_subject_combinations
                                        if teacher in teacher_subject_combinations[combo]["teachers"]
                                        ) == lpSum(
                teacher_day_lesson_combination[(teacher.index, day.index, combination)] * lesson_combinations[combination][lesson.index] for
                combination in n_lesson_combinations))

# Rausgenommen, da jede Klasse nur eine Stunde hat
# * An jedem Tag hat jede Klasse maximal eine Stunde englisch
for day in Days:
    for clazz in Classes.but_remedial():
        problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)]
                              for lesson in Lessons for combo in subject_lessons[Subjects.English]) <= 1)

# * An jedem Tag hat jede Klasse maximal eine Stunde religion
for day in Days:
    for clazz in Classes.but_remedial():
        problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)]
                              for lesson in Lessons for combo in subject_lessons[Subjects.Religion]) <= 1)

# * Für jeden Slot darf nur eine Combination ausgewählt sein
for day in Days:
    for lesson in Lessons:
        for clazz in Classes:
            problem.addConstraint(
                lpSum(x[(day.index, lesson.index, clazz.index, combo)] for combo in n_teacher_subject_combinations) == 1 * lesson_used[(day.index, lesson.index, clazz.index)])

# * Jeder Lehrer darf nur eine bestimmte Stundenzahl pro Woche unterrichten
for teacher in Teachers:
    problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)]
                                for day in Days
                                for lesson in Lessons
                                for clazz in Classes
                                for combo in n_teacher_subject_combinations
                                if teacher in teacher_subject_combinations[combo]["teachers"]
                                )
                          + lpSum(teacher_day_ogs[(teacher.index, day.index, slot.index)]
                                  for day in Days for slot in OgsSlots)
                          == teacher.value.lesson_ct)

# * Alle Klassenstufen haben paarweise gleichzeitig schluss (1a+1b gleichzeitig!) => kann muss aber nicht
for classLevel in ClassLevels:
    for day in Days:
        problem.addConstraint((lpSum(x[(day.index, lesson.index, classLevel.value.classes[0].index, combo)]
                                     for combo in n_teacher_subject_combinations
                                     for lesson in Lessons)-lpSum(
            x[(day.index, lesson.index, classLevel.value.classes[1].index, combo)]
            for combo in n_teacher_subject_combinations
            for lesson in Lessons)) == p_school_end_deviation[(day.index, classLevel.index)])

# * Keine FREISTUNDEN
for day in Days:
    for clazz in Classes.but_remedial():
        for lesson in list(Lessons)[:-1]:
            problem.addConstraint(
                lesson_used[(day.index, lesson.index, clazz.index)] - lesson_used[(day.index, lesson.index + 1, clazz.index)] >= 0)
# endregion

# * Alle Lehrer haben mindestens einmal die Woche gleichzeitig Schluss => muss (am besten Montags)
for teacher in Teachers:
    for day in Days:
        for school_end_lesson in school_end_lessons:
            problem.addConstraint(teacher_school_end[(
                teacher.index, day.index, school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE)] ==
                lpSum(teacher_day_lesson_combination[(teacher.index, day.index, combo)] for combo in last_lesson_to_lesson_combination[school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE]))

for day in Days:
    for school_end_lesson in school_end_lessons:
        problem.addConstraint((lpSum(teacher_school_end[(teacher.index, day.index, school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE)] for teacher in Teachers) - (len(
            Teachers)-lpSum(teacher_school_end[(teacher.index, day.index, LESSONS_NONE)]for teacher in Teachers)))*-1 <= 30*(1-same_day_school_end[(day.index, school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE)]))

for day in Days:
    problem.addConstraint(lpSum(same_day_school_end[(
        day.index, school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE)] for school_end_lesson in school_end_lessons) <= 1)

# * am Konferenztag hat niemand frei
problem.addConstraint(lpSum(teacher_school_end[(
    teacher.index, CONFERENCE_DAY.index, LESSONS_NONE)] for teacher in Teachers) == p_no_school_conference_day)

# * am konferenztag haben möglichst alle die letzten beiden Stunden unterricht
for teacher in Teachers:
    problem.addConstraint(lpSum(x[(CONFERENCE_DAY.index, lesson.index, clazz.index, combo)]
                                for clazz in Classes
                                for lesson in Lessons
                                for combo in n_teacher_subject_combinations
                                if teacher in teacher_subject_combinations[combo]["teachers"]
                                ) == p_two_hours_on_conference_day[(teacher.index)])

# * Alle Klassen haben nach der 5. Stunde Schluss am Konferenztag
problem.addConstraint(same_day_school_end[(
    CONFERENCE_DAY.index, CONFERENCE_LESSON.index-1)] == 1)

# * Freitags 5 Stunden
for teacher in Teachers:
    problem.addConstraint(lpSum(x[(Days.Friday.index, Lessons.Sixth.index, clazz.index, combo)]
                                for clazz in Classes
                                for combo in n_teacher_subject_combinations
                                if teacher in teacher_subject_combinations[combo]["teachers"]
                                ) == 0)

# * keine SPRINGSTUNDEN
# nicht zwingend aber höchst wünschenswert
for teacher in Teachers:
    for day in Days:
        problem.addConstraint(lpSum(teacher_day_lesson_combination[(
            teacher.index, day.index, combo)] for combo in n_lesson_combinations) == 1)

# * Eine Klasse hat minimum 4h / Tag
for day in Days:
    for clazz in Classes.but_remedial():
        problem.addConstraint(
            lpSum(lesson_used[(day.index, lesson.index, clazz.index)] for lesson in Lessons) >= 4)

for day in Days:
    for clazz in Classes.but_remedial():
        for lesson in list(Lessons)[:4]:
            problem.addConstraint(
                lesson_used[(day.index, lesson.index, clazz.index)] == 1)

# * Jede Klasse hat maximal drei Lehrkräfte (frisst unnormal viel Zeit)
teacher_teaches_class_optimized = {}

for clazz in Classes:
    eligible_teachers = []

    # Pre-filter: only consider teachers who CAN teach in this class
    for teacher in Teachers:
        can_teach_in_class = any(
            teacher in teacher_subject_combinations[combo]["teachers"]
            and teacher_subject_combinations[combo]["subject"] in clazz.value.lessoncount
            for combo in n_teacher_subject_combinations
        )

        if can_teach_in_class:
            eligible_teachers.append(teacher)

            # Create binary indicator variable
            # Short name for memory efficiency
            var_name = f"T{teacher.index}C{clazz.index}"
            teacher_teaches_class_optimized[(clazz.index, teacher.index)] = LpVariable(
                var_name, cat=LpBinary
            )

            # Get all combinations where this teacher teaches this class
            relevant_combos = [
                combo for combo in n_teacher_subject_combinations
                if (teacher in teacher_subject_combinations[combo]["teachers"]
                    and teacher_subject_combinations[combo]["subject"] in clazz.value.lessoncount)
            ]

            if relevant_combos:  # Only add constraints if teacher can actually teach
                total_lessons_by_teacher = lpSum(
                    x[(day.index, lesson.index, clazz.index, combo)]
                    for day in Days
                    for lesson in Lessons
                    for combo in relevant_combos
                )

                # If teacher teaches any lesson, indicator must be 1
                problem.addConstraint(
                    total_lessons_by_teacher <= 30 *
                    teacher_teaches_class_optimized[(
                        clazz.index, teacher.index)]
                )

                # If indicator is 0, teacher teaches no lessons
                problem.addConstraint(
                    teacher_teaches_class_optimized[(
                        clazz.index, teacher.index)] <= total_lessons_by_teacher
                )

    # Maximum 3 teachers per class (much simpler constraint now)
    problem.addConstraint(
        lpSum(teacher_teaches_class_optimized.get((clazz.index, teacher.index), 0)
              for teacher in eligible_teachers) <= 3
    )

# * Die Klassenleitung hat mindestens 2 Stunden pro Tag in seiner Klasse
for clazz in Classes:
    for day in Days:
        problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)]
                                    for combo in n_teacher_subject_combinations
                                    for lesson in Lessons
                                    for teacher in teacher_subject_combinations[combo]["teachers"]
                                    if teacher in clazz.value.classteachers) >= 2)
# region ogs
# Ein lehrer von 12 - 13 ( 5. Stunde + 15 Min)
# 1. Lehrer kann nach der OGS keinen Unterricht mehr haben
# Zweite und Dritte Lehrer von 14-15 Uhr
# * ogs an jedem ogs tag - automatically assign teachers based on OGS_DAYS
for day in Days:
    if day not in OGS_DAYS:
        # * kein ogs an tagen ohne ogs
        problem.addConstraint(lpSum(
            teacher_day_ogs[(teacher.index, day.index, slot.index)] for slot in OgsSlots for teacher in Teachers) == 0)
        continue
    # * Exact number of teachers needed for OGS on this day
    problem.addConstraint(lpSum(
        teacher_day_ogs[(teacher.index, day.index, slot.index)] for teacher in Teachers for slot in OgsSlots) == OGS_DAYS[day])

# * each teacher can have OGS at most once per week
for teacher in Teachers:
    problem.addConstraint(lpSum(
        teacher_day_ogs[(teacher.index, day.index, slot.index)]
        for day in Days
        for slot in OgsSlots) <= 1)

# * jeder lehrer maximal einmal ogs pro tag
for teacher in Teachers:
    for day in Days:
        problem.addConstraint(
            lpSum(teacher_day_ogs[(teacher.index, day.index, slot.index)] for slot in OgsSlots) <= 1)

# * lehrer haben in der 6. stunde unterricht, wenn sie im anschluss ogs haben
for teacher in Teachers:
    for day in Days:
        problem.addConstraint(
            teacher_day_ogs[(teacher.index, day.index, OgsSlots.Seventh.index)] <= teacher_school_end[(teacher.index, day.index, Lessons.Sixth.index)])
# endregion


# * religion in der letzten stunde
# 3. und 4. Stufe
for day in Days:
    for clazz in Classes.but_remedial():
        for slot in list(Lessons)[:-1]:
            problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)] for combo in subject_lessons[Subjects.Religion]) <= 1 -
                                  lesson_used[(day.index, lesson.index+1, clazz.index)])

# * teils fixe sportzeiten (mehrere Klassen gleichzeitig => zwei hallen 3./4.)
# stufenweise zusammen
# ein lehrer
# doppelstunde


# TODO test if this makes sense:
# * if a class does not have a subject, no teacher can teach sports in that class
for clazz in Classes:
    for subject in Subjects:
        if subject not in clazz.value.lessoncount:
            for day in Days:
                for lesson in Lessons:
                    for combo in subject_lessons[subject]:
                        problem.addConstraint(
                            x[(day.index, lesson.index, clazz.index, combo)] == 0)

for clazz in Classes.but_remedial():
    if Subjects.Sports not in clazz.value.lessoncount:
        continue
    for day in Days:
        for lesson in Lessons:
            if day in SPORT_SLOTS and lesson in SPORT_SLOTS[day]:
                continue
            for combo in subject_lessons[Subjects.Sports]:
                problem.addConstraint(
                    x[(day.index, lesson.index, clazz.index, combo)] == 0)

for sport_day in SPORT_SLOTS:
    for sport_lesson in SPORT_SLOTS[sport_day]:
        problem.addConstraint(lpSum(x[(sport_day.index, sport_lesson.index, clazz.index, combo)]  # 2 klassen gleichzeitig sport
                              for clazz in Classes.but_remedial()
                              for combo in subject_lessons[Subjects.Sports]) == 2)
        problem.addConstraint(lpSum(x[(sport_day.index, sport_lesson.index, Classes.ThirdA.index, combo)]  # dritte stufe hat gleichzeitig sport
                                    for combo in subject_lessons[Subjects.Sports]) == lpSum(
            x[(sport_day.index, sport_lesson.index, Classes.ThirdB.index, combo)]
            for combo in subject_lessons[Subjects.Sports]))
        problem.addConstraint(lpSum(x[(sport_day.index, sport_lesson.index, Classes.FourthA.index, combo)]  # vierte stufe hat gleichzeitig sport
                                    for combo in subject_lessons[Subjects.Sports]) == lpSum(
            x[(sport_day.index, sport_lesson.index, Classes.FourthB.index, combo)]
            for combo in subject_lessons[Subjects.Sports]))
#     # gleicher lehrer in doppelstunde
    for combo in subject_lessons[Subjects.Sports]:
        for clazz in Classes.but_remedial():
            problem.addConstraint(x[(sport_day.index, SPORT_SLOTS[sport_day][0].index, clazz.index, combo)] == x[(
                sport_day.index, SPORT_SLOTS[sport_day][1].index, clazz.index, combo)])

# * fixe schwimmzeiten muss Doppelstunde sein (selber lehrer)
# for swim_day in SWIMMING_SLOTS:
#     for swim_lesson in SWIMMING_SLOTS[swim_day]:
#         problem.addConstraint(lpSum(x[(swim_day.index, swim_lesson.index, clazz.index, combo)]  # 2 klassen gleichzeitig schwimmen
#                               for clazz in Classes.but_remedial()
#                               for combo in subject_lessons[Subjects.Swimming]) == 1)

# * Stufen haben gleich viele Doppelbesetzungen
for clazz in [Classes.FirstA, Classes.SecondA]:
    problem.addConstraint(lpSum(x[(day.index, lesson.index, clazz.index, combo)]
                                for day in Days
                                for lesson in Lessons
                                for combo in n_teacher_subject_combinations
                                if len(teacher_subject_combinations[combo]["teachers"]) == 2 and teacher_subject_combinations[combo]["subject"] != Subjects.Swimming) ==
                          lpSum(x[(day.index, lesson.index, clazz.index+1, combo)]
                                for day in Days
                                for lesson in Lessons
                                for combo in n_teacher_subject_combinations
                                if len(teacher_subject_combinations[combo]["teachers"]) == 2 and teacher_subject_combinations[combo]["subject"] != Subjects.Swimming))

# * Erste Klasse hat keine sechs Stunden
for clazz in [Classes.FirstA, Classes.FirstB]:
    problem.addConstraint(
        lpSum(lesson_used[(day.index, Lessons.Sixth.index, clazz.index)] for day in Days) == 0)

# * Teachers.Sc hat kein OGS!
problem.addConstraint(lpSum(teacher_day_ogs[(
    Teachers.Sc.index, day.index, slot.index)] == 0 for day in Days for slot in OgsSlots) == 0)


# * Teachers.Sc hat Englisch in der Classes.ThirdA und Classes.ThirdB (Zwingend)
for clazz in [Classes.ThirdA, Classes.ThirdB]:
    for teacher in list(filter(lambda teacher: Subjects.English in teacher.value.subjects, Teachers)):
        if teacher == Teachers.Sc:
            problem.addConstraint(
                english_teached_by[(clazz.index, teacher.index)] == 1)
        else:
            problem.addConstraint(
                english_teached_by[(clazz.index, teacher.index)] == 0)
# *  Teachers.Him hat Englisch in der Classes.FourthA und Classes.FourthB (Zwingend)
for clazz in [Classes.FourthA, Classes.FourthB]:
    for teacher in list(filter(lambda teacher: Subjects.English in teacher.value.subjects, Teachers)):
        if teacher == Teachers.Him:
            problem.addConstraint(
                english_teached_by[(clazz.index, teacher.index)] == 1)
        else:
            problem.addConstraint(
                english_teached_by[(clazz.index, teacher.index)] == 0)

########################################################
#################  OBJECTIVE  ##################
# Maximize teacher hours in main class
problem.setObjective(
    lpSum(x[(day.index, lesson.index, clazz.index, combo)]
          for day in Days
          for lesson in Lessons
          for clazz in Classes
          for combo in n_teacher_subject_combinations
          for teacher in teacher_subject_combinations[combo]["teachers"]
          if teacher in clazz.value.classteachers
          ) * 1600
    - lpSum(p_school_end_deviation[(day.index, classLevel.index)]
            for classLevel in ClassLevels
            for day in Days)
    - p_no_school_conference_day*120
    + lpSum(lesson_used[(day.index, lesson.index, clazz.index)] for lesson in [Lessons.Fifth]
            for day in Days for clazz in Classes.but_remedial())*40  # fünf stunden pro tag belohnen
    + lpSum(p_two_hours_on_conference_day[(teacher.index)]
            for teacher in Teachers)*20
)
################################################
# The problem is solved using PuLP's choice of Solver
print("Constraints: %s" % (len(problem.constraints)))
constraint_count = len(problem.constraints)
variable_count = len(problem.variables())
print(
    f"Problem size: {variable_count} variables, {constraint_count} constraints")

if variable_count > 100000:
    print("WARNING: Large problem detected. Consider further optimization.")
problem.solve(HiGHS_CMD(msg=1))

print("Status:", LpStatus[problem.status])
if problem.status == LpStatusNotSolved:
    exit()


day_data = {}
for day in Days:
    day_data[day] = []

for day in Days:
    for lesson in Lessons:
        lesson_data = [lesson.text]
        day_data[day].append(lesson_data)
        for clazz in Classes:
            if sum(value(x[(day.index, lesson.index, clazz.index, combo)]) for combo in n_teacher_subject_combinations) == 0:
                lesson_data.append("-")
                continue

            for combo in n_teacher_subject_combinations:
                if value(x[(day.index, lesson.index, clazz.index, combo)]) == 0:
                    continue
                lesson_data.append(", ".join(list(map(
                    lambda x: x.text, teacher_subject_combinations[combo]["teachers"]))) + teacher_subject_combinations[combo]["subject"].value.short)
        lesson_data.append("-")
    print("lesson-data")
    print(lesson_data)
    teacher_ogs_data = ["7."]
    if sum(value(teacher_day_ogs[(teacher.index, day.index, OgsSlots.Seventh.index)]) for teacher in Teachers) >= 1:
        teachers = []
        for teacher in Teachers:
            if value(teacher_day_ogs[(teacher.index, day.index, OgsSlots.Seventh.index)]) == 1:
                teachers.append(teacher.text)
        for _ in Classes:
            teacher_ogs_data.append("-")
        teacher_ogs_data.append(", ".join(teachers))
    day_data[day].append(teacher_ogs_data)
    print("Day-Data")
    print(day_data[day])

# region console output
for day in Days:
    print()
    print(day.text + ":")
    header = ["Stunde"]
    for clazz in Classes:
        header.append("%s - %s" % (clazz.text, ",".join(
            [a.text for a in clazz.value.classteachers])))
    header.append("OGS")
    print(tabulate(day_data[day], headers=header))

# endregion

# region write to file
with open("Stundenplan.csv", "w", encoding="utf-8") as text_file:
    for day in Days:
        header = [day.text, "Stunde"]
        for clazz in Classes:
            header.append("%s - %s" % (clazz.text, ",".join(
                [a.text for a in clazz.value.classteachers])))
        header.append("OGS")
        # text_file.write(";".join([day.text,
        #                           "Stunde", *["%s - %s" % x for x in zip([c.text for c in Classes], list(map(lambda t: ",".join([a.text for a in t]), [
        #                               c.value.classteachers for c in Classes])))]])+"\n")
        text_file.write(";".join(header)+"\n")
        for lesson in range(len(day_data[day])):
            text_file.write(";"+";".join(day_data[day][lesson])+"\n")
        text_file.write("\n")
    text_file.close()
# endregion
