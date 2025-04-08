import os
import random
import shutil

from PIL import Image
import pandas as pd

from a_psat.models import Problem

BASE_IMAGE_FOLDER = 'static/image/PSAT/'
BASE_PDF_FOLDER = '//Newpsatncs/3_배승철/#PSAT 기출문제/'
TARGET_SAVE_FOLDER = 'a_psat/data/selected_problems/'
TARGET_EXCEL_FILE = 'problem_list.xlsx'
OPTION_PROMPT = """
0. 문제 리스트 엑셀·그림·한글 파일로 저장
1. 문제 리스트 추출하여 EXCEL 파일로 저장
2. 추출된 문제 리스트 PNG 파일로 저장
3. 추출된 문제 리스트 PDF 파일로 저장
옵션을 선택해주세요: """


def run():
    if not os.path.exists(TARGET_SAVE_FOLDER):
        os.makedirs(TARGET_SAVE_FOLDER)
    wb_filepath = TARGET_SAVE_FOLDER + TARGET_EXCEL_FILE

    option = get_user_input(OPTION_PROMPT, 0, int)

    if option == 2:
        sheet_name = get_user_input('시트 이름(sheet_name): ', '1', str)
        if os.path.exists(wb_filepath):
            save_image_files(wb_filepath, sheet_name)
        else:
            print(f'{wb_filepath} 파일이 존재하지 않습니다.')
        exit()

    if option == 3:
        sheet_name = get_user_input('시트 이름(sheet_name): ', '1', str)
        pdf_type = get_user_input('PDF 타입(pdf_type)[0: 문제, 1: 손필기]: ', '0', str)
        if os.path.exists(wb_filepath):
            save_pdf_files(wb_filepath, sheet_name, pdf_type)
        else:
            print(f'{wb_filepath} 파일이 존재하지 않습니다.')
        exit()

    start_year = get_user_input('시작 연도(start_year): ', 2004, int)
    end_year = get_user_input('끝 연도(end_year): ', 2025, int)
    exam_type = get_user_input('시험 종류(exam_type)[0: 전체, 1: 기본, 2: 심화]: ', 0, int)
    problem_count = get_user_input('문제 개수(problem_count): ', 40, int)
    subject = get_user_input('과목(subject): ', '', str)

    print('\n[입력 요약]')
    print(f'- 시작 연도: {start_year}')
    print(f'- 끝 연도: {end_year}')
    print(f'- 시험 종류: {exam_type}')
    print(f'- 문제 개수: {problem_count}')
    print(f'- 과목: {subject}')
    print('작업을 시작합니다...\n')

    if option == 1:
        sheet_name, extracted_problem_ids = get_extracted_problem_ids(wb_filepath)
        problem_list = get_selected_problem_list(start_year, end_year, exam_type, problem_count, subject,
                                                 extracted_problem_ids)
        save_to_excel(wb_filepath, problem_list, sheet_name)


def get_user_input(prompt, default, type_func):
    user_input = input(f"{prompt} [default: {default}]: ").strip()
    return type_func(user_input) if user_input else default


def get_extracted_problem_ids(wb_filepath):
    extracted_problem_ids = set()

    if not os.path.exists(wb_filepath):
        return '1', extracted_problem_ids

    xls = pd.ExcelFile(wb_filepath)
    sheet_names = xls.sheet_names
    number_sheets = [int(name) for name in sheet_names if name.isdigit()]
    new_worksheet_number = str(max(number_sheets) + 1) if number_sheets else '1'

    for sheet in sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet)
            extracted_problem_ids.update(set(df['ID'].dropna()))
        except Exception as e:
            print(f"시트 '{sheet}' 로딩 실패: {e}")

    return str(new_worksheet_number), list(extracted_problem_ids)


def get_selected_problem_list(
        start_year, end_year, exam_type, problem_count, subject, extracted_problem_ids,
):
    subjects = [subject] if subject else ['언어', '자료', '상황']
    selected_problem_list = []
    for sub in subjects:
        problems = (
            Problem.objects.select_related('psat')
            .filter(psat__year__range=(start_year, end_year), subject=sub)
            .exclude(psat__exam='입시').exclude(question='').select_related('psat')
        )
        if extracted_problem_ids:
            problems = problems.exclude(id__in=extracted_problem_ids)
        if exam_type == 1:
            problems = problems.filter(psat__exam__in=['민경', '칠급', '칠예', '칠모'])
        elif exam_type == 2:
            problems = problems.filter(psat__exam__in=['행시'])
        selected_problems = random.sample(list(problems), min(problem_count, len(problems)))
        selected_problem_list.extend(selected_problems)

    exam_order = {'민경': 1, '칠급': 2, '외시': 3, '행시': 4}
    selected_problem_list_sorted = sorted(
        selected_problem_list, key=lambda prob: (prob.subject, exam_order.get(prob.psat.exam, 5), prob.number))

    return selected_problem_list_sorted


