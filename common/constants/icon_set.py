class ConstantIconSet:
    """Represent icon constant."""
    ICON_MENU = {
        'admin': '<i class="fa-solid fa-crown fa-fw"></i>',

        'notice': '<i class="fa-solid fa-bullhorn fa-fw"></i>',
        'dashboard': '<i class="fa-solid fa-list fa-fw"></i>',
        'psat': '<i class="fa-solid fa-layer-group fa-fw"></i>',
        'problem': '<i class="fa-solid fa-file-lines fa-fw"></i>',
        'like': '<i class="fa-solid fa-heart fa-fw"></i>',
        'rate': '<i class="fa-solid fa-star fa-fw"></i>',
        'solve': '<i class="fa-solid fa-circle-check fa-fw"></i>',
        'memo': '<i class="fa-solid fa-note-sticky fa-fw"></i>',
        'tag': '<i class="fa-solid fa-tag fa-fw"></i>',
        'search': '<i class="fa-solid fa-magnifying-glass fa-fw"></i>',
        'community': '<i class="fa-solid fa-users-line fa-fw"></i>',
        'score': '<i class="fa-solid fa-chart-simple fa-fw"></i>',
        'prime': '<i class="fa-solid fa-file fa-fw"></i>',
        'schedule': '<i class="fa-regular fa-calendar-days fa-fw"></i>',

        'qna': '<i class="fa-solid fa-clipboard-question fa-fw"></i>',
        'profile': '<i class="fa-solid fa-user fa-fw"></i>',
        'account': '<i class="fa-solid fa-user fa-fw"></i>',
        'signup': '<i class="fa-solid fa-door-open fa-fw"></i>',
        'login': '<i class="fa-solid fa-sign-in-alt fa-fw"></i>',
        'logout': '<i class="fa-solid fa-sign-out-alt fa-fw"></i>',
        'study': '<i class="fa-solid fa-tag fa-fw"></i>',
    }

    ICON_BOARD = {
        'top_fixed': '<i class="fa-solid fa-bullhorn fa-fw"></i>',
        'is_hidden': '<i class="fa-solid fa-lock fa-fw"></i>',
        'list': '<i class="fa-solid fa-list fa-fw"></i>',
        'reply': '<i class="fa-solid fa-reply fa-fw"></i>',
        'update': '<i class="fa-solid fa-pen"></i>',
        'delete': '<i class="fa-solid fa-trash"></i>',
        'prev': '<i class="fa-solid fa-arrow-down fa-fw"></i>',
        'next': '<i class="fa-solid fa-arrow-up fa-fw"></i>',
        'category0': '<i class="fa-solid fa-bars fa-fw"></i>',
        'category1': '<i class="fa-regular fa-bell fa-fw"></i>',
        'category2': '<i class="fa-regular fa-bookmark fa-fw"></i>',
    }

    ICON_LIKE = {
        'true': '<i class="fa-solid fa-heart"></i>',
        'false': '<i class="fa-solid fa-heart text-gray-300"></i>',
        'filter': '<i class="fa-regular fa-heart"></i>',
    }

    ICON_SOLVE = {
        'true': '<i class="fa-solid fa-circle-check"></i>',
        'false': '<i class="fa-solid fa-circle-xmark"></i>',
        'none': '<i class="fa-solid fa-circle-check text-gray-300"></i>',
        'filter': '<i class="fa-regular fa-circle-check"></i>',
    }

    ICON_MEMO = {
        'true': '<i class="fa-solid fa-note-sticky"></i>',
        'false': '<i class="fa-solid fa-note-sticky text-gray-300"></i>',
        'filter': '<i class="fa-regular fa-note-sticky"></i>',
        'white': '<i class="fa-regular fa-note-sticky fa-fw text-white"></i>',
    }

    ICON_TAG = {
        'true': '<i class="fa-solid fa-tag text-primary"></i>',
        'false': '<i class="fa-solid fa-tag text-gray-300"></i>',
        'filter': '<i class="fa-solid fa-tag"></i>',
        'white': '<i class="fa-solid fa-tag fa-fw text-white"></i>',
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
        }
    ICON_RATE = get_star_icons()

    ICON_NAV = {
        'left_arrow': '<i class="fa-solid fa-arrow-left"></i>',
        'prev_prob': '<i class="fa-solid fa-arrow-up"></i>',
        'next_prob': '<i class="fa-solid fa-arrow-down"></i>',
        'list': '<i class="fa-solid fa-list"></i>',
        'print': '<i class="fa-solid fa-print"></i>',
    }

    ICON_FILTER = '<i class="fa-solid fa-filter"></i>'

    ICON_SUBJECT = {
        '전체': '<i class="fa-solid fa-bars fa-fw"></i>',
        '언어': '<i class="fa-solid fa-language fa-fw"></i>',
        '자료': '<i class="fa-solid fa-table-cells-large fa-fw"></i>',
        '상황': '<i class="fa-solid fa-scale-balanced fa-fw"></i>',
        '헌법': '<i class="fa-solid fa-gavel"></i>',
    }

    ICON_SEARCH = '<i class="fa-solid fa-magnifying-glass fa-fw"></i>'
