from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.forms import modelformset_factory
from django.utils import timezone
from datetime import datetime, timedelta

# 引入所有模型
from .models import (
    Dentist, ClinicHours, Symptom, Appointment, 
    DailyClinicState, ClinicInfo, DentalHabit, ContinuousHabit,
    AppointmentHabitResponse, AppointmentContinuousResponse
)

# 引入所有表單
from .forms import (
    DentistForm, ClinicHoursForm, ClinicGlobalTimeForm,
    SymptomForm, ClinicInfoForm, DentalHabitForm, ContinuousHabitForm,
    BookingPatientForm, BookingHabitForm
)

# 檢查是否為管理員的輔助函式
def is_admin(user):
    return user.is_staff

# ==========================================
# 0. 首頁 (會員/訪客專區)
# ==========================================
def member_home(request):
    """
    首頁：顯示診所看診狀態 (包含醫師與門診表)
    """
    # 1. 時間初始化
    now = timezone.localtime(timezone.now())
    current_time = now.time()
    current_weekday = now.weekday() + 1 

    clinic_status = "目前休診中"
    status_color = "text-red-500"
    is_open = False
    current_number = "--"
    current_session = None
    
    try:
        # 2. 抓取今天的設定
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
            except Exception:
                return False

        # 3. 依序檢查
        if today_schedule.morning and check_time(today_schedule.morning_time):
            clinic_status = "目前看診時段：早診"
            status_color = "text-[#228B22]"
            is_open = True
            current_session = 'morning'

        elif today_schedule.afternoon and check_time(today_schedule.afternoon_time):
            clinic_status = "目前看診時段：午診"
            status_color = "text-[#228B22]"
            is_open = True
            current_session = 'afternoon'

        elif today_schedule.evening and check_time(today_schedule.evening_time):
            clinic_status = "目前看診時段：晚診"
            status_color = "text-[#228B22]"
            is_open = True
            current_session = 'evening'
            
        # 4. 撈取叫號
        if is_open and current_session:
            daily_state = DailyClinicState.objects.filter(
                date=now.date(), 
                time_slot=current_session
            ).last()
            
            if daily_state:
                current_number = daily_state.current_number
            else:
                current_number = "準備中"

    except ClinicHours.DoesNotExist:
        pass
    except Exception as e:
        print(e)

    # 4. 準備所有要顯示的資料
    site_clinic_info = ClinicInfo.objects.first()
    dentists = Dentist.objects.all()
    hours = ClinicHours.objects.all().order_by('day_of_week')

    return render(request, 'member/home.html', {
        'clinic_status': clinic_status,
        'status_color': status_color,
        'is_open': is_open,
        'current_number': current_number,
        'site_clinic_info': site_clinic_info,
        'dentists': dentists,
        'hours': hours,
    })

# ==========================================
# 1. 更新醫師介紹
# ==========================================
@user_passes_test(is_admin, login_url='/admin/login/')
def update_dentist_description(request):
    DentistFormSet = modelformset_factory(Dentist, form=DentistForm, extra=0)
    
    if request.method == 'POST':
        formset = DentistFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            messages.success(request, '醫師介紹已更新成功！')
            return redirect('update_dentist_description')
    else:
        formset = DentistFormSet(queryset=Dentist.objects.all())

    return render(request, 'clinic/update_dentist_description.html', {
        'formset': formset,
        'title': '更新醫師介紹',
        'site_clinic_info': ClinicInfo.objects.first(), 
    })

