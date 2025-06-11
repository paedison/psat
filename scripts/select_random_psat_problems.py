from pathlib import Path
import random
import shutil
from collections import defaultdict
from datetime import datetime

import pandas as pd
from PIL import Image
from PyPDF2 import PdfMerger
from openpyxl import load_workbook
from pyhwpx import Hwp

from a_psat.models import Problem
from a_psat.models.choices import answer_choice

BASE_IMAGE_FOLDER = Path('static/image/PSAT')
BASE_NAS_FOLDER = Path('//Newpsatncs/3_배승철/#PSAT 기출문제')
BASE_OUTPUT_FOLDER = Path('a_psat/data/selected_problems')
DEFAULT_EXCEL_FILENAME = 'problem_list'

BLANK_PNG = BASE_OUTPUT_FOLDER / 'blank.png'
BLANK_PDF = BASE_OUTPUT_FOLDER / 'blank.pdf'
BLANK_HWP = BASE_OUTPUT_FOLDER / 'blank.hwp'

OPTION_PROMPT = """
0. 프로그램 종료
1. 문제 리스트 추출 및 파일(EXCEL, PNG, PDF, HWP)로 저장
2. 문제 리스트 추출하여 EXCEL 파일로 저장
3. EXCEL 파일에서 누락된 문제ID 채우기
4. 추출된 문제 리스트 PNG 파일로 저장
5. 추출된 문제 리스트 PDF 파일로 저장
6. 추출된 문제 리스트 HWP 파일로 저장
옵션을 선택해주세요: """

EXAM_ORDER = {'민경': 1, '칠예': 2, '칠급': 3, '견습': 4, '외시': 5, '행시': 6, '입시': 7}
SUB_MAP = {'언어': '01', '자료': '02', '상황': '03'}
SUBJECT_LIST = ['언어', '자료', '상황']
ANSWER_CHOICE_DICT = answer_choice()


def run():
    excel_filename = get_user_input('엑셀 파일 이름(excel_filename): ', DEFAULT_EXCEL_FILENAME, str)
    sheet_name = get_user_input('시트 이름(sheet_name): ', '1', str)

    output_folder = BASE_OUTPUT_FOLDER / excel_filename
    output_sheet_folder = output_folder / sheet_name
    wb_filepath = output_folder / f'{excel_filename}.xlsx'
    ws_exist_warning = f"'{wb_filepath}' 파일 안에 같은 이름의 시트가 존재합니다.\n👋 프로그램을 종료합니다."

    for folder in [BASE_OUTPUT_FOLDER, output_folder, output_sheet_folder]:
        folder.mkdir(parents=True, exist_ok=True)

    xls, df = None, None
    if wb_filepath.exists():
        xls = pd.ExcelFile(wb_filepath)
        if sheet_name in xls.sheet_names:
            df = pd.read_excel(
                wb_filepath, sheet_name=sheet_name, index_col=0, dtype={'구분': str, '회차': str, '샘플': str}
            )
            df = df.infer_objects(copy=False)

    def sheet_exists():
        return xls and sheet_name in xls.sheet_names

    def handle_option_1():
        """문제 리스트 추출 및 파일(EXCEL, PNG, PDF, HWP)로 저장"""
        if sheet_exists():
            print(ws_exist_warning)
            return False
        problem_list = get_problem_list(wb_filepath, sheet_name)
        problem_list_df = get_problem_list_df(problem_list)
        save_to_excel(wb_filepath, sheet_name, problem_list_df)
        print('✅ 문제 목록 추출 완료')

        print('===================')
        print(f'👉 PNG 파일 복사 중...')
        save_png_files(output_sheet_folder, problem_list_df)
        print('✅ PNG 파일 복사 완료')
        print('===================')
        print(f'👉 문제 PDF 파일 복사 중...')
        save_pdf_files(output_sheet_folder, problem_list_df, '문제')
        print('-------------------')
        print(f'👉 손필기 PDF 파일 복사 중...')
        save_pdf_files(output_sheet_folder, problem_list_df, '손필기')
        print('✅ PDF 파일 복사 완료')
        print('===================')
        print(f'👉 HWP 파일 병합 중...')
        save_hwp_files(output_sheet_folder, problem_list_df, '문제')
        return True

    def handle_option_2():
        """문제 리스트 추출하여 EXCEL 파일로 저장"""
        if sheet_exists():
            print(ws_exist_warning)
            return False
        problem_list = get_problem_list(wb_filepath, sheet_name)
        problem_list_df = get_problem_list_df(problem_list)
        save_to_excel(wb_filepath, sheet_name, problem_list_df)
        print("✅ 옵션 2 종료\n")
        return True

    def handle_other_options(_choice):
        if not sheet_exists():
            print(f"'{wb_filepath}' 파일이 존재하지 않습니다.")
            return False

        print('\n[입력 요약]')
        print(f'- 엑셀 파일: {wb_filepath}')
        print(f'- 시트 이름: {sheet_name}')
        print('===================')
        print(f'👉 옵션 {_choice} 실행 중...')

        if _choice == 3:  # EXCEL 파일에서 누락된 문제ID 채우기
            df_local = fill_empty_problem_ids(df)
            save_to_excel(wb_filepath, sheet_name, df_local)
        elif _choice == 4:  # 추출된 문제 리스트 PNG 파일로 저장
            save_png_files(output_sheet_folder, df)
        elif _choice == 5:  # 추출된 문제 리스트 PDF 파일로 저장
            save_pdf_files(output_sheet_folder, df, '문제')
            save_pdf_files(output_sheet_folder, df, '손필기')
        elif _choice == 6:  # 추출된 문제 리스트 HWP 파일로 저장
            save_hwp_files(output_sheet_folder, df, '문제')
        else:
            print('❌ 잘못된 입력입니다. 다시 선택해주세요.\n')
            return True

        print(f"✅ 옵션 {_choice} 종료")
        return True

    while True:
        choice = get_user_input(OPTION_PROMPT, 0, int)
        if choice == 0:
            print("👋 프로그램을 종료합니다.")
            break
        elif choice == 1:
            if not handle_option_1():
                break
        elif choice == 2:
            if not handle_option_2():
                break
        else:
            if not handle_other_options(choice):
                break


