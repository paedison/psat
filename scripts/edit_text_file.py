import os
import re
from pathlib import Path

import chardet

from . import utils

BASE_DIR = Path('D:/projects/#edit_text_file')
OUTPUT_FOLDER = BASE_DIR / 'output'


def run():
    input_filename = utils.get_user_input('입력 파일(txt): ', '입력 파일', str)
    output_filename = utils.get_user_input('출력 파일(txt): ', '작업 결과', str)

    input_file = BASE_DIR / f'{input_filename}.txt'
    output_file = OUTPUT_FOLDER / f'{output_filename}.txt'
    process_text_file(input_file, output_file)


def detect_encoding(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
        result = chardet.detect(raw)
        return result['encoding'], raw.decode(result['encoding'])


def clean_and_format_lines(lines):
    output = []
    current_line = ""

    for line in lines:
        # 탭 + 공백 정리
        line = re.sub(r'[\t ]+', ' ', line)
        stripped = line.strip()
        if not stripped:
            continue

        # 숫자. 단독 줄
        if re.fullmatch(r'\d+\.', stripped):
            if current_line:
                output.append(current_line)
            current_line = stripped + ' '

        # 숫자. 뒤에 공백 0개 이상 + 숫자 아닌 문자로 시작
        elif re.match(r'^\d+\.\s*\D', stripped):
            if current_line:
                output.append(current_line)
            stripped = re.sub(r'^(\d+\.)\s*(\D)', r'\1 \2', stripped)
            current_line = stripped + '\t'
        else:
            current_line += stripped

    if current_line:
        output.append(current_line)
    return output


def normalize_numbering(lines):
    final_lines = []
    prev_num = 0
    reset_points = {30, 35, 40}

    for line in lines:
        match = re.match(r'^(\d+)\.\s(.*)', line)
        if not match:
            if final_lines:
                final_lines[-1] += line.strip()
            continue

        curr_num, content = int(match.group(1)), match.group(2).strip()

        if prev_num in reset_points:
            if curr_num != 1 and curr_num != prev_num + 1:
                final_lines[-1] += content
                continue
        elif curr_num <= prev_num:
            final_lines[-1] += content
            continue

        final_lines.append(f"{curr_num}. {content}")
        prev_num = curr_num

    return final_lines


def split_on_range_marker(lines):
    updated_lines = []
    range_pattern = re.compile(r'\[\d+~\d+\]')

    for line in lines:
        match = range_pattern.search(line)
        if match:
            idx = match.start()
            before = line[:idx].rstrip()
            after = line[idx:].lstrip()
            updated_lines.extend([before, after])
        else:
            updated_lines.append(line)

    return updated_lines


def distribute_text_by_range_marker(lines):
    pattern = re.compile(r'\[(\d+)~(\d+)\]')
    updated = []
    pending_attaches = {}  # {줄번호: [붙일 텍스트들]}

    for line in lines:
        match = pattern.search(line)
        if match:
            start, end = int(match[1]), int(match[2])
            idx = match.start()
            full_marker = line[idx:]  # 숫자 범위 마커부터 끝까지 전체 붙이기

            # 대상 줄들에 붙일 텍스트로 등록
            for num in range(start, end + 1):
                pending_attaches.setdefault(num, []).append(full_marker.strip())

            base = line[:idx].rstrip()
            if base:
                updated.append(base)
            continue

        # 줄이 숫자로 시작하는 경우만 처리
        num_match = re.match(r'^(\d+)\.\s(.*)', line)
        if num_match:
            n = int(num_match[1])
            content = num_match[2]

            # 이 줄에 붙여야 할 내용이 있다면
            if n in pending_attaches:
                for fragment in pending_attaches[n]:
                    content += ' ' + fragment
            updated.append(f"{n}. {content}")
        else:
            # 번호 없는 줄은 그대로 유지
            updated.append(line)

    return updated


def process_text_file(input_file, output_file):
    # 출력 폴더 생성
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    encoding, text = detect_encoding(input_file)
    lines = text.splitlines()
    cleaned = clean_and_format_lines(lines)
    final_result = normalize_numbering(cleaned)
    final_result = split_on_range_marker(final_result)
    final_result = distribute_text_by_range_marker(final_result)

    with open(output_file, 'w', encoding='utf-8') as f:
        for line in final_result:
            f.write(line + '\n')
