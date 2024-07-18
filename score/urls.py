from django.urls import path, include

from score.views.psat_v4 import score_views, student_views
from score.views.prime_v3 import normal_views, admin_views
from score.views.predict_v1 import (
    normal_views as predict_normal_views,
    test_views as predict_test_views,
    admin_views as predict_admin_views,
)

app_name = 'score_old'

psat_urlpatterns = [
    path('', score_views.list_view, name='psat-list'),

    path('detail/', score_views.detail_view, name='psat-detail'),
    path('detail/<int:year>/<str:ex>/', score_views.detail_view, name='psat-detail-year-ex'),
    path('detail/filter/exam/', score_views.exam_filter, name='psat-filter'),

    path('submit/<int:problem_id>/', score_views.submit_view, name='psat-submit'),
    path('confirm/modal/', score_views.confirm_modal_view, name='psat-confirm-modal'),

    path('no_student/modal/<int:year>/<str:ex>/',
         student_views.no_student_modal_view, name='psat-no-student-modal'),

    path('student/create/modal/<int:year>/<str:ex>/',
         student_views.student_create_modal_view, name='psat-student-create-modal'),
    path('student/create/department/',
         student_views.student_create_department, name='psat-student-create-department'),
    path('student/create/',
         student_views.student_create_view, name='psat-student-create'),

    path('student/update/modal/<int:student_id>/',
         student_views.student_update_modal_view, name='psat-student-update-modal'),
    path('student/update/department/<int:student_id>/',
         student_views.student_update_department, name='psat-student-update-department'),
    path('student/update/<int:student_id>/',
         student_views.student_update_view, name='psat-student-update'),
]

prime_urlpatterns = [
    path('', normal_views.list_view, name='prime-list'),

    path('<int:year>/<int:round>/', normal_views.detail_view, name='prime-detail'),
    path('<int:year>/<int:round>/print/', normal_views.detail_print_view, name='prime-print'),

    path('<int:year>/<int:round>/no_open/', normal_views.no_open_modal_view, name='prime-no-open-modal'),
    path('<int:year>/<int:round>/no_student/', normal_views.no_student_modal_view, name='prime-no-student-modal'),

    path('predict/no_open/', normal_views.no_predict_open_modal, name='prime-no-predict-open-modal'),

    path('<int:year>/<int:round>/student/modal/',
         normal_views.student_connect_modal_view, name='prime-student-connect-modal'),
    path('<int:year>/<int:round>/student/connect/',
         normal_views.student_connect_view, name='prime-student-connect'),
    path('<int:year>/<int:round>/student/reset/',
         normal_views.student_reset_view, name='prime-student-reset'),
]

prime_admin_urlpatterns = [
    path('', admin_views.list_view, name='prime-admin-list'),
    path('student/', admin_views.list_student_view, name='prime-admin-list-student'),

    path('<int:year>/<int:round>/', admin_views.detail_view, name='prime-admin-detail'),
    path('search/<int:year>/<int:round>/', admin_views.catalog_view, name='prime-admin-catalog-year-round'),

    path('print/<int:year>/<int:round>/', admin_views.print_view, name='prime-admin-print'),
    path('print/<int:year>/<int:round>/<int:student_id>',
         admin_views.individual_student_print_view, name='prime-admin-individual-student-print'),

    path('export/transcript/<int:year>/<int:round>/',
         admin_views.export_transcript_to_pdf_view, name='prime-admin-export-transcript'),
    path('export/statistics/<int:year>/<int:round>/',
         admin_views.export_statistics_to_excel_view, name='prime-admin-export-statistics'),
    path('export/analysis/<int:year>/<int:round>/',
         admin_views.export_analysis_to_excel_view, name='prime-admin-export-analysis'),
    path('export/students_score/<int:year>/<int:round>/',
         admin_views.export_scores_to_excel_view, name='prime-admin-export-scores'),
]

