# Advanced & Difficult Programming Techniques

This document explains all the **difficult and advanced** programming techniques used in this Django project, with detailed code examples and explanations.

---

## 🔴 **CRITICAL DIFFICULTY LEVEL**

### 1. **Transaction.on_commit() for Signal Synchronization**

**Difficulty**: ⭐⭐⭐⭐⭐ (Very Advanced)

**Location**: `apps/clinic/signals.py`

**Problem**: Django signals fire during database transactions, but ManyToMany relationships may not be fully committed yet. This causes race conditions and incomplete data synchronization.

**Solution**: Use `transaction.on_commit()` to defer signal execution until after the transaction commits.

```python
from django.db import transaction

@receiver(post_save, sender=Appointment)
def sync_appointment_on_save(sender, instance, created, **kwargs):
    """
    Critical: Use transaction.on_commit to ensure ManyToMany relationships
    are fully saved before synchronization
    """
    # Lambda function is deferred until transaction commits
    transaction.on_commit(lambda: sync_appointment_to_did(instance))

@receiver(m2m_changed, sender=Appointment.symptoms.through)
def sync_appointment_symptoms_changed(sender, instance, action, **kwargs):
    """
    ManyToMany changes require special handling - must wait for commit
    """
    if action in ('post_add', 'post_remove', 'post_clear'):
        transaction.on_commit(lambda: sync_appointment_to_did(instance))
```

**Why This is Difficult**:
- Requires deep understanding of Django's transaction lifecycle
- Must know when to use `on_commit` vs direct execution
- Lambda closures must capture correct instance references
- Debugging transaction timing issues is extremely challenging

**Key Insight**: `transaction.on_commit()` ensures the callback runs **after** the database transaction successfully commits, guaranteeing all related data (including ManyToMany) is persisted.

---

### 2. **Multiple ModelFormSets with Prefixes in Single View**

**Difficulty**: ⭐⭐⭐⭐ (Advanced)

**Location**: `apps/clinic/views.py` (lines 232-255)

**Problem**: Handling two different ModelFormSets in the same view without field name conflicts.

**Solution**: Use `prefix` parameter to namespace form fields.

```python
@user_passes_test(is_admin, login_url='/accounts/login/')
def update_habits(request):
    # Create two separate formsets for different models
    LikertFormSet = modelformset_factory(
        DentalHabit, 
        form=DentalHabitForm, 
        extra=1, 
        can_delete=True
    )
    ContinuousFormSet = modelformset_factory(
        ContinuousHabit, 
        form=ContinuousHabitForm, 
        extra=1, 
        can_delete=True
    )

    if request.method == 'POST':
        # CRITICAL: Use different prefixes to avoid field name collisions
        likert_formset = LikertFormSet(
            request.POST, 
            prefix='likert'  # Fields become: likert-0-name, likert-1-name, etc.
        )
        continuous_formset = ContinuousFormSet(
            request.POST, 
            prefix='continuous'  # Fields become: continuous-0-question, etc.
        )
        
        # Both must be valid before saving
        if likert_formset.is_valid() and continuous_formset.is_valid():
            likert_formset.save()
            continuous_formset.save()
            messages.success(request, '所有習慣調查題目已更新成功！')
            return redirect('update_habits')
    else:
        likert_formset = LikertFormSet(
            queryset=DentalHabit.objects.all(), 
            prefix='likert'
        )
        continuous_formset = ContinuousFormSet(
            queryset=ContinuousHabit.objects.all(), 
            prefix='continuous'
        )
```

**Why This is Difficult**:
- Must understand Django's formset prefix mechanism
- Field name collisions can cause silent validation failures
- Both formsets must be validated together
- Template rendering requires careful handling of both formsets

**Key Insight**: Prefixes create namespaced field names like `likert-0-name` and `continuous-0-question`, preventing conflicts when both formsets submit to the same view.

---

### 3. **Dynamic Form Field Generation with Custom Attributes**

