# Notable Programming & Development Techniques

This document explains the key programming techniques and patterns used in this Django project.

---

## 1. Soft Delete Pattern (軟刪除模式)

### Implementation

**Location**: `apps/clinic/models.py` and `apps/clinic/views.py`

The project implements a **soft delete** pattern using a boolean flag instead of physically deleting records from the database.

### Key Components:

#### Model Field
```python
# apps/clinic/models.py (line 153)
class Appointment(models.Model):
    # ... other fields ...
    is_visible = models.BooleanField(default=True, verbose_name="是否顯示在總表")
```

#### Soft Delete Action
```python
# apps/clinic/views.py (lines 749-756)
@user_passes_test(is_admin, login_url='/accounts/login/')
def hide_appointment(request, appt_id):
    if request.method == 'POST':
        appt = get_object_or_404(Appointment, id=appt_id)
        appt.is_visible = False  # 標記為不顯示
        appt.save()
        messages.success(request, f"已刪除(隱藏) {appt.real_name} 的掛號資料。")
    return redirect('patient_data_sheet')
```

#### Query Filtering
```python
# apps/clinic/views.py (line 585, 712)
appointments = Appointment.objects.filter(is_visible=True).select_related('user')
```

### Benefits:
- **Data Preservation**: Records are never lost, allowing for data recovery
- **Audit Trail**: Historical data remains intact for analysis
- **Referential Integrity**: Related records (like DID sync) remain consistent
- **Reversible**: Can easily restore "deleted" records by setting `is_visible=True`

### Usage Pattern:
1. Default state: `is_visible=True` (visible)
2. "Delete" action: Set `is_visible=False` (hidden)
3. All queries filter by `is_visible=True` to exclude soft-deleted records
4. Data remains in database for backup/analysis purposes

---

## 2. Two-Section Survey in Single Form (單表單雙區段調查)

### Implementation

**Location**: `apps/clinic/forms.py` and `apps/clinic/templates/clinic/booking_habit_survey.html`

The survey form handles **two distinct question types** in a single Django form using dynamic field generation and custom attributes.

### Architecture:

#### Form Structure
```python
# apps/clinic/forms.py (lines 93-132)
class BookingHabitForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BookingHabitForm, self).__init__(*args, **kwargs)
        
        # --- Section 1: Likert Scale (李克特量表 1-7分) ---
        self.likert_habits = DentalHabit.objects.filter(is_active=True)
        for habit in self.likert_habits:
            field_name = f'habit_{habit.id}'
            self.fields[field_name] = forms.ChoiceField(
                label=f"{habit.name} ({habit.min_label} ~ {habit.max_label})",
                choices=[(i, str(i)) for i in range(1, 8)],  # 1-7分
                widget=forms.RadioSelect(attrs={'class': 'hidden peer'}),
                required=True,
            )
            self.fields[field_name].is_likert = True  # Custom attribute
        
        # --- Section 2: Continuous Data (連續資料數值輸入) ---
        self.continuous_habits = ContinuousHabit.objects.filter(is_active=True)
        for q in self.continuous_habits:
            field_name = f'chabit_{q.id}'
            self.fields[field_name] = forms.DecimalField(
                label=q.question + (f" (單位: {q.unit})" if q.unit else ""),
                widget=forms.NumberInput(attrs={...}),
                required=True,
            )
            self.fields[field_name].is_likert = False  # Custom attribute
            self.fields[field_name].unit = q.unit  # Store unit for display
```

### Key Techniques:

#### 1. **Dynamic Field Generation**
- Fields are created dynamically in `__init__` based on database records
- Allows admin to add/remove questions without code changes
- Uses naming convention: `habit_{id}` for Likert, `chabit_{id}` for continuous

#### 2. **Custom Field Attributes**
- `is_likert` flag distinguishes question types in templates
- `unit` attribute stores measurement unit for display
- Enables template-level conditional rendering

#### 3. **Unified Template Rendering**
```html
<!-- apps/clinic/templates/clinic/booking_habit_survey.html -->
{% for field in form %}
    {% if field.field.widget.input_type == 'radio' %}
        <!-- Render Likert scale as radio buttons -->
    {% else %}
        <!-- Render continuous data as number input -->
    {% endif %}
{% endfor %}
```

#### 4. **Separate Data Processing**
```python
# apps/clinic/views.py (lines 462-472)
for field_name, value in form.cleaned_data.items():
    if field_name.startswith('habit_'):
        # Process Likert responses → AppointmentHabitResponse
        h_id = int(field_name.split('_')[1])
        AppointmentHabitResponse.objects.create(
            appointment=appointment, habit_id=h_id, score=int(value)
        )
    elif field_name.startswith('chabit_'):
        # Process continuous responses → AppointmentContinuousResponse
        c_id = int(field_name.split('_')[1])
        AppointmentContinuousResponse.objects.create(
            appointment=appointment, question_id=c_id, value=value
        )
```