# ==========================================
# 2. 更新營業時間
# ==========================================
@user_passes_test(is_admin, login_url='/admin/login/')
def update_clinic_hours(request):
    HoursFormSet = modelformset_factory(ClinicHours, form=ClinicHoursForm, extra=0)
    first_record = ClinicHours.objects.first()
    initial_time = {
        'morning_time': first_record.morning_time if first_record else "09:00-12:00",
        'afternoon_time': first_record.afternoon_time if first_record else "14:00-17:30",
        'evening_time': first_record.evening_time if first_record else "18:30-21:30",
    }

    if request.method == 'POST':
        formset = HoursFormSet(request.POST)
        time_form = ClinicGlobalTimeForm(request.POST)
        
        if formset.is_valid() and time_form.is_valid():
            formset.save()
            m_time = time_form.cleaned_data['morning_time']
            a_time = time_form.cleaned_data['afternoon_time']
            e_time = time_form.cleaned_data['evening_time']
            ClinicHours.objects.all().update(
                morning_time=m_time,
                afternoon_time=a_time,
                evening_time=e_time
            )
            messages.success(request, '營業時間與人數上限已更新！')
            return redirect('update_clinic_hours')
    else:
        formset = HoursFormSet(queryset=ClinicHours.objects.all().order_by('day_of_week'))
        time_form = ClinicGlobalTimeForm(initial=initial_time)

    return render(request, 'clinic/update_clinic_hours.html', {
        'formset': formset,
        'time_form': time_form,
        'title': '更新營業時間',
        'site_clinic_info': ClinicInfo.objects.first(),
    })

# ==========================================
# 3. 管理看診問題 (症狀)
# ==========================================
@user_passes_test(is_admin, login_url='/admin/login/')
def update_symptoms(request):
    SymptomFormSet = modelformset_factory(Symptom, form=SymptomForm, extra=1, can_delete=True)

    if request.method == 'POST':
        formset = SymptomFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            messages.success(request, '看診問題設定已更新！')
            return redirect('update_symptoms')
    else:
        formset = SymptomFormSet(queryset=Symptom.objects.all())

    return render(request, 'clinic/update_symptoms.html', {
        'formset': formset,
        'title': '管理看診問題',
        'site_clinic_info': ClinicInfo.objects.first(),
    })

# ==========================================
# 4. 設定診所資訊 (地址/電話)
# ==========================================
@staff_member_required
def update_clinic_info(request):
    info, created = ClinicInfo.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = ClinicInfoForm(request.POST, instance=info)
        if form.is_valid():
            form.save()
            messages.success(request, "診所資訊已更新！")
            return redirect('update_clinic_info')
    else:
        form = ClinicInfoForm(instance=info)

    return render(request, 'clinic/update_clinic_info.html', {
        'form': form,
        'title': '設定診所資訊',
        'site_clinic_info': info, 
    })

# ==========================================
# 5. 管理習慣調查
# ==========================================
@user_passes_test(is_admin, login_url='/admin/login/')
def update_habits(request):
    LikertFormSet = modelformset_factory(DentalHabit, form=DentalHabitForm, extra=1, can_delete=True)
    ContinuousFormSet = modelformset_factory(ContinuousHabit, form=ContinuousHabitForm, extra=1, can_delete=True)

    if request.method == 'POST':
        likert_formset = LikertFormSet(request.POST, prefix='likert')
        continuous_formset = ContinuousFormSet(request.POST, prefix='continuous')
        
        if likert_formset.is_valid() and continuous_formset.is_valid():
            likert_formset.save()
            continuous_formset.save()
            messages.success(request, '所有習慣調查題目已更新成功！')
            return redirect('update_habits')
    else:
        likert_formset = LikertFormSet(queryset=DentalHabit.objects.all(), prefix='likert')
        continuous_formset = ContinuousFormSet(queryset=ContinuousHabit.objects.all(), prefix='continuous')

    return render(request, 'clinic/update_habits.html', {
        'likert_formset': likert_formset,
        'continuous_formset': continuous_formset,
        'title': '管理習慣調查',
        'site_clinic_info': ClinicInfo.objects.first(),
    })

