import io
from urllib.parse import quote

from django.http import HttpResponse

from common.utils.decorators import *


@for_all_views
def get_response_for_excel_file(df, filename, excel_data=None) -> HttpResponse:
    if excel_data is None:
        excel_data = io.BytesIO()
        df.to_excel(excel_data, engine='xlsxwriter')

    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={quote(filename)}'

    return response
