from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for

from services.content_service import (
    ContentServiceError,
    add_hero_slide,
    add_nav_link,
    add_notice,
    add_about_item,
    delete_hero_slide,
    delete_nav_link,
    delete_notice,
    delete_about_item,
    get_hero_slides,
    get_nav_links,
    get_notices,
    get_about_items,
    get_homepage_content,
    get_legacy_content_map,
    reorder_about_items,
    update_about_item,
    update_homepage_content,
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
        """Legacy endpoint maintained for backward compatibility."""
        try:
            content_map = get_legacy_content_map()
            return jsonify(content_map), 200
        except ContentServiceError as exc:
            return jsonify({"error": str(exc)}), 503
        except Exception:
            return jsonify({"error": "Failed to fetch site content"}), 500

    @content_bp.route("/api/homepage", methods=["GET"])
    def api_homepage():
        try:
            data = get_homepage_content()
            return jsonify(data), 200
        except ContentServiceError as exc:
            return jsonify({"error": str(exc)}), 503
        except Exception:
            return jsonify({"error": "Failed to fetch homepage content"}), 500

    @content_bp.route("/api/about", methods=["GET"])
    def api_about():
        try:
            items = get_about_items()
            return jsonify(items), 200
        except ContentServiceError as exc:
            return jsonify({"error": str(exc)}), 503
        except Exception:
            return jsonify({"error": "Failed to fetch about items"}), 500

    @content_bp.route("/api/nav-links", methods=["GET"])
    def api_nav_links():
        try:
            return jsonify(get_nav_links()), 200
        except Exception:
            return jsonify({"error": "Failed to fetch nav links"}), 500

    @content_bp.route("/api/hero-slides", methods=["GET"])
    def api_hero_slides():
        try:
            return jsonify(get_hero_slides()), 200
        except Exception:
            return jsonify({"error": "Failed to fetch hero slides"}), 500

    @content_bp.route("/api/notices", methods=["GET"])
    def api_notices():
        try:
            return jsonify(get_notices()), 200
        except Exception:
            return jsonify({"error": "Failed to fetch notices"}), 500

    @content_bp.route("/admin/content", methods=["GET"])
    @admin_required
    def admin_cms_dashboard():
        try:
            homepage = get_homepage_content()
            about_items = get_about_items()
            nav_links = get_nav_links()
            hero_slides = get_hero_slides()
            notices = get_notices()
        except Exception as exc:
            flash(f"Could not load CMS data: {exc}", "error")
            homepage = {
                "title": "",
                "description": "",
                "notice_text": "",
                "hero_image": "",
                "hero_image_value": "",
            }
            about_items = []
            nav_links = []
            hero_slides = []
            notices = []
        return render_template(
            "admin/content.html",
            homepage=homepage,
            about_items=about_items,
            nav_links=nav_links,
            hero_slides=hero_slides,
            notices=notices,
        )

    @content_bp.route("/admin/add-nav-link", methods=["POST"])
    @admin_required
    def admin_add_nav_link():
        payload = request.get_json(silent=True) if request.is_json else request.form
        try:
            row = add_nav_link(payload)
            return jsonify({"success": True, "data": row}), 200
        except ContentServiceError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400
        except Exception:
            return jsonify({"success": False, "error": "Failed to add nav link"}), 500

    @content_bp.route("/admin/delete-nav-link/<int:link_id>", methods=["POST"])
    @admin_required
    def admin_delete_nav_link(link_id):
        try:
            deleted = delete_nav_link(link_id)
            if not deleted:
                return jsonify({"success": False, "error": "Link not found"}), 404
            return jsonify({"success": True}), 200
        except Exception:
            return jsonify({"success": False, "error": "Failed to delete nav link"}), 500

    @content_bp.route("/admin/add-slide", methods=["POST"])
    @admin_required
    def admin_add_slide():
        payload = request.get_json(silent=True) if request.is_json else request.form
        try:
            row = add_hero_slide(payload)
            return jsonify({"success": True, "data": row}), 200
        except ContentServiceError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400
        except Exception:
            return jsonify({"success": False, "error": "Failed to add slide"}), 500

    @content_bp.route("/admin/delete-slide/<int:slide_id>", methods=["POST"])
    @admin_required
    def admin_delete_slide(slide_id):
        try:
            deleted = delete_hero_slide(slide_id)
            if not deleted:
                return jsonify({"success": False, "error": "Slide not found"}), 404
            return jsonify({"success": True}), 200
        except Exception:
            return jsonify({"success": False, "error": "Failed to delete slide"}), 500

    @content_bp.route("/admin/add-notice", methods=["POST"])
    @admin_required
    def admin_add_notice():
        payload = request.get_json(silent=True) if request.is_json else request.form
        try:
            row = add_notice(payload)
            return jsonify({"success": True, "data": row}), 200
        except ContentServiceError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400
        except Exception:
            return jsonify({"success": False, "error": "Failed to add notice"}), 500

    @content_bp.route("/admin/delete-notice/<int:notice_id>", methods=["POST"])
    @admin_required
    def admin_delete_notice(notice_id):
        try:
            deleted = delete_notice(notice_id)
            if not deleted:
                return jsonify({"success": False, "error": "Notice not found"}), 404
            return jsonify({"success": True}), 200
        except Exception:
            return jsonify({"success": False, "error": "Failed to delete notice"}), 500

    @content_bp.route("/admin/update-homepage", methods=["POST"])
    @admin_required
    def admin_update_homepage():
        payload = request.get_json(silent=True) if request.is_json else request.form

        try:
            homepage = update_homepage_content(payload)
        except ContentServiceError as exc:
            if wants_json_response():
                return jsonify({"success": False, "error": str(exc)}), 400
            flash(str(exc), "error")
            return redirect(url_for("content.admin_cms_dashboard"))
        except Exception:
            if wants_json_response():
                return jsonify({"success": False, "error": "Failed to update homepage"}), 500
            flash("Failed to update homepage", "error")
            return redirect(url_for("content.admin_cms_dashboard"))

        if wants_json_response():
            return jsonify({"success": True, "message": "Homepage updated", "data": homepage}), 200

        flash("Homepage updated successfully", "success")
        return redirect(url_for("content.admin_cms_dashboard"))

    @content_bp.route("/admin/add-about-item", methods=["POST"])
    @admin_required
    def admin_add_about_item():
        payload = request.get_json(silent=True) if request.is_json else request.form
        try:
            item = add_about_item(payload)
            return jsonify({"success": True, "message": "About item added", "data": item}), 200
        except ContentServiceError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400
        except Exception:
            return jsonify({"success": False, "error": "Failed to add about item"}), 500

    @content_bp.route("/admin/update-about-item/<int:item_id>", methods=["POST"])
    @admin_required
    def admin_update_about_item(item_id):
        payload = request.get_json(silent=True) if request.is_json else request.form
        try:
            item = update_about_item(item_id, payload)
            return jsonify({"success": True, "message": "About item updated", "data": item}), 200
        except ContentServiceError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400
        except Exception:
            return jsonify({"success": False, "error": "Failed to update about item"}), 500

    @content_bp.route("/admin/delete-about-item/<int:item_id>", methods=["POST"])
    @admin_required
    def admin_delete_about_item(item_id):
        try:
            deleted = delete_about_item(item_id)
            if not deleted:
                return jsonify({"success": False, "error": "Item not found"}), 404
            return jsonify({"success": True, "message": "About item deleted"}), 200
        except Exception:
            return jsonify({"success": False, "error": "Failed to delete about item"}), 500

    @content_bp.route("/admin/reorder-about", methods=["POST"])
    @admin_required
    def admin_reorder_about():
        payload = request.get_json(silent=True) or {}
        ids = payload.get("ids")
        try:
            items = reorder_about_items(ids)
            return jsonify({"success": True, "message": "About items reordered", "data": items}), 200
        except ContentServiceError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400
        except Exception:
            return jsonify({"success": False, "error": "Failed to reorder about items"}), 500

    @content_bp.route("/admin/upload-image", methods=["POST"])
    @admin_required
    def admin_upload_image():
        image_file = request.files.get("image")
        key = (request.form.get("key") or request.args.get("key") or "").strip()

        try:
            upload_result = upload_image(image_file)
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
        if key:
            response["key"] = key

        return jsonify(response), 200

    return content_bp