**Difficulty**: ⭐⭐⭐⭐⭐ (Very Advanced)

**Location**: `apps/clinic/forms.py` (lines 93-132)

**Problem**: Creating form fields dynamically at runtime based on database content, with different field types and custom metadata.

**Solution**: Override `__init__()` to generate fields and attach custom attributes.

```python
class BookingHabitForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BookingHabitForm, self).__init__(*args, **kwargs)
        
        # Section 1: Dynamically generate Likert scale fields
        self.likert_habits = DentalHabit.objects.filter(is_active=True)
        for habit in self.likert_habits:
            field_name = f'habit_{habit.id}'  # Dynamic naming: habit_1, habit_2, etc.
            
            # Create ChoiceField with radio buttons
            self.fields[field_name] = forms.ChoiceField(
                label=f"{habit.name} ({habit.min_label} ~ {habit.max_label})",
                choices=[(i, str(i)) for i in range(1, 8)],
                widget=forms.RadioSelect(attrs={'class': 'hidden peer'}),
                required=True,
                error_messages={'required': '此題尚未作答'}
            )
            # CRITICAL: Attach custom attribute to field object
            self.fields[field_name].is_likert = True  # Custom metadata!
            
        # Section 2: Dynamically generate continuous data fields
        self.continuous_habits = ContinuousHabit.objects.filter(is_active=True)
        for q in self.continuous_habits:
            field_name = f'chabit_{q.id}'  # Different prefix: chabit_1, chabit_2, etc.
            
            # Build label with unit information
            label_text = q.question
            if q.unit:
                label_text += f" (單位: {q.unit})"
            
            # Create DecimalField for numeric input
            self.fields[field_name] = forms.DecimalField(
                label=label_text,
                widget=forms.NumberInput(attrs={...}),
                required=True,
            )
            # CRITICAL: Attach multiple custom attributes
            self.fields[field_name].is_likert = False
            self.fields[field_name].unit = q.unit  # Store unit for template use
```

**Why This is Difficult**:
- Form fields are created at runtime, not at class definition
- Must understand Django's form field lifecycle
- Custom attributes must be attached correctly for template access
- Field naming conventions must be consistent for processing
- Template must handle different field types dynamically

**Processing in View**:
```python
# apps/clinic/views.py (lines 462-472)
for field_name, value in form.cleaned_data.items():
    if field_name.startswith('habit_'):  # Likert fields
        h_id = int(field_name.split('_')[1])  # Extract ID from name
        AppointmentHabitResponse.objects.create(
            appointment=appointment, 
            habit_id=h_id, 
            score=int(value)
        )
    elif field_name.startswith('chabit_'):  # Continuous fields
        c_id = int(field_name.split('_')[1])  # Extract ID from name
        AppointmentContinuousResponse.objects.create(
            appointment=appointment, 
            question_id=c_id, 
            value=value
        )
```

**Key Insight**: Dynamic field generation allows admin-driven form configuration without code changes. Custom attributes enable template-level differentiation.

---

## 🟠 **HIGH DIFFICULTY LEVEL**

### 4. **Complex Time Parsing with Multiple Delimiters**

**Difficulty**: ⭐⭐⭐⭐ (Advanced)

**Location**: `apps/clinic/views.py` (lines 50-64, 271-281, 519-532)

**Problem**: Parse time strings with various formats (`09:00-12:00`, `09:00~12:00`, `09：00-12：00`) and handle edge cases.

**Solution**: Robust string cleaning and multiple delimiter support.

```python
def check_time(time_str):
    if not time_str: 
        return False
    try:
        # Handle full-width colon (全形冒號) and spaces
        clean_str = time_str.replace(" ", "").replace("：", ":")
        
        # Support multiple delimiters: '-' and '~'
        if '-' in clean_str:
            start_str, end_str = clean_str.split('-')
        elif '~' in clean_str:
            start_str, end_str = clean_str.split('~')
        else:
            return False
        
        # Parse time objects
        start_t = datetime.strptime(start_str, "%H:%M").time()
        end_t = datetime.strptime(end_str, "%H:%M").time()
        
        # Check if current time is within range
        return start_t <= current_time <= end_t
    except Exception:
        return False  # Fail gracefully on any parsing error
```

