from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for

from services.content_service import (
    ContentServiceError,
    get_content_map,
    list_content_rows,
    upsert_content,
    upload_image,
)


def create_content_blueprint(admin_required):
    content_bp = Blueprint("content", __name__)

    def wants_json_response():
        if request.is_json:
            return True
        return "application/json" in (request.headers.get("Accept") or "")

    @content_bp.route("/api/content", methods=["GET"])
    def api_content():
        try:
            content_map = get_content_map()
            return jsonify(content_map), 200
        except ContentServiceError as exc:
            return jsonify({"error": str(exc)}), 503
        except Exception:
            return jsonify({"error": "Failed to fetch site content"}), 500

    @content_bp.route("/admin/content", methods=["GET"])
    @admin_required
    def admin_content_page():
        try:
            rows = list_content_rows()
        except Exception as exc:
            flash(f"Could not load content keys: {exc}", "error")
            rows = []
        return render_template("admin/content.html", content_rows=rows)

    @content_bp.route("/admin/update-content", methods=["POST"])
    @admin_required
    def admin_update_content():
        payload = request.get_json(silent=True) if request.is_json else request.form
        key = (payload.get("key") or "").strip()
        value = payload.get("value", "")
        content_type = (payload.get("type") or "text").strip()

        try:
            row = upsert_content(key, value, content_type)
        except ContentServiceError as exc:
            if wants_json_response():
                return jsonify({"success": False, "error": str(exc)}), 400
            flash(str(exc), "error")
            return redirect(url_for("content.admin_content_page"))
        except Exception:
            if wants_json_response():
                return jsonify({"success": False, "error": "Failed to save content"}), 500
            flash("Failed to save content", "error")
            return redirect(url_for("content.admin_content_page"))

        if wants_json_response():
            return jsonify({"success": True, "message": "Content updated", "data": row}), 200

        flash(f"Saved content key '{key}'", "success")
        return redirect(url_for("content.admin_content_page"))

    @content_bp.route("/admin/upload-image", methods=["POST"])
    @admin_required
    def admin_upload_image():
        image_file = request.files.get("image")
        key = (request.form.get("key") or request.args.get("key") or "").strip()

        try:
            upload_result = upload_image(image_file)
            saved_row = None
            if key:
                saved_row = upsert_content(key, upload_result["stored_value"], "image")
        except ContentServiceError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400
        except Exception:
            return jsonify({"success": False, "error": "Failed to upload image"}), 500

        response = {
            "success": True,
            "message": "Image uploaded successfully",
            "url": upload_result["url"],
            "stored_value": upload_result["stored_value"],
            "storage_path": upload_result["storage_path"],
            "private_bucket": upload_result["private_bucket"],
        }
        if saved_row:
            response["data"] = saved_row

        return jsonify(response), 200

    return content_bp
