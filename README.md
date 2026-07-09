# PhuLinhMedia

Website quản lý dự án domain và công việc nội bộ bằng Django, PostgreSQL, Tailwind CSS, HTMX, Celery, Redis, Docker, Nginx và Gunicorn.

## Chạy bằng Docker

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Mở `http://localhost`, đăng nhập bằng superuser rồi tạo manager, staff và gán staff cho manager.

## Chạy local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Celery:

```bash
celery -A phulinhmedia worker -l info
celery -A phulinhmedia beat -l info
```

## Chức năng chính

- Đăng nhập bằng email, không có đăng ký công khai.
- Role Admin, Manager, Staff với giới hạn dữ liệu theo phạm vi.
- Quản lý dự án domain, chuẩn hóa domain từ URL.
- Quản lý công việc, tiến độ, vướng mắc, duyệt hoàn thành, file minh chứng.
- Import Excel domain có preview, kiểm tra trùng file và trùng hệ thống.
- Xuất Excel/PDF cho dự án, công việc, hiệu suất và log.
- Thông báo web và Telegram Bot API.
- Celery beat kiểm tra deadline hằng ngày và đánh dấu quá hạn.
