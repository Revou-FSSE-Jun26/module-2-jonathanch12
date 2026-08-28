from flask import Blueprint, jsonify

# Main blueprint (general/utility routes)
main_bp = Blueprint('main', __name__)


# Database connection test
@main_bp.route('/')
def home():
    return jsonify({"message": "Connected to database successfully", "status": "ok"})