**Why This is Difficult**:
- Must handle multiple input formats
- Full-width vs half-width character issues
- Timezone-aware vs naive datetime handling
- Edge cases (empty strings, malformed input)
- Graceful error handling

**Key Insight**: Defensive programming with multiple fallbacks ensures robust time parsing across different input formats.

---

### 5. **In-Memory Sorting with Custom Key Functions**

**Difficulty**: ⭐⭐⭐⭐ (Advanced)

**Location**: `apps/clinic/views.py` (lines 619-656)

**Problem**: Sort complex data structures with mixed types (dates, strings, numbers, empty values) by user-selected columns.

**Solution**: Custom key function with type handling and reverse logic.

```python
# Complex sorting function
def sort_helper(row):
    val = None
    
    # A. Fixed column sorting (simple cases)
    if sort_by == 'date': 
        return row['date']
    if sort_by == 'time': 
        return row['time']
    if sort_by == 'pid': 
        return row['pid']
    if sort_by == 'name': 
        return row['name']
    if sort_by == 'age': 
        return row['age']
    
    # B. Dynamic column sorting (complex case)
    if sort_by.startswith('dyn_'):
        try:
            idx = int(sort_by.split('_')[1])  # Extract index: dyn_0 → 0
            val = row['answers'][idx]  # Get value from answers list
            
            # Handle empty values ("-") for numeric sorting
            if val == "-": 
                return -1  # Treat empty as minimum value
            
            return float(val)  # Convert to float for numeric sorting
        except:
            return -1  # Error case: treat as minimum
    
    return row['date']  # Default fallback

# Determine sort direction
reverse = False
if sort_by == 'date_desc':
    key_func = lambda x: x['date']
    reverse = True
else:
    key_func = sort_helper

# Execute sort
data_rows.sort(key=key_func, reverse=reverse)
```

**Why This is Difficult**:
- Mixed data types (dates, strings, numbers)
- Empty value handling ("-" must sort correctly)
- Dynamic column indexing
- Type conversion with error handling
- Reverse sort logic

**Key Insight**: Python's `sort()` with custom key functions provides flexible sorting, but requires careful type handling for edge cases.

---

### 6. **ManyToMany with Through Models (Intermediate Tables)**

**Difficulty**: ⭐⭐⭐⭐ (Advanced)

**Location**: `apps/clinic/models.py` (lines 138-177)

**Problem**: Store additional data in ManyToMany relationships (e.g., scores, timestamps).

**Solution**: Use `through` parameter to specify custom intermediate model.

```python
class Appointment(models.Model):
    # Standard ManyToMany (no extra data)
    symptoms = models.ManyToManyField(Symptom, verbose_name="主訴問題")
    
    # ManyToMany with Through (stores score 1-7)
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

# Intermediate model stores additional data
class AppointmentHabitResponse(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    habit = models.ForeignKey(DentalHabit, on_delete=models.CASCADE)
    score = models.IntegerField(verbose_name="評分(1-7)")  # Extra data!
    
    class Meta:
        unique_together = ('appointment', 'habit')  # Prevent duplicate responses
```

**Why This is Difficult**:
- Cannot use `.add()` or `.set()` directly - must create intermediate objects
- Must understand relationship direction
- Query patterns change (need to access through intermediate model)
- Unique constraints prevent duplicate relationships

**Usage Pattern**:
```python
# Cannot do: appointment.habits.add(habit)  # ❌ Doesn't work with through

# Must do:
AppointmentHabitResponse.objects.create(
    appointment=appointment,
    habit=habit,
    score=5  # Store additional data
)
```

**Key Insight**: Through models enable storing relationship metadata, but require manual object creation instead of direct ManyToMany methods.

