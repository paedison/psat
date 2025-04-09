import os
import random
import shutil
from datetime import datetime

import pandas as pd
from PIL import Image
from PyPDF2 import PdfMerger
from pyhwpx import Hwp

from a_psat.models import Problem

BASE_IMAGE_FOLDER = os.path.join('static', 'image', 'PSAT')
NAS_BASE_FOLDER = os.path.join('//Newpsatncs', '3_배승철', '#PSAT 기출문제')
TARGET_SAVE_FOLDER = os.path.join('a_psat', 'data', 'selected_problems')
TARGET_EXCEL_FILE = 'problem_list.xlsx'
OPTION_PROMPT = """
0. 문제 리스트 추출 및 파일(EXCEL, PNG, PDF, HWP)로 저장
1. 문제 리스트 추출하여 EXCEL 파일로 저장
2. 추출된 문제 리스트 PNG 파일로 저장
3. 추출된 문제 리스트 PDF 파일로 저장
4. 추출된 문제 리스트 HWP 파일로 저장
5. 프로그램 종료
옵션을 선택해주세요: """

EXAM_ORDER = {'민경': 1, '칠예': 2, '칠급': 3, '견습': 4, '외시': 5, '행시': 6, '입시': 7}
SUB_MAP = {'언어': '01', '자료': '02', '상황': '03'}

BLANK_PNG = os.path.join(TARGET_SAVE_FOLDER, 'blank.png')
BLANK_PDF = os.path.join(TARGET_SAVE_FOLDER, 'blank.pdf')
BLANK_HWP = os.path.join(TARGET_SAVE_FOLDER, 'blank.hwp')


def run():
    if not os.path.exists(TARGET_SAVE_FOLDER):
        os.makedirs(TARGET_SAVE_FOLDER)
    wb_filepath = os.path.join(TARGET_SAVE_FOLDER, TARGET_EXCEL_FILE)

    while True:
        choice = get_user_input(OPTION_PROMPT, 0, int)
        if choice == 0:
            sheet_name = run_option_1(wb_filepath)
            run_option_2(wb_filepath, sheet_name)
            run_option_3(wb_filepath, sheet_name)
            run_option_4(wb_filepath, sheet_name)
        elif choice == 1:
            run_option_1(wb_filepath)
        elif choice == 2:
            run_option_2(wb_filepath)
        elif choice == 3:
            run_option_3(wb_filepath)
        elif choice == 4:
            run_option_4(wb_filepath)
        elif choice == 5:
            print("👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 잘못된 입력입니다. 다시 선택해주세요.\n")


def get_user_input(prompt, default, type_func):
    user_input = input(f"{prompt} [default: {default}]: ").strip()
    return type_func(user_input) if user_input else default


def run_option_1(wb_filepath):
    start_year = get_user_input('시작 연도(start_year): ', 2007, int)
    end_year = get_user_input('끝 연도(end_year): ', datetime.now().year, int)
    exam_type = get_user_input('시험 종류(exam_type)[0: 전체, 1: 기본, 2: 심화]: ', 0, int)
    problem_count = get_user_input('문제 개수(problem_count): ', 40, int)
    subject = get_user_input('과목(subject): ', '', str)

    print('\n[입력 요약]')
    print(f'- 시작 연도: {start_year}')
    print(f'- 끝 연도: {end_year}')
    print(f'- 시험 종류: {exam_type}')
    print(f'- 문제 개수: {problem_count}')
    print(f'- 과목: {subject}\n')

    print("===================")
    print("👉 옵션 1 실행 중...")
    sheet_name, extracted_problem_ids = get_extracted_problem_ids(wb_filepath)
    problem_list = get_selected_problem_list(
        start_year, end_year, exam_type, problem_count, subject, extracted_problem_ids)
    save_to_excel(wb_filepath, problem_list, sheet_name)
    print("✅ 옵션 1 종료\n")
    return sheet_name


def run_option_2(wb_filepath, sheet_name=None):
    if sheet_name is None:
        sheet_name = get_user_input('시트 이름(sheet_name): ', '1', str)

    print("===================")
    print("👉 옵션 2 실행 중...")
    if os.path.exists(wb_filepath):
        save_image_files(wb_filepath, sheet_name)
    else:
        print(f'{wb_filepath} 파일이 존재하지 않습니다.')
    print("✅ 옵션 2 종료\n")


def run_option_3(wb_filepath, sheet_name=None):
    if sheet_name is None:
        sheet_name = get_user_input('시트 이름(sheet_name): ', '1', str)

    print("===================")
    print("👉 옵션 3 실행 중...")
    if os.path.exists(wb_filepath):
        save_pdf_files(wb_filepath, sheet_name, '문제')
        save_pdf_files(wb_filepath, sheet_name, '손필기')
    else:
        print(f'{wb_filepath} 파일이 존재하지 않습니다.')
    print("✅ 옵션 3 종료\n")


