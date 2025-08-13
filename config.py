
from models import BaseEnum, Day, Lesson, OgsSlot, Subject


class Days(BaseEnum):
    Monday = Day("Montag")
    Tuesday = Day("Dienstag")
    Wednesday = Day("Mittwoch")
    Thursday = Day("Donnerstag")
    Friday = Day("Freitag")

    def length() -> int:
        return len(Days)

    def range() -> range:
        return range(Days.length())

    @staticmethod
    def by_index(index) -> "BaseEnum":
        return list(Days)[index].value

    @staticmethod
    def text_by_index(index) -> str:
        return Days.by_index(index).text


LESSONS_NONE = -1


class Lessons(BaseEnum):
    First = Lesson("1.")
    Second = Lesson("2.")
    Third = Lesson("3.")
    Fourth = Lesson("4.")
    Fifth = Lesson("5.")
    Sixth = Lesson("6.")

    def length() -> int:
        return len(Lessons)

    def range() -> range:
        return range(Lessons.length())

    @staticmethod
    def by_index(index) -> "BaseEnum":
        return list(Lessons)[index].value

    @staticmethod
    def text_by_index(index) -> str:
        return Lessons.by_index(index).text


class Subjects(BaseEnum):
    Misc = Subject("Sonstiges", "")
    English = Subject("Englisch", " 'E'")
    Swimming = Subject("Schwimmen", " 'Schw'")
    Religion = Subject("Religion", " 'Rel'")
    Sports = Subject("Sport", " 'Sp'")

    def length() -> int:
        return len(Subjects)

    def range() -> range:
        return range(Subjects.length())

    @staticmethod
    def by_index(index) -> "BaseEnum":
        return list(Subjects)[index].value

    @staticmethod
    def text_by_index(index) -> str:
        return Subjects.by_index(index).text


class OgsSlots(BaseEnum):
    Fifth = OgsSlot("5.")
    Eigth = OgsSlot("8.")
