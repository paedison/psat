from pathlib import Path
import math
from multiprocessing import cpu_count, Pool

import pandas as pd
from pdf2image import convert_from_path
from PIL import Image, ImageChops

from . import utils

BASE_DIR = Path('D:/projects/#script_data/#extract_png_images')
SAVE_DIR = BASE_DIR / 'output_images'


def run():
    Path.mkdir(SAVE_DIR, exist_ok=True)

    print('=== PDF to JPEG Converter ===')
    input_file = utils.get_user_input('입력 파일명: ', 'input', str)
    output_folder = utils.get_user_input('저장 폴더명: ', '', str)
    margin_mm = utils.get_user_input('이미지 여백(mm): ', 5, float)
    dpi = utils.get_user_input('이미지 해상도(DPI): ', 300, int)
    thread_count = utils.get_user_input('쓰레드 개수: ', cpu_count(), int)

    if output_folder:
        save_folder = SAVE_DIR / output_folder
    else:
        save_folder = SAVE_DIR

    pdf_path = Path(input_file).with_suffix('.pdf')
    if pdf_path.parent == Path('.'):
        pdf_path = BASE_DIR / pdf_path
    excel_path = Path(pdf_path).with_suffix('.xlsx')

    filename_list = []
    df = pd.read_excel(excel_path)
    for idx, row in df.iterrows():
        year = row['연도']
        ex = row['시험']
        sub = row['과목']
        number = row['번호']
        filename_list.append({'year': year, 'filename': f'PSAT{year}{ex}{sub}{number:02}'})

    total_files = len(filename_list)

    print(f'🔄 총 파일 수: {total_files} / 병렬 처리: {thread_count} threads')

    for chunk_start, filename_chunk in chunked(filename_list):
        first_page = chunk_start + 1
        last_page = chunk_start + len(filename_chunk)
        print(f'📄 처리 중: {first_page} ~ {last_page} 페이지...')

        images = convert_from_path(
            pdf_path=pdf_path,
            dpi=dpi,
            thread_count=thread_count,
            first_page=first_page,
            last_page=last_page,
        )

        task_list = [
            (
                chunk_start + idx + 1,
                image,
                filename_chunk[idx]['year'],
                filename_chunk[idx]['filename'],
                margin_mm,
                dpi,
                save_folder
            ) for idx, image in enumerate(images)
        ]

        with Pool(processes=thread_count) as pool:
            pool.map(process_page, task_list)

    print('🎉 모든 작업 완료!')


def chunked(lst, chunk_size=30):
    for i in range(0, len(lst), chunk_size):
        yield i, lst[i:i+chunk_size]


def process_page(args):
    index, image, year, filename, margin_mm, dpi, save_folder = args
    try:
        Path.mkdir(save_folder / str(year), exist_ok=True)
        save_path = save_folder / str(year) / f'{filename}.png'

        if save_path.exists():
            print(f'[{index}] ⏭ 이미 존재하는 파일: {save_path}')
            return

        cropped = auto_crop_with_margin(image, margin_mm, dpi)
        cropped.save(save_path, "PNG")
        print(f"[{index}] ✅ 저장 완료: {save_path}")
    except Exception as e:
        print(f'[{index}] ❌ 오류 발생: {e}')


def auto_crop_with_margin(img, margin_mm=5, dpi=300):
    # Convert to grayscale for more reliable bounding box detection
    gray = img.convert("L")
    bg = Image.new("L", img.size, 255)  # white background
    diff = ImageChops.difference(gray, bg)
    bbox = diff.getbbox()

    if not bbox:
        return img  # nothing to crop

    margin_px = mm_to_pixels(margin_mm, dpi)
    left = max(bbox[0] - margin_px, 0)
    top = max(bbox[1] - margin_px, 0)
    right = min(bbox[2] + margin_px, img.width)
    bottom = min(bbox[3] + margin_px, img.height)
    return img.crop((left, top, right, bottom))


def mm_to_pixels(mm, dpi):
    return math.ceil((mm / 25.4) * dpi)
