import json

import gspread  # 구글스프레드시트 함수 불러오기
from oauth2client.service_account import ServiceAccountCredentials

scopes = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/cloud-platform',
]
json_file_name = r'google_key.json'
credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scopes)
gc = gspread.authorize(credentials)  # 간소화 변수로 구글스프레드시트 접근인증하기 / Client 클래스 인스턴스 생성
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1Pa9DDI2Uy2hbf_zq1ppsFeFN5rpc1CkE7ePl_bXyHuc/'
copy_worksheet_file = 'copy_worksheet.json'


def get_sheet_data(name: str, cell_range: str = None):
    spreadsheet = gc.open_by_url(spreadsheet_url)  # url 열기 / Spreadsheet 클래스 호출
    worksheet = spreadsheet.worksheet(name)  # 시트 선택하기 / Worksheet 클래스 호출

    if cell_range:
        data = worksheet.get_values(cell_range)
    else:
        data = worksheet.get_all_values()

    return data


def get_answer_dict(worksheet: str, id_range: str, answer_range: str):
    id_data = get_sheet_data(worksheet, id_range)
    answer_data = get_sheet_data(worksheet, answer_range)

    id_list = [item for sublist in id_data for item in sublist]
    answer_list = [item for sublist in answer_data for item in sublist]

    if len(id_list) == len(answer_list):
        answer_set = list(zip(id_list, answer_list))

        with open('answer_set.txt', 'w') as file:
            for pair in answer_set:
                file.write(f'{pair[0]}, {pair[1]}\n')
        print(dict(answer_set))
    else:
        print('Error')


def get_copy_data():
    spreadsheet = gc.open_by_url(spreadsheet_url)  # url 열기 / Spreadsheet 클래스 호출
    worksheet = spreadsheet.worksheet('copy')  # 시트 선택하기 / Worksheet 클래스 호출
    copy_worksheet = worksheet.get_all_records()

    with open(copy_worksheet_file, 'w', encoding='utf-8') as file:
        json.dump(copy_worksheet, file, ensure_ascii=False, indent=4)

# get_answer_dict('settings', 'K:K', 'R:R')
# get_copy_data()

# copy, result, reference, data_all, data_statistics


# verify_new_data_exists_or_not()
