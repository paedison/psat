from pathlib import Path

import pandas as pd
from pyhwpx import Hwp

BASE_DIR = Path('D:/projects/test')
SAVE_DIR = BASE_DIR / 'data'


def run():
    Path.mkdir(SAVE_DIR, exist_ok=True)

    input_file = get_user_input('입력 파일: ', "original", str).replace('"', '')
    output_folder = get_user_input('저장 폴더: ', "", str).replace('"', '')

    if output_folder:
        save_folder = SAVE_DIR / output_folder
    else:
        save_folder = SAVE_DIR

    hwp_path = Path(input_file).with_suffix('.hwp')
    if hwp_path.parent == Path('.'):
        hwp_path = BASE_DIR / hwp_path
    excel_path = Path(hwp_path).with_suffix('.xlsx')

    df = pd.read_excel(excel_path)
    file_names = df['일련번호'].tolist()

    hwp = Hwp(visible=False)
    hwp.open(str(hwp_path), arg='versionwarning:false')
    hwp.MoveDocBegin()
    total_pages = hwp.PageCount

    if total_pages != len(file_names):
        print(f'페이지 수({total_pages})와 파일명 수({len(file_names)})가 다릅니다.')
        hwp.quit()
        return

    for idx, row in df.iterrows():
        serial = row['일련번호']
        file_name = f'{serial}.hwp'
        save_path = save_folder / file_name

        hwp.Select()
        hwp.MovePageEnd()
        if save_path.exists():
            print(f'{idx + 1}페이지 → {file_name} ❌  이미 존재하는 파일')
        else:
            print(f'{idx + 1}페이지 → {file_name}')
            hwp.save_block_as(str(save_path))
        hwp.DeleteBack()
        hwp.Delete()
        hwp.Delete()

    hwp.close()
    hwp.quit()
    print("✅ 모든 페이지 분할 및 저장 완료.")


def get_user_input(prompt, default, type_func):
    user_input = input(f"{prompt} [default: {default}]: ").strip()
    return type_func(user_input) if user_input else default
