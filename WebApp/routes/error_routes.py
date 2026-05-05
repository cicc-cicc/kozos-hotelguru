from flask import Blueprint, render_template, request, jsonify
from .. import db

# Blueprint létrehozása a hibakezeléshez
error_bp = Blueprint('errors', __name__)

# A .app_errorhandler kiterjeszti a hibakezelést az egész alkalmazásra (minden blueprintre)
@error_bp.app_errorhandler(404)
def not_found_error(error):
    # Ha a kérés az API-hoz jött, JSON-t adunk vissza
    if request.path.startswith('/api/'):
        return jsonify({"error": "A keresett erőforrás nem található."}), 404
    
    # Különben a böngészőnek HTML oldalt renderelünk
    return render_template('errors/404.html'), 404

@error_bp.app_errorhandler(500)
def internal_error(error):
    # Adatbázis hiba esetén visszavonjuk a tranzakciót (nagyon fontos best-practice!)
    db.session.rollback()
    
    if request.path.startswith('/api/'):
        return jsonify({"error": "Belső szerver hiba történt."}), 500
        
    return render_template('errors/500.html'), 500