def run_option_4(wb_filepath, sheet_name=None):
    if sheet_name is None:
        sheet_name = get_user_input('시트 이름(sheet_name): ', '1', str)

    print("===================")
    print("👉 옵션 4 실행 중...")
    if os.path.exists(wb_filepath):
        save_hwp_files(wb_filepath, sheet_name)
    else:
        print(f'{wb_filepath} 파일이 존재하지 않습니다.')
    print("✅ 옵션 4 종료\n")


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
            Problem.objects.psat_problem_qs_annotate_subject_code().select_related('psat')
            .filter(psat__year__range=(start_year, end_year), subject=sub)
            .exclude(psat__exam='입시').exclude(question='')
        )
        if extracted_problem_ids:
            problems = problems.exclude(id__in=extracted_problem_ids)
        if exam_type == 1:
            problems = problems.filter(psat__exam__in=['민경', '칠급', '칠예', '칠모'])
        elif exam_type == 2:
            problems = problems.filter(psat__exam__in=['행시'])
        selected_problems = random.sample(list(problems), min(problem_count, len(problems)))
        selected_problem_list.extend(selected_problems)

    selected_problem_list_sorted = sorted(
        selected_problem_list, key=lambda prob: (prob.subject_code, EXAM_ORDER.get(prob.psat.exam, 5), prob.number))

    return selected_problem_list_sorted


def save_to_excel(wb_filepath, selected_problem_list, sheet_name='1'):
    # 과목별로 정렬된 문제에 대해 sorted_number를 증가시키면서 파일 복사
    subject_counters = {}

    data = []
    for idx, problem in enumerate(selected_problem_list, start=1):
        _id = problem.id
        year = problem.psat.year
        ex = problem.psat.exam
        sub = problem.subject
        paper_type = problem.paper_type or ''
        number = problem.number
        answer = problem.answer
        question = problem.question

        # 각 과목별로 번호를 독립적으로 관리
        if sub not in subject_counters:
            subject_counters[sub] = 1
        sorted_number = subject_counters[sub]

        serial = f'{year}{ex[0]}{sub[0]}{paper_type}-{number:02}'
        data.append([
            idx, sub, sorted_number,
            _id, serial, year, ex, sub, paper_type, number, answer, question,
        ])

        # 과목별로 sorted_number 증가
        subject_counters[sub] += 1

    columns = [
        '순서', '정렬과목', '정렬번호',
        'ID', '일련번호', '연도', '시험', '과목', '책형', '번호', '정답', '발문',
    ]
    df = pd.DataFrame(data, columns=columns)

    if sheet_name == '1':
        df.to_excel(wb_filepath, sheet_name=sheet_name, index=False)
    else:
        with pd.ExcelWriter(wb_filepath, mode='a', engine='openpyxl', if_sheet_exists='new') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"문제가 '{wb_filepath}' 파일의 '{sheet_name}'번 시트로 저장되었습니다.")


def save_image_files(wb_filepath, sheet_name):
    output_base_folder = os.path.join(TARGET_SAVE_FOLDER, str(sheet_name), 'PNG')
    os.makedirs(output_base_folder, exist_ok=True)

    for sub, code in SUB_MAP.items():
        os.makedirs(os.path.join(output_base_folder, f'{code}_{sub}'), exist_ok=True)

    df = pd.read_excel(wb_filepath, sheet_name=sheet_name, index_col=0)
    for idx, row in df.iterrows():
        year, ex, sub, number, sorted_number = row['연도'], row['시험'], row['과목'], row['번호'], row['정렬번호']
        output_folder = os.path.join(output_base_folder, f'{SUB_MAP[sub]}_{sub}')
        image_name = f'PSAT{year}{ex}{sub}{number:02}'

        def get_input_filename_and_path(image_number) -> tuple[str, str]:
            filename = f'{image_name}-{image_number}.png' if image_number else f'{image_name}.png'
            path = os.path.join(BASE_IMAGE_FOLDER, str(year), filename)
            if os.path.exists(path):
                return filename, path
            return filename, ''

        input_filename_0, input_path_0 = get_input_filename_and_path(0)
        output_filename = f'{sub}{sorted_number:02}_{input_filename_0}'
        output_path = os.path.join(output_folder, output_filename)

        if os.path.exists(output_path):
            print(f'✅ 이미 존재하는 이미지: {output_path}')
        else:
            if os.path.exists(input_path_0):
                shutil.copy(input_path_0, output_path)
                print(f'✅ 이미지 저장 완료: {output_path}')
            else:
                _, input_path_1 = get_input_filename_and_path(1)
                _, input_path_2 = get_input_filename_and_path(2)
                if input_path_1:
                    if input_path_2:
                        merge_images_vertically(input_path_1, input_path_2, output_path)
                        print(f'✅ 이미지 결합 및 저장 완료: {output_path}')
                    else:
                        shutil.copy(input_path_1, output_path)
                        print(f'✅ 이미지 저장 완료: {output_path}')
                else:
                    output_filename = f'{sub}{sorted_number:02}_blank.png'
                    output_path = os.path.join(output_folder, output_filename)
                    shutil.copy(BLANK_PNG, output_path)
                    print(f'❌ 해당 이미지 없음(빈 이미지 저장): {output_path}')


