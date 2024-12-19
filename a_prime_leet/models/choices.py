from datetime import datetime


def year_choice() -> list:
    choice = [(year, f'{year}년') for year in range(2025, datetime.now().year + 3)]
    choice.reverse()
    return choice


def exam_choice() -> dict:
    return {'프모': '프라임 LEET 전국모의고사'}


def round_choice() -> list:
    return [(rnd, f'{rnd}회') for rnd in range(1, 7)]


def subject_choice() -> dict:
    return {
        '언어': '언어이해',
        '추리': '추리논증',
    }


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
