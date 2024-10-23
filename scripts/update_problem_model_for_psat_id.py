import traceback

import django.db.utils
from django.db import transaction

from a_psat import models


def run():
    qs_problem = models.Problem.objects.all()
    update_list = []
    for problem in qs_problem:
        try:
            psat = models.Psat.objects.get(year=problem.year, exam=problem.exam)
            if problem.psat != psat:
                problem.psat_id = psat.id
                update_list.append(problem)
        except models.Psat.DoesNotExist:
            print(f'Does not exist matching for {problem.year}{problem.exam}.')

    messages = {}
    try:
        with transaction.atomic():
            if update_list:
                models.Problem.objects.bulk_update(update_list, ['psat_id'])
                messages['update'] = f'Successfully updated {len(update_list)} Problem instances.'
            else:
                messages['error'] = f'No changes were made to Problem instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        messages['error'] = 'An error occurred during the transaction.'

    for message in messages.values():
        if message:
            print(message)
