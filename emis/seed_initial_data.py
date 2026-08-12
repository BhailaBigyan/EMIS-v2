import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')
django.setup()

from academics.models import Department, Program

def seed():
    print("Seeding initial Academic Departments & Programs...")

    cs_dept, _ = Department.objects.get_or_create(
        code="CS",
        defaults={
            "name": "Department of Computer Science & IT",
            "description": "Faculty of Science and Information Technology",
        }
    )

    mgmt_dept, _ = Department.objects.get_or_create(
        code="MGMT",
        defaults={
            "name": "Department of Management",
            "description": "Faculty of Management & Business Studies",
        }
    )

    bca, _ = Program.objects.get_or_create(
        code="BCA",
        defaults={
            "name": "Bachelor in Computer Application",
            "department": cs_dept,
            "duration_years": 4,
            "total_semesters": 8,
            "is_active": True,
        }
    )

    csit, _ = Program.objects.get_or_create(
        code="BSCCSIT",
        defaults={
            "name": "B.Sc. Computer Science and Information Technology",
            "department": cs_dept,
            "duration_years": 4,
            "total_semesters": 8,
            "is_active": True,
        }
    )

    bim, _ = Program.objects.get_or_create(
        code="BIM",
        defaults={
            "name": "Bachelor of Information Management",
            "department": mgmt_dept,
            "duration_years": 4,
            "total_semesters": 8,
            "is_active": True,
        }
    )

    print(f"Created/Verified Departments: {cs_dept.code}, {mgmt_dept.code}")
    print(f"Created/Verified Programs: {bca.code}, {csit.code}, {bim.code}")
    print("Seed complete!")

if __name__ == "__main__":
    seed()
