def get_star_icons():
    solid_star = '<i class="fa-solid fa-star rate_true"></i>'
    empty_star = '<i class="fa-solid fa-star rate_false"></i>'
    return {
        'True': solid_star,
        'False': empty_star,
        'star': "".join([empty_star for _ in range(0, 5)]),
        'starNone': "".join([empty_star for _ in range(0, 5)]),
        'star0': "".join([empty_star for _ in range(0, 5)]),
        'star1': "".join([solid_star for _ in range(0, 1)] + [empty_star for _ in range(0, 4)]),
        'star2': "".join([solid_star for _ in range(0, 2)] + [empty_star for _ in range(0, 3)]),
        'star3': "".join([solid_star for _ in range(0, 3)] + [empty_star for _ in range(0, 2)]),
        'star4': "".join([solid_star for _ in range(0, 4)] + [empty_star for _ in range(0, 1)]),
        'star5': "".join([solid_star for _ in range(0, 5)]),
        'filter': '<i class="fa-regular fa-star"></i>',
        'white': '<i class="fa-solid fa-star text-white"></i>',
    }


ICON_MENU = {
    'admin': '<i class="fa-solid fa-fw fa-crown"></i>',

    'notice': '<i class="fa-solid fa-fw fa-bullhorn"></i>',
    'dashboard': '<i class="fa-solid fa-fw fa-list"></i>',
    'psat': '<i class="fa-solid fa-fw fa-layer-group"></i>',
    'problem': '<i class="fa-solid fa-fw fa-file-lines"></i>',
    'like': '<i class="fa-solid fa-fw fa-heart"></i>',
    'rate': '<i class="fa-solid fa-fw fa-star"></i>',
    'solve': '<i class="fa-solid fa-fw fa-circle-check"></i>',
    'memo': '<i class="fa-solid fa-fw fa-note-sticky"></i>',
    'tag': '<i class="fa-solid fa-fw fa-tag"></i>',
    'search': '<i class="fa-solid fa-fw fa-magnifying-glass"></i>',
    'community': '<i class="fa-solid fa-fw fa-users-line"></i>',
    'predict': '<i class="fa-solid fa-fw fa-arrows-up-to-line"></i>',
    'score': '<i class="fa-solid fa-fw fa-chart-simple"></i>',
    'prime': '<i class="fa-solid fa-fw fa-file"></i>',
    'schedule': '<i class="fa-regular fa-fw fa-calendar-days"></i>',

    'qna': '<i class="fa-solid fa-fw fa-clipboard-question"></i>',
    'profile': '<i class="fa-solid fa-fw fa-user"></i>',
    'account': '<i class="fa-solid fa-fw fa-user"></i>',
    'signup': '<i class="fa-solid fa-fw fa-door-open"></i>',
    'login': '<i class="fa-solid fa-fw fa-sign-in-alt"></i>',
    'logout': '<i class="fa-solid fa-fw fa-sign-out-alt"></i>',
    'lecture': '<i class="fa-solid fa-fw fa-pen-to-square"></i>',
}

ICON_BOARD = {
    'top_fixed': '<i class="fa-solid fa-fw fa-bullhorn"></i>',
    'is_hidden': '<i class="fa-solid fa-fw fa-lock"></i>',
    'list': '<i class="fa-solid fa-fw fa-list"></i>',
    'reply': '<i class="fa-solid fa-fw fa-reply fa-fw rotate-180"></i>',
    'update': '<i class="fa-solid fa-fw fa-pen"></i>',
    'delete': '<i class="fa-solid fa-fw fa-trash"></i>',
    'prev': '<i class="fa-solid fa-fw fa-arrow-down"></i>',
    'next': '<i class="fa-solid fa-fw fa-arrow-up"></i>',
    'category0': '<i class="fa-solid fa-fw fa-bars"></i>',
    'category1': '<i class="fa-regular fa-fw fa-bell"></i>',
    'category2': '<i class="fa-regular fa-fw fa-bookmark"></i>',
}

ICON_LIKE = {
    'True': '<i class="fa-solid fa-heart like_true"></i>',
    'False': '<i class="fa-solid fa-heart like_false"></i>',
    'filter': '<i class="fa-regular fa-heart"></i>',
    'white': '<i class="fa-solid fa-heart text-white"></i>',
}

ICON_SOLVE = {
    'True': '<i class="fa-solid fa-circle-check answer_true"></i>',
    'False': '<i class="fa-solid fa-circle-xmark answer_false"></i>',
    'None': '<i class="fa-solid fa-circle-check answer_none"></i>',
    'filter': '<i class="fa-regular fa-circle-check"></i>',
    'white': '<i class="fa-solid fa-circle-check text-white"></i>',
}

ICON_MEMO = {
    'True': '<i class="fa-solid fa-note-sticky memo_true"></i>',
    'False': '<i class="fa-solid fa-note-sticky memo_false"></i>',
    'filter': '<i class="fa-regular fa-note-sticky"></i>',
    'white': '<i class="fa-solid fa-note-sticky text-white"></i>',
}

