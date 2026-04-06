# Gramin Santa Foundation - Setup Guide

## Quick Start

### 1. Database Setup (Supabase)

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **SQL Editor** and run the SQL from `schema.sql` file
4. Copy your credentials:
   - Go to **Settings → API**
   - Copy **Project URL**
   - Copy **anon** key (public)
5. Update `.env` file with your credentials:
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJhbGci...
   ```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run the Backend

```bash
python app.py
```

You should see:
```
[INFO] Supabase client initialized successfully
[SEED] Default admin created: admin@graminsanta.org
 * Running on http://127.0.0.1:5000
```

### 4. Access the Application

- **Frontend:** http://127.0.0.1:5000/
- **Admin Panel:** http://127.0.0.1:5000/admin/login
  - Email: `admin@graminsanta.org`
  - Password: `admin123` (change after first login)

## Architecture

### Frontend (HTML)
- Located in `../Frontend/` folder
- Served by Flask from the backend
- Forms submit to Python API endpoints

### Backend (Flask)
- **API Endpoints:**
  - `POST /api/contact` - Save contact form data
  - `POST /api/volunteer` - Save volunteer registration
- **Admin Routes:**
  - `/admin/login` - Login page
  - `/admin/dashboard` - Stats & quick links
  - `/admin/contacts` - View/manage contact submissions
  - `/admin/volunteers` - View/manage volunteer registrations
  - `/admin/payments` - Payments (future scope placeholder)

### Database (Supabase PostgreSQL)
- **Tables:**
  - `contacts` - Contact form submissions
  - `volunteers` - Volunteer registrations
  - `payments` - Donation/payment records (ready for future use)
  - `admin_users` - Admin credentials
- **RLS Policies:** Configured to allow frontend submissions and admin access

## Features

✅ **Contact Form** - Public users submit contact requests
✅ **Volunteer Registration** - Users register as volunteers
✅ **Admin Dashboard** - View statistics and summaries
✅ **Contact Management** - View/update contact request status
✅ **Volunteer Management** - Approve/reject volunteer applications
✅ **Responsive Design** - Works on mobile & desktop
✅ **Government Theme** - Official Indian government color scheme

## File Structure

```
backend/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── supabase_client.py     # Supabase client initialization
├── schema.sql             # Database schema (run in Supabase)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from .env.example)
└── templates/
    └── admin/             # Admin panel templates
        ├── base.html      # Base layout
        ├── login.html     # Login page
        ├── dashboard.html # Dashboard
        ├── contacts.html  # Contact management
        ├── volunteers.html# Volunteer management
        └── payments.html  # Payment management
```

## Production Deployment

Before deploying to production:

1. Update `FLASK_DEBUG=False` in `.env`
2. Change `FLASK_SECRET_KEY` to a strong random value
3. Update admin password in database
4. Configure CORS to allow only your domain
5. Use a production WSGI server (Gunicorn, uWSGI)
6. Set up HTTPS/SSL certificate
7. Configure environment variables securely

## Troubleshooting

### Supabase Connection Error
- **Issue:** `[Errno 11001] getaddrinfo failed`
- **Solution:** Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`

### Admin login not working
- **Solution:** Run `schema.sql` in Supabase to create tables and seed admin user
- **Reset admin:** Update password in database admin_users table

### Frontend forms not submitting
- **Check:** Supabase tables are created and RLS policies are enabled
- **Enable CORS:** Backend already has CORS enabled for all origins

## API Endpoints

### Contact Form (POST /api/contact)
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+91 9876543210",
  "subject": "general",
  "message": "I have a query..."
}
```

### Volunteer Registration (POST /api/volunteer)
```json
{
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "+91 9876543210",
  "address": "123 Main St, City, State",
  "occupation": "Teacher",
  "skills": ["teaching", "medical"],
  "availability": "weekends",
  "experience": "5 years volunteering...",
  "message": "I want to help..."
}
```

## Support

For issues or questions, contact: admin@graminsanta.org

---
**Last Updated:** February 2026
**Version:** 1.0 - Beta
