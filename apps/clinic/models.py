from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# 1. 牙醫模型
class Dentist(models.Model):
    name = models.CharField(max_length=100, verbose_name="牙醫姓名")
    description = models.TextField(verbose_name="牙醫描述", help_text="請輸入醫生的詳細介紹")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "牙醫資料"
        verbose_name_plural = "牙醫資料"

# 2. 症狀/看診問題模型
class Symptom(models.Model):
    name = models.CharField(max_length=50, verbose_name="症狀名稱")
    is_active = models.BooleanField(default=True, verbose_name="啟用中")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "看診問題設定"
        verbose_name_plural = "看診問題設定"

# 3. 營業時間模型
class ClinicHours(models.Model):
    DAY_CHOICES = [
        (0, '星期一'), (1, '星期二'), (2, '星期三'), (3, '星期四'),
        (4, '星期五'), (5, '星期六'), (6, '星期日'),
    ]

    day_of_week = models.IntegerField(choices=DAY_CHOICES, unique=True, verbose_name="星期")
    
    # 開關
    morning = models.BooleanField(default=True, verbose_name="早診開關")
    afternoon = models.BooleanField(default=True, verbose_name="午診開關")
    evening = models.BooleanField(default=True, verbose_name="晚診開關")

    # 人數上限
    morning_limit = models.PositiveIntegerField(default=10, verbose_name="早診上限")
    afternoon_limit = models.PositiveIntegerField(default=10, verbose_name="午診上限")
    evening_limit = models.PositiveIntegerField(default=10, verbose_name="晚診上限")

    # 時間顯示字串
    morning_time = models.CharField(max_length=50, default="09:00-12:00", verbose_name="早診時間")
    afternoon_time = models.CharField(max_length=50, default="14:00-17:30", verbose_name="午診時間")
    evening_time = models.CharField(max_length=50, default="18:30-21:00", verbose_name="晚診時間")

    def __str__(self):
        return self.get_day_of_week_display()

    class Meta:
        verbose_name = "診所營業時間與上限"
        verbose_name_plural = "診所營業時間與上限"
        ordering = ['day_of_week']

# 4. 每日診次叫號狀態
class DailyClinicState(models.Model):
    date = models.DateField(default=timezone.now, verbose_name="日期")
    time_slot = models.CharField(max_length=20, verbose_name="時段")
    current_number = models.PositiveIntegerField(default=0, verbose_name="目前叫號")
    
    class Meta:
        verbose_name = "每日診次叫號狀態"
        verbose_name_plural = "每日診次叫號狀態"
        unique_together = ('date', 'time_slot')

    def __str__(self):
        return f"{self.date} {self.time_slot} - 目前叫號: {self.current_number}"

# 5. 診所基本資訊
class ClinicInfo(models.Model):
    address = models.CharField(max_length=200, verbose_name="診所地址", default="請更新診所地址")
    phone = models.CharField(max_length=50, verbose_name="聯絡電話", default="02-1234-5678")
    slogan_title = models.CharField(max_length=100, verbose_name="首頁大標題", default="微笑，從這裡開始")
    slogan_content = models.TextField(verbose_name="首頁副標題", default="我們提供最專業的牙科服務，守護您與家人的口腔健康。線上預約，輕鬆看診。")
    
    class Meta:
        verbose_name = "診所基本資訊"
        verbose_name_plural = "診所基本資訊"

    def __str__(self):
        return "診所資訊設定"

# 6. 用牙習慣調查題目 (李克特量表)
class DentalHabit(models.Model):
    name = models.CharField(max_length=100, verbose_name="習慣調查題目")
    min_label = models.CharField(max_length=50, verbose_name="選項1代表", default="非常不同意")
    max_label = models.CharField(max_length=50, verbose_name="選項7代表", default="非常同意")
    is_active = models.BooleanField(default=True, verbose_name="啟用中")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "用牙習慣設定"
        verbose_name_plural = "用牙習慣設定"

# 7. 連續資料問題 (數值輸入)
class ContinuousHabit(models.Model):
    question = models.CharField(max_length=100, verbose_name="問題內容")
    unit = models.CharField(max_length=20, verbose_name="單位", blank=True, null=True, help_text="例如：次/天")
    is_active = models.BooleanField(default=True, verbose_name="啟用中")

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "連續資料問題設定"
        verbose_name_plural = "連續資料問題設定"

