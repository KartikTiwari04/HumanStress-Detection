class MouseTracker {
    constructor() {
        this.mouseEvents = [];
        this.isTracking = false;
        this.lastMousePosition = { x: 0, y: 0 };
        this.lastMouseMoveTime = null;
        this.clickCount = 0;
        this.totalDistance = 0;
        
        // Pressure simulation (real pressure would require specific hardware)
        this.simulatedPressure = 1.0;
        this.pressureVariation = 0;
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Mouse move event
        document.addEventListener('mousemove', (event) => {
            if (!this.isTracking) return;
            
            const now = new Date();
            const movementData = {
                type: 'mouse',
                eventType: 'move',
                x: event.clientX,
                y: event.clientY,
                timestamp: now.toISOString(),
                movementSpeed: this.calculateMovementSpeed(event, now)
            };
            
            this.mouseEvents.push(movementData);
            
            // Calculate distance moved
            if (this.lastMousePosition.x !== 0 || this.lastMousePosition.y !== 0) {
                const dx = event.clientX - this.lastMousePosition.x;
                const dy = event.clientY - this.lastMousePosition.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                this.totalDistance += distance;
            }
            
            this.lastMousePosition = { x: event.clientX, y: event.clientY };
            this.lastMouseMoveTime = now;
            
            // Send to WebSocket if connected
            if (window.stressApp?.ws) {
                window.stressApp.ws.send(JSON.stringify(movementData));
            }
            
            // Update visualization
            this.updateVisualization(event);
            this.updateUI();
        });
        
        // Mouse click events
        document.addEventListener('mousedown', (event) => {
            if (!this.isTracking) return;
            
            // Simulate pressure variation based on stress level
            const currentStress = window.stressApp?.currentStressLevel || 0;
            this.pressureVariation = 0.1 + (currentStress / 4) * 0.3; // More stress = more pressure variation
            
            this.simulatedPressure = 0.8 + Math.random() * this.pressureVariation;
            
            const clickData = {
                type: 'mouse',
                eventType: 'click',
                button: event.button,
                x: event.clientX,
                y: event.clientY,
                timestamp: new Date().toISOString(),
                pressure: this.simulatedPressure
            };
            
            this.mouseEvents.push(clickData);
            this.clickCount++;
            
            if (window.stressApp?.ws) {
                window.stressApp.ws.send(JSON.stringify(clickData));
            }
            
            this.updateUI();
        });
        
        document.addEventListener('mouseup', (event) => {
            if (!this.isTracking) return;
            
            const clickData = {
                type: 'mouse',
                eventType: 'release',
                button: event.button,
                x: event.clientX,
                y: event.clientY,
                timestamp: new Date().toISOString(),
                pressure: 0
            };
            
            if (window.stressApp?.ws) {
                window.stressApp.ws.send(JSON.stringify(clickData));
            }
        });
        
        // Mouse wheel event
        document.addEventListener('wheel', (event) => {
            if (!this.isTracking) return;
            
            const wheelData = {
                type: 'mouse',
                eventType: 'scroll',
                deltaX: event.deltaX,
                deltaY: event.deltaY,
                timestamp: new Date().toISOString()
            };
            
            this.mouseEvents.push(wheelData);
            
            if (window.stressApp?.ws) {
                window.stressApp.ws.send(JSON.stringify(wheelData));
            }
        });
    }
    
    calculateMovementSpeed(event, currentTime) {
        if (!this.lastMouseMoveTime) return 0;
        
        const timeDiff = (currentTime - this.lastMouseMoveTime) / 1000; // in seconds
        if (timeDiff === 0) return 0;
        
        const dx = event.clientX - this.lastMousePosition.x;
        const dy = event.clientY - this.lastMousePosition.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        return distance / timeDiff; // pixels per second
    }
    
    calculateMouseRandomness() {
        if (this.mouseEvents.length < 3) return 0.1;
        
        // Analyze movement patterns
        const moveEvents = this.mouseEvents.filter(e => e.eventType === 'move');
        if (moveEvents.length < 3) return 0.1;
        
        // Calculate angle changes between movements
        let angleChanges = [];
        for (let i = 2; i < moveEvents.length; i++) {
            const dx1 = moveEvents[i-1].x - moveEvents[i-2].x;
            const dy1 = moveEvents[i-1].y - moveEvents[i-2].y;
            const dx2 = moveEvents[i].x - moveEvents[i-1].x;
            const dy2 = moveEvents[i].y - moveEvents[i-1].y;
            
            const dot = dx1 * dx2 + dy1 * dy2;
            const mag1 = Math.sqrt(dx1 * dx1 + dy1 * dy1);
            const mag2 = Math.sqrt(dx2 * dx2 + dy2 * dy2);
            
            if (mag1 > 0 && mag2 > 0) {
                const cosAngle = dot / (mag1 * mag2);
                const clampedCos = Math.max(-1, Math.min(1, cosAngle));
                const angle = Math.acos(clampedCos);
                angleChanges.push(angle);
            }
        }
        
        if (angleChanges.length === 0) return 0.1;
        
        // Calculate variance of angle changes
        const mean = angleChanges.reduce((a, b) => a + b, 0) / angleChanges.length;
        const variance = angleChanges.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / angleChanges.length;
        
        // Normalize to 0-1 range
        return Math.min(variance * 10, 1);
    }
    
    calculateClickFrequency() {
        if (this.mouseEvents.length < 2) return 0;
        
        const clickEvents = this.mouseEvents.filter(e => e.eventType === 'click');
        if (clickEvents.length < 2) return 0;
        
        const firstClick = new Date(clickEvents[0].timestamp);
        const lastClick = new Date(clickEvents[clickEvents.length - 1].timestamp);
        const timeDiff = (lastClick - firstClick) / 1000; // in seconds
        
        if (timeDiff === 0) return 0;
        
        return clickEvents.length / timeDiff; // clicks per second
    }
    
    calculateAveragePressure() {
        const clickEvents = this.mouseEvents.filter(e => e.eventType === 'click' && e.pressure);
        if (clickEvents.length === 0) return 1.0;
        
        const totalPressure = clickEvents.reduce((sum, event) => sum + event.pressure, 0);
        return totalPressure / clickEvents.length;
    }
    
    startTracking() {
        this.isTracking = true;
        this.mouseEvents = [];
        this.clickCount = 0;
        this.totalDistance = 0;
        console.log('Mouse tracking started');
    }
    
    stopTracking() {
        this.isTracking = false;
        console.log('Mouse tracking stopped');
    }
    
    reset() {
        this.mouseEvents = [];
        this.clickCount = 0;
        this.totalDistance = 0;
        this.lastMousePosition = { x: 0, y: 0 };
        this.lastMouseMoveTime = null;
    }
    
    getStats() {
        return {
            mouseRandomness: this.calculateMouseRandomness(),
            clickFrequency: this.calculateClickFrequency(),
            averagePressure: this.calculateAveragePressure(),
            totalClicks: this.clickCount,
            totalDistance: Math.round(this.totalDistance),
            moveCount: this.mouseEvents.filter(e => e.eventType === 'move').length
        };
    }
    
    updateUI() {
        const stats = this.getStats();
        
        // Update mouse randomness display
        const mouseRandElement = document.getElementById('mouseRandomness');
        if (mouseRandElement) {
            mouseRandElement.textContent = stats.mouseRandomness.toFixed(3);
        }
        
        // Update mouse move count
        const mouseMoveElement = document.getElementById('mouseMoveCount');
        if (mouseMoveElement) {
            mouseMoveElement.textContent = stats.moveCount;
        }
        
        // Update progress bars
        this.updateProgressBars(stats);
    }
    
    updateProgressBars(stats) {
        // Mouse randomness bar
        const mouseBar = document.getElementById('mouseBar');
        if (mouseBar) {
            mouseBar.style.width = `${stats.mouseRandomness * 100}%`;
        }
    }
    
    updateVisualization(event) {
        // This would update the heatmap visualization
        if (window.stressApp?.visualization) {
            window.stressApp.visualization.addMousePoint(event.clientX, event.clientY);
        }
    }
}