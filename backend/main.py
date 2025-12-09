from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import uuid
import json
import asyncio
from typing import Dict, List, Any
import uvicorn

# Import our modules
from data_processing import DataProcessor
from stress_model import StressPredictor
from database import StressDatabase
from app_monitor import ApplicationMonitor
from wellness_tracker import WellnessTracker

# Initialize FastAPI app
app = FastAPI(
    title="Human Stress Detection API",
    description="Real-time stress level detection using keyboard and mouse patterns",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
print("Initializing Stress Detection System...")
db = StressDatabase()
data_processor = DataProcessor()
stress_predictor = StressPredictor()
app_monitor = ApplicationMonitor()
wellness_tracker = WellnessTracker()

print("✅ Database initialized")
print("✅ Stress predictor model loaded")
print("✅ Application monitor started")
print("✅ Wellness tracker ready")

# Store active sessions and WebSocket connections
active_sessions: Dict[str, Dict] = {}
active_connections: Dict[str, WebSocket] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Human Stress Detection API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "keyboard_pattern_tracking",
            "mouse_movement_analysis", 
            "stress_level_prediction",
            "application_specific_tracking",
            "wellness_recommendations"
        ],
        "endpoints": {
            "websocket": "/ws/track",
            "api_docs": "/api/docs",
            "history": "/api/history/{user_id}",
            "app_analytics": "/api/apps/analytics",
            "wellness": "/api/wellness/recommendations"
        }
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": "connected",
            "model": "loaded",
            "app_monitor": "running",
            "wellness_tracker": "active"
        }
    }

