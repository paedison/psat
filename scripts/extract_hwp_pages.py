import os
from time import sleep

import pandas as pd
from pyhwpx import Hwp


def run():
    blank_path = r"D:\projects\test\blank.hwp"
    save_dir = r"D:\projects\test\data"
    os.makedirs(save_dir, exist_ok=True)

    source_filename = get_user_input('원본 파일명 경로(source_filename): ', "original", str)
    source_path = f'D:\\projects\\test\\{source_filename}.hwp'
    excel_path = f'D:\\projects\\test\\{source_filename}.xlsx'

    df = pd.read_excel(excel_path)
    file_names = df['일련번호'].tolist()

    # hwp = Hwp()
    hwp = Hwp(visible=False)
    try:
        hwp.open(source_path, arg="versionwarning:false")

        hwp.add_tab()
        hwp.switch_to(0)
        hwp.MoveDocBegin()

        total_pages = hwp.PageCount
        if total_pages != len(file_names):
            print(f"페이지 수({total_pages})와 파일명 수({len(file_names)})가 다릅니다.")
            hwp.quit()
            return exit()

        # 각 페이지별로 저장
        for i in range(total_pages):
            print(f"{i + 1}페이지 처리 중...")

            hwp.MoveDocBegin()
            hwp.Select()
            hwp.MovePageDown()
            hwp.MoveLeft()
            hwp.Cut()
            hwp.DeletePage()

            hwp.switch_to(1)
            hwp.open(blank_path)
            hwp.MoveDocBegin()
            hwp.Paste()

            save_path = os.path.join(save_dir, f"{file_names[i]}.hwp")
            hwp.save_as(save_path)
            hwp.switch_to(0)
            sleep(0.5)
    finally:
        hwp.close()
        hwp.quit()


def get_user_input(prompt, default, type_func):
    user_input = input(f"{prompt} [default: {default}]: ").strip()
    return type_func(user_input) if user_input else default