### Benefits:
- **Single Form Submission**: Both sections submitted together
- **Type Safety**: Different widgets and validation per section
- **Maintainability**: Admin can manage questions via Django admin
- **Flexible**: Easy to add more question types in the future
- **Clean Separation**: Different models for different data types

---

## 3. Many-to-Many with Through Model (中介模型多對多關係)

### Implementation

**Location**: `apps/clinic/models.py`

Uses Django's `through` parameter to store additional data in ManyToMany relationships.

### Example:
```python
# apps/clinic/models.py (lines 138-149)
class Appointment(models.Model):
    # Standard ManyToMany (no extra data)
    symptoms = models.ManyToManyField(Symptom, verbose_name="主訴問題")
    
    # ManyToMany with Through (stores score)
    habits = models.ManyToManyField(
        DentalHabit, 
        through='AppointmentHabitResponse',  # Custom intermediate model
        verbose_name="用牙習慣調查結果", 
        blank=True
    )
    
    # ManyToMany with Through (stores decimal value)
    continuous_data = models.ManyToManyField(
        ContinuousHabit,
        through='AppointmentContinuousResponse',  # Custom intermediate model
        verbose_name="連續資料調查結果",
        blank=True
    )

# Intermediate models store additional data
class AppointmentHabitResponse(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    habit = models.ForeignKey(DentalHabit, on_delete=models.CASCADE)
    score = models.IntegerField(verbose_name="評分(1-7)")  # Extra data!
    
    class Meta:
        unique_together = ('appointment', 'habit')  # Prevent duplicates
```

### Benefits:
- **Store Additional Data**: Can store scores, timestamps, or other metadata
- **Data Integrity**: `unique_together` prevents duplicate responses
- **Query Flexibility**: Can filter/order by intermediate model fields

---

## 4. Django Signals for Data Synchronization (信號同步機制)

### Implementation

**Location**: `apps/clinic/signals.py`

Automatically synchronizes `Appointment` data to a backup `DID` model using Django signals.

### Architecture:
```python
# apps/clinic/signals.py

@receiver(post_save, sender=Appointment)
def sync_appointment_on_save(sender, instance, created, **kwargs):
    """Auto-sync when Appointment is created/updated"""
    transaction.on_commit(lambda: sync_appointment_to_did(instance))

@receiver(m2m_changed, sender=Appointment.symptoms.through)
def sync_appointment_symptoms_changed(sender, instance, action, **kwargs):
    """Re-sync when ManyToMany relationships change"""
    if action in ('post_add', 'post_remove', 'post_clear'):
        transaction.on_commit(lambda: sync_appointment_to_did(instance))

@receiver(post_save, sender=AppointmentHabitResponse)
def sync_habit_response_changed(sender, instance, **kwargs):
    """Re-sync when survey responses change"""
    transaction.on_commit(lambda: sync_appointment_to_did(instance.appointment))
```

### Key Techniques:

#### 1. **Transaction Safety**
- Uses `transaction.on_commit()` to ensure sync happens after database commit
- Prevents race conditions with ManyToMany relationships

#### 2. **Comprehensive Coverage**
- Monitors `post_save`, `post_delete`, and `m2m_changed` signals
- Covers all data modification paths

#### 3. **Data Serialization**
- Converts ManyToMany relationships to JSON/text for backup storage
- Maintains data structure in flat format

### Benefits:
- **Automatic Backup**: No manual sync required
- **Data Consistency**: Always up-to-date backup
- **Separation of Concerns**: Main model vs. backup model
- **Analytics Ready**: DID model optimized for reporting

---

## 5. Session-Based Multi-Step Form (會話式多步驟表單)

### Implementation

**Location**: `apps/clinic/views.py` (booking flow)

Implements a multi-step booking process using Django sessions to persist data between steps.

### Flow:
1. **Step 1**: Select date/time → Store in session
2. **Step 2**: Patient info → Store in session
3. **Step 3**: Survey → Create final record

### Code Pattern:
```python
# Step 2: Store data in session
# apps/clinic/views.py (lines 387-394)
request.session['booking_data'] = {
    'date': date_str,
    'slot': slot_key,
    'real_name': form.cleaned_data['real_name'],
    'age': form.cleaned_data['age'],
    'national_id': nid,
    'symptoms_ids': [s.id for s in form.cleaned_data['symptoms']]
}
return redirect('booking_habit_survey')

# Step 3: Retrieve from session
# apps/clinic/views.py (lines 426-428)
booking_data = request.session.get('booking_data')
if not booking_data:
    return redirect('booking_select_time')

# After completion: Clear session
# apps/clinic/views.py (line 474)
del request.session['booking_data']
```