# ==========================================
# 6. 叫下一號 (功能實作)
# ==========================================
@user_passes_test(is_admin, login_url='/admin/login/')
def call_next_number(request):
    if request.method == 'POST':
        try:
            now = timezone.localtime(timezone.now())
            current_time = now.time()
            current_weekday = now.weekday() + 1
            today_schedule = ClinicHours.objects.get(day_of_week=current_weekday)
            session_name = None 
            
            def is_in_range(time_str):
                if not time_str: return False
                try:
                    clean = time_str.replace(" ", "").replace("：", ":")
                    if '-' in clean: s, e = clean.split('-')
                    elif '~' in clean: s, e = clean.split('~')
                    else: return False
                    st = datetime.strptime(s, "%H:%M").time()
                    et = datetime.strptime(e, "%H:%M").time()
                    return st <= current_time <= et
                except: return False

            if today_schedule.morning and is_in_range(today_schedule.morning_time):
                session_name = 'morning'
            elif today_schedule.afternoon and is_in_range(today_schedule.afternoon_time):
                session_name = 'afternoon'
            elif today_schedule.evening and is_in_range(today_schedule.evening_time):
                session_name = 'evening'
            
            if session_name:
                daily_state, created = DailyClinicState.objects.get_or_create(
                    date=now.date(),
                    time_slot=session_name,
                    defaults={'current_number': 0}
                )
                daily_state.current_number += 1
                daily_state.save()
                messages.success(request, f"成功叫號：{daily_state.current_number} 號")
            else:
                messages.warning(request, "目前非看診時段，無法叫號。")

        except Exception as e:
            print(f"叫號錯誤: {e}")
            messages.error(request, f"系統錯誤：{e}")

    return redirect(request.META.get('HTTP_REFERER', '/'))

# ==========================================
# ★★★ 新版預約系統 Start ★★★
# ==========================================

# 1. 選擇時段 (近7日)
@login_required(login_url='/accounts/login/')
def booking_select_time(request):
    if 'booking_data' in request.session:
        del request.session['booking_data']

    today = timezone.localtime(timezone.now()).date()
    start_date = today + timedelta(days=1)
    days_data = []

    for i in range(7):
        target_date = start_date + timedelta(days=i)
        weekday_idx = target_date.weekday()
        
        try:
            hours = ClinicHours.objects.get(day_of_week=weekday_idx)
            slots = []
            
            def check_slot(key, name, limit, time_str, is_open):
                if is_open:
                    count = Appointment.objects.filter(date=target_date, time_slot=key).count()
                    remaining = max(0, limit - count)
                    return {
                        'key': key, 'name': name, 'time': time_str,
                        'remaining': remaining, 'is_full': remaining <= 0
                    }
                return None

            if hours.morning:
                slots.append(check_slot('morning', '早診', hours.morning_limit, hours.morning_time, hours.morning))
            if hours.afternoon:
                slots.append(check_slot('afternoon', '午診', hours.afternoon_limit, hours.afternoon_time, hours.afternoon))
            if hours.evening:
                slots.append(check_slot('evening', '晚診', hours.evening_limit, hours.evening_time, hours.evening))
            
            days_data.append({
                'date': target_date,
                'weekday_name': hours.get_day_of_week_display(),
                'slots': [s for s in slots if s]
            })
        except ClinicHours.DoesNotExist:
            continue

    return render(request, 'clinic/booking_select_time.html', {
        'days_data': days_data,
        'site_clinic_info': ClinicInfo.objects.first()
    })

# 2. 填寫資料 (第一頁)
@login_required
def booking_patient_info(request):
    date_str = request.GET.get('date')
    slot_key = request.GET.get('slot')
    
    if not date_str or not slot_key:
        saved = request.session.get('booking_data', {})
        date_str = saved.get('date')
        slot_key = saved.get('slot')
        if not date_str:
            return redirect('booking_select_time')

    if request.method == 'POST':
        form = BookingPatientForm(request.POST)
        if form.is_valid():
            nid = form.cleaned_data['national_id']
            
            is_duplicate = Appointment.objects.filter(
                date=date_str,
                time_slot=slot_key,
                patient_id=nid
            ).exists()
            
            if is_duplicate:
                messages.error(request, "您已經掛號，無須再次預約掛號")
            else:
                request.session['booking_data'] = {
                    'date': date_str,
                    'slot': slot_key,
                    'real_name': form.cleaned_data['real_name'],
                    'age': form.cleaned_data['age'],
                    'national_id': nid,
                    'symptoms_ids': [s.id for s in form.cleaned_data['symptoms']]
                }
                return redirect('booking_habit_survey')
    else:
        initial_data = {}
        if 'booking_data' in request.session:
            data = request.session['booking_data']
            initial_data = {
                'real_name': data.get('real_name'),
                'phone': data.get('phone'),
                'national_id': data.get('national_id'),
                'symptoms': data.get('symptoms_ids')
            }
        form = BookingPatientForm(initial=initial_data)

    slot_map = {'morning': '早診', 'afternoon': '午診', 'evening': '晚診'}
    slot_name = slot_map.get(slot_key, slot_key)

    return render(request, 'clinic/booking_patient_info.html', {
        'form': form,
        'date_str': date_str,
        'slot_key': slot_key,
        'slot_name': slot_name,
        'site_clinic_info': ClinicInfo.objects.first()
    })