def save_to_excel(wb_filepath, selected_problem_list, sheet_name='1'):
    data = []
    for no, problem in enumerate(selected_problem_list, start=1):
        _id = problem.id
        year = problem.psat.year
        exam = problem.psat.exam
        subject = problem.subject
        paper_type = problem.paper_type or ''
        number = problem.number
        answer = problem.answer
        question = problem.question

        serial = f'{year}{exam[0]}{subject[0]}{paper_type}-{number:02}'
        data.append([no, _id, serial, year, exam, subject, paper_type, number, answer, question])

    columns = ['순서', 'ID', '일련번호', '연도', '시험', '과목', '책형', '번호', '정답', '발문']
    df = pd.DataFrame(data, columns=columns)

    if sheet_name != '1':
        with pd.ExcelWriter(wb_filepath, mode='a', engine='openpyxl', if_sheet_exists='new') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df.to_excel(wb_filepath, sheet_name=sheet_name, index=False)
    print(f"문제가 '{wb_filepath}' 파일의 '{sheet_name}'번 시트로 저장되었습니다.")


def save_image_files(wb_filepath, sheet_name):
    folder = os.path.join(TARGET_SAVE_FOLDER, str(sheet_name))
    if not os.path.exists(folder):
        os.makedirs(folder)

    # 과목별로 정렬된 문제에 대해 sorted_number를 증가시키면서 파일 복사
    subject_counters = {}

    df = pd.read_excel(wb_filepath, sheet_name=sheet_name, index_col=0)
    for idx, row in df.iterrows():
        year, exam, subject, number = row['연도'], row['시험'], row['과목'], row['번호']
        image_name = f'PSAT{year}{exam}{subject}{number:02}'

        # 각 과목별로 번호를 독립적으로 관리
        if subject not in subject_counters:
            subject_counters[subject] = 1
        sorted_number = subject_counters[subject]

        def get_image_path(image_number) -> tuple[str, str]:
            filename = f'{image_name}-{image_number}.png' if image_number else f'{image_name}.png'
            image_path = os.path.join(BASE_IMAGE_FOLDER, str(year), filename)
            new_filename = f"{subject}{sorted_number:02}_{filename}"
            new_image_path = os.path.join(folder, new_filename)
            return image_path, new_image_path

        image_path_0, target_image_path = get_image_path(0)
        if os.path.exists(target_image_path):
            print(f'✅ 이미 존재하는 이미지: {target_image_path}')
        else:
            if os.path.exists(image_path_0):
                shutil.copy(image_path_0, target_image_path)
            else:
                image_path_1, new_image_path_1 = get_image_path(1)
                image_path_2, new_image_path_2 = get_image_path(2)
                if os.path.exists(image_path_1):
                    if os.path.exists(image_path_2):
                        merge_images_vertically(image_path_1, image_path_2, target_image_path)
                    else:
                        shutil.copy(image_path_1, target_image_path)

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
    print(f'✅ 이미지 저장 완료: {output_path}')


def save_pdf_files(wb_filepath: str, sheet_name: str, pdf_type=0):
    folder = os.path.join(TARGET_SAVE_FOLDER, str(sheet_name))
    if not os.path.exists(folder):
        os.makedirs(folder)

    pdf_folder = '#손필기/' if pdf_type else '#문제/'

    # 과목별로 정렬된 문제에 대해 sorted_number를 증가시키면서 파일 복사
    subject_counters = {}

    subject_map = {'언어': '01', '자료': '02', '상황': '03'}
    df = pd.read_excel(wb_filepath, sheet_name=sheet_name, index_col=0)
    for idx, row in df.iterrows():
        serial, subject = row['일련번호'], row['과목']

        # 각 과목별로 번호를 독립적으로 관리
        if subject not in subject_counters:
            subject_counters[subject] = 1
        sorted_number = subject_counters[subject]

        subject_code = subject_map[subject]
        folder_name = f'{subject_code}_{subject}'
        subject_folder = os.path.join(BASE_PDF_FOLDER, pdf_folder, folder_name)
        original_file_path = os.path.join(subject_folder, f'{serial}.pdf')

        if os.path.exists(original_file_path):
            subject_output_folder = os.path.join(folder, folder_name)
            if not os.path.exists(subject_output_folder):
                os.makedirs(subject_output_folder)

            target_file_path = os.path.join(subject_output_folder, f'{subject}{sorted_number:02}_{serial}.pdf')
            if os.path.exists(target_file_path):
                print(f'✅ 이미 존재하는 PDF: {target_file_path}')
            else:
                shutil.copyfile(original_file_path, target_file_path)
                print(f'✅ PDF 저장 완료: {original_file_path} to {target_file_path}')
        else:
            print(f'파일이 존재하지 않습니다: {original_file_path}')

        # 과목별로 sorted_number 증가
        subject_counters[subject] += 1
