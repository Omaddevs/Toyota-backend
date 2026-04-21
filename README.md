# ToyMakon backend (Django REST Framework)

Bosh sahifa bloklari, kategoriyalar, vendorlar, promo postlar, foydalanuvchi ro‘yxatdan o‘tish va JWT autentifikatsiya. Boshqaruv **Django Admin** orqali: qo‘shish, tahrirlash, o‘chirish, filtrlash, qidiruv, bulk action.

## Talablar

- Python 3.11+
- (Ixtiyoriy) MySQL 8 — `MYSQL_*` o‘zgaruvchilari berilsa ishlatiladi, aks holda **SQLite** (`db.sqlite3`).

## O‘rnatish

```bash
cd toymakon-backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- API: `http://127.0.0.1:8000/api/`
- Admin: `http://127.0.0.1:8000/admin/`

Frontend (Vite) allaqachon `vite.config.js` orqali `/api` ni `127.0.0.1:8000` ga proxylaydi.

## Production uchun muhim sozlamalar

- `DJANGO_DEBUG=0`
- `DJANGO_SECRET_KEY` ni kuchli qiymat bilan almashtiring
- `DJANGO_ALLOWED_HOSTS=api.sizning-domen.uz`
- `CORS_ALLOWED_ORIGINS=https://sizning-frontend-domen.uz`
- `CSRF_TRUSTED_ORIGINS=https://sizning-frontend-domen.uz`

`DJANGO_DEBUG=0` bo‘lganda `settings.py` avtomatik ravishda secure cookie/HSTS/SSL redirect konfiguratsiyalarini yoqadi.

## Asosiy API yo‘llari

| Yo‘l | Tavsif |
|------|--------|
| `GET /api/health/` | Tekshiruv |
| `GET /api/categories/` | Barcha kategoriyalar (`zone`: primary / extra) |
| `GET /api/categories/<slug>/` | Bitta kategoriya |
| `GET /api/vendors/` | Vendorlar (`?category=venue` va hokazo) |
| `GET /api/vendors/<code>/` | Batafsil (masalan `v-versal`) |
| `GET /api/promo-posts/` | Promo karusel |
| `POST /api/promo-posts/<slug>/record-view/` | Ko‘rishlar soni +1 |
| `GET /api/home/` | Asosiy qator, qo‘shimcha qator, Top to‘yxonalar, Tavsiya qilamiz |
| `POST /api/auth/register/` | Ro‘yxatdan o‘tish (`username`, `password`, `password_confirm`, ixtiyoriy `email`, `full_name`, `phone`) |
| `POST /api/auth/token/` | JWT (`username`, `password`) — javobda `access`, `refresh`, `user` |
| `POST /api/auth/token/refresh/` | Access yangilash |
| `GET /api/auth/me/` | Joriy foydalanuvchi (Bearer token) |

## Admin panel

- **Kategoriyalar** — To‘yxona, FotoStudio, Dekor, … tartib va zona.
- **Vendorlar** — sharhlar inline, galereya/specs JSON, bulk: chop etish/yashirish, reytingni qayta hisoblash.
- **Promo postlar** — karusel bannerlari.
- **Bosh sahifa joylashuvlari** — «Top to‘yxonalar» faqat `venue` kategoriyasi uchun tekshiriladi.
- **Foydalanuvchilar** — Django User + profil (telefon, ism).

`0002_seed_catalog` migratsiyasi demo ma’lumot qo‘shmaydi — kategoriya, vendor va promolarni **admin panel** orqali kiriting. Eski `db.sqlite3` da qolgan demo qatorlar bo‘lsa, admin orqali o‘chirib tashlashingiz mumkin.

## MySQL

```bash
pip install mysqlclient
```

`.env` da `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` va hokazoni to‘ldiring, keyin `migrate`.