---

### 7. **Session-Based Multi-Step Form with State Management**

**Difficulty**: ⭐⭐⭐ (Moderate-Advanced)

**Location**: `apps/clinic/views.py` (lines 361-491)

**Problem**: Maintain form data across multiple HTTP requests without database writes until final submission.

**Solution**: Django sessions to store intermediate data.

```python
# Step 1: Store data in session
@login_required
def booking_patient_info(request):
    if request.method == 'POST':
        form = BookingPatientForm(request.POST)
        if form.is_valid():
            # Store in session (not database yet)
            request.session['booking_data'] = {
                'date': date_str,
                'slot': slot_key,
                'real_name': form.cleaned_data['real_name'],
                'age': form.cleaned_data['age'],
                'national_id': nid,
                'symptoms_ids': [s.id for s in form.cleaned_data['symptoms']]
            }
            return redirect('booking_habit_survey')  # Next step

# Step 2: Retrieve from session
@login_required
def booking_habit_survey(request):
    booking_data = request.session.get('booking_data')
    if not booking_data:
        return redirect('booking_select_time')  # Validation: must have session data
    
    if request.method == 'POST':
        form = BookingHabitForm(request.POST)
        if form.is_valid():
            # Now create database record
            appointment = Appointment.objects.create(...)
            
            # CRITICAL: Clear session after successful creation
            del request.session['booking_data']
            return render(request, 'clinic/booking_success.html', {...})
```

**Why This is Difficult**:
- Session data must be validated at each step
- Must handle session expiration
- Date serialization (dates become strings in sessions)
- Cleanup on success/failure
- Back navigation requires session restoration

**Date Serialization Issue**:
```python
# Session stores dates as strings: "2025-12-20"
date_str = booking_data['date']

# Must convert back to date object
date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
appointment = Appointment.objects.create(date=date_obj, ...)
```

**Key Insight**: Sessions provide stateless multi-step forms, but require careful serialization/deserialization and cleanup.

---

### 8. **Complex Data Aggregation and Dictionary Building**

**Difficulty**: ⭐⭐⭐⭐ (Advanced)

**Location**: `apps/clinic/views.py` (lines 588-617, 729-740)

**Problem**: Efficiently aggregate related data from multiple queries into structured format.

**Solution**: Pre-build dictionaries for O(1) lookup instead of repeated queries.

```python
# INEFFICIENT (N+1 queries):
for appt in appointments:
    symptoms = appt.symptoms.all()  # Query per appointment
    for response in AppointmentHabitResponse.objects.filter(appointment=appt):
        # Another query per appointment
        pass

# EFFICIENT (Batch queries):
appointments = Appointment.objects.filter(is_visible=True).select_related('user')

data_rows = []
for appt in appointments:
    # Build lookup dictionaries once
    l_answers = {
        r.habit_id: r.score 
        for r in AppointmentHabitResponse.objects.filter(appointment=appt)
    }
    c_answers = {
        r.question_id: r.value 
        for r in AppointmentContinuousResponse.objects.filter(appointment=appt)
    }
    
    # Use dictionaries for O(1) lookup
    answers_list = []
    for h in headers:
        val = "-"
        if h['type'] == 'likert':
            val = l_answers.get(h['id'], "-")  # Fast dictionary lookup
        elif h['type'] == 'continuous':
            val = c_answers.get(h['id'], "-")
        answers_list.append(val)
```

**Why This is Difficult**:
- Must understand query optimization
- Dictionary comprehension for data transformation
- O(1) vs O(n) lookup performance
- Handling missing keys gracefully

**Key Insight**: Pre-aggregating data into dictionaries eliminates N+1 query problems and enables fast lookups.

---

### 9. **CSV Export with BOM for Excel Compatibility**

**Difficulty**: ⭐⭐⭐ (Moderate-Advanced)

**Location**: `apps/clinic/views.py` (lines 675-745)

**Problem**: Excel opens UTF-8 CSV files with Chinese characters as garbled text.

