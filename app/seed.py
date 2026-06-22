from datetime import datetime, timedelta
from sqlalchemy import text


SEED_USERS = [
    ("Alice Johnson", "alice.johnson@example.com", "active", "United Kingdom", 320),
    ("Bob Smith", "bob.smith@example.com", "inactive", "United States", 290),
    ("Carlos Mendez", "carlos.mendez@example.com", "active", "Spain", 260),
    ("Diana Chen", "diana.chen@example.com", "active", "China", 240),
    ("Evan Patel", "evan.patel@example.com", "inactive", "India", 210),
    ("Fatima Al-Rashid", "fatima.alrashid@example.com", "active", "UAE", 200),
    ("George Okafor", "george.okafor@example.com", "active", "Nigeria", 180),
    ("Hannah Müller", "hannah.muller@example.com", "inactive", "Germany", 160),
    ("Ivan Petrov", "ivan.petrov@example.com", "active", "Russia", 140),
    ("Julia Santos", "julia.santos@example.com", "active", "Brazil", 120),
    ("Kevin Lee", "kevin.lee@example.com", "active", "South Korea", 100),
    ("Laura Bianchi", "laura.bianchi@example.com", "inactive", "Italy", 90),
    ("Mohammed Hassan", "mohammed.hassan@example.com", "active", "Egypt", 80),
    ("Nina Kowalski", "nina.kowalski@example.com", "active", "Poland", 70),
    ("Oliver Brown", "oliver.brown@example.com", "inactive", "Australia", 60),
    ("Priya Sharma", "priya.sharma@example.com", "active", "India", 50),
    ("Quinn Murphy", "quinn.murphy@example.com", "active", "Ireland", 45),
    ("Rosa Fernandez", "rosa.fernandez@example.com", "active", "Mexico", 40),
    ("Samuel Yeboah", "samuel.yeboah@example.com", "inactive", "Ghana", 35),
    ("Tina Nakamura", "tina.nakamura@example.com", "active", "Japan", 30),
    ("Umar Farooq", "umar.farooq@example.com", "active", "Pakistan", 25),
    ("Vera Novak", "vera.novak@example.com", "inactive", "Czech Republic", 20),
    ("William Clark", "william.clark@example.com", "active", "United States", 15),
    ("Xiao Wei", "xiao.wei@example.com", "active", "China", 10),
    ("Yuki Tanaka", "yuki.tanaka@example.com", "active", "Japan", 5),
]


def seed_if_empty(conn):
    result = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
    if result and result > 0:
        return

    now = datetime.utcnow()
    rows = []
    for name, email, status, country, days_ago in SEED_USERS:
        created_at = now - timedelta(days=days_ago)
        rows.append({
            "name": name,
            "email": email,
            "status": status,
            "country": country,
            "created_at": created_at,
        })

    conn.execute(
        text(
            "INSERT INTO users (name, email, status, country, created_at) "
            "VALUES (:name, :email, :status, :country, :created_at)"
        ),
        rows,
    )
    conn.commit()