predict_urlpatterns = [
    path('', predict_normal_views.index_view, name='predict-index'),
    path('test/', predict_test_views.TestView.as_view(), name='predict-test'),

    path('student/', predict_normal_views.student_create_view, name='predict-student-create'),
    path('student/department/',
         predict_normal_views.student_create_department, name='predict-student-create-department'),

    path('answer/<str:sub>/', predict_normal_views.answer_input_view, name='predict-answer-input'),
    path('answer/<str:sub>/submit/', predict_normal_views.answer_submit_view, name='predict-answer-submit'),
    path('answer/<str:sub>/confirm/', predict_normal_views.answer_confirm_view, name='predict-answer-confirm'),

    path('update/info_answer/', predict_normal_views.update_info_answer, name='predict-update-info-answer'),
    path('update/sheet_answer/', predict_normal_views.update_sheet_answer, name='predict-update-sheet-answer'),
    path('update/sheet_score/', predict_normal_views.update_sheet_score, name='predict-update-sheet-score'),
]

predict_admin_urlpatterns = [
    path('', predict_admin_views.list_view, name='predict-admin-list'),
    path('student/', predict_admin_views.list_student_view, name='predict-admin-list-student'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/', predict_admin_views.detail_view, name='predict-admin-detail'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/catalog/', predict_admin_views.catalog_view, name='predict-admin-catalog'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/user<int:user_id>/',
         predict_admin_views.individual_index_view, name='predict-admin-individual'),

    path('test/', predict_admin_views.test_view, name='predict-admin-test'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/update/answer/',
         predict_admin_views.update_answer, name='predict-admin-update-answer'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/update/score/',
         predict_admin_views.update_score, name='predict-admin-update-score'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/update/statistics/',
         predict_admin_views.update_statistics, name='predict-admin-update-statistics'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/print/', predict_admin_views.print_view, name='predict-admin-print'),
    # path('print/<int:year>/<int:round>/<int:student_id>',
    #      predict_admin_views.individual_student_print_view, name='predict-admin-individual-student-print'),

    path('<str:category>/<int:year>/<str:ex>/<int:round>/export/transcript',
         predict_admin_views.export_transcript_to_pdf_view, name='predict-admin-export-transcript'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/export/statistics/',
         predict_admin_views.export_statistics_to_excel_view, name='predict-admin-export-statistics'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/export/analysis/',
         predict_admin_views.export_analysis_to_excel_view, name='predict-admin-export-analysis'),
    path('<str:category>/<int:year>/<str:ex>/<int:round>/export/students_score/',
         predict_admin_views.export_scores_to_excel_view, name='predict-admin-export-scores'),
    path('export/predict/google_sheet',
         predict_admin_views.export_predict_data_to_google_sheet_view, name='predict-admin-export-predict-to-google'),
]

urlpatterns = [
    path('psat/', include(psat_urlpatterns)),  # Psat score current version
    path('prime/', include(prime_urlpatterns)),  # Prime score current version
    path('prime/admin/', include(prime_admin_urlpatterns)),  # Prime_admin score current version
    path('predict/', include(predict_urlpatterns)),  # Predict score current version
    path('predict/admin/', include(predict_admin_urlpatterns)),  # Predict_admin score current version
]
#
# urlpatterns = [
#     path('psat/', include('score.urls_module.psat_v4')),  # Psat score current version
#     # path('psat/', include('score.urls_module.psat_v3')),  # Psat score current version
#     # path('psat_v2/', include('score.urls_module.psat_v2')),  # Psat score version 2.0
#     # path('psat_v1/', include('score.urls_module.psat_v1')),  # Psat score version 1.0
#
#     path('prime/', include('score.urls_module.prime_v3')),  # Prime score current version
#     # path('prime/', include('score.urls_module.prime_v2')),  # Prime score version 2.0
#     # path('prime_v1/', include('score.urls_module.prime_v1')),  # Prime score version 1.0
#
#     path('prime/admin/', include('score.urls_module.prime_admin_v3')),  # Prime_admin score current version
#     # path('prime/admin/', include('score.urls_module.prime_admin_v2')),  # Prime_admin score version 2.0
#     # path('prime_v1/admin/', include('score.urls_module.prime_admin_v1')),  # Prime_admin score version 1.0
#
#     path('predict/', include('score.urls_module.predict_v1')),  # Predict score current version
#     path('predict/admin/', include('score.urls_module.predict_admin_v1')),  # Predict_admin score current version
# ]