ICON_TAG = {
    'True': '<i class="fa-solid fa-tag text-primary"></i>',
    'False': '<i class="fa-solid fa-tag text-gray-300"></i>',
    'filter': '<i class="fa-solid fa-tag"></i>',
    'white': '<i class="fa-solid fa-tag text-white"></i>',
}

ICON_COLLECTION = {
    'True': '<i class="fa-solid fa-folder-plus text-primary"></i>',
    'False': '<i class="fa-solid fa-folder-plus text-gray-300"></i>',
}

ICON_QUESTION = {
    'True': '<i class="fa-solid fa-circle-question text-success"></i>',
    'False': '<i class="fa-solid fa-circle-question text-gray-300"></i>',
    'filter': '<i class="fa-regular fa-circle-question"></i>',
    'white': '<i class="fa-regular fa-circle-question text-white"></i>',
}

ICON_IMAGE = {
    'True': '<i class="fa-solid fa-image text-danger"></i>',
    'False': '<i class="fa-solid fa-image text-gray-300"></i>',
}

ICON_RATE = get_star_icons()

ICON_NAV = {
    'left_arrow': '<i class="fa-solid fa-arrow-left"></i>',
    'prev_prob': '<i class="fa-solid fa-arrow-up"></i>',
    'next_prob': '<i class="fa-solid fa-arrow-down"></i>',
    'left': '<i class="fa-solid fa-arrow-left"></i>',
    'up': '<i class="fa-solid fa-arrow-up"></i>',
    'down': '<i class="fa-solid fa-arrow-down"></i>',
    'list': '<i class="fa-solid fa-list"></i>',
    'print': '<i class="fa-solid fa-print"></i>',
}

ICON_FILTER = '<i class="fa-solid fa-filter"></i>'

ICON_SUBJECT = {
    '전체': '<i class="fa-solid fa-fw fa-bars"></i>',
    '헌법': '<i class="fa-solid fa-fw fa-gavel"></i>',
    '언어': '<i class="fa-solid fa-fw fa-language"></i>',
    '자료': '<i class="fa-solid fa-fw fa-table-cells-large"></i>',
    '상황': '<i class="fa-solid fa-fw fa-scale-balanced"></i>',
    '피셋': '',
    '총점': '',
    '평균': '',
    '형사': '',
    '경찰': '',
    '범죄': '',
    '민법': '',
    '행학': '',
    '행법': '',
}

ICON_SEARCH = '<i class="fa-solid fa-fw fa-magnifying-glass"></i>'


