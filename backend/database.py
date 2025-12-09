import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any

class StressDatabase:
    def __init__(self, db_name: str = "stress_data.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration INTEGER,
                stress_level TEXT,
                confidence REAL
            )
        ''')
        
        # Keyboard events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keyboard_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TIMESTAMP,
                key_pressed TEXT,
                key_released TEXT,
                press_duration REAL,
                typing_speed REAL,
                backspace_count INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        # Mouse events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mouse_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TIMESTAMP,
                x INTEGER,
                y INTEGER,
                movement_distance REAL,
                movement_speed REAL,
                click_type TEXT,
                scroll_delta INTEGER,
                pressure REAL DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        # Stress predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stress_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TIMESTAMP,
                typing_speed_avg REAL,
                mouse_randomness REAL,
                click_frequency REAL,
                backspace_ratio REAL,
                predicted_stress TEXT,
                confidence REAL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        self.conn.commit()
    
    def save_session(self, session_data: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (session_id, user_id, start_time, end_time, duration, stress_level, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_data['session_id'],
            session_data.get('user_id', 'anonymous'),
            session_data['start_time'],
            session_data['end_time'],
            session_data['duration'],
            session_data['stress_level'],
            session_data['confidence']
        ))
        self.conn.commit()
    
    def save_keyboard_event(self, event_data: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO keyboard_events (session_id, timestamp, key_pressed, key_released, press_duration, typing_speed, backspace_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_data['session_id'],
            event_data['timestamp'],
            event_data.get('key_pressed'),
            event_data.get('key_released'),
            event_data.get('press_duration'),
            event_data.get('typing_speed'),
            event_data.get('backspace_count', 0)
        ))
        self.conn.commit()
    
    def save_mouse_event(self, event_data: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO mouse_events (session_id, timestamp, x, y, movement_distance, movement_speed, click_type, scroll_delta, pressure)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_data['session_id'],
            event_data['timestamp'],
            event_data['x'],
            event_data['y'],
            event_data.get('movement_distance', 0),
            event_data.get('movement_speed', 0),
            event_data.get('click_type'),
            event_data.get('scroll_delta', 0),
            event_data.get('pressure', 0)
        ))
        self.conn.commit()
    
    def save_stress_prediction(self, prediction_data: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO stress_predictions (session_id, timestamp, typing_speed_avg, mouse_randomness, click_frequency, backspace_ratio, predicted_stress, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prediction_data['session_id'],
            prediction_data['timestamp'],
            prediction_data['typing_speed_avg'],
            prediction_data['mouse_randomness'],
            prediction_data['click_frequency'],
            prediction_data['backspace_ratio'],
            prediction_data['predicted_stress'],
            prediction_data['confidence']
        ))
        self.conn.commit()
    
    def get_session_history(self, user_id: str = None, limit: int = 10):
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute('''
                SELECT * FROM sessions 
                WHERE user_id = ? 
                ORDER BY start_time DESC 
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM sessions 
                ORDER BY start_time DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        sessions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return sessions

    def close(self):
        self.conn.close()