# 8. 掛號紀錄模型 (Updated)
class Appointment(models.Model):
    SLOT_CHOICES = [
        ('morning', '早診'),
        ('afternoon', '午診'),
        ('evening', '晚診'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="掛號會員")
    date = models.DateField(verbose_name="看診日期")
    time_slot = models.CharField(max_length=20, choices=SLOT_CHOICES, verbose_name="時段")
    
    # ★ 新增欄位：符合您的第一頁需求
    real_name = models.CharField(max_length=50, verbose_name="真實姓名", default="")
    age = models.PositiveIntegerField(verbose_name="年齡", default=0)
    patient_id = models.CharField(max_length=10, verbose_name="身分證字號")
    
    symptoms = models.ManyToManyField(Symptom, verbose_name="主訴問題")
    
    # 習慣調查關聯
    habits = models.ManyToManyField(
        DentalHabit, 
        through='AppointmentHabitResponse',
        verbose_name="用牙習慣調查結果", 
        blank=True
    )
    continuous_data = models.ManyToManyField(
        ContinuousHabit,
        through='AppointmentContinuousResponse',
        verbose_name="連續資料調查結果",
        blank=True
    )
    
    registration_number = models.PositiveIntegerField(verbose_name="掛號號碼")
    created_at = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True, verbose_name="是否顯示在總表")
    class Meta:
        verbose_name = "掛號紀錄"
        verbose_name_plural = "掛號紀錄"

    def __str__(self):
        return f"{self.date} {self.get_time_slot_display()} - {self.real_name} (#{self.registration_number})"

# 9. 習慣調查回應 (中間表：李克特)
class AppointmentHabitResponse(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    habit = models.ForeignKey(DentalHabit, on_delete=models.CASCADE)
    score = models.IntegerField(verbose_name="評分(1-7)")

    class Meta:
        unique_together = ('appointment', 'habit')

# 10. 連續資料回應 (中間表：數值)
class AppointmentContinuousResponse(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    question = models.ForeignKey(ContinuousHabit, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=10, decimal_places=1, verbose_name="數值")

    class Meta:
        unique_together = ('appointment', 'question')

# 11. DID 看診資料總表 (完全同步於 Appointment，不顯示給使用者)
class DID(models.Model):
    """
    看診資料總表備份資料庫
    完全同步於 Appointment 模型，用於內部資料備份與分析
    不顯示在管理介面中
    """
    SLOT_CHOICES = [
        ('morning', '早診'),
        ('afternoon', '午診'),
        ('evening', '晚診'),
    ]
    
    # 對應原始 Appointment 的 ID，用於追蹤
    appointment_id = models.IntegerField(verbose_name="原始掛號ID", unique=True, db_index=True)
    
    # 基本資料欄位（與 Appointment 完全一致）
    user_id = models.IntegerField(verbose_name="會員ID")
    user_username = models.CharField(max_length=150, verbose_name="會員帳號", blank=True)
    date = models.DateField(verbose_name="看診日期")
    time_slot = models.CharField(max_length=20, choices=SLOT_CHOICES, verbose_name="時段")
    real_name = models.CharField(max_length=50, verbose_name="真實姓名", default="")
    age = models.PositiveIntegerField(verbose_name="年齡", default=0)
    patient_id = models.CharField(max_length=10, verbose_name="身分證字號")
    
    # 多對多關係以文字形式儲存（症狀、習慣調查結果）
    symptoms_text = models.TextField(verbose_name="主訴問題", blank=True, help_text="以逗號分隔的症狀名稱")
    
    # 習慣調查結果（李克特量表）- JSON 格式儲存
    habits_data = models.TextField(verbose_name="用牙習慣調查結果", blank=True, help_text="JSON 格式：{habit_id: score}")
    
    # 連續資料調查結果 - JSON 格式儲存
    continuous_data = models.TextField(verbose_name="連續資料調查結果", blank=True, help_text="JSON 格式：{question_id: value}")
    
    registration_number = models.PositiveIntegerField(verbose_name="掛號號碼")
    created_at = models.DateTimeField(verbose_name="建立時間")
    is_visible = models.BooleanField(default=True, verbose_name="是否顯示在總表")
    
    # 同步時間戳記
    synced_at = models.DateTimeField(auto_now=True, verbose_name="最後同步時間")
    
    class Meta:
        verbose_name = "DID 看診資料總表"
        verbose_name_plural = "DID 看診資料總表"
        # 不在 admin 中顯示
        managed = True
        db_table = 'clinic_did'
        indexes = [
            models.Index(fields=['appointment_id']),
            models.Index(fields=['date', 'time_slot']),
            models.Index(fields=['patient_id']),
        ]
    
    def __str__(self):
        return f"DID-{self.appointment_id}: {self.date} {self.get_time_slot_display()} - {self.real_name}"