class ConstantIconSet:
    """Represent icon constant."""
    ICON_MENU = {
        'admin': '<i class="fa-solid fa-fw fa-crown"></i>',

        'notice': '<i class="fa-solid fa-fw fa-bullhorn"></i>',
        'dashboard': '<i class="fa-solid fa-fw fa-list"></i>',
        'psat': '<i class="fa-solid fa-fw fa-layer-group"></i>',
        'problem': '<i class="fa-solid fa-fw fa-file-lines"></i>',
        'like': '<i class="fa-solid fa-fw fa-heart"></i>',
        'rate': '<i class="fa-solid fa-fw fa-star"></i>',
        'solve': '<i class="fa-solid fa-fw fa-circle-check"></i>',
        'memo': '<i class="fa-solid fa-fw fa-note-sticky"></i>',
        'tag': '<i class="fa-solid fa-fw fa-tag"></i>',
        'search': '<i class="fa-solid fa-fw fa-magnifying-glass"></i>',
        'community': '<i class="fa-solid fa-fw fa-users-line"></i>',
        'predict': '<i class="fa-solid fa-fw fa-arrows-up-to-line"></i>',
        'score': '<i class="fa-solid fa-fw fa-chart-simple"></i>',
        'prime': '<i class="fa-solid fa-fw fa-file"></i>',
        'schedule': '<i class="fa-regular fa-fw fa-calendar-days"></i>',

        'qna': '<i class="fa-solid fa-fw fa-clipboard-question"></i>',
        'profile': '<i class="fa-solid fa-fw fa-user"></i>',
        'account': '<i class="fa-solid fa-fw fa-user"></i>',
        'signup': '<i class="fa-solid fa-fw fa-door-open"></i>',
        'login': '<i class="fa-solid fa-fw fa-sign-in-alt"></i>',
        'logout': '<i class="fa-solid fa-fw fa-sign-out-alt"></i>',
        'lecture': '<i class="fa-solid fa-fw fa-pen-to-square"></i>',
    }

    ICON_BOARD = {
        'top_fixed': '<i class="fa-solid fa-fw fa-bullhorn"></i>',
        'is_hidden': '<i class="fa-solid fa-fw fa-lock"></i>',
        'list': '<i class="fa-solid fa-fw fa-list"></i>',
        'reply': '<i class="fa-solid fa-fw fa-reply fa-fw rotate-180"></i>',
        'update': '<i class="fa-solid fa-fw fa-pen"></i>',
        'delete': '<i class="fa-solid fa-fw fa-trash"></i>',
        'prev': '<i class="fa-solid fa-fw fa-arrow-down"></i>',
        'next': '<i class="fa-solid fa-fw fa-arrow-up"></i>',
        'category0': '<i class="fa-solid fa-fw fa-bars"></i>',
        'category1': '<i class="fa-regular fa-fw fa-bell"></i>',
        'category2': '<i class="fa-regular fa-fw fa-bookmark"></i>',
    }

    ICON_LIKE = {
        'true': '<i class="fa-solid fa-heart"></i>',
        'false': '<i class="fa-solid fa-heart text-gray-300"></i>',
        'filter': '<i class="fa-regular fa-heart"></i>',
        'white': '<i class="fa-solid fa-heart text-white"></i>',
    }

    ICON_SOLVE = {
        'true': '<i class="fa-solid fa-circle-check"></i>',
        'false': '<i class="fa-solid fa-circle-xmark"></i>',
        'none': '<i class="fa-solid fa-circle-check text-gray-300"></i>',
        'filter': '<i class="fa-regular fa-circle-check"></i>',
        'white': '<i class="fa-solid fa-circle-check text-white"></i>',
    }

    ICON_MEMO = {
        'true': '<i class="fa-solid fa-note-sticky"></i>',
        'false': '<i class="fa-solid fa-note-sticky text-gray-300"></i>',
        'filter': '<i class="fa-regular fa-note-sticky"></i>',
        'white': '<i class="fa-solid fa-note-sticky text-white"></i>',
    }

    ICON_TAG = {
        'true': '<i class="fa-solid fa-tag text-primary"></i>',
        'false': '<i class="fa-solid fa-tag text-gray-300"></i>',
        'filter': '<i class="fa-solid fa-tag"></i>',
        'white': '<i class="fa-solid fa-tag text-white"></i>',
    }

    ICON_COLLECTION = {
        'true': '<i class="fa-solid fa-folder-plus text-primary"></i>',
        'false': '<i class="fa-solid fa-folder-plus text-gray-300"></i>',
    }

    ICON_QUESTION = {
        'true': '<i class="fa-solid fa-circle-question text-success"></i>',
        'false': '<i class="fa-solid fa-circle-question text-gray-300"></i>',
        'filter': '<i class="fa-regular fa-circle-question"></i>',
        'white': '<i class="fa-regular fa-circle-question text-white"></i>',
    }

    ICON_IMAGE = {
        'true': '<i class="fa-solid fa-image text-danger"></i>',
        'false': '<i class="fa-solid fa-image text-gray-300"></i>',
    }

    @staticmethod
    def get_star_icons():
        solid_star = '<i class="fa-solid fa-star m-0"></i>'
        empty_star = '<i class="fa-solid fa-star m-0 text-gray-300"></i>'
        return {
            'star': "".join([empty_star for _ in range(0, 5)]),
            'starNone': "".join([empty_star for _ in range(0, 5)]),
            'star0': "".join([empty_star for _ in range(0, 5)]),
            'star1': "".join([solid_star for _ in range(0, 1)] + [empty_star for _ in range(0, 4)]),
            'star2': "".join([solid_star for _ in range(0, 2)] + [empty_star for _ in range(0, 3)]),
            'star3': "".join([solid_star for _ in range(0, 3)] + [empty_star for _ in range(0, 2)]),
            'star4': "".join([solid_star for _ in range(0, 4)] + [empty_star for _ in range(0, 1)]),
            'star5': "".join([solid_star for _ in range(0, 5)]),
            'filter': '<i class="fa-regular fa-star"></i>',
            'white': '<i class="fa-solid fa-star text-white"></i>',
        }
    ICON_RATE = get_star_icons()

    ICON_NAV = {
        'left_arrow': '<i class="fa-solid fa-arrow-left"></i>',
        'prev_prob': '<i class="fa-solid fa-arrow-up"></i>',
        'next_prob': '<i class="fa-solid fa-arrow-down"></i>',
        'left': '<i class="fa-solid fa-arrow-left"></i>',
        'up': '<i class="fa-solid fa-arrow-up"></i>',
        'down': '<i class="fa-solid fa-arrow-down"></i>',
        'list': '<i class="fa-solid fa-list"></i>',
        'print': '<i class="fa-solid fa-print"></i>',
    }

    ICON_FILTER = '<i class="fa-solid fa-filter"></i>'

    ICON_SUBJECT = {
        '전체': '<i class="fa-solid fa-fw fa-bars"></i>',
        '언어': '<i class="fa-solid fa-fw fa-language"></i>',
        '자료': '<i class="fa-solid fa-fw fa-table-cells-large"></i>',
        '상황': '<i class="fa-solid fa-fw fa-scale-balanced"></i>',
        '헌법': '<i class="fa-solid fa-fw fa-gavel"></i>',
        '피셋': '',
    }

    ICON_SEARCH = '<i class="fa-solid fa-fw fa-magnifying-glass"></i>'
