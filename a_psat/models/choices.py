from datetime import datetime


def year_choice() -> list:
    choice = [(year, f'{year}년') for year in range(2004, datetime.now().year + 2)]
    choice.reverse()
    return choice


def exam_choice() -> dict:
    return {
        '행시': '5급공채/행정고시',
        '입시': '입법고시',
        '칠급': '7급공채',
        '칠예': '7급공채 예시',
        '민경': '민간경력',
        '외시': '외교원/외무고시',
        '견습': '견습',
    }


def predict_exam_choice() -> dict:
    return {
        '행시': '5급공채/외교관/지역인재 7급',
        '입시': '입법고시',
        '칠급': '7급공채/민간경력 5·7급',
    }


def predict_unit_choice() -> dict:
    return {
        '5급 행정': '5급 행정',
        '5급 과학기술': '5급 과학기술',
        '외교관후보자': '외교관후보자',
        '지역인재 7급': '지역인재 7급',
        '입법고시': '입법고시',
        '7급': '7급',
        '민간경력': '민간경력',
    }


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
