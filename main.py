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
        # * Schimmel nur in Doppelbesetzung oder Englisch
        if subject != Subjects.English and len(combination) == 1 and Teachers.Sc in combination:
            continue
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

# Pre-compute mappings for better performance
print("Pre-computing mappings...")

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
teacher_to_lessons = {}
for teacher in Teachers:
    _lessons = []
    for lesson in n_teacher_subject_combinations:
        if teacher in teacher_subject_combinations[lesson]["teachers"]:
            _lessons.append(lesson)
    teacher_to_lessons[teacher] = _lessons
# endregion

# Pre-compute class-teacher eligibility for performance
class_teacher_eligibility = {}
for clazz in Classes:
    class_teacher_eligibility[clazz] = {}
    for teacher in Teachers:
        # Check if teacher can teach any subject in this class
        can_teach = any(
            teacher in teacher_subject_combinations[combo]["teachers"]
            and teacher_subject_combinations[combo]["subject"] in clazz.value.lessoncount
            for combo in n_teacher_subject_combinations
        )
        if can_teach:
            relevant_combos = [
                combo for combo in n_teacher_subject_combinations
                if (teacher in teacher_subject_combinations[combo]["teachers"]
                    and teacher_subject_combinations[combo]["subject"] in clazz.value.lessoncount)
            ]
            class_teacher_eligibility[clazz][teacher] = relevant_combos
        else:
            class_teacher_eligibility[clazz][teacher] = []

print(
    f"Pre-computing done. Found {len(teacher_subject_combinations)} teacher-subject combinations.")

# region lesson combinations


def generate_combinations(length=6):
    result = []
    for i in range(2**length):
        binary = format(i, f'0{length}b')
        combination = [int(bit) for bit in binary]
        first_one = binary.find('1')
        if first_one == -1 or '01' not in binary[first_one:]:
            result.append(combination)
    return result


lesson_combinations = generate_combinations()
n_lesson_combinations = range(len(lesson_combinations))

lesson_combination_start_lessons = []
for lesson_combination in lesson_combinations:
    if 1 not in lesson_combination:
        lesson_combination_start_lessons.append(LESSONS_NONE)
    else:
        lesson_combination_start_lessons.append(
            Lessons.by_index(lesson_combination.index(1)))

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

school_end_lessons = [LESSONS_NONE] + list(Lessons)

print("Creating decision variables...")

# region variables
# region penalties
p_school_end_deviation = {
    (day.index, classLevel.index): LpVariable(f"school_end_dev_{day.index}_{classLevel.index}",
                                              cat=LpInteger, lowBound=0)
    for classLevel in ClassLevels
    for day in Days
}

p_no_school_conference_day = LpVariable(
    "no_school_conf", cat=LpInteger, lowBound=0, upBound=Teachers.length())

p_two_hours_on_conference_day = {
    teacher.index: LpVariable(f"two_hours_conf_{teacher.index}",
                              cat=LpInteger, lowBound=0, upBound=len(teacher_subject_combinations))
    for teacher in Teachers
}
# endregion

# Optimized main decision variable with shorter names
x = {}
for day in Days:
    for lesson in Lessons:
        for clazz in Classes:
            for combo in n_teacher_subject_combinations:
                # Only create variables for valid teacher-subject-class combinations
                subject = teacher_subject_combinations[combo]["subject"]
                if subject in clazz.value.lessoncount:
                    var_name = f"x_{day.index}_{lesson.index}_{clazz.index}_{combo}"
                    x[(day.index, lesson.index, clazz.index, combo)
                      ] = LpVariable(var_name, cat=LpBinary)

print(f"Created {len(x)} main decision variables (reduced from potential {len(Days) * len(Lessons) * len(Classes) * len(teacher_subject_combinations)})")

# Other variables with shorter names
teacher_day_lesson_combination = {
    (teacher.index, day.index, lesson_combination): LpVariable(f"tdlc_{teacher.index}_{day.index}_{lesson_combination}", cat=LpBinary)
    for day in Days
    for teacher in Teachers
    for lesson_combination in range(len(lesson_combinations))
}

lesson_used = {
    (day.index, lesson.index, clazz.index): LpVariable(f"lu_{day.index}_{lesson.index}_{clazz.index}", cat=LpBinary)
    for day in Days
    for lesson in Lessons
    for clazz in Classes
}

