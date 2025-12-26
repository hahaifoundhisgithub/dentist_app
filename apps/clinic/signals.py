"""
Django Signals for DID Model Synchronization
自動同步 Appointment 資料到 DID 模型
"""
import json
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.db import transaction
from .models import Appointment, DID, AppointmentHabitResponse, AppointmentContinuousResponse


def sync_appointment_to_did(appointment):
    """
    將 Appointment 資料同步到 DID 模型
    """
    # 1. 收集症狀文字（多對多關係）
    symptoms_list = list(appointment.symptoms.values_list('name', flat=True))
    symptoms_text = "、".join(symptoms_list) if symptoms_list else ""
    
    # 2. 收集習慣調查結果（李克特量表）
    habits_dict = {}
    habit_responses = AppointmentHabitResponse.objects.filter(appointment=appointment)
    for response in habit_responses:
        habits_dict[str(response.habit_id)] = response.score
    habits_data = json.dumps(habits_dict, ensure_ascii=False)
    
    # 3. 收集連續資料調查結果
    continuous_dict = {}
    continuous_responses = AppointmentContinuousResponse.objects.filter(appointment=appointment)
    for response in continuous_responses:
        continuous_dict[str(response.question_id)] = str(response.value)
    continuous_data = json.dumps(continuous_dict, ensure_ascii=False)
    
    # 4. 取得使用者資訊
    user_username = appointment.user.username if appointment.user else ""
    
    # 5. 建立或更新 DID 記錄
    did, created = DID.objects.update_or_create(
        appointment_id=appointment.id,
        defaults={
            'user_id': appointment.user.id,
            'user_username': user_username,
            'date': appointment.date,
            'time_slot': appointment.time_slot,
            'real_name': appointment.real_name,
            'age': appointment.age,
            'patient_id': appointment.patient_id,
            'symptoms_text': symptoms_text,
            'habits_data': habits_data,
            'continuous_data': continuous_data,
            'registration_number': appointment.registration_number,
            'created_at': appointment.created_at,
            'is_visible': appointment.is_visible,
        }
    )
    
    return did


@receiver(post_save, sender=Appointment)
def sync_appointment_on_save(sender, instance, created, **kwargs):
    """
    當 Appointment 被建立或更新時，自動同步到 DID
    """
    # 使用 transaction.on_commit 確保在事務提交後執行
    # 這樣可以確保 ManyToMany 關係已經保存
    transaction.on_commit(lambda: sync_appointment_to_did(instance))


@receiver(post_delete, sender=Appointment)
def sync_appointment_on_delete(sender, instance, **kwargs):
    """
    當 Appointment 被刪除時，也刪除對應的 DID 記錄
    """
    try:
        DID.objects.filter(appointment_id=instance.id).delete()
    except Exception as e:
        # 記錄錯誤但不中斷刪除流程
        print(f"Error deleting DID record for appointment {instance.id}: {e}")


@receiver(m2m_changed, sender=Appointment.symptoms.through)
def sync_appointment_symptoms_changed(sender, instance, action, **kwargs):
    """
    當 Appointment 的症狀（ManyToMany）關係變更時，重新同步
    """
    if action in ('post_add', 'post_remove', 'post_clear'):
        transaction.on_commit(lambda: sync_appointment_to_did(instance))


@receiver(post_save, sender=AppointmentHabitResponse)
def sync_habit_response_changed(sender, instance, **kwargs):
    """
    當習慣調查回應被建立或更新時，重新同步對應的 Appointment
    """
    transaction.on_commit(lambda: sync_appointment_to_did(instance.appointment))


@receiver(post_delete, sender=AppointmentHabitResponse)
def sync_habit_response_deleted(sender, instance, **kwargs):
    """
    當習慣調查回應被刪除時，重新同步對應的 Appointment
    """
    transaction.on_commit(lambda: sync_appointment_to_did(instance.appointment))


@receiver(post_save, sender=AppointmentContinuousResponse)
def sync_continuous_response_changed(sender, instance, **kwargs):
    """
    當連續資料回應被建立或更新時，重新同步對應的 Appointment
    """
    transaction.on_commit(lambda: sync_appointment_to_did(instance.appointment))


@receiver(post_delete, sender=AppointmentContinuousResponse)
def sync_continuous_response_deleted(sender, instance, **kwargs):
    """
    當連續資料回應被刪除時，重新同步對應的 Appointment
    """
    transaction.on_commit(lambda: sync_appointment_to_did(instance.appointment))

