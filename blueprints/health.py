from flask import Blueprint, jsonify
from static.Controleur.ControleurLog import write_log
from datetime import datetime
import shutil

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def healthcheck():
    """Endpoint de healthcheck pour monitoring et orchestrateurs."""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    # 1. Vérifier Redis
    try:
        from redis import Redis
        redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        health_status['checks']['redis'] = 'ok'
    except Exception as e:
        health_status['checks']['redis'] = 'fail'
        health_status['status'] = 'degraded'
        write_log(f"Healthcheck Redis fail: {e}", "WARNING")
    
    # 2. Vérifier LDAP
    try:
        from static.Controleur.ControleurLdap import ControleurLdap
        ds = ControleurLdap()
        ds.disconnect()
        health_status['checks']['ldap'] = 'ok'
    except Exception as e:
        health_status['checks']['ldap'] = 'fail'
        health_status['status'] = 'degraded'
        write_log(f"Healthcheck LDAP fail: {e}", "WARNING")
    
    # 3. Vérifier espace disque
    try:
        from static.Controleur.ControleurConf import ControleurConf
        conf = ControleurConf()
        movies_path = conf.get_config('DLT', 'movies')
        usage = shutil.disk_usage(movies_path)
        free_percent = (usage.free / usage.total) * 100
        
        if free_percent < 5:
            health_status['checks']['disk'] = 'critical'
            health_status['status'] = 'unhealthy'
        elif free_percent < 10:
            health_status['checks']['disk'] = 'warning'
            health_status['status'] = 'degraded'
        else:
            health_status['checks']['disk'] = 'ok'
        
        health_status['checks']['disk_free_percent'] = round(free_percent, 2)
    except Exception as e:
        health_status['checks']['disk'] = 'fail'
        health_status['status'] = 'degraded'
        write_log(f"Healthcheck disk fail: {e}", "WARNING")
    
    # 4. Vérifier libtorrent session
    try:
        from static.Controleur.ControleurLibtorrent import get_session
        session = get_session()
        if session:
            health_status['checks']['libtorrent'] = 'ok'
        else:
            health_status['checks']['libtorrent'] = 'fail'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['libtorrent'] = 'fail'
        health_status['status'] = 'degraded'
        write_log(f"Healthcheck libtorrent fail: {e}", "WARNING")
    
    # Déterminer le code de statut HTTP
    if health_status['status'] == 'healthy':
        status_code = 200
    elif health_status['status'] == 'degraded':
        status_code = 200  # Dégradé mais fonctionnel
    else:
        status_code = 503  # Service unavailable
    
    return jsonify(health_status), status_code
