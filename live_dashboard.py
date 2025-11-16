"""
Real-Time LLM Security Testing Dashboard
Flask + Socket.IO for live updates
Port: 5000 (http://localhost:5000)
Version: 2.0 - Enhanced with prompt display
FIXED: Removed broadcast parameter, added v2 route
"""
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
import logging

# Disable Flask logging for cleaner output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'llm-security-framework-2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state - shared with main_orchestrator
stats = {
    'total_tests': 0,
    'successful_jailbreaks': 0,
    'blocked_attacks': 0,
    'current_model': None,
    'start_time': None
}


@app.route('/')
def index():
    """Main dashboard page (original version)"""
    return render_template('dashboard.html')


@app.route('/v2')
def index_v2():
    """Enhanced dashboard v2 with prompt display"""
    return render_template('dashboard_v2.html')


@app.route('/api/stats')
def get_stats():
    """Get current statistics - REST API endpoint"""
    return jsonify(stats)


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0',
        'uptime': datetime.now().isoformat(),
        'active_tests': stats['total_tests']
    })


@socketio.on('connect')
def handle_connect():
    """
    Client connected to WebSocket
    Send initial stats on connection
    """
    print(f'[DASHBOARD] Client connected: {datetime.now().strftime("%H:%M:%S")}')
    emit('status', {'message': 'Connected to live dashboard', 'version': '2.0'})
    emit('stats_update', stats)


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected from WebSocket"""
    print(f'[DASHBOARD] Client disconnected: {datetime.now().strftime("%H:%M:%S")}')


@socketio.on('ping')
def handle_ping():
    """Handle ping from client for keep-alive"""
    emit('pong', {'timestamp': datetime.now().isoformat()})


def broadcast_test_update(test_data):
    """
    Broadcast test update to all connected clients
    FIXED: Use namespace='/' instead of broadcast=True
    
    Args:
        test_data (dict): Dictionary containing:
            - name (str): Test name
            - prompt (str): Attack prompt text (NEW in v2)
            - success (bool): Whether attack succeeded
            - confidence (float): Confidence score (0-1)
            - severity (str): Severity level (LOW/MEDIUM/HIGH/CRITICAL)
            - response (str): Model response text
    """
    socketio.emit('test_update', test_data, namespace='/')


def broadcast_stats_update():
    """
    Broadcast statistics update to all connected clients
    FIXED: Use namespace='/' instead of broadcast=True
    """
    socketio.emit('stats_update', stats, namespace='/')


def reset_stats():
    """Reset all statistics (useful for new test runs)"""
    global stats
    stats = {
        'total_tests': 0,
        'successful_jailbreaks': 0,
        'blocked_attacks': 0,
        'current_model': None,
        'start_time': datetime.now().isoformat()
    }
    broadcast_stats_update()


def start_dashboard_server():
    """
    Start Flask dashboard in background thread
    Runs on http://0.0.0.0:5000 (accessible from network)
    """
    print("\n" + "="*70)
    print("🌐 LIVE DASHBOARD STARTING")
    print("="*70)
    print(f"  Version: 2.0 (Enhanced)")
    print(f"  Main URL: http://localhost:5000")
    print(f"  Enhanced: http://localhost:5000/v2")
    print(f"  API Stats: http://localhost:5000/api/stats")
    print(f"  Health: http://localhost:5000/api/health")
    print(f"  Status: Waiting for tests...")
    print("="*70 + "\n")
    
    socketio.run(
        app, 
        host='0.0.0.0',  # Accessible from network
        port=5000, 
        debug=False, 
        allow_unsafe_werkzeug=True, 
        log_output=False  # Suppress werkzeug logs
    )


if __name__ == '__main__':
    # Standalone mode - start dashboard without orchestrator
    print("\n" + "="*70)
    print("🔒 LLM SECURITY DASHBOARD - STANDALONE MODE")
    print("="*70)
    print("  This is the dashboard server only.")
    print("  To run full framework with tests:")
    print("  py -3.13 main_orchestrator_DASHBOARD_v2.py --models gemma3 --attacks 20")
    print("="*70 + "\n")
    start_dashboard_server()