def get_user_input(prompt, default, type_func):
    user_input = input(f"{prompt} [default: {default}]: ").strip()
    return type_func(user_input) if user_input else default


def get_problem_list(wb_filepath: Path, sheet_name):
    start_year = get_user_input('시작 연도(start_year): ', 2007, int)
    end_year = get_user_input('끝 연도(end_year): ', datetime.now().year, int)
    exam_type = get_user_input('시험 종류(exam_type)[0: 전체, 1: 기본, 2: 심화]: ', 0, int)
    problem_count = get_user_input('문제 개수(problem_count): ', 40, int)
    subject = get_user_input('과목(subject): ', '', str)

    print('\n[입력 요약]')
    print(f'- 엑셀 파일: {wb_filepath}')
    print(f'- 시트 이름: {sheet_name}')
    print(f'- 시작 연도: {start_year}')
    print(f'- 끝 연도: {end_year}')
    print(f'- 시험 종류: {exam_type}')
    print(f'- 문제 개수: {problem_count}')
    print(f'- 과목: {subject}')
    print('===================')
    print('👉 문제 목록 추출 중...')

    exclude_ids = set()
    if wb_filepath.exists():
        xls = pd.ExcelFile(wb_filepath)
        sheet_names = xls.sheet_names
        for sheet in sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet)
                exclude_ids.update(set(df['ID'].dropna()))
            except Exception as e:
                print(f"❌ 시트 '{sheet}' 로딩 실패: {e}")
    exclude_id_list = list(exclude_ids)

    problem_list = []
    subjects = [subject] if subject else SUBJECT_LIST

    for sub in subjects:
        problems = (
            Problem.objects.annotate_subject_code().select_related('psat')
            .filter(psat__year__range=(start_year, end_year), subject=sub)
            .exclude(psat__exam='입시').exclude(question='')
        )
        if exclude_id_list:
            problems = problems.exclude(id__in=exclude_id_list)
        if exam_type == 1:
            problems = problems.filter(psat__exam__in=['민경', '칠급', '칠예', '칠모'])
        elif exam_type == 2:
            problems = problems.filter(psat__exam__in=['행시'])
        selected_problems = random.sample(list(problems), min(problem_count, len(problems)))
        problem_list.extend(selected_problems)

    return sorted(
        problem_list, key=lambda prob: (prob.subject_code, EXAM_ORDER.get(prob.psat.exam, 5), prob.number))