**Solution**: Add UTF-8 BOM (Byte Order Mark) to CSV file.

```python
import csv
import codecs
from django.http import HttpResponse

@user_passes_test(is_admin, login_url='/accounts/login/')
def export_patient_csv(request):
    # 1. Create HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    
    # 2. Set filename with timestamp to avoid conflicts
    filename = f"patient_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # 3. CRITICAL: Write BOM for Excel UTF-8 compatibility
    response.write(codecs.BOM_UTF8)  # Excel recognizes UTF-8 with BOM
    
    writer = csv.writer(response)
    
    # 4. Write headers
    csv_headers = ['看診日期', '時段', '身分證字號', '姓名', '年齡', '主訴問題']
    # ... add dynamic headers ...
    writer.writerow(csv_headers)
    
    # 5. Write data rows
    for appt in appointments:
        row = [
            appt.date.strftime('%Y/%m/%d'),
            appt.get_time_slot_display(),
            # ... more fields ...
        ]
        writer.writerow(row)
    
    return response
```

**Why This is Difficult**:
- BOM is invisible but critical for Excel
- Must understand character encoding
- File download headers require correct syntax
- Dynamic column generation

**Key Insight**: `codecs.BOM_UTF8` tells Excel the file is UTF-8 encoded, preventing Chinese character corruption.

---

### 10. **Regex Validator with Custom Error Messages**

**Difficulty**: ⭐⭐⭐ (Moderate)

**Location**: `apps/clinic/forms.py` (lines 68-81)

**Problem**: Validate Taiwan ID format (1 uppercase letter + 9 digits) with user-friendly error messages.

**Solution**: Django's `RegexValidator` with custom regex pattern.

```python
from django.core.validators import RegexValidator

class BookingPatientForm(forms.Form):
    national_id = forms.CharField(
        label='身分證字號',
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '首字大寫英文+9碼數字',
            'style': 'text-transform: uppercase;'  # Auto-uppercase in browser
        }),
        validators=[
            RegexValidator(
                regex=r'^[A-Z][0-9]{9}$',  # Pattern: 1 letter + 9 digits
                message='身分證格式錯誤 (需首字大寫英文+9碼數字)'
            )
        ]
    )
```

**Why This is Difficult**:
- Regex syntax must be correct
- Understanding character classes `[A-Z]`, `[0-9]`
- Anchors `^` (start) and `$` (end) for exact matching
- Custom error messages for user experience

**Key Insight**: Regex validators provide powerful pattern matching with custom error messages for better UX.

---

## 🟡 **MODERATE DIFFICULTY LEVEL**

### 11. **Soft Delete Pattern with Boolean Flag**

**Difficulty**: ⭐⭐⭐ (Moderate)

**Location**: `apps/clinic/models.py` (line 153), `apps/clinic/views.py` (lines 585, 712, 750-756)

**Implementation**:
```python
# Model
class Appointment(models.Model):
    is_visible = models.BooleanField(default=True, verbose_name="是否顯示在總表")

# Soft delete action
def hide_appointment(request, appt_id):
    appt = get_object_or_404(Appointment, id=appt_id)
    appt.is_visible = False  # Mark as deleted
    appt.save()

# Query filtering
appointments = Appointment.objects.filter(is_visible=True)
```

**Why Moderate**: Concept is simple, but requires consistent filtering across all queries.

---

### 12. **get_or_create and update_or_create Patterns**

**Difficulty**: ⭐⭐⭐ (Moderate)

**Location**: `apps/clinic/views.py` (lines 291-295, 544-548), `apps/clinic/signals.py` (line 38)

**Implementation**:
```python
# Atomic get-or-create
daily_state, created = DailyClinicState.objects.get_or_create(
    date=now.date(),
    time_slot=session_name,
    defaults={'current_number': 0}  # Only used if creating
)

# Atomic update-or-create
did, created = DID.objects.update_or_create(
    appointment_id=appointment.id,
    defaults={  # Updates if exists, creates with these if not
        'user_id': appointment.user.id,
        'date': appointment.date,
        # ... more fields ...
    }
)
```

