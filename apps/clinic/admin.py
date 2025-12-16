from django.contrib import admin
from .models import (
    Dentist, ClinicHours, Symptom, DailyClinicState, ClinicInfo,
    DentalHabit, ContinuousHabit, Appointment,
    AppointmentHabitResponse, AppointmentContinuousResponse
)

# 1. 牙醫管理
@admin.register(Dentist)
class DentistAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

# 2. 症狀管理
@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_editable = ('is_active',)

# 3. 營業時間管理
@admin.register(ClinicHours)
class ClinicHoursAdmin(admin.ModelAdmin):
    list_display = ('get_day_of_week_display', 'morning', 'afternoon', 'evening')
    list_display_links = ('get_day_of_week_display',)

# 4. 每日叫號狀態
@admin.register(DailyClinicState)
class DailyClinicStateAdmin(admin.ModelAdmin):
    list_display = ('date', 'time_slot', 'current_number')
    list_filter = ('date', 'time_slot')

# 5. 診所資訊
@admin.register(ClinicInfo)
class ClinicInfoAdmin(admin.ModelAdmin):
    list_display = ('slogan_title', 'phone', 'address')

# 6. 習慣調查 (李克特)
@admin.register(DentalHabit)
class DentalHabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_label', 'max_label', 'is_active')
    list_editable = ('is_active',)

# 7. 連續資料題目
@admin.register(ContinuousHabit)
class ContinuousHabitAdmin(admin.ModelAdmin):
    list_display = ('question', 'unit', 'is_active')
    list_editable = ('is_active',)

# 設定 Inline 讓管理員能在掛號單裡面直接看調查結果
class AppointmentHabitResponseInline(admin.TabularInline):
    model = AppointmentHabitResponse
    extra = 0
    readonly_fields = ('habit', 'score')
    can_delete = False

class AppointmentContinuousResponseInline(admin.TabularInline):
    model = AppointmentContinuousResponse
    extra = 0
    readonly_fields = ('question', 'value')
    can_delete = False

# 8. 掛號紀錄管理 (修正這裡！)
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    # ★★★ 把 phone 改成 age ★★★
    list_display = ('date', 'time_slot', 'real_name', 'age', 'patient_id', 'registration_number')
    list_filter = ('date', 'time_slot')
    search_fields = ('real_name', 'patient_id') # phone 移除了，所以搜尋也移除
    date_hierarchy = 'date'
    
    # 加入 Inline 顯示調查結果
    inlines = [AppointmentHabitResponseInline, AppointmentContinuousResponseInline]