teacher_school_end = {
    (teacher.index, day.index, school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE):
    LpVariable(
        f"tse_{teacher.index}_{day.index}_{school_end_lesson.index if school_end_lesson != LESSONS_NONE else 'N'}", cat=LpBinary)
    for day in Days
    for teacher in Teachers
    for school_end_lesson in school_end_lessons
}

same_day_school_end = {
    (day.index, school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE):
    LpVariable(
        f"sdse_{day.index}_{school_end_lesson.index if school_end_lesson != LESSONS_NONE else 'N'}", cat=LpBinary)
    for day in Days
    for school_end_lesson in school_end_lessons
}

teacher_day_ogs = {
    (teacher.index, day.index, ogs_slot.index): LpVariable(f"tdo_{teacher.index}_{day.index}_{ogs_slot.index}", cat=LpBinary)
    for teacher in Teachers
    for day in Days
    for ogs_slot in OgsSlots
}

english_teached_by = {
    (clazz.index, teacher.index): LpVariable(f"etb_{clazz.index}_{teacher.index}", cat=LpBinary)
    for clazz in list(filter(lambda clazz: Subjects.English in clazz.value.lessoncount, Classes))
    for teacher in list(filter(lambda teacher: Subjects.English in teacher.value.subjects, Teachers))
}

# OPTIMIZED: Much more efficient teacher-class constraint
# Instead of creating indicator variables and complex constraints,
# we'll use a direct formulation that's more efficient
print("Creating problem and constraints...")
problem = LpProblem("Stundenplan", sense=LpMaximize)
# endregion

# region persönliche constraints
# * Ma startet um 8 oder hat frei
for day in Days:
    ma_lessons = [x.get((day.index, Lessons.First.index, clazz.index, lesson), 0)
                  for clazz in Classes
                  for lesson in teacher_to_lessons[Teachers.Ma]
                  if (day.index, Lessons.First.index, clazz.index, lesson) in x]

    problem.addConstraint(lpSum(ma_lessons) +
                          teacher_school_end[(Teachers.Ma.index, day.index, LESSONS_NONE)] == 1)
# endregion

print("Adding main constraints...")

# region default constraints
# * Jede Klasse hat genau n stunden aus fach c pro Woche
for clazz in Classes:
    for subject in list(filter(lambda s: s in clazz.value.lessoncount, list(Subjects))):
        subject_vars = [x.get((day.index, lesson.index, clazz.index, combo), 0)
                        for day in Days
                        for lesson in Lessons
                        for combo in subject_lessons[subject]
                        if (day.index, lesson.index, clazz.index, combo) in x]

        if clazz.value.lessoncount[subject].min == clazz.value.lessoncount[subject].max:
            problem.addConstraint(lpSum(subject_vars) ==
                                  clazz.value.lessoncount[subject].min)
        else:
            problem.addConstraint(lpSum(subject_vars) >=
                                  clazz.value.lessoncount[subject].min)
            problem.addConstraint(lpSum(subject_vars) <=
                                  clazz.value.lessoncount[subject].max)

# Klassen haben stufenweise gleich viele Stunden
for clazz in [Classes.FirstA, Classes.SecondA, Classes.ThirdA, Classes.FourthA]:
    clazz_vars = [x.get((day.index, lesson.index, clazz.index, combo), 0)
                  for day in Days for lesson in Lessons for combo in n_teacher_subject_combinations
                  if (day.index, lesson.index, clazz.index, combo) in x]

    clazz_b_vars = [x.get((day.index, lesson.index, clazz.index+1, combo), 0)
                    for day in Days for lesson in Lessons for combo in n_teacher_subject_combinations
                    if (day.index, lesson.index, clazz.index+1, combo) in x]

    problem.addConstraint(lpSum(clazz_vars) == lpSum(clazz_b_vars))

# * Jede klasse hat in der ersten Stunde jeden tages unterricht
for day in Days:
    for clazz in Classes.but_remedial():
        first_hour_vars = [x.get((day.index, Lessons.First.index, clazz.index, combo), 0)
                           for combo in n_teacher_subject_combinations
                           if (day.index, Lessons.First.index, clazz.index, combo) in x]
        problem.addConstraint(lpSum(first_hour_vars) == 1)