# 3. 習慣調查 (第二頁) -> 完成
# apps/clinic/views.py

# ... (上面的程式碼不用動)

@login_required
def booking_habit_survey(request):
    booking_data = request.session.get('booking_data')
    if not booking_data:
        return redirect('booking_select_time')

    if request.method == 'POST':
        form = BookingHabitForm(request.POST)
        if form.is_valid():
            try:
                count = Appointment.objects.filter(
                    date=booking_data['date'],
                    time_slot=booking_data['slot']
                ).count()
                new_number = count + 1

                # ★★★ 修正開始：將文字字串轉回日期物件 ★★★
                # Session 存的是字串 "2025-12-20"，我們要把它轉成 date 物件
                date_str = booking_data['date']
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                # ★★★ 修正結束 ★★★

                appointment = Appointment.objects.create(
                    user=request.user,
                    
                    # ★ 這裡改成使用轉換後的 date_obj
                    date=date_obj, 
                    
                    time_slot=booking_data['slot'],
                    real_name=booking_data['real_name'],
                    age=booking_data['age'],
                    patient_id=booking_data['national_id'],
                    registration_number=new_number,
                )
                
                if booking_data['symptoms_ids']:
                    appointment.symptoms.set(booking_data['symptoms_ids'])

                for field_name, value in form.cleaned_data.items():
                    if field_name.startswith('habit_'):
                        h_id = int(field_name.split('_')[1])
                        AppointmentHabitResponse.objects.create(
                            appointment=appointment, habit_id=h_id, score=int(value)
                        )
                    elif field_name.startswith('chabit_'):
                        c_id = int(field_name.split('_')[1])
                        AppointmentContinuousResponse.objects.create(
                            appointment=appointment, question_id=c_id, value=value
                        )

                del request.session['booking_data']

                return render(request, 'clinic/booking_success.html', {
                    'appointment': appointment,
                    'site_clinic_info': ClinicInfo.objects.first()
                })

            except Exception as e:
                print(f"Error: {e}")
                messages.error(request, "掛號失敗，請聯繫櫃台")
                return redirect('booking_select_time')
    else:
        form = BookingHabitForm()

    return render(request, 'clinic/booking_habit_survey.html', {
        'form': form,
        'site_clinic_info': ClinicInfo.objects.first()
    })
# 7. 手動歸零功能 (新增)
# apps/clinic/views.py

# ... (上面的程式碼不用動)

# ==========================================
# 7. 手動歸零功能 (修正版)
# ==========================================
@user_passes_test(is_admin, login_url='/admin/login/')
def reset_number(request):
    if request.method == 'POST':
        try:
            now = timezone.localtime(timezone.now())
            current_time = now.time()
            
            # 修正：Python的 weekday 0=週一，剛好對應 Model 的 0=週一，不需 +1
            current_weekday = now.weekday() 
            
            # 使用 filter().first() 避免如果沒設定班表會直接當機 (Crash)
            today_schedule = ClinicHours.objects.filter(day_of_week=current_weekday).first()
            
            if not today_schedule:
                messages.warning(request, "錯誤：找不到今天的營業時間設定，請先至後台設定班表。")
                return redirect(request.META.get('HTTP_REFERER', '/'))

            session_name = None 
            
            def is_in_range(time_str):
                if not time_str: return False
                try:
                    # 處理全形冒號與空格
                    clean = time_str.replace(" ", "").replace("：", ":")
                    if '-' in clean: s, e = clean.split('-')
                    elif '~' in clean: s, e = clean.split('~')
                    else: return False
                    
                    st = datetime.strptime(s, "%H:%M").time()
                    et = datetime.strptime(e, "%H:%M").time()
                    return st <= current_time <= et
                except: 
                    return False

            # 依序檢查時段
            if today_schedule.morning and is_in_range(today_schedule.morning_time):
                session_name = 'morning'
            elif today_schedule.afternoon and is_in_range(today_schedule.afternoon_time):
                session_name = 'afternoon'
            elif today_schedule.evening and is_in_range(today_schedule.evening_time):
                session_name = 'evening'
            
            # 執行歸零
            if session_name:
                daily_state, created = DailyClinicState.objects.get_or_create(
                    date=now.date(),
                    time_slot=session_name,
                    defaults={'current_number': 0}
                )
                daily_state.current_number = 0 # 強制歸零
                daily_state.save()
                
                # 顯示成功訊息 (包含時段名稱)
                slot_map = {'morning': '早診', 'afternoon': '午診', 'evening': '晚診'}
                display_name = slot_map.get(session_name, session_name)
                messages.success(request, f"已成功將【{display_name}】號碼歸零！")
            else:
                messages.warning(request, "目前時間不在任何看診時段內，無法執行歸零。")

        except Exception as e:
            # ★ 關鍵修改：將具體錯誤顯示出來，而不是只顯示「系統錯誤」
            print(f"歸零錯誤: {e}")
            messages.error(request, f"執行失敗，錯誤原因：{e}")

    return redirect(request.META.get('HTTP_REFERER', '/'))
