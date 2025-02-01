from datetime import datetime


def year_choice() -> list:
    choice = [(year, f'{year}년') for year in range(2004, datetime.now().year + 2)]
    choice.reverse()
    return choice


def exam_choice() -> dict:
    return {'프모': '프라임 PSAT 전국모의고사'}


def round_choice() -> list:
    return [(rnd, f'{rnd}회') for rnd in range(1, 7)]


def unit_choice() -> dict:
    return {
        '5급공채': '5급공채',
        '7급공채': '7급공채',
        '외교관후보자': '외교관후보자',
        '지역인재 7급': '지역인재 7급',
        '기타': '기타',
    }


def department_choice() -> dict:
    return {
        '5급공채': {
            '5급 일반행정': '5급 일반행정',
            '5급 재경': '5급 재경',
            '5급 과학기술': '5급 과학기술',
            '5급 기타': '5급 기타'
        },
        '7급공채': {
            '7급공채': '7급공채',
        },
        '외교관후보자': {'일반외교': '일반외교'},
        '지역인재 7급': {
            '지역인재 7급': '지역인재 7급',
        },
        '기타': {'기타 직렬': '기타 직렬'},
    }


def statistics_department_choice() -> dict:
    departments = department_choice()
    departments.update({'전체': {'전체': '전체'}})
    return departments


def get_departments():
    departments = []
    for unit, department in department_choice().items():
        for key in department.keys():
            departments.append(key)
    return departments


def subject_choice() -> dict:
    return {
        '헌법': '헌법',
        '언어': '언어논리',
        '자료': '자료해석',
        '상황': '상황판단',
    }


def lecture_subject_choice() -> dict:
    return {'언어': '언어논리', '자료': '자료해석', '상황': '상황판단'}


def number_choice() -> list:
    return [(number, f'{number}번') for number in range(1, 41)]


def answer_choice() -> dict:
    return {
        1: '①', 2: '②', 3: '③', 4: '④', 5: '⑤',
        12: '①②', 13: '①③', 14: '①④', 15: '①⑤',
        23: '②③', 24: '②④', 25: '②⑤',
        34: '③④', 35: '③⑤', 45: '④⑤',
        123: '①②③', 124: '①②④', 125: '①②⑤',
        134: '①③④', 135: '①③⑤', 145: '①④⑤',
        234: '②③④', 235: '②③⑤', 245: '②④⑤', 345: '③④⑤',
        1234: '①②③④', 1235: '①②③⑤', 1245: '①②④⑤', 1345: '①③④⑤',
        12345: '①②③④⑤',
    }