# * Jeder Lehrer darf an jedem Tag in jeder Stunde nur eine Klasse unterrichten
for teacher in Teachers:
    for day in Days:
        for lesson in Lessons:
            teacher_vars = [x.get((day.index, lesson.index, clazz.index, combo), 0)
                            for clazz in Classes
                            for combo in n_teacher_subject_combinations
                            if teacher in teacher_subject_combinations[combo]["teachers"]
                            and (day.index, lesson.index, clazz.index, combo) in x]

            combination_vars = [teacher_day_lesson_combination[(teacher.index, day.index, combination)] * lesson_combinations[combination][lesson.index]
                                for combination in n_lesson_combinations]

            problem.addConstraint(lpSum(teacher_vars) ==
                                  lpSum(combination_vars))

# * An jedem Tag hat jede Klasse maximal eine Stunde englisch
for day in Days:
    for clazz in Classes.but_remedial():
        english_vars = [x.get((day.index, lesson.index, clazz.index, combo), 0)
                        for lesson in Lessons for combo in subject_lessons[Subjects.English]
                        if (day.index, lesson.index, clazz.index, combo) in x]
        problem.addConstraint(lpSum(english_vars) <= 1)

# * An jedem Tag hat jede Klasse maximal eine Stunde religion
for day in Days:
    for clazz in Classes.but_remedial():
        religion_vars = [x.get((day.index, lesson.index, clazz.index, combo), 0)
                         for lesson in Lessons for combo in subject_lessons[Subjects.Religion]
                         if (day.index, lesson.index, clazz.index, combo) in x]
        problem.addConstraint(lpSum(religion_vars) <= 1)

# * Für jeden Slot darf nur eine Combination ausgewählt sein
for day in Days:
    for lesson in Lessons:
        for clazz in Classes:
            slot_vars = [x.get((day.index, lesson.index, clazz.index, combo), 0)
                         for combo in n_teacher_subject_combinations
                         if (day.index, lesson.index, clazz.index, combo) in x]
            problem.addConstraint(lpSum(slot_vars) == lesson_used[(
                day.index, lesson.index, clazz.index)])

# * Jeder Lehrer darf nur eine bestimmte Stundenzahl pro Woche unterrichten
for teacher in Teachers:
    teacher_lesson_vars = [x.get((day.index, lesson.index, clazz.index, combo), 0)
                           for day in Days
                           for lesson in Lessons
                           for clazz in Classes
                           for combo in n_teacher_subject_combinations
                           if teacher in teacher_subject_combinations[combo]["teachers"]
                           and (day.index, lesson.index, clazz.index, combo) in x]

    ogs_vars = [teacher_day_ogs[(teacher.index, day.index, slot.index)]
                for day in Days for slot in OgsSlots]

    problem.addConstraint(lpSum(teacher_lesson_vars) +
                          lpSum(ogs_vars) == teacher.value.lesson_ct)

# * Alle Klassenstufen haben paarweise gleichzeitig schluss
for classLevel in ClassLevels:
    for day in Days:
        class_a_vars = [x.get((day.index, lesson.index, classLevel.value.classes[0].index, combo), 0)
                        for combo in n_teacher_subject_combinations
                        for lesson in Lessons
                        if (day.index, lesson.index, classLevel.value.classes[0].index, combo) in x]

        class_b_vars = [x.get((day.index, lesson.index, classLevel.value.classes[1].index, combo), 0)
                        for combo in n_teacher_subject_combinations
                        for lesson in Lessons
                        if (day.index, lesson.index, classLevel.value.classes[1].index, combo) in x]

        problem.addConstraint((lpSum(class_a_vars) - lpSum(class_b_vars)) ==
                              p_school_end_deviation[(day.index, classLevel.index)])

# * Keine FREISTUNDEN
for day in Days:
    for clazz in Classes.but_remedial():
        for lesson in list(Lessons)[:-1]:
            problem.addConstraint(
                lesson_used[(day.index, lesson.index, clazz.index)] -
                lesson_used[(day.index, lesson.index + 1, clazz.index)] >= 0)

print("Adding teacher schedule constraints...")

# Teacher end time constraints
for teacher in Teachers:
    for day in Days:
        for school_end_lesson in school_end_lessons:
            end_lesson_idx = school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE
            relevant_combos = last_lesson_to_lesson_combination[end_lesson_idx]

            problem.addConstraint(
                teacher_school_end[(teacher.index, day.index, end_lesson_idx)] ==
                lpSum(teacher_day_lesson_combination[(teacher.index, day.index, combo)] for combo in relevant_combos))

