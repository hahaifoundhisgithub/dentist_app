# apps/member/views.py
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import datetime

# ★ 關鍵：引入 Clinic 的模型
from apps.clinic.models import (
    ClinicHours, DailyClinicState, ClinicInfo, Dentist
)

def home(request):
    """
    會員首頁：整合診所看診狀態 + 醫師列表 + 門診時間表
    """
    # 1. 時間初始化
    now = timezone.localtime(timezone.now())
    current_time = now.time()
    current_weekday = now.weekday() + 1 

    # 2. 預設狀態
    clinic_status = "目前休診中"
    status_color = "text-red-500"
    is_open = False
    current_number = "--"
    current_session = None

    # 3. 判斷看診狀態
    try:
        today_schedule = ClinicHours.objects.get(day_of_week=current_weekday)
        
        def check_time(time_str):
            if not time_str: return False
            try:
                clean_str = time_str.replace(" ", "").replace("：", ":")
                if '-' in clean_str:
                    start_str, end_str = clean_str.split('-')
                elif '~' in clean_str:
                    start_str, end_str = clean_str.split('~')
                else:
                    return False
                start_t = datetime.strptime(start_str, "%H:%M").time()
                end_t = datetime.strptime(end_str, "%H:%M").time()
                return start_t <= current_time <= end_t
            except:
                return False

        if today_schedule.morning and check_time(today_schedule.morning_time):
            clinic_status = "目前看診時段：早診"
            status_color = "text-[#228B22]" # 綠色
            is_open = True
            current_session = 'morning'
        elif today_schedule.afternoon and check_time(today_schedule.afternoon_time):
            clinic_status = "目前看診時段：午診"
            status_color = "text-[#228B22]" # 綠色
            is_open = True
            current_session = 'afternoon'
        elif today_schedule.evening and check_time(today_schedule.evening_time):
            clinic_status = "目前看診時段：晚診"
            status_color = "text-[#228B22]" # 綠色
            is_open = True
            current_session = 'evening'

        # 4. 撈取叫號

        # 4. 撈取叫號
        if is_open and current_session:
            # ★★★ 修正這裡：將 session= 改為 time_slot= ★★★
            daily_state = DailyClinicState.objects.filter(
                date=now.date(), 
                time_slot=current_session # 這裡改了！
            ).last()
            
            if daily_state:
                current_number = daily_state.current_number
            else:
                current_number = "準備中"
        
        # ... (後面程式碼保留) ...

    except Exception as e:
        print(f"會員首頁錯誤: {e}")

    # ==========================================
    # ★ 補回遺失的資料：醫師與時間表
    # ==========================================
    site_clinic_info = ClinicInfo.objects.first()
    dentists = Dentist.objects.all()  # 撈取所有醫師
    hours = ClinicHours.objects.all().order_by('day_of_week') # 撈取本週時間表

    return render(request, 'member/home.html', {
        'clinic_status': clinic_status,
        'status_color': status_color,
        'is_open': is_open,
        'current_number': current_number,
        'site_clinic_info': site_clinic_info,
        
        # ★ 記得傳進去，網頁才看得到
        'dentists': dentists,
        'hours': hours,
    })