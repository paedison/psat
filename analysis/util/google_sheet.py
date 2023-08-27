import gspread  # 구글스프레드시트 함수 불러오기
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account


scopes=[
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/cloud-platform',
]

# credentials, project = google.auth.default(
#     scopes=[
#         'https://spreadsheets.google.com/feeds',
#         'https://www.googleapis.com/auth/drive',
#         'https://www.googleapis.com/auth/cloud-platform',
#     ]
# )

json_file_name = r'google_service_key.json'
credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scopes)
# scoped_credentials = credentials.with_scopes[
#     'https://spreadsheets.google.com/feeds',
#     'https://www.googleapis.com/auth/drive',
#     'https://www.googleapis.com/auth/cloud-platform',
# ]

gc = gspread.authorize(credentials)  # 간소화 변수로 구글스프레드시트 접근인증하기
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1Pa9DDI2Uy2hbf_zq1ppsFeFN5rpc1CkE7ePl_bXyHuc/edit#gid=896405220'
doc = gc.open_by_url(spreadsheet_url)  # url 열기

# 스프레스시트 문서 가져오기
worksheet = doc.worksheet('copy')  # 시트 선택하기 (0=첫번째시트, 1=두번째시트)

print(doc.get_worksheet(1))

val = worksheet.acell('a1').value  # a1 값 불러오기(테스트해봄)
# val = worksheet.cell(6, 2).value  # 6행,2열 값 불러오기(테스트해봄)

row_values_list = worksheet.row_values(6)  # 첫 번째 행에서 모든 값을 가져옵니다.
col_values_list = worksheet.col_values(1)  # 첫 번째 열에서 모든 값을 가져옵니다.

list_of_lists = worksheet.get_all_values()  # 워크 시트의 모든 값을 목록 목록으로 가져 오기
print(list_of_lists[6])
