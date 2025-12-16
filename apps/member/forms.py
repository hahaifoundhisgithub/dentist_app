from django import forms
# ★ 關鍵：不要 import allauth 的 SignupForm，這會導致循環引用！

# 改成繼承 django 的 forms.Form 即可
class MemberSignupForm(forms.Form):
    full_name = forms.CharField(
        max_length=30,
        label='真實姓名',
        widget=forms.TextInput(attrs={
            'placeholder': '請輸入您的真實姓名', 
            'class': 'form-control',
        })
    )

    # Allauth 會呼叫這個 signup 方法
    def signup(self, request, user):
        user.first_name = self.cleaned_data['full_name']
        user.save()