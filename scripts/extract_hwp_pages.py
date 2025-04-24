import os

import pandas as pd
from pyhwpx import Hwp


def run():
    save_dir = r'D:\projects\test\data'
    os.makedirs(save_dir, exist_ok=True)

    source_filename = get_user_input('원본 파일명 경로(source_filename): ', "original", str)
    source_path = f'D:\\projects\\test\\{source_filename}.hwp'
    excel_path = f'D:\\projects\\test\\{source_filename}.xlsx'

    df = pd.read_excel(excel_path)
    file_names = df['일련번호'].tolist()

    hwp = Hwp(visible=False)
    hwp.open(source_path, arg='versionwarning:false')
    hwp.MoveDocBegin()
    total_pages = hwp.PageCount

    if total_pages != len(file_names):
        print(f'페이지 수({total_pages})와 파일명 수({len(file_names)})가 다릅니다.')
        hwp.quit()
        return

    for idx, row in df.iterrows():
        serial = row['일련번호']
        file_name = f'{serial}.hwp'
        save_path = os.path.join(save_dir, file_name)

        print(f'{idx + 1}페이지 처리 중: {file_name}')
        hwp.Select()
        hwp.MovePageEnd()
        hwp.save_block_as(save_path)
        hwp.DeleteBack()
        hwp.Delete()
        hwp.Delete()

    hwp.close()
    hwp.quit()
    print("✅ 모든 페이지 분할 및 저장 완료.")


def get_user_input(prompt, default, type_func):
    user_input = input(f"{prompt} [default: {default}]: ").strip()
    return type_func(user_input) if user_input else default
