import os
import random
import shutil

from openpyxl import Workbook, load_workbook

from a_psat.models import Problem


def run(
        start_year=2004, end_year=2025, problem_count=40, subject='',
        file_name='problem_list.xlsx',
        folder_name='a_psat/data/selected_problems',
):
    subjects = ['언어', '자료', '상황']
    start_year = int(start_year)
    end_year = int(end_year)
    problem_count = int(problem_count)

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    wb_filepath = f'{folder_name}/{file_name}'
    wb, ws, new_worksheet_number = get_workbook_and_worksheet(wb_filepath)

    # 기존 엑셀 파일에서 문제 리스트 읽기
    extracted_problem_ids = load_existing_problem_ids(wb)

    # 문제 추출
    selected_problems = []
    if subject:
        selected_problems = get_selected_problems(
            start_year, end_year, problem_count, subject,
            selected_problems, extracted_problem_ids
        )
    else:
        for sub in subjects:
            selected_problems = get_selected_problems(
                start_year, end_year, problem_count, sub,
                selected_problems, extracted_problem_ids
            )

    exam_order = {'민경': 1, '칠급': 2, '외시': 3, '행시': 4}
    selected_problems_sorted = sorted(
        selected_problems, key=lambda prob: (prob.subject, exam_order.get(prob.psat.exam, 5), prob.number))

    # 엑셀 파일로 저장
    save_to_excel(selected_problems_sorted, ws)
    wb.save(wb_filepath)
    print(f"문제가 '{folder_name}/{wb_filepath}' 파일로 저장되었습니다.")

    # 이미지 파일 복사 및 정리
    organize_image_files(selected_problems_sorted, folder_name, new_worksheet_number)


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


def get_selected_problems(
        start_year, end_year, problem_count, subject,
        all_selected_problems, extracted_problem_ids,
):
    problems = (
        Problem.objects.select_related('psat')
        .filter(psat__year__range=(start_year, end_year), subject=subject)
        .exclude(id__in=extracted_problem_ids).exclude(psat__exam='입시')
    )
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


def organize_image_files(problems, folder_name, worksheet_number):
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

        # 원본 파일명
        original_file_1 = f"PSAT{year}{exam}{subject}{number:02}-1.png"
        original_file_2 = f"PSAT{year}{exam}{subject}{number:02}-2.png"

        # 원본 파일 경로
        original_file_path_1 = os.path.join(base_image_path, str(year), original_file_1)
        original_file_path_2 = os.path.join(base_image_path, str(year), original_file_2)

        # 새로운 파일명
        new_file_1 = f"{subject}{sorted_number:02}_{original_file_1}"
        new_file_2 = f"{subject}{sorted_number:02}_{original_file_2}"

        # 새로운 파일 경로
        new_file_path_1 = os.path.join(folder, new_file_1)
        new_file_path_2 = os.path.join(folder, new_file_2)

        # 파일이 존재하면 복사
        if os.path.exists(original_file_path_1):
            shutil.copy(original_file_path_1, new_file_path_1)
            # self.stdout.write(f"Copied {original_file_1} to {new_file_path_1}")

        if os.path.exists(original_file_path_2):
            shutil.copy(original_file_path_2, new_file_path_2)
            # self.stdout.write(f"Copied {original_file_2} to {new_file_path_2}")

        # 과목별로 sorted_number 증가
        subject_counters[subject] += 1