### Benefits:
- **User-Friendly**: Can navigate back/forward
- **No Database Writes**: Until final submission
- **State Management**: Maintains context across requests
- **Validation**: Each step validates independently

---

## 6. Query Optimization (查詢優化)

### Implementation

**Location**: `apps/clinic/views.py`

Uses Django ORM optimization techniques to reduce database queries.

### Techniques:

#### 1. **select_related()** (Foreign Key Optimization)
```python
# apps/clinic/views.py (line 585)
appointments = Appointment.objects.filter(is_visible=True).select_related('user')
```
- Reduces N+1 queries for ForeignKey relationships
- Joins related tables in single query

#### 2. **Prefetch Pattern** (ManyToMany Optimization)
```python
# Implicit prefetching in templates
# When accessing appt.symptoms.all(), Django batches queries
```

### Benefits:
- **Performance**: Fewer database round trips
- **Scalability**: Handles large datasets efficiently
- **Best Practice**: Follows Django ORM optimization guidelines

---

## 7. Dynamic Form Field Generation (動態表單欄位生成)

### Implementation

**Location**: `apps/clinic/forms.py`

Forms are generated dynamically based on database content, not hardcoded.

### Pattern:
```python
class BookingHabitForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Query database for active questions
        habits = DentalHabit.objects.filter(is_active=True)
        
        # Generate fields dynamically
        for habit in habits:
            self.fields[f'habit_{habit.id}'] = forms.ChoiceField(...)
```

### Benefits:
- **Admin-Driven**: Non-developers can add questions
- **Flexible**: No code changes needed for new questions
- **Maintainable**: Single source of truth (database)

---

## 8. Custom Model Managers & Filtering (自訂模型管理器)

### Pattern:
While not explicitly implemented, the codebase follows Django best practices:
- Filtering by `is_active=True` for soft-enabled records
- Filtering by `is_visible=True` for soft-deleted records
- Could be enhanced with custom managers for cleaner code

### Potential Enhancement:
```python
class VisibleAppointmentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_visible=True)

class Appointment(models.Model):
    objects = models.Manager()
    visible = VisibleAppointmentManager()
    
# Usage: Appointment.visible.all() instead of Appointment.objects.filter(is_visible=True)
```

---

## 9. Error Handling & User Feedback (錯誤處理)

### Implementation

**Location**: Throughout `apps/clinic/views.py`

### Patterns:

#### 1. **Try-Except Blocks**
```python
# apps/clinic/views.py (lines 481-484)
try:
    # Create appointment
except Exception as e:
    print(f"Error: {e}")
    messages.error(request, "掛號失敗，請聯繫櫃台")
    return redirect('booking_select_time')
```

#### 2. **Django Messages Framework**
```python
messages.success(request, f"已刪除(隱藏) {appt.real_name} 的掛號資料。")
messages.error(request, "您已經掛號，無須再次預約掛號")
```

### Benefits:
- **User Experience**: Clear feedback on actions
- **Debugging**: Error logging for developers
- **Graceful Degradation**: App continues functioning on errors

---

## 10. Model Design Patterns (模型設計模式)

### Notable Patterns:

#### 1. **Choice Fields with Display Methods**
```python
SLOT_CHOICES = [
    ('morning', '早診'),
    ('afternoon', '午診'),
    ('evening', '晚診'),
]
# Usage: appointment.get_time_slot_display() → "早診"
```

#### 2. **Unique Constraints**
```python
class Meta:
    unique_together = ('appointment', 'habit')  # Prevent duplicate responses
    unique_together = ('date', 'time_slot')  # One state per time slot
```

#### 3. **Default Values & Auto-Timestamps**
```python
is_visible = models.BooleanField(default=True)
created_at = models.DateTimeField(auto_now_add=True)
synced_at = models.DateTimeField(auto_now=True)
```

---

## Summary

This Django project demonstrates several advanced patterns:

1. ✅ **Soft Delete** - Data preservation with boolean flags
2. ✅ **Two-Section Survey** - Single form handling multiple question types
3. ✅ **ManyToMany with Through** - Storing additional relationship data
4. ✅ **Django Signals** - Automatic data synchronization
5. ✅ **Session Management** - Multi-step form workflows
6. ✅ **Query Optimization** - select_related, efficient filtering
7. ✅ **Dynamic Forms** - Database-driven form generation
8. ✅ **Error Handling** - User-friendly error messages
9. ✅ **Model Best Practices** - Choices, constraints, defaults

These techniques create a maintainable, scalable, and user-friendly application.

