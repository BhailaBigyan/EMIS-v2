# EMIS Admin Dashboard — Complete Implementation Plan

## Current State Assessment

After exhaustive review of the codebase, here is what exists:

| Component | Status | Notes |
|---|---|---|
| Admin Login | ✅ Hardcoded | `admin/admin123` session-based, no Django auth |
| Dashboard Home | ✅ Static | Stat cards with dummy data, no real DB queries |
| Student Model | ⚠️ Minimal | Only `username`, `password` fields — no roll no, program, batch, etc. |
| Academics Models | ⚠️ Partial | Department, Program, Course, AcademicYear, Semester, CourseAssignment, Timetable defined but `teacher` FK commented out |
| Examinations Models | ⚠️ Partial | Exam, ExamSchedule, Grade, Result defined but `student` FK commented out |
| Finances Models | ⚠️ Partial | FeeStructure, FeePayment, Salary defined but `student` FK commented out |
| Library / Notices | ❌ Empty | Models empty, views are stub-only |
| Templates | ⚠️ Scaffold | Admin management list pages exist but are mostly empty shells |

### Critical Issues Found
- `base.html` references `{% static 'js/emis.js' %}` but the actual file is `main.js`
- `CourseAssignment.__str__` references `self.teacher` (commented-out FK → will crash)
- `Grade.__str__`, `Result.__str__`, `FeePayment.__str__` reference `self.student` (commented-out FK)
- No `MEDIA_ROOT` / `MEDIA_URL` configured (needed for CSV/Excel file uploads)
- `openpyxl` dependency needed for Excel parsing
- No Teacher/Staff model exists anywhere

---

## Scope: Admin Dashboard — 4 Modules

### Module 1: Student Management (Bulk Add via CSV/Excel)
### Module 2: Academic Management (Departments, Courses, Programs, Assign Teacher, Timetable)
### Module 3: Fees / Finance Management
### Module 4: Examination Management

---

## Proposed Changes

### Phase 0 — Foundation & Fixes

> [!IMPORTANT]
> These fixes are prerequisites for all 4 modules to work correctly.

#### [MODIFY] [settings.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/emis/settings.py)
- Add `MEDIA_URL = '/media/'` and `MEDIA_ROOT = BASE_DIR / 'media'` for file uploads
- Fix the duplicate `BASE_DIR` definitions (lines 16, 61, 80 — keep only one)
- Set `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`

#### [MODIFY] [base.html](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/templates/base.html)
- Fix JS reference from `emis.js` → `main.js`

#### [NEW] `emis/emis/decorators.py`
- Create `admin_login_required` decorator to replace repetitive session checks in every view

#### [NEW] `emis/teachers/` (New Django App)
- **Teacher model**: `name`, `email`, `phone`, `department` (FK→Department), `designation`, `qualification`, `employee_id`, `is_active`, `date_joined`
- This is needed because `CourseAssignment`, `ExamSchedule`, `Salary`, etc. all reference a "teacher" entity

---

### Phase 1 — Student Management (Bulk Import)

#### [MODIFY] [students/models.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/students/models.py)
Significantly expand the `Students` model:

