class StressVisualization {
    constructor() {
        this.mouseHeatmapCanvas = document.getElementById('mouseHeatmap');
        this.stressGaugeCanvas = document.getElementById('stressGauge');
        this.historyChartCanvas = document.getElementById('stressHistoryChart');
        
        this.mousePoints = [];
        this.stressHistory = [];
        this.maxPoints = 1000;
        
        this.initializeCanvases();
    }
    
    initializeCanvases() {
        // Initialize heatmap context
        if (this.mouseHeatmapCanvas) {
            this.heatmapCtx = this.mouseHeatmapCanvas.getContext('2d');
            this.mouseHeatmapCanvas.width = this.mouseHeatmapCanvas.parentElement.clientWidth;
            this.mouseHeatmapCanvas.height = 200;
        }
        
        // Initialize gauge
        if (this.stressGaugeCanvas) {
            this.gaugeCtx = this.stressGaugeCanvas.getContext('2d');
            this.stressGaugeCanvas.width = 200;
            this.stressGaugeCanvas.height = 200;
            this.drawGauge(0); // Initial calm state
        }
        
        // Initialize history chart
        if (this.historyChartCanvas) {
            this.initializeHistoryChart();
        }
    }
    
    drawGauge(stressLevel) {
        if (!this.gaugeCtx) return;
        
        const ctx = this.gaugeCtx;
        const centerX = this.stressGaugeCanvas.width / 2;
        const centerY = this.stressGaugeCanvas.height / 2;
        const radius = 80;
        
        // Clear canvas
        ctx.clearRect(0, 0, this.stressGaugeCanvas.width, this.stressGaugeCanvas.height);
        
        // Draw background circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.fillStyle = '#1a2238';
        ctx.fill();
        
        // Draw stress level arc
        const startAngle = -Math.PI / 2;
        const endAngle = startAngle + (Math.PI * 2 * stressLevel);
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, startAngle, endAngle);
        ctx.lineWidth = 12;
        
        // Color based on stress level
        let gradient;
        if (stressLevel < 0.25) {
            gradient = ctx.createLinearGradient(0, 0, 200, 0);
            gradient.addColorStop(0, '#2ec4b6');
            gradient.addColorStop(1, '#4cc9f0');
        } else if (stressLevel < 0.5) {
            gradient = ctx.createLinearGradient(0, 0, 200, 0);
            gradient.addColorStop(0, '#ff9f1c');
            gradient.addColorStop(1, '#ff9e00');
        } else if (stressLevel < 0.75) {
            gradient = ctx.createLinearGradient(0, 0, 200, 0);
            gradient.addColorStop(0, '#ff6b6b');
            gradient.addColorStop(1, '#ff4757');
        } else {
            gradient = ctx.createLinearGradient(0, 0, 200, 0);
            gradient.addColorStop(0, '#ef476f');
            gradient.addColorStop(1, '#9d0208');
        }
        
        ctx.strokeStyle = gradient;
        ctx.stroke();
        