def get_problem_list_df(problem_list):
    data = []
    subject_counters = defaultdict(int)

    for problem in problem_list:
        _id = problem.id
        year = problem.psat.year
        ex = problem.psat.exam
        sub = problem.subject
        paper_type = problem.paper_type or ''
        number = problem.number
        answer = problem.answer
        question = problem.question

        subject_counters[sub] += 1
        sorted_number = subject_counters[sub]

        serial = f'{year}{ex[0]}{sub[0]}{paper_type}-{number:02}'
        data.append(['', '', '', sorted_number, _id, year, ex, sub, paper_type, number, serial, answer, question])

    columns = ['구분', '회차', '샘플', '정렬번호', 'ID', '연도', '시험', '과목', '책형', '번호', '일련번호', '정답', '발문']
    df = pd.DataFrame(data, columns=columns)
    df.index += 1
    return df


def save_to_excel(wb_filepath: Path, sheet_name, df):
    if wb_filepath.exists():
        with pd.ExcelWriter(wb_filepath, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=True, index_label='순서')
    else:
        df.to_excel(wb_filepath, sheet_name=sheet_name, index=True, index_label='순서')
    wb = load_workbook(wb_filepath)
    ws = wb[sheet_name]
    ws.freeze_panes = 'A2'
    wb.save(wb_filepath)
    print(f"✅ '{wb_filepath}' 파일의 '{sheet_name}' 시트로 저장되었습니다.")
    return df


def fill_empty_problem_ids(df):
    for idx, row in df.iterrows():
        year = row['연도']
        ex = row['시험']
        sub = row['과목']
        number = row['번호']
        serial = row['번호']
        try:
            df.at[idx, 'ID'] = Problem.objects.get(psat__year=year, psat__exam=ex, subject=sub, number=number).id
        except Problem.DoesNotExist:
            print(f'❌ 데이터베이스에 존재하지 않는 문제입니다: {serial}')
    return df


def save_png_files(output_sheet_folder: Path, df):
    parent_folder = output_sheet_folder / 'PNG'
    count = {'exist': 0, 'saved': 0, 'merged': 0, 'blank': 0}

    def get_base_name(row) -> str:
        year, ex, sub, number = row['연도'], row['시험'], row['과목'], row['번호']
        return f'PSAT{year}{ex}{sub}{number:02}'

    def get_child_folder(row) -> Path:
        category = row['구분']
        sub = row['과목']
        if pd.isna(category) or not category:
            return parent_folder / f'{SUB_MAP[sub]}_{sub}'
        else:
            rnd = int(row['회차'])
            sample = '' if pd.isna(row['샘플']) else row['샘플']
            folder_name = f'샘플_{rnd:02}_{sample}' if sample else f'{rnd:02}'
            return parent_folder / category / folder_name

    def get_input_path(row, base_name, image_number) -> tuple[str, Path | None]:
        year = row['연도']
        filename = f'{base_name}-{image_number}.png' if image_number else f'{base_name}.png'
        path = Path(BASE_IMAGE_FOLDER) / str(year) / filename
        return filename, (path if path.exists() else None)

    for idx, problem_row in df.iterrows():
        sorted_number = problem_row['정렬번호']
        image_base_name = get_base_name(problem_row)
        child_folder = get_child_folder(problem_row)
        child_folder.mkdir(parents=True, exist_ok=True)

        filename_0, path_0 = get_input_path(problem_row, image_base_name, 0)
        output_path = child_folder / f'{sorted_number:02}_{filename_0}'

        if output_path.exists():
            count['exist'] += 1
            continue

        if path_0:
            shutil.copy(path_0, output_path)
            count['saved'] += 1
            continue

        _, path_1 = get_input_path(problem_row, image_base_name, 1)
        _, path_2 = get_input_path(problem_row, image_base_name, 2)
        if path_1 and path_2:
            merge_images_vertically(path_1, path_2, output_path)
            count['merged'] += 1
            continue
        elif path_1:
            shutil.copy(path_1, output_path)
            count['saved'] += 1
            continue

        blank_output_path = child_folder / f'{sorted_number:02}_blank.png'
        if blank_output_path.exists():
            count['exist'] += 1
        else:
            shutil.copy(BLANK_PNG, blank_output_path)
            count['blank'] += 1

    print("=== 처리 결과 요약 ===")
    if count['saved']:
        print(f"✅ 저장한 PNG 파일: {count['saved']}개")
    if count['merged']:
        print(f"➕ 결합한 PNG 파일: {count['merged']}개")
    if count['blank']:
        print(f"❌ 빈 PNG 파일: {count['blank']}개")
    if count['exist']:
        print(f"⛔ 이미 존재하는 PNG 파일: {count['exist']}개")