# WebSocket endpoint for real-time tracking
@app.websocket("/ws/track")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Create new session
    session_id = str(uuid.uuid4())
    user_id = "anonymous"
    
    # Initialize session data
    session_data = {
        'session_id': session_id,
        'user_id': user_id,
        'websocket': websocket,
        'start_time': datetime.now(),
        'key_events': [],
        'mouse_events': [],
        'last_prediction_time': datetime.now(),
        'last_app_check': datetime.now(),
        'current_app': None
    }
    
    active_sessions[session_id] = session_data
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "message": "Connected to Stress Detection System",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Receive data from client
            data = await websocket.receive_text()
            
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                continue
            
            # Add timestamp and session ID
            event['timestamp'] = datetime.now().isoformat()
            event['session_id'] = session_id
            
            # Store event based on type
            if event['type'] == 'keyboard':
                session_data['key_events'].append(event)
                db.save_keyboard_event(event)
                
                # Update app monitor with key press
                app_monitor.update_app_interaction('key_press')
                
            elif event['type'] == 'mouse':
                session_data['mouse_events'].append(event)
                db.save_mouse_event(event)
                
                # Update app monitor based on mouse event type
                if event.get('eventType') == 'click':
                    app_monitor.update_app_interaction('click')
                elif event.get('eventType') == 'move':
                    app_monitor.update_app_interaction('mouse_move')
                    
            elif event['type'] == 'wellness_feedback':
                # Handle wellness feedback from client
                wellness_tracker.record_feedback(event.get('feedback', {}))
                continue
            else:
                # Unknown event type
                continue
            
            # Check if it's time to make a prediction (every 30 seconds)
            current_time = datetime.now()
            prediction_time_diff = (current_time - session_data['last_prediction_time']).total_seconds()
            
            # Check application every 5 seconds
            app_check_diff = (current_time - session_data['last_app_check']).total_seconds()
            if app_check_diff >= 5:
                current_app = app_monitor.track_application_switch()
                if current_app and current_app != session_data['current_app']:
                    session_data['current_app'] = current_app
                    # Send app update to client
                    await websocket.send_json({
                        'type': 'app_update',
                        'current_app': current_app,
                        'timestamp': current_time.isoformat()
                    })
                session_data['last_app_check'] = current_time
            
            # Make prediction if we have enough data and 30 seconds have passed
            if prediction_time_diff >= 30 and len(session_data['key_events']) > 10:
                try:
                    # Process data and make prediction
                    features = data_processor.extract_features(
                        session_data['key_events'][-100:],
                        session_data['mouse_events'][-100:]
                    )
                    
                    prediction = stress_predictor.predict_stress(features)
                    
                    # Save prediction to database
                    prediction_data = {
                        'session_id': session_id,
                        'timestamp': current_time.isoformat(),
                        'typing_speed_avg': features['typing_speed'],
                        'mouse_randomness': features['mouse_randomness'],
                        'click_frequency': features['click_frequency'],
                        'backspace_ratio': features['backspace_ratio'],
                        'predicted_stress': prediction['stress_level'],
                        'confidence': prediction['confidence']
                    }
                    
                    db.save_stress_prediction(prediction_data)
                    
                    # Update last prediction time
                    session_data['last_prediction_time'] = current_time
                    
                    # Update wellness tracker with new stress data
                    app_context = session_data['current_app']['app_name'] if session_data['current_app'] else 'unknown'
                    wellness_recommendations = wellness_tracker.update_stress_data(
                        prediction['level_index'],
                        prediction['confidence'],
                        app_context
                    )
                    
                    # Send prediction to client
                    await websocket.send_json({
                        'type': 'prediction',
                        'prediction': prediction,
                        'features': features,
                        'timestamp': current_time.isoformat(),
                        'session_id': session_id
                    })
                    
                    # Send wellness recommendations if any
                    if wellness_recommendations:
                        await websocket.send_json({
                            'type': 'wellness_recommendations',
                            'recommendations': wellness_recommendations,
                            'timestamp': current_time.isoformat()
                        })
                    
                    # Send app analytics every 3 predictions (every 1.5 minutes)
                    prediction_count = len([p for p in session_data.values() if isinstance(p, dict) and 'prediction' in p])
                    if prediction_count % 3 == 0:
                        app_analytics = app_monitor.get_app_analytics(5)
                        await websocket.send_json({
                            'type': 'app_analytics',
                            'analytics': app_analytics,
                            'timestamp': current_time.isoformat()
                        })
                        
                except Exception as e:
                    print(f"Prediction error: {e}")
                    await websocket.send_json({
                        'type': 'error',
                        'message': f"Prediction failed: {str(e)}",
                        'timestamp': current_time.isoformat()
                    })
            
            # Send heartbeat every 10 seconds
            if int(current_time.timestamp()) % 10 == 0:
                await websocket.send_json({
                    'type': 'heartbeat',
                    'timestamp': current_time.isoformat(),
                    'session_stats': {
                        'key_events': len(session_data['key_events']),
                        'mouse_events': len(session_data['mouse_events']),
                        'session_duration': int((current_time - session_data['start_time']).total_seconds())
                    }
                })
            
    except WebSocketDisconnect:
        # Handle disconnection
        print(f"Client disconnected: {session_id}")
        manager.disconnect(websocket)
        
        if session_id in active_sessions:
            # Calculate final statistics
            session_info = active_sessions[session_id]
            end_time = datetime.now()
            duration = (end_time - session_info['start_time']).total_seconds()
            
            # Save final app session if any
            if session_info['current_app']:
                app_monitor.save_app_session(session_info['current_app']['app_id'])
            
            # Save session to database
            db.save_session({
                'session_id': session_id,
                'user_id': user_id,
                'start_time': session_info['start_time'].isoformat(),
                'end_time': end_time.isoformat(),
                'duration': duration,
                'stress_level': 'Unknown',
                'confidence': 0
            })
            
            # Generate session report
            try:
                session_stats = {
                    'total_key_events': len(session_info['key_events']),
                    'total_mouse_events': len(session_info['mouse_events']),
                    'session_duration': f"{duration:.1f} seconds",
                    'average_typing_speed': data_processor.calculate_typing_speed(session_info['key_events']) if session_info['key_events'] else 0,
                    'applications_used': list(set([app['app_name'] for app in session_info.values() if isinstance(app, dict) and 'app_name' in app])) if session_info['current_app'] else []
                }
                
                print(f"Session {session_id} ended. Stats: {session_stats}")
                
            except Exception as e:
                print(f"Error generating session report: {e}")
            
            # Remove from active sessions
            del active_sessions[session_id]
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
        if session_id in active_sessions:
            del active_sessions[session_id]

