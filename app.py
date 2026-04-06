"""
Gramin Santa Foundation - Flask Backend
========================================
API endpoints for contact/volunteer forms + Admin panel
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os
from config import Config
from supabase_client import supabase
from routes.content import create_content_blueprint

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=["*"])  # Allow frontend requests

# Path to Frontend files
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '..', 'Frontend')


# =====================================================
# HELPERS
# =====================================================

def admin_required(f):
    """Decorator to protect admin routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


app.register_blueprint(create_content_blueprint(admin_required))


def seed_admin():
    """Create default admin user if none exists."""
    if not supabase:
        print("[SEED] Supabase not configured, skipping admin seed")
        return
    try:
        result = supabase.table("admin_users").select("id").limit(1).execute()
        if not result.data:
            supabase.table("admin_users").insert({
                "name": "Admin",
                "email": Config.ADMIN_DEFAULT_EMAIL,
                "password_hash": generate_password_hash(Config.ADMIN_DEFAULT_PASSWORD),
                "role": "superadmin"
            }).execute()
            print(f"[SEED] Default admin created: {Config.ADMIN_DEFAULT_EMAIL}")
    except Exception as e:
        print(f"[SEED] Could not seed admin (run schema.sql first): {e}")


def ensure_default_admin_user():
    """Ensure default admin user exists and return it when possible."""
    if not supabase:
        return None

    default_email = (Config.ADMIN_DEFAULT_EMAIL or "").strip().lower()
    if not default_email:
        return None

    try:
        existing = supabase.table("admin_users").select("*").eq("email", default_email).limit(1).execute()
        if existing.data:
            return existing.data[0]

        inserted = supabase.table("admin_users").insert({
            "name": "Admin",
            "email": default_email,
            "password_hash": generate_password_hash(Config.ADMIN_DEFAULT_PASSWORD),
            "role": "superadmin"
        }).execute()
        if inserted.data:
            print(f"[SEED] Default admin created on-demand: {default_email}")
            return inserted.data[0]
    except Exception as e:
        print(f"[SEED] ensure_default_admin_user failed: {e}")

    return None


# Seed at import time so production app servers also initialize admin.
seed_admin()


# =====================================================
# FRONTEND ROUTES
# =====================================================

@app.route("/")
def index():
    """Serve main index.html"""
    try:
        return send_from_directory(FRONTEND_PATH, "index.html")
    except:
        return "<h1>Gramin Santa Foundation</h1><p><a href='/admin/login'>Admin Login</a></p>", 200

@app.route("/<path:filename>")
def serve_frontend(filename):
    """Serve frontend static files (HTML, CSS, etc)"""
    valid_files = ["index.html", "contact.html", "volunteer.html", "donation.html"]
    if filename in valid_files:
        try:
            return send_from_directory(FRONTEND_PATH, filename)
        except:
            return "File not found", 404
    return "Not found", 404

def check_supabase():
    """Check if Supabase is available."""
    if not supabase:
        return jsonify({"error": "Database not configured. Contact administrator."}), 503
    return None


# =====================================================
# PUBLIC API ROUTES
# =====================================================