def merge_images_vertically(input_path_1, input_path_2, output_path):
    # 이미지 열기
    img1 = Image.open(input_path_1)
    img2 = Image.open(input_path_2)

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


def save_pdf_files(wb_filepath: str, sheet_name: str, pdf_type: str):
    output_base_folder = os.path.join(TARGET_SAVE_FOLDER, str(sheet_name), f'PDF_{pdf_type}')
    os.makedirs(output_base_folder, exist_ok=True)

    for sub, code in SUB_MAP.items():
        os.makedirs(os.path.join(output_base_folder, f'{code}_{sub}'), exist_ok=True)

    df = pd.read_excel(wb_filepath, sheet_name=sheet_name, index_col=0)
    for idx, row in df.iterrows():
        serial, sub, sorted_number = row['일련번호'], row['과목'], row['정렬번호']
        input_folder_last = f'{SUB_MAP[sub]}_{sub}'
        input_folder = os.path.join(NAS_BASE_FOLDER, f'#{pdf_type}', input_folder_last)
        input_filename = f'{serial}.pdf'
        input_path = os.path.join(input_folder, input_filename)

        output_folder = os.path.join(output_base_folder, f'{SUB_MAP[sub]}_{sub}')

        if os.path.exists(input_path):
            output_filename = f'{sub}{sorted_number:02}_{input_filename}'
            output_path = os.path.join(output_folder, output_filename)
            shutil.copy(input_path, output_path)
            print(f'✅ 파일 저장 완료: {output_path}')
        else:
            output_filename = f'{sub}{sorted_number:02}_blank.pdf'
            output_path = os.path.join(output_folder, output_filename)
            shutil.copy(BLANK_PDF, output_path)
            print(f'❌ 해당 파일 없음(빈 페이지 저장): {output_path}')

#
#
# def save_pdf_files(wb_filepath: str, sheet_name: str, pdf_type: str):
#     output_folder = os.path.join(TARGET_SAVE_FOLDER, str(sheet_name))
#     os.makedirs(output_folder, exist_ok=True)
#     output_path = os.path.join(output_folder, f'{pdf_type}.pdf')
#
#     if os.path.exists(output_path):
#         print(f'✅ 이미 존재하는 파일: {output_path}')
#     else:
#         file_list = get_file_list(wb_filepath, sheet_name, f'#{pdf_type}', 'pdf')
#
#         print("🔧 병합 시작...")
#         merger = PdfMerger()
#
#         for f in file_list:
#             if f.strip() == '':
#                 merger.append(BLANK_PDF)
#                 print(f'❌ 해당 파일 없음(빈 페이지 삽입)')
#             else:
#                 merger.append(f)
#                 print(f'✅ PDF 병합 완료: {f}')
#
#         merger.write(output_path)
#         merger.close()
#         print(f"✅ PDF 병합 완료! 저장 위치: {output_path}")


def save_hwp_files(wb_filepath: str, sheet_name: str):
    output_folder = os.path.join(TARGET_SAVE_FOLDER, str(sheet_name))
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, f'문제.hwp')

    if os.path.exists(output_path):
        print(f'✅ 이미 존재하는 파일: {output_path}')
    else:
        file_list = get_file_list(wb_filepath, sheet_name, '#HWP', 'hwp')

        print("🔧 병합 시작...")
        hwp = Hwp(visible=False)
        hwp.open(file_list[0])
        hwp.MoveDocEnd()

        for f in file_list[1:]:
            if f.strip() == '':
                hwp.insert_file(BLANK_HWP)
                print(f'❌ 해당 파일 없음(빈 페이지 삽입)')
            else:
                hwp.insert_file(f)
                print(f'✅ HWP 병합 완료: {f}')
            hwp.MoveDocEnd()

        hwp.save_as(output_path)
        hwp.quit()
        print(f'✅ 파일 저장 완료: {output_path}')


def get_file_list(wb_filepath: str, sheet_name: str, folder: str, extension: str) -> list:
    file_list = []
    df = pd.read_excel(wb_filepath, sheet_name=sheet_name, index_col=0)
    for idx, row in df.iterrows():
        serial, sub = row['일련번호'], row['과목']
        input_folder_last = f'{SUB_MAP[sub]}_{sub}'
        input_folder = os.path.join(NAS_BASE_FOLDER, folder, input_folder_last)
        input_path = os.path.join(input_folder, f'{serial}.{extension}')

        if os.path.exists(input_path):
            file_list.append(input_path)
        else:
            file_list.append('')
    return file_list