# API Endpoints

@app.get("/api/history/{user_id}")
async def get_history(user_id: str, limit: int = 10):
    """Get stress history for a user"""
    try:
        sessions = db.get_session_history(user_id, limit)
        return JSONResponse({
            "user_id": user_id,
            "sessions": sessions,
            "count": len(sessions)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@app.get("/api/stats/{session_id}")
async def get_session_stats(session_id: str):
    """Get detailed statistics for a session"""
    try:
        # Get session data from database
        cursor = db.conn.cursor()
        
        # Get session info
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get keyboard stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_keys,
                AVG(press_duration) as avg_press_duration,
                AVG(typing_speed) as avg_typing_speed,
                SUM(backspace_count) as total_backspaces
            FROM keyboard_events 
            WHERE session_id = ?
        ''', (session_id,))
        keyboard_stats = cursor.fetchone()
        
        # Get mouse stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_moves,
                AVG(movement_speed) as avg_movement_speed,
                SUM(movement_distance) as total_distance,
                COUNT(CASE WHEN click_type IS NOT NULL THEN 1 END) as total_clicks
            FROM mouse_events 
            WHERE session_id = ?
        ''', (session_id,))
        mouse_stats = cursor.fetchone()
        
        # Get stress predictions
        cursor.execute('''
            SELECT 
                COUNT(*) as prediction_count,
                AVG(typing_speed_avg) as avg_typing_speed,
                AVG(mouse_randomness) as avg_mouse_randomness,
                AVG(click_frequency) as avg_click_frequency,
                AVG(backspace_ratio) as avg_backspace_ratio,
                AVG(confidence) as avg_confidence
            FROM stress_predictions 
            WHERE session_id = ?
        ''', (session_id,))
        prediction_stats = cursor.fetchone()
        
        columns = [desc[0] for desc in cursor.description]
        
        return JSONResponse({
            "session_id": session_id,
            "keyboard_stats": {
                "total_keys": keyboard_stats[0] if keyboard_stats else 0,
                "avg_press_duration": round(keyboard_stats[1], 3) if keyboard_stats and keyboard_stats[1] else 0,
                "avg_typing_speed": round(keyboard_stats[2], 1) if keyboard_stats and keyboard_stats[2] else 0,
                "total_backspaces": keyboard_stats[3] if keyboard_stats else 0
            },
            "mouse_stats": {
                "total_moves": mouse_stats[0] if mouse_stats else 0,
                "avg_movement_speed": round(mouse_stats[1], 1) if mouse_stats and mouse_stats[1] else 0,
                "total_distance": round(mouse_stats[2], 1) if mouse_stats and mouse_stats[2] else 0,
                "total_clicks": mouse_stats[3] if mouse_stats else 0
            },
            "stress_stats": {
                "prediction_count": prediction_stats[0] if prediction_stats else 0,
                "avg_typing_speed": round(prediction_stats[1], 1) if prediction_stats and prediction_stats[1] else 0,
                "avg_mouse_randomness": round(prediction_stats[2], 3) if prediction_stats and prediction_stats[2] else 0,
                "avg_click_frequency": round(prediction_stats[3], 1) if prediction_stats and prediction_stats[3] else 0,
                "avg_backspace_ratio": round(prediction_stats[4] * 100, 1) if prediction_stats and prediction_stats[4] else 0,
                "avg_confidence": round(prediction_stats[5] * 100, 1) if prediction_stats and prediction_stats[5] else 0
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session stats: {str(e)}")

@app.get("/api/apps/analytics")
async def get_app_analytics(limit: int = 10, hours: int = 24):
    """Get application analytics"""
    try:
        analytics = app_monitor.get_app_analytics(limit)
        
        # Get most stressful apps
        stressful_apps = app_monitor.get_most_stressful_apps(5)
        
        return JSONResponse({
            "analytics": analytics,
            "most_stressful_apps": [
                {
                    "app_name": app[0],
                    "category": app[1],
                    "avg_stress": round(app[2], 2),
                    "usage_count": app[3]
                }
                for app in stressful_apps
            ],
            "time_range": f"Last {hours} hours"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching app analytics: {str(e)}")

@app.get("/api/apps/stress-trends/{app_id}")
async def get_app_stress_trends(app_id: str, hours: int = 24):
    """Get stress trends for specific application"""
    try:
        trends = app_monitor.get_app_stress_trends(app_id, hours)
        
        return JSONResponse({
            "app_id": app_id,
            "trends": [
                {
                    "hour": trend[0],
                    "avg_stress": round(trend[1], 2),
                    "session_count": trend[2]
                }
                for trend in trends
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stress trends: {str(e)}")

@app.get("/api/wellness/recommendations")
async def get_wellness_recommendations(limit: int = 5):
    """Get wellness recommendations"""
    try:
        recommendations = wellness_tracker.get_recommendations(limit)
        
        # Get wellness stats
        stats = wellness_tracker.get_wellness_stats()
        
        return JSONResponse({
            "recommendations": recommendations,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {str(e)}")

@app.post("/api/wellness/feedback")
async def submit_wellness_feedback(feedback: dict):
    """Submit feedback on wellness recommendations"""
    try:
        wellness_tracker.record_feedback(feedback)
        return JSONResponse({
            "status": "success",
            "message": "Feedback recorded successfully",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}")

@app.get("/api/wellness/stats")
async def get_wellness_statistics(days: int = 7):
    """Get wellness statistics"""
    try:
        stats = wellness_tracker.get_wellness_stats()
        
        # Add additional stats
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT 
                date(timestamp) as date,
                AVG(confidence) as avg_confidence,
                COUNT(*) as prediction_count
            FROM stress_predictions
            WHERE timestamp >= date('now', ? || ' days')
            GROUP BY date(timestamp)
            ORDER BY date
        ''', (f'-{days}',))
        
        daily_stats = cursor.fetchall()
        
        return JSONResponse({
            "wellness_stats": stats,
            "daily_stress_trends": [
                {
                    "date": day[0],
                    "avg_confidence": round(day[1] * 100, 1) if day[1] else 0,
                    "prediction_count": day[2]
                }
                for day in daily_stats
            ],
            "time_period": f"{days} days"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching wellness stats: {str(e)}")

@app.get("/api/system/stats")
async def get_system_statistics():
    """Get overall system statistics"""
    try:
        cursor = db.conn.cursor()
        
        # Total sessions
        cursor.execute('SELECT COUNT(*) FROM sessions')
        total_sessions = cursor.fetchone()[0]
        
        # Today's sessions
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE date(start_time) = date('now')")
        today_sessions = cursor.fetchone()[0]
        
        # Total predictions
        cursor.execute('SELECT COUNT(*) FROM stress_predictions')
        total_predictions = cursor.fetchone()[0]
        
        # Active sessions
        active_session_count = len(active_sessions)
        
        # Average stress level
        cursor.execute('SELECT AVG(confidence) FROM stress_predictions')
        avg_confidence = cursor.fetchone()[0] or 0
        
        # Most common stress level
        cursor.execute('''
            SELECT predicted_stress, COUNT(*) as count
            FROM stress_predictions
            GROUP BY predicted_stress
            ORDER BY count DESC
            LIMIT 1
        ''')
        most_common_stress = cursor.fetchone()
        
        return JSONResponse({
            "system": {
                "total_sessions": total_sessions,
                "active_sessions": active_session_count,
                "today_sessions": today_sessions,
                "total_predictions": total_predictions,
                "avg_confidence": f"{round(avg_confidence * 100, 1)}%",
                "most_common_stress": most_common_stress[0] if most_common_stress else "Unknown",
                "uptime": "Running"  # Could add actual uptime calculation
            },
            "active_features": {
                "keyboard_tracking": True,
                "mouse_tracking": True,
                "app_monitoring": True,
                "wellness_tracking": True,
                "real_time_predictions": True
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching system stats: {str(e)}")

@app.get("/api/sessions/active")
async def get_active_sessions():
    """Get list of active sessions"""
    try:
        sessions = []
        for session_id, session_data in active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "user_id": session_data['user_id'],
                "start_time": session_data['start_time'].isoformat(),
                "duration": int((datetime.now() - session_data['start_time']).total_seconds()),
                "key_events": len(session_data['key_events']),
                "mouse_events": len(session_data['mouse_events']),
                "current_app": session_data['current_app']['app_name'] if session_data['current_app'] else None
            })
        
        return JSONResponse({
            "active_sessions": sessions,
            "count": len(sessions),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching active sessions: {str(e)}")

@app.get("/api/export/session/{session_id}")
async def export_session_data(session_id: str, format: str = "json"):
    """Export session data in specified format"""
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        # Get session data
        cursor = db.conn.cursor()
        
        # Session info
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        session_info = cursor.fetchone()
        
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Keyboard events
        cursor.execute('SELECT * FROM keyboard_events WHERE session_id = ? ORDER BY timestamp', (session_id,))
        keyboard_events = cursor.fetchall()
        
        # Mouse events
        cursor.execute('SELECT * FROM mouse_events WHERE session_id = ? ORDER BY timestamp', (session_id,))
        mouse_events = cursor.fetchall()
        
        # Stress predictions
        cursor.execute('SELECT * FROM stress_predictions WHERE session_id = ? ORDER BY timestamp', (session_id,))
        stress_predictions = cursor.fetchall()
        
        if format == "json":
            # Get column names
            cursor.execute('PRAGMA table_info(sessions)')
            session_columns = [col[1] for col in cursor.fetchall()]
            
            cursor.execute('PRAGMA table_info(keyboard_events)')
            keyboard_columns = [col[1] for col in cursor.fetchall()]
            
            cursor.execute('PRAGMA table_info(mouse_events)')
            mouse_columns = [col[1] for col in cursor.fetchall()]
            
            cursor.execute('PRAGMA table_info(stress_predictions)')
            prediction_columns = [col[1] for col in cursor.fetchall()]
            
            # Build JSON response
            data = {
                "session_info": dict(zip(session_columns, session_info)),
                "keyboard_events": [dict(zip(keyboard_columns, event)) for event in keyboard_events],
                "mouse_events": [dict(zip(mouse_columns, event)) for event in mouse_events],
                "stress_predictions": [dict(zip(prediction_columns, prediction)) for prediction in stress_predictions],
                "summary": {
                    "total_keyboard_events": len(keyboard_events),
                    "total_mouse_events": len(mouse_events),
                    "total_predictions": len(stress_predictions),
                    "export_time": datetime.now().isoformat()
                }
            }
            
            return JSONResponse(data)
        
        elif format == "csv":
            # For CSV, you'd generate and return a file
            # This is a simplified version - in production you'd use a proper CSV library
            csv_data = f"Session ID: {session_id}\n"
            csv_data += f"Export Time: {datetime.now().isoformat()}\n\n"
            
            csv_data += "Stress Predictions:\n"
            csv_data += "Timestamp,Typing Speed,Mouse Randomness,Click Frequency,Backspace Ratio,Predicted Stress,Confidence\n"
            for pred in stress_predictions:
                csv_data += f"{pred[2]},{pred[3]},{pred[4]},{pred[5]},{pred[6]},{pred[7]},{pred[8]}\n"
            
            return JSONResponse({
                "csv_data": csv_data,
                "message": "CSV format requested - data prepared"
            })
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting session data: {str(e)}")

# Error handlers
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found", "path": request.url.path}
    )

@app.exception_handler(500)
async def internal_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    print("🚀 Stress Detection System starting up...")
    print(f"📊 System initialized at {datetime.now()}")
    print(f"🔗 WebSocket endpoint available at: ws://localhost:8000/ws/track")
    print(f"📚 API documentation available at: http://localhost:8000/api/docs")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Stress Detection System shutting down...")
    
    # Save all active app sessions
    for session_id, session_data in active_sessions.items():
        if session_data.get('current_app'):
            app_monitor.save_app_session(session_data['current_app']['app_id'])
    
    # Close database connections
    db.close()
    print("✅ All resources cleaned up")

# Run the application
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Human Stress Detection System")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    print(f"🌐 Starting server on {args.host}:{args.port}")
    print("💡 Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )