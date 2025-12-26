from django.urls import path
from . import views

urlpatterns = [
    # 0. 診所首頁 (會員看診狀態)
    path('', views.member_home, name='member_home'),

    # 1. 後台管理功能
    path('management/dentists/', views.update_dentist_description, name='update_dentist_description'),
    path('management/hours/', views.update_clinic_hours, name='update_clinic_hours'),
    path('management/symptoms/', views.update_symptoms, name='update_symptoms'),
    path('management/info/', views.update_clinic_info, name='update_clinic_info'),
    path('management/habits/', views.update_habits, name='update_habits'),

    # 2. 叫號功能
    path('call_next/', views.call_next_number, name='call_next_number'),

    # ==========================================
    # 3. ★★★ 新版預約系統路徑 (關鍵修正) ★★★
    # ==========================================
    # 第一步：選擇時段 (近七日)
    path('booking/select/', views.booking_select_time, name='booking_select_time'),
    
    # 第二步：填寫個資 (身分證驗證)
    path('booking/info/', views.booking_patient_info, name='booking_patient_info'),
    
    # 第三步：習慣調查 (完成掛號)
    path('booking/habit/', views.booking_habit_survey, name='booking_habit_survey'),
    path('reset_number/', views.reset_number, name='reset_number'),
    path('data/sheet/', views.patient_data_sheet, name='patient_data_sheet'),
    path('data/export/', views.export_patient_csv, name='export_patient_csv'),
    path('data/hide/<int:appt_id>/', views.hide_appointment, name='hide_appointment'),
    path('dashboard/', views.clinic_dashboard, name='clinic_dashboard'),
    
]