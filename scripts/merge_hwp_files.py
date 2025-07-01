import os
from pathlib import Path

import win32com.client as win32

from . import utils

BASE_DIR = Path('D:/projects/#script_data/#merge_hwp_files')
OUTPUT_FOLDER = BASE_DIR / 'output'


def run():
    input_folder_input = utils.get_user_input('폴더 경로: ', 'D:/projects/#merge_hwp_files', str)
    output_folder_input = utils.get_user_input('폴더 경로: ', 'D:/projects/#merge_hwp_files/output', str)
    output_filename = utils.get_user_input('출력 파일(hwp): ', '작업 결과', str)

    output_folder = Path(output_folder_input)
    output_file = output_folder / f'{output_filename}.hwp'
    merge_hwp_files(input_folder_input, output_file)


def merge_hwp_files(folder_path, output_file):
    # 출력 폴더 생성
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 파일명 기준 정렬된 .hwp 목록
    file_list = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(".hwp")])
    if not file_list:
        print("병합할 .hwp 파일이 없습니다.")
        return

    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "SecurityModule")

    for i, file in enumerate(file_list):
        file_path = os.path.join(folder_path, file)
        print(f"→ 처리 중: {file}")

        if i == 0:
            hwp.Open(file_path)
        else:
            hwp.MovePos(3)
            hwp.HAction.Run("BreakPage")

            hwp.HAction.GetDefault("InsertFile", hwp.HParameterSet.HInsertFile.HSet)
            hwp.HParameterSet.HInsertFile.filename = file_path
            hwp.HParameterSet.HInsertFile.KeepSection = 0  # 구역 없이 붙이기
            hwp.HAction.Execute("InsertFile", hwp.HParameterSet.HInsertFile.HSet)

    hwp.SaveAs(output_file)
    hwp.Quit()
    print(f"✅ 병합 완료: {output_file}")
