from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_login import LoginManager, login_required, current_user
import os
import json
import numpy as np
from session_loader import load_session
from telemetry import get_fastest_lap_telemetry, get_fastest_lap
from analytics import get_driver_stats, get_sector_analysis, get_throttle_brake_zones
from trackmap import create_track_map, create_speed_heatmap
from plotter import plot_speed_graph
from comparison import get_multiple_drivers_telemetry, compare_driver_speeds, plot_driver_comparison, get_race_pace_analysis
from models import db, User
from auth import auth_bp
from history import history_bp

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Custom JSON encoder for numpy/pandas types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

app = Flask(
    __name__,
    template_folder=os.path.join(project_root, 'templates'),
    static_folder=os.path.join(project_root, 'static')
)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
app.json_encoder = NumpyEncoder

# Database configuration
db_path = os.path.join(project_root, 'f1mapfeed.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'f1-mapfeed-secret-key-change-in-production'

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(history_bp)


@app.route('/')
def index():
    """Home page with session and driver selection"""
    return render_template('index.html')


@app.route('/api/sessions')
def get_sessions():
    """Return available F1 sessions"""
    # For now, hardcode some popular sessions
    sessions = [
        {"year": 2025, "race": "Monaco Grand Prix", "session": "R", "display": "Monaco 2025 - Race"},
        {"year": 2025, "race": "Monaco Grand Prix", "session": "Q", "display": "Monaco 2025 - Qualifying"},
        {"year": 2024, "race": "Silverstone Grand Prix", "session": "R", "display": "Silverstone 2024 - Race"},
    ]
    return jsonify(sessions)


@app.route('/api/drivers/<year>/<race>/<session_type>')
def get_drivers(year, race, session_type):
    """Get available drivers for a session"""
    try:
        session = load_session(int(year), race, session_type)
        drivers = session.drivers
        driver_list = [{"code": d, "name": session.get_driver(d).name} for d in drivers]
        return jsonify(driver_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/driver-analysis', methods=['POST'])
def analyze_driver():
    """Analyze single driver telemetry and generate plots"""
    try:
        data = request.json
        year = int(data['year'])
        race = data['race']
        session_type = data['session']
        driver_code = data['driver']
        
        # Load session and telemetry
        session = load_session(year, race, session_type)
        telemetry = get_fastest_lap_telemetry(session, driver_code)
        lap = get_fastest_lap(session, driver_code)
        
        # Generate analysis
        stats = get_driver_stats(telemetry)
        sectors = get_sector_analysis(lap)
        throttle_brake = get_throttle_brake_zones(telemetry)
        
        # Generate visualizations
        plot_speed_graph(telemetry)
        create_track_map(lap)
        create_speed_heatmap(lap, telemetry)
        
        # Format sector times
        sector_data = {}
        for sector, info in sectors.items():
            if info["time"]:
                sector_data[sector] = str(info["time"])
        
        # Convert numpy types to Python native types
        stats_converted = {}
        for k, v in stats.items():
            if isinstance(v, (np.integer, np.floating)):
                stats_converted[k] = float(v)
            else:
                stats_converted[k] = v
        
        throttle_brake_converted = {
            "full_throttle_points": int(throttle_brake['full_throttle_points']),
            "full_brake_points": int(throttle_brake['full_brake_points']),
            "throttle_percentage": float(throttle_brake['throttle_percentage'])
        }
        
        result = {
            "stats": {k: round(v, 2) if isinstance(v, float) else v for k, v in stats_converted.items()},
            "sectors": sector_data,
            "throttle_brake": throttle_brake_converted,
            "plots": {
                "speed_graph": "speed_graph.png",
                "track_map": "track_map.png",
                "speed_heatmap": "speed_heatmap.png"
            }
        }
        
        # Save analysis if requested
        if data.get('save'):
            from models import Analysis
            analysis = Analysis(
                user_id=current_user.id,
                year=year,
                race=race,
                session_type=session_type,
                analysis_type='single',
                drivers=driver_code,
                results=json.dumps(result),
                notes=data.get('notes', '')
            )
            db.session.add(analysis)
            db.session.commit()
            result['analysis_id'] = analysis.id
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/compare-drivers', methods=['POST'])
def compare_drivers():
    """Compare multiple drivers"""
    try:
        data = request.json
        year = int(data['year'])
        race = data['race']
        session_type = data['session']
        drivers = data['drivers']
        
        # Load session
        session = load_session(year, race, session_type)
        
        # Get telemetry for all drivers
        telemetry_dict = get_multiple_drivers_telemetry(session, drivers)
        
        # Get comparison stats
        speed_comparison = compare_driver_speeds(telemetry_dict)
        race_pace = get_race_pace_analysis(session, drivers)
        
        # Generate comparison plot
        if len(telemetry_dict) > 1:
            plot_driver_comparison(telemetry_dict)
        
        # Convert numpy types to Python native types
        speed_comparison_converted = {}
        for driver, stats in speed_comparison.items():
            speed_comparison_converted[driver] = {
                "max_speed": float(stats['max_speed']),
                "avg_speed": float(stats['avg_speed']),
                "consistency": float(stats['speed_std'])
            }
        
        race_pace_converted = {}
        for driver, stats in race_pace.items():
            race_pace_converted[driver] = {
                "avg_pace": float(stats['avg_pace']),
                "fastest_lap": float(stats['fastest_lap']),
                "consistency": float(stats['consistency'])
            }
        
        result = {
            "speed_comparison": {
                driver: {
                    "max_speed": round(stats['max_speed'], 1),
                    "avg_speed": round(stats['avg_speed'], 1),
                    "consistency": round(stats['consistency'], 2)
                }
                for driver, stats in speed_comparison_converted.items()
            },
            "race_pace": {
                driver: {
                    "avg_pace": round(stats['avg_pace'], 2),
                    "fastest_lap": round(stats['fastest_lap'], 2),
                    "consistency": round(stats['consistency'], 2)
                }
                for driver, stats in race_pace_converted.items()
            },
            "plots": {
                "comparison": "driver_comparison.png"
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/plots/<filename>')
def serve_plot(filename):
    """Serve plot images"""
    plots_dir = os.path.join(project_root, 'plots')
    return send_from_directory(plots_dir, filename)


if __name__ == '__main__':
    # Create plots directory if it doesn't exist
    os.makedirs(os.path.join(project_root, 'plots'), exist_ok=True)
    app.run(debug=True, port=5000)