# Same day school end constraints
for day in Days:
    for school_end_lesson in school_end_lessons:
        end_lesson_idx = school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE

        teacher_end_vars = [teacher_school_end[(
            teacher.index, day.index, end_lesson_idx)] for teacher in Teachers]
        free_teachers = [teacher_school_end[(
            teacher.index, day.index, LESSONS_NONE)] for teacher in Teachers]

        problem.addConstraint(
            (lpSum(teacher_end_vars) - (len(Teachers) - lpSum(free_teachers))) * -1 <=
            30 * (1 - same_day_school_end[(day.index, end_lesson_idx)]))

for day in Days:
    end_vars = [same_day_school_end[(day.index, school_end_lesson.index if school_end_lesson != LESSONS_NONE else LESSONS_NONE)]
                for school_end_lesson in school_end_lessons]
    problem.addConstraint(lpSum(end_vars) <= 1)

print("Adding conference day constraints...")

# Conference day constraints
problem.addConstraint(
    lpSum(teacher_school_end[(teacher.index, CONFERENCE_DAY.index, LESSONS_NONE)] for teacher in Teachers) ==
    p_no_school_conference_day)

for teacher in Teachers:
    conf_vars = [x.get((CONFERENCE_DAY.index, lesson.index, clazz.index, combo), 0)
                 for clazz in Classes
                 for lesson in Lessons
                 for combo in n_teacher_subject_combinations
                 if teacher in teacher_subject_combinations[combo]["teachers"]
                 and (CONFERENCE_DAY.index, lesson.index, clazz.index, combo) in x]

    problem.addConstraint(lpSum(conf_vars) ==
                          p_two_hours_on_conference_day[teacher.index])

problem.addConstraint(same_day_school_end[(
    CONFERENCE_DAY.index, CONFERENCE_LESSON.index-1)] == 1)

print("Adding Friday and lesson constraints...")

# Friday constraints
for teacher in Teachers:
    friday_sixth_vars = [x.get((Days.Friday.index, Lessons.Sixth.index, clazz.index, combo), 0)
                         for clazz in Classes
                         for combo in n_teacher_subject_combinations
                         if teacher in teacher_subject_combinations[combo]["teachers"]
                         and (Days.Friday.index, Lessons.Sixth.index, clazz.index, combo) in x]
    problem.addConstraint(lpSum(friday_sixth_vars) == 0)

# No gaps constraint
for teacher in Teachers:
    for day in Days:
        problem.addConstraint(
            lpSum(teacher_day_lesson_combination[(teacher.index, day.index, combo)] for combo in n_lesson_combinations) == 1)

# Minimum 4 hours per day
for day in Days:
    for clazz in Classes.but_remedial():
        problem.addConstraint(
            lpSum(lesson_used[(day.index, lesson.index, clazz.index)] for lesson in Lessons) >= 4)

for day in Days:
    for clazz in Classes.but_remedial():
        for lesson in list(Lessons)[:4]:
            problem.addConstraint(
                lesson_used[(day.index, lesson.index, clazz.index)] == 1)

print("Adding OPTIMIZED teacher-per-class constraint...")

# OPTIMIZED: Much more efficient max 3 teachers per class constraint
# Instead of creating binary indicator variables, we use a direct counting approach
for clazz in Classes:
    eligible_teachers = [
        teacher for teacher in Teachers if class_teacher_eligibility[clazz][teacher]]

    if len(eligible_teachers) <= 3:
        # If only 3 or fewer teachers can teach this class, skip the constraint
        continue

    # Create a simplified constraint using a threshold approach
    # Sum all lessons taught by each teacher, then use a threshold to limit teachers
    teacher_lesson_sums = []

    for teacher in eligible_teachers:
        relevant_combos = class_teacher_eligibility[clazz][teacher]
        if relevant_combos:
            teacher_lessons = [x.get((day.index, lesson.index, clazz.index, combo), 0)
                               for day in Days
                               for lesson in Lessons
                               for combo in relevant_combos
                               if (day.index, lesson.index, clazz.index, combo) in x]

            if teacher_lessons:
                # Create a binary variable indicating if teacher teaches this class
                teaches_var = LpVariable(
                    f"teaches_{clazz.index}_{teacher.index}", cat=LpBinary)

                # If teacher teaches any lesson, the indicator must be 1
                problem.addConstraint(
                    lpSum(teacher_lessons) <= 30 * teaches_var)
                problem.addConstraint(teaches_var <= lpSum(teacher_lessons))

                teacher_lesson_sums.append(teaches_var)

    # Maximum 3 teachers per class
    if teacher_lesson_sums:
        problem.addConstraint(lpSum(teacher_lesson_sums) <= 3)