```python
class Students(models.Model):
    student_id = models.AutoField(primary_key=True)
    roll_number = models.CharField(max_length=50, unique=True)  # Auto-generated, used as login username
    password = models.CharField(max_length=128)  # Default password (hashed)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(choices=[('M','Male'),('F','Female'),('O','Other')])
    address = models.TextField(blank=True)
    program = models.ForeignKey('academics.Program', on_delete=models.SET_NULL, null=True)
    batch = models.CharField(max_length=20, blank=True)  # e.g. "2081"
    current_semester = models.IntegerField(default=1)
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(choices=[('active','Active'),('inactive','Inactive'),('graduated','Graduated'),('suspended','Suspended')], default='active')
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

- Remove `StudentProfile` (merge fields into `Students`)
- Remove plain `username` field, replace with `roll_number` as the login identifier

**Roll Number Auto-Generation Format**: `{PROGRAM_CODE}-{BATCH}-{SEQUENCE}`
  - Example: `BCA-2081-001`, `BCA-2081-002`, `BSCCSIT-2081-001`
  - Sequence is auto-incremented per program+batch combination

**Default Password**: `emis@{roll_number}` (e.g., `emis@BCA-2081-001`)

#### [NEW] `students/forms.py`
- `StudentForm` — for single student add/edit
- `BulkStudentUploadForm` — file upload field for CSV/Excel

#### [NEW] `students/utils.py`
- `parse_csv_file(file)` — parse uploaded CSV, validate columns, return list of student dicts
- `parse_excel_file(file)` — parse uploaded Excel (`.xlsx`) using `openpyxl`, validate, return list
- `generate_roll_number(program, batch)` — auto-generate next sequential roll number
- `bulk_create_students(student_data_list)` — create students in bulk with auto-generated roll numbers

**Expected CSV/Excel columns**:
| Column | Required | Notes |
|---|---|---|
| first_name | ✅ | |
| last_name | ✅ | |
| email | ❌ | |
| phone | ❌ | |
| date_of_birth | ❌ | Format: YYYY-MM-DD |
| gender | ✅ | M/F/O |
| address | ❌ | |
| program_code | ✅ | Must match existing Program.code |
| batch | ✅ | e.g. "2081" |
| guardian_name | ❌ | |
| guardian_phone | ❌ | |

#### [MODIFY] [emis/views.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/emis/views.py)
- Update `student_list` to support search, filter by program/batch/status, pagination
- Add `student_add` view (single add)
- Add `student_bulk_upload` view (CSV/Excel upload with preview, validation, and confirmation)
- Add `student_edit` / `student_delete` views
- Add `student_export_csv` view (export all students or filtered list as CSV)
- Add `download_sample_csv` / `download_sample_excel` views (provide template files)

#### [MODIFY] [emis/urls.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/emis/urls.py)
Add new student management URL patterns:
```
dashboard/students/                    → student_list
dashboard/students/add/                → student_add
dashboard/students/bulk-upload/        → student_bulk_upload
dashboard/students/<id>/edit/          → student_edit
dashboard/students/<id>/delete/        → student_delete
dashboard/students/export/             → student_export_csv
dashboard/students/sample-csv/         → download_sample_csv
dashboard/students/sample-excel/       → download_sample_excel
```

#### Admin Templates for Student Management
- [MODIFY] `admin/students_management/list_students.html` — Full table with search/filter bar, bulk upload button, export button, pagination, status pills
- [NEW] `admin/students_management/add_student.html` — Single student add form
- [MODIFY] `admin/students_management/add_students.html` → rename to `bulk_upload.html` — Upload form with drag-drop area, file preview, validation results table, confirm button
- [NEW] `admin/students_management/edit_student.html` — Edit student form
- [MODIFY] `admin/students_management/student_profile.html` — Detailed student view with tabs (Info, Academic, Fees, Attendance)

---

### Phase 2 — Academic Management

#### [MODIFY] [academics/models.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/academics/models.py)
- Uncomment and fix `teacher` FK in `CourseAssignment` → point to `teachers.Teacher`
- Fix `CourseAssignment.__str__` to not crash
- Add `Batch` model (or use batch field in Student) for better enrollment tracking

#### [MODIFY] [academics/views.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/academics/views.py)
Complete CRUD views for:
1. **Departments** — `department_list`, `department_add`, `department_edit`, `department_delete`
2. **Programs** — `program_list`, `program_add`, `program_edit`, `program_delete`
3. **Courses** — `course_list`, `course_add`, `course_edit`, `course_delete`
4. **Academic Years & Semesters** — `academic_year_list`, `academic_year_add`, `semester_add`
5. **Course Assignments (Assign Teacher)** — `assignment_list`, `assignment_add`, `assignment_edit`
6. **Timetable** — `timetable_view` (weekly grid view), `timetable_add_slot`, `timetable_edit_slot`, `timetable_delete_slot`

#### [NEW] `academics/forms.py`
- Forms for all academic entities (Department, Program, Course, AcademicYear, Semester, CourseAssignment, Timetable)

#### [MODIFY] [academics/urls.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/academics/urls.py)
```
dashboard/academics/departments/           → department_list
dashboard/academics/departments/add/       → department_add
dashboard/academics/departments/<id>/edit/ → department_edit
dashboard/academics/programs/              → program_list
dashboard/academics/programs/add/          → program_add
dashboard/academics/programs/<id>/edit/    → program_edit
dashboard/academics/courses/               → course_list
dashboard/academics/courses/add/           → course_add
dashboard/academics/courses/<id>/edit/     → course_edit
dashboard/academics/years/                 → academic_year_list
dashboard/academics/years/add/             → academic_year_add
dashboard/academics/semesters/add/         → semester_add
dashboard/academics/assignments/           → assignment_list
dashboard/academics/assignments/add/       → assignment_add
dashboard/academics/timetable/             → timetable_view
dashboard/academics/timetable/add/         → timetable_add_slot
```

#### Admin Templates for Academics
- [NEW] `admin/academics_management/department_list.html`
- [NEW] `admin/academics_management/department_form.html` (add/edit reusable)
- [NEW] `admin/academics_management/program_list.html`
- [NEW] `admin/academics_management/program_form.html`
- [NEW] `admin/academics_management/course_list.html`
- [NEW] `admin/academics_management/course_form.html`
- [NEW] `admin/academics_management/academic_year_list.html`
- [NEW] `admin/academics_management/academic_year_form.html`
- [NEW] `admin/academics_management/assignment_list.html`
- [NEW] `admin/academics_management/assignment_form.html`
- [NEW] `admin/academics_management/timetable.html` — Interactive weekly grid view (Mon-Fri × time slots)

---

### Phase 3 — Fees / Finance Management

#### [MODIFY] [finances/models.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/finances/models.py)
- Uncomment `student` FK in `FeePayment` → point to `students.Students`
- Fix `FeePayment.__str__`
- Add `StudentFeeAccount` model to track per-student balances:
  ```python
  class StudentFeeAccount(models.Model):
      student = models.OneToOneField('students.Students', on_delete=models.CASCADE)
      fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
      total_due = models.DecimalField(...)
      total_paid = models.DecimalField(...)
      balance = property: total_due - total_paid
  ```
- Update `Salary` model to point teacher FK to `teachers.Teacher`

#### [MODIFY] [finances/views.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/finances/views.py)
Full CRUD views:
1. **Fee Structures** — `fee_structure_list`, `fee_structure_add`, `fee_structure_edit`, `fee_structure_delete`
2. **Fee Payments** — `payment_list`, `record_payment`, `payment_receipt` (printable)
3. **Student Fee Status** — `student_fee_status` (search by roll number, view balance)
4. **Financial Reports** — `finance_dashboard` (total collections, pending dues, monthly chart)

#### [NEW] `finances/forms.py`
- Forms for FeeStructure, FeePayment

#### [MODIFY] [finances/urls.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/finances/urls.py)
```
dashboard/finances/fee-structures/           → fee_structure_list
dashboard/finances/fee-structures/add/       → fee_structure_add
dashboard/finances/fee-structures/<id>/edit/ → fee_structure_edit
dashboard/finances/payments/                 → payment_list
dashboard/finances/payments/add/             → record_payment
dashboard/finances/payments/<id>/receipt/    → payment_receipt
dashboard/finances/student-fees/             → student_fee_status
dashboard/finances/reports/                  → finance_dashboard
```

#### Admin Templates for Finances
- [MODIFY] `admin/finances_management/list_fee_structures.html` — Full list with add button
- [NEW] `admin/finances_management/fee_structure_form.html`
- [NEW] `admin/finances_management/payment_list.html`
- [NEW] `admin/finances_management/record_payment.html`
- [NEW] `admin/finances_management/payment_receipt.html` (print-friendly)
- [NEW] `admin/finances_management/student_fee_status.html`
- [NEW] `admin/finances_management/finance_dashboard.html` — Summary cards + charts

---

### Phase 4 — Examination Management

#### [MODIFY] [examinations/models.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/examinations/models.py)
- Uncomment `student` FK in `Grade` → point to `students.Students`
- Uncomment `student` FK in `Result` → point to `students.Students`
- Uncomment `invigilator` FK in `ExamSchedule` → point to `teachers.Teacher`
- Fix all `__str__` methods
- Uncomment `Meta` classes with `unique_together`

#### [MODIFY] [examinations/views.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/examinations/views.py)
Full CRUD views:
1. **Exams** — `exam_list`, `exam_create`, `exam_edit`, `exam_delete`
2. **Exam Schedule** — `schedule_list`, `schedule_add` (course-wise date/time/room)
3. **Grade Entry** — `grade_entry` (per-exam, per-course, enter marks for all students in a grid)
4. **Results** — `result_list`, `result_generate` (auto-compute from grades), `result_publish`
5. **Report Cards** — `report_card_view` (per-student semester report)

#### [NEW] `examinations/forms.py`
- Forms for Exam, ExamSchedule, Grade entry

#### [MODIFY] [examinations/urls.py](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/examinations/urls.py)
```
dashboard/examinations/exams/                    → exam_list
dashboard/examinations/exams/add/                → exam_create
dashboard/examinations/exams/<id>/edit/           → exam_edit
dashboard/examinations/exams/<id>/schedule/       → schedule_list
dashboard/examinations/exams/<id>/schedule/add/   → schedule_add
dashboard/examinations/grades/<exam_id>/<course_id>/ → grade_entry
dashboard/examinations/results/                   → result_list
dashboard/examinations/results/generate/          → result_generate
dashboard/examinations/results/<id>/publish/      → result_publish
dashboard/examinations/report-card/<student_id>/  → report_card_view
```

#### Admin Templates for Examinations
- [MODIFY] `admin/examinations_management/list_examinations.html` — Full exam list
- [NEW] `admin/examinations_management/exam_form.html`
- [NEW] `admin/examinations_management/exam_schedule.html`
- [NEW] `admin/examinations_management/schedule_form.html`
- [NEW] `admin/examinations_management/grade_entry.html` — Spreadsheet-like grid for bulk grade entry
- [NEW] `admin/examinations_management/result_list.html`
- [NEW] `admin/examinations_management/report_card.html` (print-friendly)

---

### Phase 5 — Dashboard Integration & Sidebar Updates

#### [MODIFY] [general_dashboard.html](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/templates/general_dashboard.html)
- Replace hardcoded stat card values with real database queries
- Show real "Recently Enrolled Students" from DB
- Show real "Upcoming Exams" from DB
- Add "Recent Payments" card
- Add quick action buttons (Add Student, Record Payment, etc.)

#### [MODIFY] [sidebar.html](file:///d:/Bhaila%20Bigyan/Django%20Project/EMIS-v2/emis/templates/partials/sidebar.html)
- Update navigation links to point to all new views
- Add active state highlighting based on current URL
- Restructure sections:
  - **General**: Dashboard
  - **Student Management**: All Students, Add Student, Bulk Upload
  - **Academics**: Departments, Programs, Courses, Assignments, Timetable
  - **Examination & Grades**: Exams, Grade Entry, Results, Report Cards
  - **Finances**: Fee Structures, Payments, Student Fees, Reports
  - **Notices**: (future)
  - **System**: Settings, Activity Log

---

## Open Questions

> [!IMPORTANT]
> **Q1: Teacher Model Location** — Should the Teacher model be in a new `teachers` app, or should I add it to the `academics` app since teachers are tied to academic departments? I recommend a separate `teachers` app for clean separation.

> [!IMPORTANT]
> **Q2: Password Storage** — The current `Students` model stores passwords as plain text. Should I:
> - **(a)** Hash passwords using Django's `make_password()` for security (recommended)
> - **(b)** Keep plain text for simplicity during development
>
> Note: This affects student login functionality too.

> [!IMPORTANT]
> **Q3: Roll Number Format** — I propose `{PROGRAM_CODE}-{BATCH}-{SEQUENCE}` (e.g., `BCA-2081-001`). Is this format acceptable, or do you have a different institutional format?

> [!IMPORTANT]
> **Q4: Default Password Format** — I propose `emis@{roll_number}` (e.g., `emis@BCA-2081-001`). The student can change it after first login. Is this acceptable?

> [!IMPORTANT]
> **Q5: Execution Order** — Should I build all 4 modules sequentially (Phase 0→1→2→3→4→5) as listed above, or would you prefer a different priority order?

---

## Verification Plan

### Automated Tests
```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test students academics examinations finances
```

### Manual Verification
1. **Student Bulk Upload**: Upload a sample CSV/Excel → verify roll numbers generated, records created, downloadable sample files work
2. **Academic CRUD**: Create Department → Program → Course → Assign Teacher → Generate Timetable — full workflow
3. **Fee Management**: Create fee structure → record payment → verify receipt generation → check student balance
4. **Examination Flow**: Create exam → schedule → enter grades → generate results → view report card
5. **Dashboard**: Verify all stat cards show real data from database

---

## Dependencies to Install
```bash
pip install openpyxl  # For Excel file parsing
```

---

## File Count Summary

| Category | New Files | Modified Files |
|---|---|---|
| Models | 1 (teachers) | 4 (students, academics, examinations, finances) |
| Views | 1 (teachers) | 4 (emis, academics, examinations, finances) |
| Forms | 4 (students, academics, examinations, finances) | 0 |
| URLs | 1 (teachers) | 4 (emis, academics, examinations, finances) |
| Utils | 1 (students/utils.py) | 0 |
| Templates | ~25 new | ~8 modified |
| Config | 1 (decorators.py) | 1 (settings.py) |
| **Total** | **~33 new** | **~21 modified** |
