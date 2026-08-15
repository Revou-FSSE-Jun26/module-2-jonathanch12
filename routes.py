from flask import jsonify, request
from app import app, db

@app.route('/')
def home():
    return jsonify({"message": "Connected to database successfully", "status": "ok"})