print("Adding class teacher constraints...")

# Class teacher minimum hours constraint
for clazz in Classes:
    for day in Days:
        classteacher_vars = []
        for combo in n_teacher_subject_combinations:
            for teacher in teacher_subject_combinations[combo]["teachers"]:
                if teacher in clazz.value.classteachers:
                    for lesson in Lessons:
                        var = x.get(
                            (day.index, lesson.index, clazz.index, combo), 0)
                        if var != 0:
                            classteacher_vars.append(var)

        if classteacher_vars:
            problem.addConstraint(lpSum(classteacher_vars) >= 2)

print("Adding OGS constraints...")

# OGS constraints
for day in Days:
    if day not in OGS_DAYS:
        ogs_vars = [teacher_day_ogs[(teacher.index, day.index, slot.index)]
                    for slot in OgsSlots for teacher in Teachers]
        problem.addConstraint(lpSum(ogs_vars) == 0)
        continue

    ogs_vars = [teacher_day_ogs[(teacher.index, day.index, slot.index)]
                for teacher in Teachers for slot in OgsSlots]
    problem.addConstraint(lpSum(ogs_vars) == OGS_DAYS[day])

for teacher in Teachers:
    weekly_ogs = [teacher_day_ogs[(teacher.index, day.index, slot.index)]
                  for day in Days for slot in OgsSlots]
    problem.addConstraint(lpSum(weekly_ogs) <= 1)

for teacher in Teachers:
    for day in Days:
        daily_ogs = [
            teacher_day_ogs[(teacher.index, day.index, slot.index)] for slot in OgsSlots]
        problem.addConstraint(lpSum(daily_ogs) <= 1)

for teacher in Teachers:
    for day in Days:
        problem.addConstraint(
            teacher_day_ogs[(teacher.index, day.index, OgsSlots.Seventh.index)] <=
            teacher_school_end[(teacher.index, day.index, Lessons.Sixth.index)])

print("Adding subject-specific constraints...")

# Religion in last hour
for day in Days:
    for clazz in Classes.but_remedial():
        for slot in list(Lessons)[:-1]:
            religion_vars = [x.get((day.index, slot.index, clazz.index, combo), 0)
                             for combo in subject_lessons[Subjects.Religion]
                             if (day.index, slot.index, clazz.index, combo) in x]
            problem.addConstraint(
                lpSum(religion_vars) <= 1 - lesson_used[(day.index, slot.index+1, clazz.index)])

# Sports constraints
for clazz in Classes.but_remedial():
    if Subjects.Sports not in clazz.value.lessoncount:
        continue
    for day in Days:
        for lesson in Lessons:
            if day in SPORT_SLOTS and lesson in SPORT_SLOTS[day]:
                continue
            for combo in subject_lessons[Subjects.Sports]:
                if (day.index, lesson.index, clazz.index, combo) in x:
                    problem.addConstraint(
                        x[(day.index, lesson.index, clazz.index, combo)] == 0)

for sport_day in SPORT_SLOTS:
    for sport_lesson in SPORT_SLOTS[sport_day]:
        sport_vars = [x.get((sport_day.index, sport_lesson.index, clazz.index, combo), 0)
                      for clazz in Classes.but_remedial()
                      for combo in subject_lessons[Subjects.Sports]
                      if (sport_day.index, sport_lesson.index, clazz.index, combo) in x]
        problem.addConstraint(lpSum(sport_vars) == 2)

        # Third grade sports together
        third_a_vars = [x.get((sport_day.index, sport_lesson.index, Classes.ThirdA.index, combo), 0)
                        for combo in subject_lessons[Subjects.Sports]
                        if (sport_day.index, sport_lesson.index, Classes.ThirdA.index, combo) in x]
        third_b_vars = [x.get((sport_day.index, sport_lesson.index, Classes.ThirdB.index, combo), 0)
                        for combo in subject_lessons[Subjects.Sports]
                        if (sport_day.index, sport_lesson.index, Classes.ThirdB.index, combo) in x]
        problem.addConstraint(lpSum(third_a_vars) == lpSum(third_b_vars))

        # Fourth grade sports together
        fourth_a_vars = [x.get((sport_day.index, sport_lesson.index, Classes.FourthA.index, combo), 0)
                         for combo in subject_lessons[Subjects.Sports]
                         if (sport_day.index, sport_lesson.index, Classes.FourthA.index, combo) in x]
        fourth_b_vars = [x.get((sport_day.index, sport_lesson.index, Classes.FourthB.index, combo), 0)
                         for combo in subject_lessons[Subjects.Sports]
                         if (sport_day.index, sport_lesson.index, Classes.FourthB.index, combo) in x]
        problem.addConstraint(lpSum(fourth_a_vars) == lpSum(fourth_b_vars))

