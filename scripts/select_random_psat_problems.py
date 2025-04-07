import os
import random
import shutil

from PIL import Image
from openpyxl import Workbook, load_workbook

from a_psat.models import Problem


def run():
    start_year = get_user_input('시작 연도(start_year): ', 2004, int)
    end_year = get_user_input('끝 연도(end_year): ', 2025, int)
    exam_type = get_user_input('시험 종류(exam_type)[0: 전체, 1: 기본, 2: 심화]: ', 0, int)
    problem_count = get_user_input('문제 개수(problem_count): ', 40, int)
    subject = get_user_input('과목(subject): ', '', str)
    file_name = get_user_input('파일명(file_name): ', 'problem_list.xlsx', str)
    folder_name = get_user_input('폴더명(folder_name): ', 'a_psat/data/selected_problems', str)

    print('\n[입력 요약]')
    print(f'- 시작 연도: {start_year}')
    print(f'- 끝 연도: {end_year}')
    print(f'- 시험 종류: {exam_type}')
    print(f'- 문제 개수: {problem_count}')
    print(f'- 과목: {subject}')
    print(f'- 파일명: {file_name}')
    print(f'- 폴더명: {folder_name}')
    print('작업을 시작합니다...\n')

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    wb_filepath = f'{folder_name}/{file_name}'
    wb, ws, new_worksheet_number = get_workbook_and_worksheet(wb_filepath)

    # 기존 엑셀 파일에서 문제 리스트 읽기
    extracted_problem_ids = load_existing_problem_ids(wb)

    # 문제 추출
    subjects = ['언어', '자료', '상황']
    selected_problems = []
    if subject:
        selected_problems = select_problems(
            start_year, end_year, exam_type,
            problem_count, subject, selected_problems, extracted_problem_ids
        )
    else:
        for sub in subjects:
            selected_problems = select_problems(
                start_year, end_year, exam_type,
                problem_count, sub, selected_problems, extracted_problem_ids
            )

    exam_order = {'민경': 1, '칠급': 2, '외시': 3, '행시': 4}
    selected_problems_sorted = sorted(
        selected_problems, key=lambda prob: (prob.subject, exam_order.get(prob.psat.exam, 5), prob.number))

    # 엑셀 파일로 저장
    save_to_excel(selected_problems_sorted, ws)
    wb.save(wb_filepath)
    print(f"문제가 '{folder_name}/{wb_filepath}' 파일로 저장되었습니다.")

    # 이미지 파일 복사 및 정리
    organize_image_files(selected_problems_sorted, new_worksheet_number, folder_name)


def get_workbook_and_worksheet(wb_filepath):
    worksheet_number_list = [0]
    if os.path.exists(wb_filepath):
        wb = load_workbook(wb_filepath)
        for sheetname in wb.sheetnames:
            worksheet_number_list.append(int(sheetname))
        new_worksheet_number = max(worksheet_number_list) + 1
        ws = wb.create_sheet(title=str(new_worksheet_number))
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = '1'
        new_worksheet_number = 1
    return wb, ws, new_worksheet_number


def load_existing_problem_ids(workbook) -> set:
    """기존 엑셀 파일에서 추출된 문제의 ID를 읽어옵니다."""
    extracted_ids = set()
    for sheet in workbook.sheetnames:
        worksheet = workbook[sheet]
        for row in worksheet.iter_rows(min_row=2, values_only=True):  # 첫 번째 행은 헤더이므로 건너뜁니다.
            problem_id = row[0]  # 문제 ID는 첫 번째 열에 있다고 가정합니다.
            extracted_ids.add(problem_id)
    return extracted_ids


def select_problems(
        start_year, end_year, exam_type, problem_count, subject,
        all_selected_problems, extracted_problem_ids,
):
    problems = (
        Problem.objects.select_related('psat')
        .filter(psat__year__range=(start_year, end_year), subject=subject)
        .exclude(id__in=extracted_problem_ids).exclude(psat__exam='입시')
    )
    if exam_type == 1:
        problems = problems.filter(psat__exam__in=['민경', '칠급', '칠예', '칠모'])
    elif exam_type == 2:
        problems = problems.filter(psat__exam__in=['행시'])

    selected_problems = random.sample(list(problems), min(problem_count, len(problems)))

    # 추출된 문제 ID를 중복 방지를 위해 기록
    extracted_problem_ids.update(problem.id for problem in selected_problems)

    all_selected_problems.extend(selected_problems)
    return all_selected_problems


def save_to_excel(problems: list, worksheet):
    worksheet.append(["순서", "ID", "일련번호", "연도", "시험", "과목", "책형", "번호", "정답", "발문"])
    for no, problem in enumerate(problems, start=1):
        worksheet.append([
            no, problem.id, problem.reference2,
            problem.psat.year, problem.psat.exam, problem.subject, problem.paper_type,
            problem.number, problem.answer, problem.question,
        ])


def organize_image_files(problems, worksheet_number, folder_name='a_psat/data/selected_problems'):
    base_image_path = "static/image/PSAT"
    folder = os.path.join(folder_name, str(worksheet_number))
    if not os.path.exists(folder):
        os.makedirs(folder)

    # 과목별로 정렬된 문제에 대해 sorted_number를 증가시키면서 파일 복사
    subject_counters = {}

    for sorted_number, problem in enumerate(problems, start=1):
        subject = problem.subject
        year = problem.psat.year
        exam = problem.psat.exam
        number = problem.number

        # 각 과목별로 번호를 독립적으로 관리
        if subject not in subject_counters:
            subject_counters[subject] = 1
        sorted_number = subject_counters[subject]

        def get_image_path(image_number) -> tuple[str, str]:
            image_name = f'PSAT{year}{exam}{subject}{number:02}'
            filename = f'{image_name}-{image_number}.png' if image_number else f'{image_name}.png'
            image_path = os.path.join(base_image_path, str(year), filename)

            new_filename = f"{subject}{sorted_number:02}_{filename}"
            new_image_path = os.path.join(folder, new_filename)

            if os.path.exists(image_path):
                return image_path, new_image_path
            return '', ''

        image_path_0, new_image_path_0 = get_image_path(0)
        if image_path_0:
            shutil.copy(image_path_0, new_image_path_0)
        else:
            image_path_1, new_image_path_1 = get_image_path(1)
            image_path_2, new_image_path_2 = get_image_path(2)
            if image_path_1:
                merged_image_path = new_image_path_1.replace('-1', '')
                if image_path_2:
                    merge_images_vertically(image_path_1, image_path_2, merged_image_path)
                else:
                    shutil.copy(image_path_1, merged_image_path)

        # 과목별로 sorted_number 증가
        subject_counters[subject] += 1


def merge_images_vertically(image_path1, image_path2, output_path):
    # 이미지 열기
    img1 = Image.open(image_path1)
    img2 = Image.open(image_path2)

    # 너비는 동일한 것으로 가정 or 최대값 사용
    width = max(img1.width, img2.width)
    total_height = img1.height + img2.height

    # 새 이미지 생성 (RGB 기준)
    new_img = Image.new('RGB', (width, total_height), color=(255, 255, 255))

    # 이미지 붙이기
    new_img.paste(img1, (0, 0))
    new_img.paste(img2, (0, img1.height))

    # 저장
    new_img.save(output_path)
    print(f"✅ 이미지 저장 완료: {output_path}")


def get_user_input(prompt, default, type_func):
    user_input = input(f"{prompt} [default: {default}]: ").strip()
    return type_func(user_input) if user_input else default
