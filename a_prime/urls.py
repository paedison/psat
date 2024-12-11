from django.urls import path, include

from .views import score_views, predict_views, admin_views

app_name = 'prime'

score_patterns = [
    path('', score_views.list_view, name='score-list'),
    path('<int:pk>/', score_views.detail_view, name='score-detail'),
    path('register/<int:pk>/', score_views.register_view, name='score-register'),
    path('unregister/<int:pk>/', score_views.unregister_view, name='score-unregister'),

    path('print/<int:pk>/', score_views.print_view, name='score-print'),
    path('modal/<int:pk>/', score_views.modal_view, name='score-modal'),
]

admin_patterns = [
    path('', admin_views.list_view, name='score-admin-list'),
    path('<int:pk>/', admin_views.detail_view, name='score-admin-detail'),
    path('update/<int:pk>/', admin_views.update_view, name='score-admin-update'),
    # path('<int:pk>/', admin_views.admin_problem_list_view, name='admin-problem-list'),
    # path('psat/create/', admin_views.psat_create_view, name='admin-psat-create'),
    # path('psat/active/<int:pk>/', admin_views.psat_active_view, name='admin-psat-active'),
    # path('problem/update/', admin_views.problem_update_view, name='admin-problem-update'),
    # path('answer/<int:pk>/', admin_views.answer_detail_view, name='staff-answer-detail'),

    # path('search/<int:exam_year>/<int:exam_round>/', catalog_view, name='catalog_year_round'),

    # path('print/<int:exam_year>/<int:exam_round>/',
    #      prime_psat_admin_views.print_view, name='print'),
    # path('print/<int:exam_year>/<int:exam_round>/<int:student_id>',
    #      prime_psat_admin_views.individual_student_print_view, name='individual_student_print'),
    #
    # path('export/transcript/<int:exam_year>/<int:exam_round>/',
    #      prime_psat_admin_views.export_transcript_to_pdf_view, name='export_transcript'),
    # path('export/statistics/<int:exam_year>/<int:exam_round>/',
    #      prime_psat_admin_views.export_statistics_to_excel_view, name='export_statistics'),
    # path('export/analysis/<int:exam_year>/<int:exam_round>/',
    #      prime_psat_admin_views.export_analysis_to_excel_view, name='export_analysis'),
    # path('export/students_score/<int:exam_year>/<int:exam_round>/',
    #      prime_psat_admin_views.export_scores_to_excel_view, name='export_scores'),
]

predict_patterns = [
    # path('', predict_views.index_view, name='predict-index'),
    # path('<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
    #      predict_views.detail_view, name='detail'),
    # path('student/<int:exam_year>/<str:exam_exam>/<int:exam_round>/',
    #      predict_views.student_create_view, name='student-create'),
    # path('answer/<int:exam_year>/<str:exam_exam>/<int:exam_round>/<str:subject_field>/',
    #      predict_views.answer_input_view, name='answer-input'),
    # path('answer/confirm/<int:exam_year>/<str:exam_exam>/<int:exam_round>/<str:subject_field>/',
    #      predict_views.answer_confirm_view, name='answer-confirm'),
    # path('admin/', include(admin_patterns)),
]

urlpatterns = [
    path('score/', include(score_patterns)),
    path('admin/', include(admin_patterns)),
    path('predict/', include(predict_patterns)),
]