**Why Moderate**: Atomic operations prevent race conditions, but must understand `defaults` parameter behavior.

---

### 13. **Query Optimization with select_related()**

**Difficulty**: ⭐⭐⭐ (Moderate)

**Location**: `apps/clinic/views.py` (line 585)

**Implementation**:
```python
# Without optimization (N+1 queries):
appointments = Appointment.objects.filter(is_visible=True)
# Each appointment.user access triggers a separate query

# With optimization (1 query with JOIN):
appointments = Appointment.objects.filter(is_visible=True).select_related('user')
# Single query with JOIN, all user data loaded
```

**Why Moderate**: Simple to use, but requires understanding when to apply (ForeignKey only, not ManyToMany).

---

### 14. **Timezone-Aware DateTime Handling**

**Difficulty**: ⭐⭐⭐ (Moderate)

**Location**: `apps/clinic/views.py` (lines 35-38, 264-267)

**Implementation**:
```python
from django.utils import timezone

# Get timezone-aware current time
now = timezone.localtime(timezone.now())
current_time = now.time()
current_weekday = now.weekday()  # 0=Monday, 6=Sunday
```

**Why Moderate**: Django's timezone handling is automatic, but requires understanding `USE_TZ` setting and `localtime()` usage.

---

### 15. **Nested Function Definitions (Closures)**

**Difficulty**: ⭐⭐ (Moderate)

**Location**: `apps/clinic/views.py` (lines 50-64, 271-281, 330-338)

**Implementation**:
```python
def booking_select_time(request):
    # Nested function has access to outer scope
    def check_slot(key, name, limit, time_str, is_open):
        if is_open:
            # Accesses 'target_date' from outer function
            count = Appointment.objects.filter(
                date=target_date,  # Closure: accesses outer variable
                time_slot=key
            ).count()
            remaining = max(0, limit - count)
            return {...}
        return None
    
    # Use nested function
    if hours.morning:
        slots.append(check_slot('morning', '早診', ...))
```

**Why Moderate**: Closures are Python basics, but understanding variable capture and scope is important.

---

## 📊 **Summary of Difficulty Levels**

| Technique | Difficulty | Complexity | Why Difficult |
|-----------|-----------|------------|---------------|
| `transaction.on_commit()` | ⭐⭐⭐⭐⭐ | Very High | Transaction lifecycle, timing issues |
| Multiple ModelFormSets | ⭐⭐⭐⭐ | High | Prefix management, validation coordination |
| Dynamic Form Generation | ⭐⭐⭐⭐⭐ | Very High | Runtime field creation, custom attributes |
| Time Parsing | ⭐⭐⭐⭐ | High | Multiple formats, edge cases |
| Custom Sorting | ⭐⭐⭐⭐ | High | Mixed types, empty values |
| ManyToMany Through | ⭐⭐⭐⭐ | High | Relationship patterns, manual creation |
| Session Forms | ⭐⭐⭐ | Moderate | State management, serialization |
| Data Aggregation | ⭐⭐⭐⭐ | High | Query optimization, dictionary building |
| CSV BOM | ⭐⭐⭐ | Moderate | Encoding knowledge |
| Regex Validation | ⭐⭐⭐ | Moderate | Pattern syntax |

---

## 🎯 **Key Takeaways**

1. **Transaction Management**: `transaction.on_commit()` is critical for signal-based synchronization
2. **Form Complexity**: Dynamic forms and multiple formsets require careful namespace management
3. **Query Optimization**: Dictionary building and `select_related()` prevent N+1 problems
4. **Data Serialization**: Session storage and CSV export require encoding awareness
5. **Error Handling**: Defensive programming with try/except and graceful fallbacks

These techniques demonstrate **production-level Django development** with proper error handling, optimization, and maintainability.

