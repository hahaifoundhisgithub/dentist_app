from django import forms
from django.core.validators import RegexValidator
from .models import (
    Dentist, ClinicHours, Symptom, ClinicInfo, 
    DentalHabit, ContinuousHabit, Appointment
)

# ==========================================
# Part 1: 後台管理用表單 (補回這些原本的表單)
# ==========================================

class DentistForm(forms.ModelForm):
    class Meta:
        model = Dentist
        fields = '__all__'

class ClinicHoursForm(forms.ModelForm):
    class Meta:
        model = ClinicHours
        fields = ['morning', 'morning_limit', 'afternoon', 'afternoon_limit', 'evening', 'evening_limit']

class ClinicGlobalTimeForm(forms.Form):
    morning_time = forms.CharField(label="早診時間", max_length=50)
    afternoon_time = forms.CharField(label="午診時間", max_length=50)
    evening_time = forms.CharField(label="晚診時間", max_length=50)

class SymptomForm(forms.ModelForm):
    class Meta:
        model = Symptom
        fields = '__all__'

class ClinicInfoForm(forms.ModelForm):
    class Meta:
        model = ClinicInfo
        fields = '__all__'

class DentalHabitForm(forms.ModelForm):
    class Meta:
        model = DentalHabit
        fields = '__all__'

class ContinuousHabitForm(forms.ModelForm):
    class Meta:
        model = ContinuousHabit
        fields = '__all__'

# ==========================================
# Part 2: 前台預約用表單 (這是我們新加的)
# ==========================================

# 第一頁：基本資料與症狀表單
class BookingPatientForm(forms.Form):
    real_name = forms.CharField(
        label='真實姓名',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入真實姓名'})
    )
    
    age = forms.IntegerField(
        label='年齡',
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': '請輸入年齡 (例如: 25)'
        }),
        error_messages={'required': '請輸入年齡', 'invalid': '請輸入有效的數字'}
    )
    national_id = forms.CharField(
        label='身分證字號',
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '首字大寫英文+9碼數字',
            'style': 'text-transform: uppercase;'
        }),
        validators=[
            RegexValidator(
                regex=r'^[A-Z][0-9]{9}$',
                message='身分證格式錯誤 (需首字大寫英文+9碼數字)'
            )
        ]
    )

    # 動態載入啟用中的症狀
    symptoms = forms.ModelMultipleChoiceField(
        queryset=Symptom.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        label='管理看診問題 (請勾選)',
        required=False
    )

# 第二頁：完整版習慣調查表單 (包含李克特與連續資料)
class BookingHabitForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BookingHabitForm, self).__init__(*args, **kwargs)
        
        # --- 部分 1: 李克特量表 (1-7分) ---
        self.likert_habits = DentalHabit.objects.filter(is_active=True)
        for habit in self.likert_habits:
            field_name = f'habit_{habit.id}'
            self.fields[field_name] = forms.ChoiceField(
                label=f"{habit.name} ({habit.min_label} ~ {habit.max_label})",
                choices=[(i, str(i)) for i in range(1, 8)], # 1-7分
                widget=forms.RadioSelect(attrs={'class': 'hidden peer'}), # 用於前端客製化樣式
                required=True,
                error_messages={'required': '此題尚未作答'}
            )
            # 掛載額外屬性供 Template 使用
            self.fields[field_name].is_likert = True 
            
        # --- 部分 2: 連續資料 (數值輸入) ---
        self.continuous_habits = ContinuousHabit.objects.filter(is_active=True)
        for q in self.continuous_habits:
            field_name = f'chabit_{q.id}'
            
            # 組合標籤文字 (含單位)
            label_text = q.question
            if q.unit:
                label_text += f" (單位: {q.unit})"
            
            self.fields[field_name] = forms.DecimalField(
                label=label_text,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control w-full border border-gray-300 rounded-md p-2 focus:ring-brand focus:border-brand',
                    'placeholder': '請輸入數字',
                    'step': '0.1'
                }),
                required=True,
                error_messages={'required': '請輸入數值'}
            )
            self.fields[field_name].is_likert = False
            self.fields[field_name].unit = q.unit