        // Draw inner circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius - 15, 0, Math.PI * 2);
        ctx.fillStyle = '#141b2d';
        ctx.fill();
    }
    
    addMousePoint(x, y) {
        // Convert coordinates to canvas space
        const rect = this.mouseHeatmapCanvas.getBoundingClientRect();
        const canvasX = x - rect.left;
        const canvasY = y - rect.top;
        
        this.mousePoints.push({ x: canvasX, y: canvasY, time: Date.now() });
        
        // Keep only recent points
        if (this.mousePoints.length > this.maxPoints) {
            this.mousePoints.shift();
        }
        
        // Update heatmap periodically
        if (Date.now() - (this.lastHeatmapUpdate || 0) > 100) {
            this.updateHeatmap();
            this.lastHeatmapUpdate = Date.now();
        }
    }
    
    updateHeatmap() {
        if (!this.heatmapCtx || this.mousePoints.length === 0) return;
        
        const ctx = this.heatmapCtx;
        const width = this.mouseHeatmapCanvas.width;
        const height = this.mouseHeatmapCanvas.height;
        
        // Clear with fade effect
        ctx.fillStyle = 'rgba(10, 14, 23, 0.1)';
        ctx.fillRect(0, 0, width, height);
        
        // Draw recent points
        const now = Date.now();
        this.mousePoints.forEach(point => {
            const age = now - point.time;
            const opacity = Math.max(0, 1 - age / 5000); // Fade over 5 seconds
            
            // Create gradient for heat spot
            const gradient = ctx.createRadialGradient(
                point.x, point.y, 0,
                point.x, point.y, 20
            );
            
            // Color based on recency
            gradient.addColorStop(0, `rgba(67, 97, 238, ${opacity * 0.8})`);
            gradient.addColorStop(0.5, `rgba(67, 97, 238, ${opacity * 0.3})`);
            gradient.addColorStop(1, `rgba(67, 97, 238, 0)`);
            
            ctx.beginPath();
            ctx.arc(point.x, point.y, 20, 0, Math.PI * 2);
            ctx.fillStyle = gradient;
            ctx.fill();
        });
    }
    
    initializeHistoryChart() {
        const ctx = this.historyChartCanvas.getContext('2d');
        
        this.historyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Stress Level',
                    data: [],
                    borderColor: '#4361ee',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 4,
                        ticks: {
                            callback: function(value) {
                                const levels = ['Calm', 'Mild', 'Moderate', 'High', 'Extreme'];
                                return levels[value] || '';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    }
                }
            }
        });
    }
    
    addStressRecord(level, confidence) {
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Add to chart
        if (this.historyChart) {
            this.historyChart.data.labels.push(time);
            this.historyChart.data.datasets[0].data.push(level);
            
            // Keep only last 10 points
            if (this.historyChart.data.labels.length > 10) {
                this.historyChart.data.labels.shift();
                this.historyChart.data.datasets[0].data.shift();
            }
            
            this.historyChart.update();
        }
        
        // Add to history list
        this.addToHistoryList(time, level, confidence);
    }
    
    addToHistoryList(time, level, confidence) {
        const historyList = document.getElementById('historyList');
        if (!historyList) return;
        
        const stressLevels = ['Calm', 'Mild Stress', 'Moderate Stress', 'High Stress', 'Extreme Stress'];
        const levelColors = ['#2ec4b6', '#ff9f1c', '#ff6b6b', '#ef476f', '#9d0208'];
        
        const item = document.createElement('div');
        item.className = 'history-item';
        item.innerHTML = `
            <div class="history-time">${time}</div>
            <div class="history-level" style="color: ${levelColors[level]}">
                ${stressLevels[level]}
            </div>
            <div class="history-confidence">${Math.round(confidence * 100)}%</div>
        `;
        
        historyList.insertBefore(item, historyList.firstChild);
        
        // Keep only last 5 items
        while (historyList.children.length > 5) {
            historyList.removeChild(historyList.lastChild);
        }
    }
    
    updateGaugeFromPrediction(prediction) {
    const stressLevels = ['Calm', 'Mild Stress', 'Moderate Stress', 'High Stress', 'Extreme Stress'];
    const stressColors = ['#2ec4b6', '#ff9f1c', '#ff6b6b', '#ef476f', '#9d0208'];
    
    // Get stress level index (0-4)
    const levelIndex = prediction.level_index;
    const confidence = prediction.confidence;
    
    // Update gauge visualization
    if (this.gaugeCtx) {
        this.drawGauge(levelIndex / 4); // Normalize to 0-1 for gauge
    }
    
    // Update stress level text
    const stressTextElement = document.getElementById('stressLevelText');
    if (stressTextElement) {
        stressTextElement.textContent = stressLevels[levelIndex].toUpperCase();
        stressTextElement.style.color = stressColors[levelIndex];
        stressTextElement.style.textShadow = `0 0 10px ${stressColors[levelIndex]}50`;
        
        // Add pulsing animation for high stress levels
        if (levelIndex >= 3) {
            stressTextElement.style.animation = 'pulse 1.5s infinite';
        } else {
            stressTextElement.style.animation = 'none';
        }
    }
    
    // Update confidence display
    const confidenceElement = document.getElementById('stressConfidence');
    if (confidenceElement) {
        const confidencePercent = Math.round(confidence * 100);
        confidenceElement.textContent = `${confidencePercent}% confidence`;
        
        // Color code confidence level
        if (confidencePercent >= 80) {
            confidenceElement.style.color = '#4cc9f0';
        } else if (confidencePercent >= 60) {
            confidenceElement.style.color = '#ff9f1c';
        } else {
            confidenceElement.style.color = '#ff6b6b';
        }
    }
    
    // Update stress level card border
    const stressCard = document.querySelector('.stress-level-card');
    if (stressCard) {
        stressCard.style.borderColor = stressColors[levelIndex];
        stressCard.style.boxShadow = `0 0 20px ${stressColors[levelIndex]}30`;
        
        // Add glowing effect for extreme stress
        if (levelIndex === 4) {
            stressCard.style.animation = 'stressPulse 2s infinite';
        } else {
            stressCard.style.animation = 'none';
        }
    }
    
    // Update scale labels highlight
    this.highlightStressScale(levelIndex);
    
    // Add to history
    this.addStressRecord(levelIndex, confidence);
    
    // Log prediction for debugging
    console.log(`Stress Prediction: ${stressLevels[levelIndex]} (${Math.round(confidence * 100)}% confidence)`);
    
    return {
        level: stressLevels[levelIndex],
        index: levelIndex,
        color: stressColors[levelIndex],
        confidence: confidence
    };
}

highlightStressScale(activeIndex) {
    const scaleLabels = document.querySelectorAll('.scale-label');
    
    scaleLabels.forEach((label, index) => {
        if (index === activeIndex) {
            // Highlight active stress level
            label.style.transform = 'translateY(-5px)';
            label.style.fontWeight = 'bold';
            label.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
            
            // Add specific glow based on stress level
            const colors = ['#2ec4b6', '#ff9f1c', '#ff6b6b', '#ef476f', '#9d0208'];
            label.style.boxShadow = `0 4px 12px ${colors[index]}60`;
        } else {
            // Reset other labels
            label.style.transform = 'translateY(0)';
            label.style.fontWeight = 'normal';
            label.style.boxShadow = 'none';
        }
    });
}
}