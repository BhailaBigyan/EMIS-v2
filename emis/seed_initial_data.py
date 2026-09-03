import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')
django.setup()

from academics.models import Department, Program
from library.models import BookCategory, Book, Librarian
from teachers.models import Teacher

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

    print("Seeding Library catalog & demo librarian...")

    cs_cat, _ = BookCategory.objects.get_or_create(
        name="Computer Science",
        defaults={"description": "Programming, algorithms, and information technology."}
    )
    mgmt_cat, _ = BookCategory.objects.get_or_create(
        name="Business & Management",
        defaults={"description": "Business administration, finance, and accounting."}
    )
    eng_cat, _ = BookCategory.objects.get_or_create(
        name="Engineering",
        defaults={"description": "Civil, electrical, and general engineering references."}
    )

    books = [
        ("Python Crash Course", "Eric Mathews", "978-1593279288", cs_cat, 5),
        ("Django for Beginners", "William S. Vincent", "978-1735467221", cs_cat, 3),
        ("Database System Concepts", "Abraham Silberschatz", "978-1260084504", cs_cat, 4),
        ("Principles of Management", "Stephen P. Robbins", "978-0133929762", mgmt_cat, 4),
        ("Accounting for Dummies", "John A. Tracy", "978-1119837527", mgmt_cat, 3),
        ("Engineering Mechanics", "R.C. Hibbeler", "978-0133918926", eng_cat, 5),
    ]
    for title, author, isbn, category, copies in books:
        book, created = Book.objects.get_or_create(
            isbn=isbn,
            defaults={
                "title": title,
                "author": author,
                "category": category,
                "publisher": "Demo Publishers",
                "total_copies": copies,
                "available_copies": copies,
                "rack_location": "Rack 1",
            }
        )
        if created:
            print(f"  + Book: {title}")

    librarian, created = Librarian.objects.get_or_create(
        username="librarian",
        defaults={
            "full_name": "Demo Librarian",
            "email": "library@khec.edu.np",
            "phone": "9800000001",
            "is_active": True,
        }
    )
    if created:
        librarian.set_default_password()
        librarian.save()
        print("  + Librarian 'librarian' created (password: library@librarian)")
    else:
        print("  Librarian 'librarian' already exists")

    print("Seeding demo teacher...")

    teacher, created = Teacher.objects.get_or_create(
        employee_id="TCH-001",
        defaults={
            "first_name": "Demo",
            "last_name": "Teacher",
            "email": "teacher@khec.edu.np",
            "phone": "9800000002",
            "gender": "M",
            "department": cs_dept,
            "designation": "lecturer",
            "qualification": "M.Sc. Computer Science",
            "specialization": "Web Development",
            "is_active": True,
        }
    )
    if created:
        teacher.set_default_password()
        teacher.save()
        print("  + Teacher 'TCH-001' created (password: tch@TCH-001)")
    else:
        if not teacher.password:
            teacher.set_default_password()
            teacher.save()
            print("  Teacher 'TCH-001' existed without a password; set password: tch@TCH-001")
        else:
            print("  Teacher 'TCH-001' already exists")

    print("Seed complete!")

if __name__ == "__main__":
    seed()