# Same teacher for double sports lessons
for sport_day in SPORT_SLOTS:
    for combo in subject_lessons[Subjects.Sports]:
        for clazz in Classes.but_remedial():
            first_sport = x.get(
                (sport_day.index, SPORT_SLOTS[sport_day][0].index, clazz.index, combo), 0)
            second_sport = x.get(
                (sport_day.index, SPORT_SLOTS[sport_day][1].index, clazz.index, combo), 0)
            if first_sport != 0 and second_sport != 0:
                problem.addConstraint(first_sport == second_sport)

print("Adding final constraints...")

# Equal double assignments by grade level
for clazz in [Classes.FirstA, Classes.SecondA]:
    double_assign_a = [x.get((day.index, lesson.index, clazz.index, combo), 0)
                       for day in Days
                       for lesson in Lessons
                       for combo in n_teacher_subject_combinations
                       if len(teacher_subject_combinations[combo]["teachers"]) == 2
                       and teacher_subject_combinations[combo]["subject"] != Subjects.Swimming
                       and (day.index, lesson.index, clazz.index, combo) in x]

    double_assign_b = [x.get((day.index, lesson.index, clazz.index+1, combo), 0)
                       for day in Days
                       for lesson in Lessons
                       for combo in n_teacher_subject_combinations
                       if len(teacher_subject_combinations[combo]["teachers"]) == 2
                       and teacher_subject_combinations[combo]["subject"] != Subjects.Swimming
                       and (day.index, lesson.index, clazz.index+1, combo) in x]

    problem.addConstraint(lpSum(double_assign_a) == lpSum(double_assign_b))

# First grade no sixth hour
for clazz in [Classes.FirstA, Classes.FirstB]:
    sixth_hour_vars = [
        lesson_used[(day.index, Lessons.Sixth.index, clazz.index)] for day in Days]
    problem.addConstraint(lpSum(sixth_hour_vars) == 0)

# Sc has no OGS
sc_ogs_vars = [teacher_day_ogs[(Teachers.Sc.index, day.index, slot.index)]
               for day in Days for slot in OgsSlots]
problem.addConstraint(lpSum(sc_ogs_vars) == 0)

# English teacher assignments - link english_teached_by to actual lesson assignments
for teacher in Teachers:
    if Subjects.English not in teacher.value.subjects:
        continue
    for clazz in Classes.but_remedial():
        if (clazz.index, teacher.index) not in english_teached_by:
            continue

        # Sum all English lessons taught by this teacher to this class
        english_lessons_by_teacher = [x.get((day.index, lesson.index, clazz.index, combo), 0)
                                      for day in Days
                                      for lesson in Lessons
                                      for combo in subject_lessons[Subjects.English]
                                      if teacher in teacher_subject_combinations[combo]["teachers"]
                                      and (day.index, lesson.index, clazz.index, combo) in x]

        if english_lessons_by_teacher:
            # If teacher teaches any English lesson to this class, english_teached_by must be 1
            problem.addConstraint(lpSum(english_lessons_by_teacher) <=
                                  50 * english_teached_by[(clazz.index, teacher.index)])
            # If english_teached_by is 1, teacher must teach at least one English lesson
            problem.addConstraint(english_teached_by[(
                clazz.index, teacher.index)] <= lpSum(english_lessons_by_teacher))

for clazz in [Classes.ThirdA, Classes.ThirdB]:
    for teacher in list(filter(lambda teacher: Subjects.English in teacher.value.subjects, Teachers)):
        if (clazz.index, teacher.index) in english_teached_by:
            if teacher == Teachers.Sc:
                problem.addConstraint(
                    english_teached_by[(clazz.index, teacher.index)] == 1)
            else:
                problem.addConstraint(
                    english_teached_by[(clazz.index, teacher.index)] == 0)