# 8. 看診資料總表 (Sheet View)
# ==========================================
@user_passes_test(is_admin, login_url='/admin/login/')
def patient_data_sheet(request):
    # 1. 準備表頭 (Headers) - 包含 ID 以便識別
    # 固定表頭不需要在這裡查，前端寫死即可，這裡處理動態表頭
    likert_habits = DentalHabit.objects.filter(is_active=True).order_by('id')
    cont_habits = ContinuousHabit.objects.filter(is_active=True).order_by('id')
    
    headers = []
    # 給每個動態欄位一個索引 ID (index)，方便稍後排序對應
    col_index = 0
    for h in likert_habits:
        headers.append({'name': h.name, 'type': 'likert', 'id': h.id, 'sort_key': f'dyn_{col_index}'})
        col_index += 1
    for h in cont_habits:
        headers.append({'name': h.question, 'type': 'continuous', 'id': h.id, 'sort_key': f'dyn_{col_index}'})
        col_index += 1

    # 2. 抓取所有資料並組裝
    appointments = Appointment.objects.filter(is_visible=True).select_related('user') 
    
    data_rows = []
    for appt in appointments:
        # 整理症狀
        symptoms_str = "、".join([s.name for s in appt.symptoms.all()])
        if not symptoms_str: symptoms_str = "-"

        # 整理回答 (預先轉成 dict 加速查找)
        l_answers = {r.habit_id: r.score for r in AppointmentHabitResponse.objects.filter(appointment=appt)}
        c_answers = {r.question_id: r.value for r in AppointmentContinuousResponse.objects.filter(appointment=appt)}

        # 依照 headers 順序填入答案 list
        answers_list = []
        for h in headers:
            val = "-" # 預設值
            if h['type'] == 'likert':
                val = l_answers.get(h['id'], "-")
            elif h['type'] == 'continuous':
                val = c_answers.get(h['id'], "-")
            answers_list.append(val)

        # 組合該列資料
        data_rows.append({
            'appt': appt,
            'date': appt.date,               # 拉出來方便排序
            'time': appt.time_slot,          # 拉出來方便排序
            'pid': appt.patient_id,          # 拉出來方便排序
            'name': appt.real_name,          # 拉出來方便排序
            'age': appt.age,                 # 拉出來方便排序
            'symptoms': symptoms_str,
            'answers': answers_list          # 這是一個 list，對應 headers 的順序
        })

    # 3. 執行排序 (Python In-Memory Sorting)
    sort_by = request.GET.get('sort', 'date_desc') # 預設依日期新到舊

    def sort_helper(row):
        # 處理 "-" (空值) 的排序問題，將其視為 -1 或空字串
        val = None
        
        # A. 固定欄位排序
        if sort_by == 'date': return row['date']
        if sort_by == 'time': return row['time']
        if sort_by == 'pid': return row['pid']
        if sort_by == 'name': return row['name']
        if sort_by == 'age': return row['age']
        
        # B. 動態欄位排序 (格式: dyn_0, dyn_1...)
        if sort_by.startswith('dyn_'):
            try:
                idx = int(sort_by.split('_')[1])
                val = row['answers'][idx]
                # 如果是 "-" 轉為 -1 以便數字排序，否則回傳原值
                if val == "-": return -1
                return float(val) # 嘗試轉數字排序
            except:
                return -1 # 發生錯誤當作最小值
        
        return row['date'] # 預設

    # 判斷是否要反向排序 (desc)
    reverse = False
    if sort_by == 'date_desc':
        key_func = lambda x: x['date']
        reverse = True
    else:
        key_func = sort_helper
        # 如果是日期相關，通常我們希望預設反向(新到舊)，但這裡依據使用者點擊
        # 這裡為了簡單，除了 date_desc 預設反向外，其他點擊第一次皆為正向
    
    data_rows.sort(key=key_func, reverse=reverse)

    return render(request, 'clinic/patient_data_sheet.html', {
        'headers': headers,
        'data_rows': data_rows,
        'current_sort': sort_by,
        'site_clinic_info': ClinicInfo.objects.first(),
    })
