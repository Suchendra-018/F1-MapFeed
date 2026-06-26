from flask import Flask, jsonify, render_template, request
from flask_login import LoginManager, current_user
import os
import json
import numpy as np
from session_loader import load_session, get_events, get_available_years
from session_analytics import build_session_overview, driver_directory, json_safe
from telemetry import get_fastest_lap_telemetry, get_fastest_lap
from analytics import get_driver_stats, get_sector_analysis, get_throttle_brake_zones
from comparison import build_comparison
from models import db, User
from auth import auth_bp
from history import history_bp

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(project_root, 'templates'),
    static_folder=os.path.join(project_root, 'static')
)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

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
    return render_template('platform.html')


@app.route('/api/years')
def get_years():
    return jsonify(get_available_years())


@app.route('/api/events/<int:year>')
def get_session_events(year):
    try:
        return jsonify(get_events(year))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sessions/<int:year>/<int:round_number>')
def get_session_types(year, round_number):
    try:
        event = next(event for event in get_events(year) if event["round"] == round_number)
        # Qualifying and Race have the most complete, consistent FastF1 timing
        # coverage. Other session types are intentionally out of scope.
        available = [{"code": "Q", "name": "Qualifying"}, {"code": "R", "name": "Race"}]
        return jsonify({"event": event, "sessions": available})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/drivers/<year>/<race>/<session_type>')
def get_drivers(year, race, session_type):
    """Get available drivers for a session"""
    try:
        session = load_session(int(year), race, session_type)

        return jsonify(driver_directory(session))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/session-overview', methods=['POST'])
def session_overview():
    try:
        data = request.get_json()
        session = load_session(int(data['year']), data['race'], data['session'])
        return jsonify(json_safe(build_session_overview(session)))
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
        session = load_session(year, race, session_type, telemetry=True)
        telemetry = get_fastest_lap_telemetry(session, driver_code)
        lap = get_fastest_lap(session, driver_code)
        
        # Generate analysis
        stats = get_driver_stats(telemetry)
        sectors = get_sector_analysis(lap)
        throttle_brake = get_throttle_brake_zones(telemetry)
        
        # Browser-native Plotly figures replace shared PNG files.  Shared files
        # were prone to requests overwriting each other's analysis output.
        chart_layout = {"template": "plotly_dark", "margin": {"l": 40, "r": 15, "t": 45, "b": 35}}
        speed_chart = {"data": [{"x": telemetry["Distance"].tolist(), "y": telemetry["Speed"].tolist(), "type": "scatter", "mode": "lines", "name": "Speed"}],
                       "layout": {**chart_layout, "title": "Speed trace", "xaxis": {"title": "Distance (m)"}, "yaxis": {"title": "Speed (km/h)"}}}
        throttle_chart = {
            "data": [{"x": telemetry["Distance"].tolist(), "y": telemetry["Throttle"].tolist(), "type": "scatter", "mode": "lines", "name": "Throttle"}],
            "layout": {**chart_layout, "title": "Throttle trace", "xaxis": {"title": "Distance (m)"}, "yaxis": {"title": "Throttle (%)", "range": [0, 100]}},
        }
        brake_values = (telemetry["Brake"].astype(int) * 100).tolist() if "Brake" in telemetry else []
        brake_chart = {
            "data": [{"x": telemetry["Distance"].tolist(), "y": brake_values, "type": "scatter", "mode": "lines", "name": "Brake"}],
            "layout": {**chart_layout, "title": "Brake trace", "xaxis": {"title": "Distance (m)"}, "yaxis": {"title": "Brake (%)", "range": [0, 100]}},
        }
        track_chart = {
            "data": [{"x": telemetry["X"].tolist(), "y": telemetry["Y"].tolist(), "type": "scatter", "mode": "markers", "marker": {"size": 4, "color": telemetry["Speed"].tolist(), "colorscale": "Turbo", "colorbar": {"title": "km/h"}}, "name": "Track speed"}],
            "layout": {**chart_layout, "title": "Track map · speed overlay", "xaxis": {"visible": False}, "yaxis": {"visible": False, "scaleanchor": "x", "scaleratio": 1}},
        }
        
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
            "charts": {"speed": speed_chart, "throttle": throttle_chart, "brake": brake_chart, "track": track_chart}
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
        
        return jsonify(json_safe(result))
    
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
        if not isinstance(drivers, list) or len(drivers) != 2:
            return jsonify({"error": "Select exactly two drivers to compare."}), 400
        
        # Load session
        session = load_session(year, race, session_type, telemetry=True)
        
        return jsonify(build_comparison(session, drivers))
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
