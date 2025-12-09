class KeyboardTracker {
    constructor() {
        this.keyEvents = [];
        this.sessionStartTime = null;
        this.isTracking = false;
        this.lastKeyPressTime = null;
        this.backspaceCount = 0;
        this.totalKeyPresses = 0;
        
        // Initialize
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Key down event
        document.addEventListener('keydown', (event) => {
            if (!this.isTracking) return;
            
            const keyData = {
                type: 'keyboard',
                key: event.key,
                code: event.code,
                timestamp: new Date().toISOString(),
                eventType: 'keydown',
                pressure: 1.0 // Default pressure for keyboard
            };
            
            this.keyEvents.push(keyData);
            this.totalKeyPresses++;
            
            if (event.key === 'Backspace' || event.key === 'Delete') {
                this.backspaceCount++;
            }
            
            // Send to WebSocket if connected
            if (window.stressApp?.ws) {
                window.stressApp.ws.send(JSON.stringify(keyData));
            }
            
            // Update UI
            this.updateUI();
        });
        
        // Key up event
        document.addEventListener('keyup', (event) => {
            if (!this.isTracking) return;
            
            const keyData = {
                type: 'keyboard',
                key: event.key,
                code: event.code,
                timestamp: new Date().toISOString(),
                eventType: 'keyup'
            };
            
            this.keyEvents.push(keyData);
            
            // Send to WebSocket if connected
            if (window.stressApp?.ws) {
                window.stressApp.ws.send(JSON.stringify(keyData));
            }
        });
    }
    
    startTracking() {
        this.isTracking = true;
        this.sessionStartTime = new Date();
        this.keyEvents = [];
        this.backspaceCount = 0;
        this.totalKeyPresses = 0;
        console.log('Keyboard tracking started');
    }
    
    stopTracking() {
        this.isTracking = false;
        console.log('Keyboard tracking stopped');
    }
    
    reset() {
        this.keyEvents = [];
        this.backspaceCount = 0;
        this.totalKeyPresses = 0;
        this.lastKeyPressTime = null;
    }
    
    calculateTypingSpeed() {
        if (this.keyEvents.length < 2) return 0;
        
        const keyDownEvents = this.keyEvents.filter(e => e.eventType === 'keydown');
        if (keyDownEvents.length < 2) return 0;
        
        const firstEvent = new Date(keyDownEvents[0].timestamp);
        const lastEvent = new Date(keyDownEvents[keyDownEvents.length - 1].timestamp);
        const timeDiff = (lastEvent - firstEvent) / 1000; // in seconds
        
        if (timeDiff === 0) return 0;
        
        const charsPerMinute = (keyDownEvents.length / timeDiff) * 60;
        const wpm = charsPerMinute / 5; // Assuming 5 characters per word
        
        return Math.round(wpm);
    }
    
    calculateKeyPressVariance() {
        if (this.keyEvents.length < 2) return 0;
        
        // This would need more sophisticated timing data
        // For now, return a simulated value based on backspace ratio
        const backspaceRatio = this.backspaceCount / Math.max(this.totalKeyPresses, 1);
        return backspaceRatio * 0.3; // Scale to reasonable range
    }
    
    getStats() {
        return {
            typingSpeed: this.calculateTypingSpeed(),
            keyPressVariance: this.calculateKeyPressVariance(),
            backspaceCount: this.backspaceCount,
            totalKeyPresses: this.totalKeyPresses,
            backspaceRatio: this.backspaceCount / Math.max(this.totalKeyPresses, 1)
        };
    }
    
    updateUI() {
        const stats = this.getStats();
        
        // Update typing speed display
        const typingSpeedElement = document.getElementById('typingSpeed');
        if (typingSpeedElement) {
            typingSpeedElement.textContent = `${stats.typingSpeed} WPM`;
        }
        
        // Update error rate
        const errorRateElement = document.getElementById('errorRate');
        if (errorRateElement) {
            const errorRate = Math.round(stats.backspaceRatio * 100);
            errorRateElement.textContent = `${errorRate}%`;
        }
        
        // Update key press count
        const keyPressElement = document.getElementById('keyPressCount');
        if (keyPressElement) {
            keyPressElement.textContent = stats.totalKeyPresses;
        }
        
        // Update progress bars
        this.updateProgressBars(stats);
    }
    
    updateProgressBars(stats) {
        // Typing speed bar (normalize: 0-120 WPM)
        const typingBar = document.getElementById('typingBar');
        if (typingBar) {
            const normalizedSpeed = Math.min(stats.typingSpeed / 120, 1) * 100;
            typingBar.style.width = `${normalizedSpeed}%`;
        }
        
        // Error rate bar
        const errorBar = document.getElementById('errorBar');
        if (errorBar) {
            const errorRate = Math.min(stats.backspaceRatio * 5, 1) * 100; // Scale to make 20% = full
            errorBar.style.width = `${errorRate}%`;
        }
    }
}