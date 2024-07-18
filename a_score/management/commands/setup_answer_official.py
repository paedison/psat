import pandas as pd
from django.apps import apps
from django.core.management.base import BaseCommand

FIELDS = {
    '헌법': 'heonbeob', '언어': 'eoneo', '자료': 'jaryo', '상황': 'sanghwang',
    '형사': 'hyeongsa', '경찰': 'gyeongchal', '범죄': 'beomjoe',
    '행법': 'haengbeob', '행학': 'haenghag', '민법': 'minbeob', '세법': 'sebeob',
    '회계': 'hoegye', '상법': 'sangbeob', '경제': 'gyeongje', '통계': 'tonggye',
    '재정': 'jaejeong', '정보': 'jeongbo', '시네': 'sine', '데베': 'debe',
    '통신': 'tongsin', '소웨': 'sowe',
    '형사법': 'hyeongsa', '경찰학': 'gyeongchal', '범죄학': 'beomjoe',
    '행정법': 'haengbeob', '행정학': 'haenghag', '민법총칙': 'minbeob',
    '세법개론': 'sebeob', '회계학': 'hoegye', '상법총칙': 'sangbeob',
    '경제학': 'gyeongje', '통계학': 'tonggye', '재정학': 'jaejeong',
    '정보보호론': 'jeongbo', '시스템네트워크보안': 'sine', '데이터베이스론': 'debe',
    '통신이론': 'tongsin', '소프트웨어공학': 'sowe',
}


class Command(BaseCommand):
    help = 'Setup answer official'

    def add_arguments(self, parser):
        parser.add_argument('app_label', type=str, help='App name')  # a_score
        parser.add_argument('model_name', type=str, help='Model name')  # PrimePsatExam
        parser.add_argument('exam_year', type=str, help='Year')  # 2024
        parser.add_argument('exam_exam', type=str, help='Exam')  # 프모
        parser.add_argument('exam_round', type=str, help='Round')  # 1
        parser.add_argument('file_name', type=str, help='Excel file containing official answer')

    def handle(self, *args, **kwargs):
        app_label = kwargs['app_label']
        model_name = kwargs['model_name']
        exam_year = kwargs['exam_year']
        exam_exam = kwargs['exam_exam']
        exam_round = kwargs['exam_round']
        file_name = kwargs['file_name']

        exam_info = {'year': exam_year, 'exam': exam_exam, 'round': exam_round}
        exam_model = apps.get_model(app_label=app_label, model_name=model_name)
        answer_official = get_answer_official(file_name=file_name)
        create_or_update_exam_model(
            exam_model=exam_model, exam_info=exam_info, answer_official=answer_official)


def get_answer_official(file_name: str) -> dict:
    df = pd.read_excel(file_name, sheet_name='정답', header=0, index_col=0)
    df.apply(pd.to_numeric, errors='coerce').fillna(0)

    new_columns = []
    for col in df.columns:
        new_columns.append(FIELDS.get(col, col))
    df.columns = new_columns

    answer_official = {}
    for field, answers in df.items():
        answer_official.update({field: [int(ans) for ans in answers]})
    return answer_official


def create_or_update_exam_model(exam_model, exam_info: dict, answer_official: dict):
    qs_exam, created = exam_model.objects.get_or_create(**exam_info)
    model_name = exam_model._meta.model_name
    if created:
        qs_exam.answer_official = answer_official
        qs_exam.save()
        message = f'Successfully created {model_name} instance'
    else:
        if qs_exam.answer_official != answer_official:
            qs_exam.answer_official = answer_official
            qs_exam.save()
            message = f'Successfully updated {model_name} instance'
        else:
            message = f'No changes were made to {model_name} instances.'
    print(message)
