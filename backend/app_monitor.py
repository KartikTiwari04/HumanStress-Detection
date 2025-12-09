import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

class ApplicationMonitor:
    def __init__(self, db_path: str = "stress_data.db"):
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.create_app_tables()
        self.current_app = None
        self.app_start_time = None
        self.app_stress_data = {}
        
    def create_app_tables(self):
        cursor = self.db.cursor()
        
        # Applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                app_id TEXT PRIMARY KEY,
                app_name TEXT,
                process_name TEXT,
                category TEXT,
                is_productivity BOOLEAN DEFAULT 1
            )
        ''')
        
        # App usage with stress correlation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_usage_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                app_id TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration INTEGER,
                avg_stress_level INTEGER,
                max_stress_level INTEGER,
                key_presses INTEGER,
                mouse_moves INTEGER,
                clicks INTEGER,
                FOREIGN KEY (app_id) REFERENCES applications (app_id)
            )
        ''')
        
        self.db.commit()
        
        # Insert common applications
        self.initialize_default_apps()
    
    def initialize_default_apps(self):
        cursor = self.db.cursor()
        
        default_apps = [
            ('chrome', 'Google Chrome', 'chrome', 'browser', 0),
            ('firefox', 'Mozilla Firefox', 'firefox', 'browser', 0),
            ('safari', 'Safari', 'safari', 'browser', 0),
            ('slack', 'Slack', 'slack', 'communication', 1),
            ('teams', 'Microsoft Teams', 'teams', 'communication', 1),
            ('outlook', 'Microsoft Outlook', 'outlook', 'email', 1),
            ('gmail', 'Gmail Web', 'chrome', 'email', 1),
            ('vscode', 'Visual Studio Code', 'code', 'development', 1),
            ('excel', 'Microsoft Excel', 'excel', 'productivity', 1),
            ('word', 'Microsoft Word', 'word', 'productivity', 1),
            ('spotify', 'Spotify', 'spotify', 'entertainment', 0),
            ('terminal', 'Terminal/CMD', 'terminal', 'development', 1),
            ('finder', 'Finder/Explorer', 'finder', 'system', 0),
            ('zoom', 'Zoom', 'zoom', 'communication', 1),
            ('notion', 'Notion', 'notion', 'productivity', 1)
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO applications (app_id, app_name, process_name, category, is_productivity)
            VALUES (?, ?, ?, ?, ?)
        ''', default_apps)
        
        self.db.commit()
    
    def get_active_application(self) -> Optional[Dict]:
        """Get currently active application/process"""
        try:
            # For demo purposes, return a simulated app
            # In production, you'd use platform-specific code
            import random
            demo_apps = [
                {'app_id': 'chrome', 'app_name': 'Google Chrome', 'category': 'browser', 'is_productivity': 0},
                {'app_id': 'vscode', 'app_name': 'VS Code', 'category': 'development', 'is_productivity': 1},
                {'app_id': 'slack', 'app_name': 'Slack', 'category': 'communication', 'is_productivity': 1},
                {'app_id': 'terminal', 'app_name': 'Terminal', 'category': 'development', 'is_productivity': 1},
                {'app_id': 'finder', 'app_name': 'Finder', 'category': 'system', 'is_productivity': 0}
            ]
            return random.choice(demo_apps)
            
        except Exception as e:
            print(f"Error getting active app: {e}")
            return {
                'app_id': 'unknown',
                'app_name': 'Unknown Application',
                'category': 'unknown',
                'is_productivity': 0,
                'process_name': 'unknown'
            }
    
    def track_application_switch(self, stress_level: int = 0):
        """Track when user switches applications"""
        current_app = self.get_active_application()
        
        if not current_app:
            return None
        
        app_id = current_app['app_id']
        
        # Check if app changed
        if self.current_app != app_id:
            # Save previous app session
            if self.current_app and self.app_start_time:
                self.save_app_session(self.current_app)
            
            # Start new session
            self.current_app = app_id
            self.app_start_time = datetime.now()
            self.app_stress_data[app_id] = {
                'stress_levels': [],
                'key_presses': 0,
                'mouse_moves': 0,
                'clicks': 0
            }
            
            print(f"Switched to: {current_app['app_name']}")
            return current_app
        
        # Update current app stats
        if app_id in self.app_stress_data:
            self.app_stress_data[app_id]['stress_levels'].append(stress_level)
        
        return current_app
    
    def save_app_session(self, app_id: str):
        """Save completed application session"""
        if app_id not in self.app_stress_data:
            return
        
        data = self.app_stress_data[app_id]
        if not data['stress_levels']:
            return
        
        cursor = self.db.cursor()
        
        avg_stress = sum(data['stress_levels']) / len(data['stress_levels'])
        max_stress = max(data['stress_levels']) if data['stress_levels'] else 0
        
        cursor.execute('''
            INSERT INTO app_usage_sessions 
            (user_id, app_id, start_time, end_time, duration, avg_stress_level, 
             max_stress_level, key_presses, mouse_moves, clicks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'anonymous',
            app_id,
            self.app_start_time.isoformat(),
            datetime.now().isoformat(),
            int((datetime.now() - self.app_start_time).total_seconds()),
            avg_stress,
            max_stress,
            data['key_presses'],
            data['mouse_moves'],
            data['clicks']
        ))
        
        self.db.commit()
        
        # Clear data for this app
        self.app_stress_data[app_id] = {
            'stress_levels': [],
            'key_presses': 0,
            'mouse_moves': 0,
            'clicks': 0
        }
    
    def update_app_interaction(self, interaction_type: str, count: int = 1):
        """Update interaction counts for current app"""
        if not self.current_app:
            return
        
        if self.current_app not in self.app_stress_data:
            self.app_stress_data[self.current_app] = {
                'stress_levels': [],
                'key_presses': 0,
                'mouse_moves': 0,
                'clicks': 0
            }
        
        if interaction_type == 'key_press':
            self.app_stress_data[self.current_app]['key_presses'] += count
        elif interaction_type == 'mouse_move':
            self.app_stress_data[self.current_app]['mouse_moves'] += count
        elif interaction_type == 'click':
            self.app_stress_data[self.current_app]['clicks'] += count
    
    def get_app_analytics(self, limit: int = 10) -> List[Dict]:
        """Get application analytics"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                a.app_name,
                a.category,
                COUNT(DISTINCT s.session_id) as session_count,
                AVG(s.avg_stress_level) as avg_stress,
                MAX(s.max_stress_level) as max_stress,
                SUM(s.duration) as total_time,
                SUM(s.key_presses) as total_keys,
                SUM(s.clicks) as total_clicks
            FROM app_usage_sessions s
            JOIN applications a ON s.app_id = a.app_id
            GROUP BY a.app_id
            ORDER BY total_time DESC
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            result = dict(zip(columns, row))
            # Calculate stress score (0-100)
            result['stress_score'] = int(result['avg_stress'] * 25)  # Convert 0-4 to 0-100
            
            # Determine stress category
            if result['avg_stress'] < 1.5:
                result['stress_category'] = 'low'
            elif result['avg_stress'] < 2.5:
                result['stress_category'] = 'moderate'
            elif result['avg_stress'] < 3.5:
                result['stress_category'] = 'high'
            else:
                result['stress_category'] = 'very_high'
            
            results.append(result)
        
        return results
    
    def get_most_stressful_apps(self, limit: int = 5):
        """Get most stressful applications"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                a.app_name,
                a.category,
                AVG(s.avg_stress_level) as avg_stress,
                COUNT(*) as usage_count
            FROM app_usage_sessions s
            JOIN applications a ON s.app_id = a.app_id
            GROUP BY a.app_id
            HAVING usage_count >= 3
            ORDER BY avg_stress DESC
            LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()