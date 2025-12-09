class StressDetectionApp {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.isMonitoring = false;
        this.sessionStartTime = null;
        this.currentStressLevel = 0;
        this.stressConfidence = 0;
        
        // Initialize trackers
        this.keyboardTracker = new KeyboardTracker();
        this.mouseTracker = new MouseTracker();
        this.visualization = new StressVisualization();
        
        // Initialize UI
        this.initializeUI();
        this.initializeWebSocket();
        this.startSessionTimer();
    }
    
    initializeUI() {
        // Start/Stop buttons
        document.getElementById('startBtn').addEventListener('click', () => this.startMonitoring());
        document.getElementById('pauseBtn').addEventListener('click', () => this.pauseMonitoring());
        document.getElementById('resetBtn').addEventListener('click', () => this.resetSession());
        
        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());
        
        // Info modal
        document.getElementById('infoBtn').addEventListener('click', () => this.showInfoModal());
        document.querySelector('.close-modal').addEventListener('click', () => this.hideInfoModal());
        document.getElementById('infoModal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('infoModal')) {
                this.hideInfoModal();
            }
        });
        
        // Visualization toggle
        document.getElementById('vizTypeBtn').addEventListener('click', () => this.toggleVisualization());
        
        // Settings checkboxes
        document.getElementById('trackKeyboard').addEventListener('change', (e) => {
            if (!e.target.checked) {
                this.keyboardTracker.stopTracking();
            } else if (this.isMonitoring) {
                this.keyboardTracker.startTracking();
            }
        });
        
        document.getElementById('trackMouse').addEventListener('change', (e) => {
            if (!e.target.checked) {
                this.mouseTracker.stopTracking();
            } else if (this.isMonitoring) {
                this.mouseTracker.startTracking();
            }
        });
        
        // Initialize stress gauge
        this.updateStressGauge(0, 0.85);
    }
    
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/track`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'prediction') {
                this.handleStressPrediction(data);
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            
            // Try to reconnect after 5 seconds
            setTimeout(() => this.initializeWebSocket(), 5000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }
    
    startMonitoring() {
        if (!this.isMonitoring) {
            this.isMonitoring = true;
            this.sessionStartTime = new Date();
            
            // Start trackers
            if (document.getElementById('trackKeyboard').checked) {
                this.keyboardTracker.startTracking();
            }
            if (document.getElementById('trackMouse').checked) {
                this.mouseTracker.startTracking();
            }
            
            // Update UI
            document.getElementById('startBtn').disabled = true;
            document.getElementById('pauseBtn').disabled = false;
            document.getElementById('statusIndicator').querySelector('.status-text').textContent = 'Monitoring Active';
            
            // Update status dot
            const statusDot = document.getElementById('statusIndicator').querySelector('.status-dot');
            statusDot.style.background = '#4cc9f0';
            statusDot.style.animation = 'stressPulse 1s infinite';
            
            console.log('Monitoring started');
        }
    }
    
    pauseMonitoring() {
        if (this.isMonitoring) {
            this.isMonitoring = false;
            
            // Stop trackers
            this.keyboardTracker.stopTracking();
            this.mouseTracker.stopTracking();
            
            // Update UI
            document.getElementById('startBtn').disabled = false;
            document.getElementById('pauseBtn').disabled = true;
            document.getElementById('statusIndicator').querySelector('.status-text').textContent = 'Paused';
            
            // Update status dot
            const statusDot = document.getElementById('statusIndicator').querySelector('.status-dot');
            statusDot.style.background = '#ff9e00';
            statusDot.style.animation = 'none';
            
            console.log('Monitoring paused');
        }
    }
    
    resetSession() {
        this.isMonitoring = false;
        
        // Reset trackers
        this.keyboardTracker.reset();
        this.keyboardTracker.stopTracking();
        this.mouseTracker.reset();
        this.mouseTracker.stopTracking();
        
        // Reset UI
        document.getElementById('startBtn').disabled = false;
        document.getElementById('pauseBtn').disabled = true;
        document.getElementById('statusIndicator').querySelector('.status-text').textContent = 'Ready to Start';
        
        // Reset status dot
        const statusDot = document.getElementById('statusIndicator').querySelector('.status-dot');
        statusDot.style.background = '#b0b7c3';
        statusDot.style.animation = 'none';
        
        // Reset counters
        document.getElementById('keyPressCount').textContent = '0';
        document.getElementById('mouseMoveCount').textContent = '0';
        document.getElementById('sessionTime').textContent = '0s';
        document.getElementById('stressScore').textContent = '0';
        
        // Reset stress display
        this.updateStressGauge(0, 0.85);
        
        // Clear history
        const historyList = document.getElementById('historyList');
        if (historyList) {
            historyList.innerHTML = '';
        }
        
        console.log('Session reset');
    }
    
    handleStressPrediction(data) {
        const { prediction, features } = data;
        
        // Update stress level
        this.currentStressLevel = prediction.level_index;
        this.stressConfidence = prediction.confidence;
        
        // Update UI
        this.updateStressGauge(prediction.level_index, prediction.confidence);
        this.updateStressIndicators(features);
        
        // Add to history
        this.visualization.addStressRecord(prediction.level_index, prediction.confidence);
        
        // Update stress score
        document.getElementById('stressScore').textContent = prediction.level_index * 25;
        
        console.log('Stress prediction:', prediction);
    }
    
    updateStressGauge(levelIndex, confidence) {
        // Update gauge visualization
        if (this.visualization) {
            this.visualization.drawGauge(levelIndex / 4); // Normalize to 0-1
        }
        
        // Update text display
        const stressLevels = ['CALM', 'MILD STRESS', 'MODERATE STRESS', 'HIGH STRESS', 'EXTREME STRESS'];
        const stressColors = ['#2ec4b6', '#ff9f1c', '#ff6b6b', '#ef476f', '#9d0208'];
        
        document.getElementById('stressLevelText').textContent = stressLevels[levelIndex];
        document.getElementById('stressLevelText').style.color = stressColors[levelIndex];
        document.getElementById('stressConfidence').textContent = `${Math.round(confidence * 100)}% confidence`;
        
        // Update card border color based on stress level
        const stressCard = document.querySelector('.stress-level-card');
        if (stressCard) {
            stressCard.style.borderColor = stressColors[levelIndex];
        }
    }
    
    updateStressIndicators(features) {
        // Update typing speed
        const typingSpeed = Math.round(features.typing_speed);
        document.getElementById('typingSpeed').textContent = `${typingSpeed} WPM`;
        
        // Update mouse randomness
        document.getElementById('mouseRandomness').textContent = features.mouse_randomness.toFixed(3);
        
        // Update error rate (from backspace ratio)
        const errorRate = Math.round(features.backspace_ratio * 100);
        document.getElementById('errorRate').textContent = `${errorRate}%`;
        
        // Update progress bars
        this.updateProgressBars(features);
    }
    
    updateProgressBars(features) {
        // Typing speed bar (normalize 0-120 WPM)
        const typingBar = document.getElementById('typingBar');
        if (typingBar) {
            const normalizedSpeed = Math.min(features.typing_speed / 120, 1) * 100;
            typingBar.style.width = `${normalizedSpeed}%`;
        }
        
        // Mouse randomness bar
        const mouseBar = document.getElementById('mouseBar');
        if (mouseBar) {
            mouseBar.style.width = `${features.mouse_randomness * 100}%`;
        }
        
        // Error rate bar
        const errorBar = document.getElementById('errorBar');
        if (errorBar) {
            const errorRate = Math.min(features.backspace_ratio * 5, 1) * 100;
            errorBar.style.width = `${errorRate}%`;
        }
    }
    
    updateConnectionStatus(connected) {
        const connectionElement = document.getElementById('connectionStatus');
        if (connectionElement) {
            if (connected) {
                connectionElement.innerHTML = '<i class="fas fa-plug"></i> Connected';
                connectionElement.style.color = '#4cc9f0';
            } else {
                connectionElement.innerHTML = '<i class="fas fa-plug"></i> Not Connected';
                connectionElement.style.color = '#ff6b6b';
            }
        }
    }
    
    startSessionTimer() {
        setInterval(() => {
            if (this.isMonitoring && this.sessionStartTime) {
                const now = new Date();
                const diff = Math.floor((now - this.sessionStartTime) / 1000);
                document.getElementById('sessionTime').textContent = `${diff}s`;
                
                // Update data points count
                const keyboardEvents = this.keyboardTracker.keyEvents.length;
                const mouseEvents = this.mouseTracker.mouseEvents.length;
                const totalPoints = keyboardEvents + mouseEvents;
                document.getElementById('dataPoints').textContent = `Data Points: ${totalPoints}`;
            }
        }, 1000);
    }
    
    toggleTheme() {
        const body = document.body;
        const themeToggle = document.getElementById('themeToggle');
        
        if (body.classList.contains('light-theme')) {
            // Switch to dark theme
            body.classList.remove('light-theme');
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        } else {
            // Switch to light theme
            body.classList.add('light-theme');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        }
    }
    
    showInfoModal() {
        document.getElementById('infoModal').style.display = 'flex';
    }
    
    hideInfoModal() {
        document.getElementById('infoModal').style.display = 'none';
    }
    
    toggleVisualization() {
        const heatmap = document.getElementById('mouseHeatmap');
        const keyboardViz = document.getElementById('keyboardViz');
        const vizTypeBtn = document.getElementById('vizTypeBtn');
        
        if (heatmap.style.display !== 'none') {
            // Switch to keyboard visualization
            heatmap.style.display = 'none';
            keyboardViz.style.display = 'block';
            vizTypeBtn.innerHTML = '<i class="fas fa-exchange-alt"></i> Show Mouse Heatmap';
        } else {
            // Switch to mouse heatmap
            heatmap.style.display = 'block';
            keyboardViz.style.display = 'none';
            vizTypeBtn.innerHTML = '<i class="fas fa-exchange-alt"></i> Show Keyboard Pattern';
        }
    }
}

// Light theme CSS addition (add to theme.css)
const lightThemeCSS = `
.light-theme {
    --bg-primary: #f8f9fa;
    --bg-secondary: #ffffff;
    --bg-card: #ffffff;
    --text-primary: #2d3748;
    --text-secondary: #718096;
    --border-color: #e2e8f0;
    --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
    --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
}

.light-theme .card {
    border: 1px solid var(--border-color);
}

.light-theme .stat-box {
    background: #f8f9fa;
}

.light-theme .input-field,
.light-theme .textarea-field {
    background: #f8f9fa;
    border-color: #e2e8f0;
}
`;

// Add light theme styles to document
const style = document.createElement('style');
style.textContent = lightThemeCSS;
document.head.appendChild(style);

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.stressApp = new StressDetectionApp();
});