import sys

import gspread  # 구글스프레드시트 함수 불러오기
from oauth2client.service_account import ServiceAccountCredentials

scopes = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/cloud-platform',
]
json_file_name = r'google_service_key.json'
credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scopes)
gc = gspread.authorize(credentials)  # 간소화 변수로 구글스프레드시트 접근인증하기 / Client 클래스 인스턴스 생성
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1Pa9DDI2Uy2hbf_zq1ppsFeFN5rpc1CkE7ePl_bXyHuc/'


def get_sheet_data(
        url: str, name: str, cell_range: str = None,
):
    spreadsheet = gc.open_by_url(url)  # url 열기 / Spreadsheet 클래스 호출
    worksheet = spreadsheet.worksheet(name)  # 시트 선택하기 / Worksheet 클래스 호출

    if cell_range:
        data = worksheet.get_values(cell_range)
    else:
        data = worksheet.get_all_values()

    return data

    # header = data[0]
    # dict_data = []
    # for row in data[1:]:
    #     row_dict = {}
    #     for col, value in enumerate(row):
    #         row_dict[header[col]] = value
    #     dict_data.append(row_dict)
    # return dict_data


def get_answer_dict(worksheet: str, id_range: str, answer_range):
    id_data = get_sheet_data(spreadsheet_url, worksheet, id_range)
    answer_data = get_sheet_data(spreadsheet_url, worksheet, answer_range)

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


get_answer_dict('settings', 'K:K', 'R:R')
