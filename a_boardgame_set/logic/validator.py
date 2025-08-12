def is_valid_set(cards):
    if len(cards) != 3:
        return False

    for attr in ['color', 'shape', 'count', 'fill']:
        values = {getattr(card, attr) for card in cards}
        if len(values) == 2:  # 2개면 무조건 세트 아님
            return False
    return True
