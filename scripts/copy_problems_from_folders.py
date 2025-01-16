import os
import shutil
import pandas as pd


def run(input_folder, output_folder, reference_file):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    df = pd.read_excel(reference_file)
    subject_map = {'언어': '01', '자료': '02', '상황': '03'}

    for index, row in df.iterrows():
        subject = row['과목']
        no = f"{int(row['순서']):02}"
        serial = row['일련번호']

        subject_code = subject_map[subject]
        folder_name = f'{subject_code}_{subject}'
        subject_folder = os.path.join(input_folder, folder_name)
        input_file = os.path.join(subject_folder, f'{serial}.pdf')

        if os.path.exists(input_file):
            subject_output_folder = os.path.join(output_folder, folder_name)
            if not os.path.exists(subject_output_folder):
                os.makedirs(subject_output_folder)

            output_file = os.path.join(subject_output_folder, f'{subject}_{no}_{serial}.pdf')
            shutil.copyfile(input_file, output_file)
            print(f'Copied: {input_file} to {output_file}')
        else:
            print(f'File not found: {input_file}')