for clazz in [Classes.FourthA, Classes.FourthB]:
    for teacher in list(filter(lambda teacher: Subjects.English in teacher.value.subjects, Teachers)):
        if (clazz.index, teacher.index) in english_teached_by:
            if teacher == Teachers.Him:
                problem.addConstraint(
                    english_teached_by[(clazz.index, teacher.index)] == 1)
            else:
                problem.addConstraint(
                    english_teached_by[(clazz.index, teacher.index)] == 0)

print("Setting objective...")

# Objective function
classteacher_hours = []
for day in Days:
    for lesson in Lessons:
        for clazz in Classes:
            for combo in n_teacher_subject_combinations:
                for teacher in teacher_subject_combinations[combo]["teachers"]:
                    if teacher in clazz.value.classteachers:
                        var = x.get(
                            (day.index, lesson.index, clazz.index, combo), 0)
                        if var != 0:
                            classteacher_hours.append(var)

school_end_penalties = [p_school_end_deviation[(day.index, classLevel.index)]
                        for classLevel in ClassLevels for day in Days]

fifth_hour_rewards = [lesson_used[(day.index, Lessons.Fifth.index, clazz.index)]
                      for day in Days for clazz in Classes.but_remedial()]

conference_penalties = [
    p_two_hours_on_conference_day[teacher.index] for teacher in Teachers]

problem.setObjective(
    lpSum(classteacher_hours) * 1600
    - lpSum(school_end_penalties)
    - p_no_school_conference_day * 120
    + lpSum(fifth_hour_rewards) * 40
    + lpSum(conference_penalties) * 20
)

print("Problem setup complete!")
print(f"Constraints: {len(problem.constraints)}")
print(f"Variables: {len(problem.variables())}")

# Solve the problem
print("Starting optimization...")
problem.solve(HiGHS_CMD(msg=1))

print("Status:", LpStatus[problem.status])
if problem.status == LpStatusNotSolved:
    exit()

# Generate output (same as original)
day_data = {}
for day in Days:
    day_data[day] = []

for day in Days:
    for lesson in Lessons:
        lesson_data = [lesson.text]
        day_data[day].append(lesson_data)
        for clazz in Classes:
            found_lesson = False
            for combo in n_teacher_subject_combinations:
                var = x.get((day.index, lesson.index, clazz.index, combo), 0)
                if var != 0 and value(var) == 1:
                    lesson_data.append(", ".join(list(map(
                        lambda x: x.text, teacher_subject_combinations[combo]["teachers"]))) +
                        teacher_subject_combinations[combo]["subject"].value.short)
                    found_lesson = True
                    break
            if not found_lesson:
                lesson_data.append("-")
        lesson_data.append("-")

    # OGS data
    teacher_ogs_data = ["7."]
    for clazz in Classes:
        teacher_ogs_data.append("-")
    if sum(value(teacher_day_ogs[(teacher.index, day.index, OgsSlots.Seventh.index)]) for teacher in Teachers) >= 1:
        teachers = []
        for teacher in Teachers:
            if value(teacher_day_ogs[(teacher.index, day.index, OgsSlots.Seventh.index)]) == 1:
                teachers.append(teacher.text)
        teacher_ogs_data.append(", ".join(teachers))
    else:
        teacher_ogs_data.append("-")
    day_data[day].append(teacher_ogs_data)

# Console output
for day in Days:
    print()
    print(day.text + ":")
    header = ["Stunde"]
    for clazz in Classes:
        header.append("%s - %s" % (clazz.text, ",".join(
            [a.text for a in clazz.value.classteachers])))
    header.append("OGS")
    print(tabulate(day_data[day], headers=header))

# Write to file
with open("Stundenplan2.csv", "w", encoding="utf-8") as text_file:
    for day in Days:
        header = [day.text, "Stunde"]
        for clazz in Classes:
            header.append("%s - %s" % (clazz.text, ",".join(
                [a.text for a in clazz.value.classteachers])))
        header.append("OGS")
        text_file.write(";".join(header)+"\n")
        for lesson in range(len(day_data[day])):
            text_file.write(";"+";".join(day_data[day][lesson])+"\n")
        text_file.write("\n")
    text_file.close()

print("Optimized solution saved to Stundenplan2.csv")
