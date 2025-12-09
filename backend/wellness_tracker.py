import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class WellnessTracker:
    def __init__(self, db_path: str = "stress_data.db"):
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.create_wellness_tables()
        self.last_recommendation_time = {}
        
    def create_wellness_tables(self):
        cursor = self.db.cursor()
        
        # Wellness recommendations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wellness_recommendations (
                recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp TIMESTAMP,
                stress_level INTEGER,
                app_context TEXT,
                recommendation_type TEXT,
                recommendation_text TEXT,
                duration_seconds INTEGER,
                accepted BOOLEAN DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                effectiveness INTEGER DEFAULT 0
            )
        ''')
        
        # Ergonomic feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ergonomic_feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp TIMESTAMP,
                issue_type TEXT,
                severity INTEGER,
                suggestion TEXT,
                acknowledged BOOLEAN DEFAULT 0
            )
        ''')
        
        # Wellness activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wellness_activities (
                activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp TIMESTAMP,
                activity_type TEXT,
                duration_seconds INTEGER,
                stress_before INTEGER,
                stress_after INTEGER,
                notes TEXT
            )
        ''')
        
        # Eye strain patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eye_strain_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds INTEGER,
                avg_typing_speed REAL,
                avg_mouse_randomness REAL,
                screen_time_minutes INTEGER,
                likely_eye_strain BOOLEAN
            )
        ''')
        
        self.db.commit()
    
    def update_stress_data(self, stress_level: int, confidence: float, app_context: str = ""):
        """Update wellness tracker with new stress data"""
        cursor = self.db.cursor()
        
        # Check for eye strain patterns
        self._check_eye_strain(stress_level, app_context)
        
        # Check for ergonomic issues
        self._check_ergonomic_issues(stress_level)
        
        # Generate recommendations if needed
        recommendations = self._generate_recommendations(stress_level, app_context)
        
        return recommendations
    
    def _check_eye_strain(self, stress_level: int, app_context: str):
        """Detect potential eye strain patterns"""
        cursor = self.db.cursor()
        
        # Check last hour of data
        cursor.execute('''
            SELECT 
                COUNT(*) as session_count,
                AVG(typing_speed_avg) as avg_typing,
                AVG(mouse_randomness) as avg_mouse_randomness
            FROM stress_predictions
            WHERE timestamp >= datetime('now', '-1 hour')
        ''')
        
        result = cursor.fetchone()
        
        if result and result[0] > 4:  # At least 4 readings in last hour
            avg_typing = result[1] or 0
            avg_mouse_randomness = result[2] or 0
            
            # Signs of eye strain
            visual_apps = ['chrome', 'firefox', 'safari', 'vscode', 'figma', 'photoshop']
            is_visual_app = any(app in app_context.lower() for app in visual_apps)
            
            likely_eye_strain = (
                is_visual_app and 
                stress_level >= 3 and 
                avg_mouse_randomness > 0.3
            )
            
            if likely_eye_strain:
                cursor.execute('''
                    INSERT INTO eye_strain_patterns 
                    (user_id, start_time, end_time, duration_seconds, 
                     avg_typing_speed, avg_mouse_randomness, screen_time_minutes, likely_eye_strain)
                    VALUES (?, datetime('now', '-1 hour'), datetime('now'), 3600, ?, ?, 60, ?)
                ''', ('anonymous', avg_typing, avg_mouse_randomness, 1))
                
                self.db.commit()
    
    def _check_ergonomic_issues(self, stress_level: int):
        """Check for potential ergonomic issues"""
        cursor = self.db.cursor()
        
        # Get recent mouse/keyboard patterns
        cursor.execute('''
            SELECT 
                AVG(click_frequency) as avg_clicks_per_min,
                AVG(typing_speed_avg) as avg_typing_speed,
                AVG(mouse_randomness) as avg_mouse_randomness
            FROM stress_predictions
            WHERE timestamp >= datetime('now', '-30 minutes')
        ''')
        
        result = cursor.fetchone()
        
        if result:
            clicks_per_min = result[0] or 0
            typing_speed = result[1] or 0
            mouse_randomness = result[2] or 0
            
            issues = []
            
            # High click frequency + high stress = possible RSI risk
            if clicks_per_min > 20 and stress_level >= 3:
                issues.append({
                    'type': 'repetitive_strain',
                    'severity': min(5, int(clicks_per_min / 5)),
                    'suggestion': 'Consider using keyboard shortcuts more often. Take 1-minute hand stretches every 20 minutes.'
                })
            
            # High typing speed variance + erratic mouse = poor posture
            if mouse_randomness > 0.4 and stress_level >= 2:
                issues.append({
                    'type': 'posture',
                    'severity': 3,
                    'suggestion': 'Check your sitting posture: feet flat, back supported, elbows at 90 degrees.'
                })
            
            # Save issues
            for issue in issues:
                cursor.execute('''
                    INSERT INTO ergonomic_feedback (user_id, timestamp, issue_type, severity, suggestion)
                    VALUES (?, datetime('now'), ?, ?, ?)
                ''', ('anonymous', issue['type'], issue['severity'], issue['suggestion']))
            
            self.db.commit()
            
            return issues
        
        return []
    
    def _generate_recommendations(self, stress_level: int, app_context: str) -> List[Dict]:
        """Generate wellness recommendations based on stress and context"""
        recommendations = []
        
        # Don't recommend too frequently (min 5 minutes between same type)
        current_time = datetime.now()
        
        # Based on stress level
        if stress_level >= 3:  # High to Extreme stress
            if self._should_recommend('break', current_time):
                recommendations.append({
                    'type': 'micro_break',
                    'title': 'Stress Break Needed',
                    'message': 'You seem stressed. Take a 60-second break:',
                    'actions': [
                        'Look away from screen for 20 seconds',
                        'Do 3 deep breaths (inhale 4s, hold 4s, exhale 6s)',
                        'Stand up and stretch your arms overhead'
                    ],
                    'duration': 60,
                    'urgency': 'high'
                })
        
        # Based on time of day
        hour = current_time.hour
        if hour >= 14 and hour <= 16:  # Afternoon slump
            if self._should_recommend('hydration', current_time):
                recommendations.append({
                    'type': 'hydration',
                    'title': 'Hydration Reminder',
                    'message': 'Afternoon energy dip detected. Dehydration increases stress hormones.',
                    'actions': ['Drink a glass of water', 'Stand up while drinking'],
                    'duration': 30,
                    'urgency': 'medium'
                })
        
        # Based on app context
        if 'chrome' in app_context.lower() or 'firefox' in app_context.lower():
            if stress_level >= 2 and self._should_recommend('eye_care', current_time):
                recommendations.append({
                    'type': 'eye_care',
                    'title': 'Eye Strain Alert',
                    'message': 'Extended browser use detected. Follow the 20-20-20 rule:',
                    'actions': [
                        'Look at something 20 feet away for 20 seconds',
                        'Blink consciously 10 times',
                        'Adjust screen brightness if needed'
                    ],
                    'duration': 40,
                    'urgency': 'medium'
                })
        
        # Check for prolonged sitting
        if self._should_recommend('movement', current_time):
            recommendations.append({
                'type': 'movement',
                'title': 'Movement Break',
                'message': 'You have been sitting for a while. Time to move:',
                'actions': [
                    'March in place for 30 seconds',
                    'Do 5 shoulder rolls each direction',
                    'Touch your toes (or reach toward them)'
                ],
                'duration': 90,
                'urgency': 'medium'
            })
        
        # Save recommendations
        cursor = self.db.cursor()
        for rec in recommendations:
            cursor.execute('''
                INSERT INTO wellness_recommendations 
                (user_id, timestamp, stress_level, app_context, recommendation_type, 
                 recommendation_text, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'anonymous',
                current_time.isoformat(),
                stress_level,
                app_context,
                rec['type'],
                rec['message'],
                rec['duration']
            ))
        
        self.db.commit()
        
        # Update last recommendation time
        for rec in recommendations:
            self.last_recommendation_time[rec['type']] = current_time
        
        return recommendations
    
    def _should_recommend(self, rec_type: str, current_time: datetime) -> bool:
        """Check if we should recommend this type again"""
        if rec_type not in self.last_recommendation_time:
            return True
        
        last_time = self.last_recommendation_time[rec_type]
        time_diff = (current_time - last_time).total_seconds() / 60  # in minutes
        
        # Minimum time between same type of recommendation
        min_intervals = {
            'micro_break': 10,    # 10 minutes between stress breaks
            'hydration': 60,       # 1 hour between hydration reminders
            'eye_care': 30,        # 30 minutes between eye care
            'movement': 45,        # 45 minutes between movement breaks
        }
        
        return time_diff >= min_intervals.get(rec_type, 30)
    
    def get_recommendations(self, limit: int = 3) -> List[Dict]:
        """Get current wellness recommendations"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                recommendation_type,
                recommendation_text,
                timestamp,
                stress_level,
                duration_seconds
            FROM wellness_recommendations
            WHERE accepted = 0
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        recommendations = []
        for row in cursor.fetchall():
            recommendations.append({
                'type': row[0],
                'message': row[1],
                'time': row[2],
                'stress_level': row[3],
                'duration': row[4]
            })
        
        return recommendations
    
    def record_feedback(self, feedback: Dict):
        """Record user feedback on recommendations"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            UPDATE wellness_recommendations
            SET accepted = ?, completed = ?, effectiveness = ?
            WHERE recommendation_id = ?
        ''', (
            feedback.get('accepted', 0),
            feedback.get('completed', 0),
            feedback.get('effectiveness', 0),
            feedback.get('recommendation_id')
        ))
        
        self.db.commit()
    
    def get_wellness_stats(self) -> Dict:
        """Get wellness statistics"""
        cursor = self.db.cursor()
        
        # Today's stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_recommendations,
                SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                AVG(effectiveness) as avg_effectiveness
            FROM wellness_recommendations
            WHERE date(timestamp) = date('now')
        ''')
        
        today_stats = cursor.fetchone()
        
        # Weekly trend
        cursor.execute('''
            SELECT 
                date(timestamp) as day,
                COUNT(*) as recommendations,
                AVG(stress_level) as avg_stress
            FROM wellness_recommendations
            WHERE timestamp >= date('now', '-7 days')
            GROUP BY date(timestamp)
            ORDER BY day
        ''')
        
        weekly_trend = cursor.fetchall()
        
        # Most effective recommendations
        cursor.execute('''
            SELECT 
                recommendation_type,
                AVG(effectiveness) as avg_effectiveness,
                COUNT(*) as count
            FROM wellness_recommendations
            WHERE effectiveness > 0
            GROUP BY recommendation_type
            ORDER BY avg_effectiveness DESC
            LIMIT 5
        ''')
        
        effective_types = cursor.fetchall()
        
        return {
            'today': {
                'total_recommendations': today_stats[0] or 0,
                'accepted': today_stats[1] or 0,
                'completed': today_stats[2] or 0,
                'acceptance_rate': round((today_stats[1] or 0) / max(today_stats[0] or 1, 1) * 100, 1),
                'avg_effectiveness': today_stats[3] or 0
            },
            'weekly_trend': weekly_trend,
            'most_effective': effective_types
        }