# apps/clinic/views.py

import csv
import codecs # 用來處理中文編碼
from django.http import HttpResponse

# ... (上面的程式碼保留)

# ==========================================
# 9. 匯出 CSV 功能
# ==========================================
@user_passes_test(is_admin, login_url='/admin/login/')
def export_patient_csv(request):
    # 1. 設定 CSV 回應標頭
    response = HttpResponse(content_type='text/csv')
    # 設定下載檔名 (加入當下時間可避免檔名重複)
    filename = f"patient_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # 2. 寫入 BOM (Byte Order Mark) 以解決 Excel 中文亂碼問題
    response.write(codecs.BOM_UTF8)

    writer = csv.writer(response)

    # 3. 準備表頭 (Headers)
    # 固定欄位
    csv_headers = ['看診日期', '時段', '身分證字號', '姓名', '年齡', '主訴問題']
    
    # 動態欄位 (習慣調查)
    likert_habits = DentalHabit.objects.filter(is_active=True).order_by('id')
    cont_habits = ContinuousHabit.objects.filter(is_active=True).order_by('id')
    
    # 記住動態欄位的 ID 順序，以便稍後填值
    header_ids = [] 
    
    for h in likert_habits:
        csv_headers.append(h.name)
        header_ids.append({'type': 'likert', 'id': h.id})
        
    for h in cont_habits:
        csv_headers.append(h.question)
        header_ids.append({'type': 'continuous', 'id': h.id})

    # 寫入第一列 (表頭)
    writer.writerow(csv_headers)

    # 4. 準備資料內容
    # 依日期由新到舊排序匯出
    appointments = Appointment.objects.filter(is_visible=True).order_by('-date', 'time_slot')

    for appt in appointments:
        # 整理症狀
        symptoms_str = "、".join([s.name for s in appt.symptoms.all()])
        if not symptoms_str: symptoms_str = "-"

        # 準備該列資料 (固定欄位)
        row = [
            appt.date.strftime('%Y/%m/%d'),
            appt.get_time_slot_display(),
            appt.patient_id,
            appt.real_name,
            str(appt.age),
            symptoms_str
        ]

        # 整理回答 (預先轉成 dict 加速查找)
        l_answers = {r.habit_id: r.score for r in AppointmentHabitResponse.objects.filter(appointment=appt)}
        c_answers = {r.question_id: r.value for r in AppointmentContinuousResponse.objects.filter(appointment=appt)}

        # 填入動態欄位答案
        for h in header_ids:
            val = ""
            if h['type'] == 'likert':
                val = l_answers.get(h['id'], "-")
            elif h['type'] == 'continuous':
                val = c_answers.get(h['id'], "-")
            row.append(val)

        # 寫入這一列
        writer.writerow(row)

    return response
# ==========================================
# 10. 軟刪除掛號資料 (隱藏而不刪除)
# ==========================================
@user_passes_test(is_admin, login_url='/admin/login/')
def hide_appointment(request, appt_id):
    if request.method == 'POST':
        appt = get_object_or_404(Appointment, id=appt_id)
        appt.is_visible = False  # 標記為不顯示
        appt.save()
        messages.success(request, f"已刪除(隱藏) {appt.real_name} 的掛號資料。")
    return redirect('patient_data_sheet')