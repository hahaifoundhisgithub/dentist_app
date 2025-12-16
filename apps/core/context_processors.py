from apps.clinic.models import ClinicInfo

def site_info(request):
    # 取得第一筆診所資訊，如果沒有則回傳 None
    info = ClinicInfo.objects.first()
    return {'site_clinic_info': info}