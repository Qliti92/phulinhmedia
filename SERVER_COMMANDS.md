# Lệnh quản trị server PhuLinhMedia

Thư mục dự án trên server:

```bash
cd /opt/phulinhmedia
```

## Cập nhật code mới

```bash
cd /opt/phulinhmedia
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

## Restart dịch vụ

```bash
cd /opt/phulinhmedia
docker compose -f docker-compose.prod.yml restart
```

## Xem log web

```bash
cd /opt/phulinhmedia
docker compose -f docker-compose.prod.yml logs -f web
```

## Xem log Celery

```bash
cd /opt/phulinhmedia
docker compose -f docker-compose.prod.yml logs -f celery
```

## Xem log backup/deadline hằng ngày

```bash
cd /opt/phulinhmedia
docker compose -f docker-compose.prod.yml logs -f celery-beat
```

## Chạy migrate thủ công

```bash
cd /opt/phulinhmedia
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

## Tạo admin mới

```bash
cd /opt/phulinhmedia
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Thu static file

```bash
cd /opt/phulinhmedia
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Kiểm tra container

```bash
cd /opt/phulinhmedia
docker compose -f docker-compose.prod.yml ps
```

## Dừng toàn bộ app

```bash
cd /opt/phulinhmedia
docker compose -f docker-compose.prod.yml down
```

## Khởi động lại toàn bộ app

```bash
cd /opt/phulinhmedia
docker compose -f docker-compose.prod.yml up -d
```

## Kiểm tra Nginx và reload

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Gia hạn SSL thủ công

```bash
sudo certbot renew --dry-run
```