@app.route("/api/contact", methods=["POST"])
def api_contact():
    """Save a contact-us form submission."""
    db_check = check_supabase()
    if db_check:
        return db_check
    data = request.get_json()
    required = ["name", "email", "subject", "message"]
    for field in required:
        if not data.get(field, "").strip():
            return jsonify({"error": f"'{field}' is required"}), 400

    row = {
        "name": data["name"].strip(),
        "email": data["email"].strip(),
        "phone": data.get("phone", "").strip(),
        "subject": data["subject"].strip(),
        "message": data["message"].strip(),
        "status": "new"
    }

    try:
        supabase.table("contacts").insert(row).execute()
        return jsonify({"success": True, "message": "Contact form submitted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/volunteer", methods=["POST"])
def api_volunteer():
    """Save a volunteer registration."""
    db_check = check_supabase()
    if db_check:
        return db_check
    data = request.get_json()
    required = ["full_name", "email", "phone", "address", "availability", "message"]
    for field in required:
        if not data.get(field, "").strip():
            return jsonify({"error": f"'{field}' is required"}), 400

    row = {
        "full_name": data["full_name"].strip(),
        "email": data["email"].strip(),
        "phone": data["phone"].strip(),
        "address": data["address"].strip(),
        "occupation": data.get("occupation", "").strip(),
        "skills": data.get("skills", []),
        "availability": data["availability"].strip(),
        "experience": data.get("experience", "").strip(),
        "message": data["message"].strip(),
        "status": "pending"
    }

    try:
        supabase.table("volunteers").insert(row).execute()
        return jsonify({"success": True, "message": "Volunteer registration submitted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# ADMIN AUTH ROUTES
# =====================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = None

        if not email or not password:
            flash("Email and password are required", "error")
            return render_template("admin/login.html")

        try:
            if supabase:
                result = supabase.table("admin_users").select("*").eq("email", email).limit(1).execute()
                if result.data:
                    user = result.data[0]

            if user and check_password_hash(user.get("password_hash", ""), password):
                session["admin_logged_in"] = True
                session["admin_id"] = user.get("id")
                session["admin_name"] = user.get("name", "Admin")
                session["admin_email"] = user.get("email", email)
                session["admin_role"] = user.get("role", "admin")

                try:
                    if supabase and user.get("id"):
                        supabase.table("admin_users").update(
                            {"last_login": datetime.utcnow().isoformat()}
                        ).eq("id", user["id"]).execute()
                except Exception:
                    pass

                return redirect(url_for("admin_dashboard"))

            # Fallback for env default credentials when DB row is missing/inconsistent.
            if email == (Config.ADMIN_DEFAULT_EMAIL or "").strip().lower() and password == Config.ADMIN_DEFAULT_PASSWORD:
                default_user = ensure_default_admin_user() or {
                    "id": None,
                    "name": "Admin",
                    "email": email,
                    "role": "superadmin",
                }
                session["admin_logged_in"] = True
                session["admin_id"] = default_user.get("id")
                session["admin_name"] = default_user.get("name", "Admin")
                session["admin_email"] = default_user.get("email", email)
                session["admin_role"] = default_user.get("role", "superadmin")
                return redirect(url_for("admin_dashboard"))

            flash("Invalid email or password", "error")
        except Exception as e:
            flash("Login failed. Please check database setup and try again.", "error")
            print(f"[LOGIN] Login error: {e}")

    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# =====================================================
# ADMIN DASHBOARD ROUTES
# =====================================================

@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Main admin dashboard with summary counts."""
    try:
        contacts = supabase.table("contacts").select("id, status").execute()
        volunteers = supabase.table("volunteers").select("id, status").execute()
        payments = supabase.table("payments").select("id, status").execute()
        homepage_rows = supabase.table("homepage").select("id").limit(1).execute()
        about_rows = supabase.table("about_items").select("id").execute()
        cms_total = len(about_rows.data) + (1 if homepage_rows.data else 0)

        stats = {
            "contacts_total": len(contacts.data),
            "contacts_new": len([c for c in contacts.data if c["status"] == "new"]),
            "volunteers_total": len(volunteers.data),
            "volunteers_pending": len([v for v in volunteers.data if v["status"] == "pending"]),
            "payments_total": len(payments.data),
            "content_total": cms_total,
        }
    except Exception:
        stats = {
            "contacts_total": 0, "contacts_new": 0,
            "volunteers_total": 0, "volunteers_pending": 0,
            "payments_total": 0,
            "content_total": 0,
        }

    return render_template("admin/dashboard.html", stats=stats)


# ---- CONTACTS MANAGEMENT ----

@app.route("/admin/contacts")
@admin_required
def admin_contacts():
    """View all contact submissions."""
    status_filter = request.args.get("status", "")
    try:
        query = supabase.table("contacts").select("*").order("created_at", desc=True)
        if status_filter:
            query = query.eq("status", status_filter)
        result = query.execute()
        contacts = result.data
    except Exception:
        contacts = []
    return render_template("admin/contacts.html", contacts=contacts, current_filter=status_filter)


@app.route("/admin/contacts/<int:contact_id>", methods=["POST"])
@admin_required
def admin_update_contact(contact_id):
    """Update contact status/notes."""
    new_status = request.form.get("status")
    admin_notes = request.form.get("admin_notes", "")
    try:
        supabase.table("contacts").update({
            "status": new_status,
            "admin_notes": admin_notes
        }).eq("id", contact_id).execute()
        flash("Contact updated successfully", "success")
    except Exception as e:
        flash(f"Error updating contact: {e}", "error")
    return redirect(url_for("admin_contacts"))


# ---- VOLUNTEERS MANAGEMENT ----

@app.route("/admin/volunteers")
@admin_required
def admin_volunteers():
    """View all volunteer registrations."""
    status_filter = request.args.get("status", "")
    try:
        query = supabase.table("volunteers").select("*").order("created_at", desc=True)
        if status_filter:
            query = query.eq("status", status_filter)
        result = query.execute()
        volunteers = result.data
    except Exception:
        volunteers = []
    return render_template("admin/volunteers.html", volunteers=volunteers, current_filter=status_filter)


@app.route("/admin/volunteers/<int:vol_id>", methods=["POST"])
@admin_required
def admin_update_volunteer(vol_id):
    """Update volunteer status/notes."""
    new_status = request.form.get("status")
    admin_notes = request.form.get("admin_notes", "")
    try:
        supabase.table("volunteers").update({
            "status": new_status,
            "admin_notes": admin_notes
        }).eq("id", vol_id).execute()
        flash("Volunteer updated successfully", "success")
    except Exception as e:
        flash(f"Error updating volunteer: {e}", "error")
    return redirect(url_for("admin_volunteers"))


# ---- PAYMENTS (FUTURE SCOPE) ----

@app.route("/admin/payments")
@admin_required
def admin_payments():
    """Payments management - future scope placeholder."""
    try:
        result = supabase.table("payments").select("*").order("created_at", desc=True).execute()
        payments = result.data
    except Exception:
        payments = []
    return render_template("admin/payments.html", payments=payments)


# =====================================================
# RUN
# =====================================================

# if __name__ == "__main__":
#     seed_admin()
#     app.run(debug=Config.DEBUG, port=5000)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