def merge_images_vertically(input_path_1: Path, input_path_2: Path, output_path: Path):
    img1 = Image.open(input_path_1)
    img2 = Image.open(input_path_2)
    width = max(img1.width, img2.width)
    total_height = img1.height + img2.height

    new_img = Image.new('RGB', (width, total_height), color=(255, 255, 255))
    new_img.paste(img1, (0, 0))
    new_img.paste(img2, (0, img1.height))
    new_img.save(output_path)


def save_pdf_files(output_sheet_folder: Path, df, pdf_type: str):
    parent_folder = output_sheet_folder / f'PDF_{pdf_type}'
    count = {'exist': 0, 'saved': 0, 'blank': 0}

    for idx, row in df.iterrows():
        category = row['구분']
        rnd = row['회차']
        sample = row['샘플']
        serial = row['일련번호']
        sub = row['과목']
        sorted_number = row['정렬번호']

        input_folder_name = f'{SUB_MAP[sub]}_{sub}'
        if pd.isna(category) or not category:
            child_folder = parent_folder / input_folder_name
        else:
            rnd = int(rnd)
            sample = str(sample) if pd.notna(sample) and sample else ''
            folder_name = f'샘플_{rnd:02}_{sample}' if sample else f'{rnd:02}'
            child_folder = parent_folder / category / folder_name
        child_folder.mkdir(parents=True, exist_ok=True)

        input_folder = BASE_NAS_FOLDER / '#PDF' / pdf_type / input_folder_name
        input_filename = f'{serial}.pdf'
        input_path = input_folder / input_filename
        output_path = child_folder / f'{sorted_number:02}_{input_filename}'

        if input_path.exists():
            if output_path.exists():
                count['exist'] += 1
            else:
                shutil.copy(input_path, output_path)
                count['saved'] += 1
            continue

        blank_output_path = child_folder / f'{sorted_number:02}_blank.pdf'
        if blank_output_path.exists():
            count['exist'] += 1
            continue

        shutil.copy(BLANK_PDF, blank_output_path)
        count['blank'] += 1

    print("=== 처리 결과 요약 ===")
    if count['saved']:
        print(f"✅ 저장한 {pdf_type} PDF 파일: {count['saved']}개")
    if count['blank']:
        print(f"❌ 빈 {pdf_type} PDF 파일: {count['blank']}개")
    if count['exist']:
        print(f"⛔ 이미 존재하는 {pdf_type} PDF 파일: {count['exist']}개")


def save_hwp_files(output_sheet_folder: Path, df, hwp_type: str):
    output_hwp_path = output_sheet_folder / f'{hwp_type}.hwp'
    count = {'exist': 0, 'saved': 0, 'blank': 0}

    if output_hwp_path.exists():
        print(f'✅ 이미 존재하는 파일: {output_hwp_path}')
    else:
        hwp = Hwp(visible=False)
        for idx, row in df.iterrows():
            serial = row['일련번호']
            sub = row['과목']
            answer = ANSWER_CHOICE_DICT.get(row['정답'])

            input_folder = BASE_NAS_FOLDER / '#HWP' / hwp_type / f'{SUB_MAP[sub]}_{sub}'
            input_path = input_folder / f'{serial}.hwp'

            if input_path.exists():
                file = str(input_path)
                if idx == 1:
                    print("🔧 병합 시작...")
                    hwp.open(file)
                    hwp.MoveDocBegin()
                else:
                    hwp.insert_file(file)
                    hwp.MoveRight()
                    hwp.DeleteBack()
                hwp.find(answer)
                hwp.CharShapeTextColorRed()
                count['saved'] += 1
            else:
                hwp.insert_file(str(BLANK_HWP))
                hwp.MoveRight()
                hwp.DeleteBack()
                count['blank'] += 1

            hwp.MoveDocEnd()
            hwp.BreakPage()

        hwp.save_as(str(output_hwp_path))
        hwp.quit()

    print("=== 처리 결과 요약 ===")
    if count['saved']:
        print(f"✅ 저장한 HWP 파일: {count['saved']}개")
    if count['blank']:
        print(f"❌ 빈 HWP 파일: {count['blank']}개")
