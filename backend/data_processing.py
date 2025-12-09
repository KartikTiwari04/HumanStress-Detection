import numpy as np
from typing import List, Dict, Any
from collections import deque
import math

class DataProcessor:
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.key_events = deque(maxlen=window_size)
        self.mouse_events = deque(maxlen=window_size)
        
    def calculate_typing_speed(self, key_events: List[Dict]) -> float:
        if len(key_events) < 2:
            return 0
        
        # Calculate words per minute
        key_presses = [event for event in key_events if event.get('key_pressed')]
        
        if len(key_presses) < 2:
            return 0
        
        # Get time difference between first and last key press
        time_diff = (key_presses[-1]['timestamp'] - key_presses[0]['timestamp']).total_seconds()
        
        if time_diff == 0:
            return 0
        
        # Average characters per minute (assuming 5 chars per word)
        chars_per_minute = (len(key_presses) / time_diff) * 60
        wpm = chars_per_minute / 5
        
        return wpm
    
    def calculate_key_press_variance(self, key_events: List[Dict]) -> float:
        press_durations = [event.get('press_duration', 0) for event in key_events 
                          if event.get('press_duration') and event.get('press_duration') > 0]
        
        if len(press_durations) < 2:
            return 0
        
        return np.var(press_durations)
    
    def calculate_mouse_randomness(self, mouse_events: List[Dict]) -> float:
        if len(mouse_events) < 3:
            return 0
        
        # Extract movement vectors
        movements = []
        for i in range(1, len(mouse_events)):
            dx = mouse_events[i]['x'] - mouse_events[i-1]['x']
            dy = mouse_events[i]['y'] - mouse_events[i-1]['y']
            movements.append((dx, dy))
        
        # Calculate angle changes between movements
        angle_changes = []
        for i in range(1, len(movements)):
            v1 = movements[i-1]
            v2 = movements[i]
            
            # Calculate angle between vectors
            dot = v1[0]*v2[0] + v1[1]*v2[1]
            norm1 = math.sqrt(v1[0]**2 + v1[1]**2)
            norm2 = math.sqrt(v2[0]**2 + v2[1]**2)
            
            if norm1 * norm2 == 0:
                continue
            
            cos_angle = dot / (norm1 * norm2)
            cos_angle = max(-1, min(1, cos_angle))  # Clamp to valid range
            angle = math.acos(cos_angle)
            angle_changes.append(angle)
        
        if not angle_changes:
            return 0
        
        # Higher variance in angle changes indicates more random movement
        return np.var(angle_changes)
    
    def calculate_click_frequency(self, mouse_events: List[Dict]) -> float:
        clicks = [event for event in mouse_events if event.get('click_type')]
        
        if len(clicks) < 2:
            return 0
        
        # Calculate clicks per minute
        time_diff = (mouse_events[-1]['timestamp'] - mouse_events[0]['timestamp']).total_seconds()
        
        if time_diff == 0:
            return 0
        
        return (len(clicks) / time_diff) * 60
    
    def calculate_backspace_ratio(self, key_events: List[Dict]) -> float:
        total_keys = len([event for event in key_events if event.get('key_pressed')])
        backspace_keys = len([event for event in key_events 
                             if event.get('key_pressed') in ['Backspace', 'Delete']])
        
        if total_keys == 0:
            return 0
        
        return backspace_keys / total_keys
    
    def calculate_mouse_speed_variance(self, mouse_events: List[Dict]) -> float:
        speeds = [event.get('movement_speed', 0) for event in mouse_events 
                 if event.get('movement_speed', 0) > 0]
        
        if len(speeds) < 2:
            return 0
        
        return np.var(speeds)
    
    def extract_features(self, key_events: List[Dict], mouse_events: List[Dict]) -> Dict[str, float]:
        features = {
            'typing_speed': self.calculate_typing_speed(key_events),
            'key_press_variance': self.calculate_key_press_variance(key_events),
            'mouse_randomness': self.calculate_mouse_randomness(mouse_events),
            'click_frequency': self.calculate_click_frequency(mouse_events),
            'backspace_ratio': self.calculate_backspace_ratio(key_events),
            'mouse_speed_variance': self.calculate_mouse_speed_variance(mouse_events)
        }
        
        return features