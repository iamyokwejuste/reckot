'use strict';

window.ChartTheme = {
    getChartTheme() {
        const isDark = document.documentElement.classList.contains('dark') ||
                      document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            backgroundColor: isDark ? '#1f2937' : '#ffffff',
            gridColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
            textColor: isDark ? '#e5e7eb' : '#374151'
        };
    },

    initializeDarkMode() {
        Chart.defaults.color = this.getChartTheme().textColor;
        Chart.defaults.borderColor = this.getChartTheme().gridColor;
    },

    registerPlugin() {
        Chart.register({
            id: 'canvasBackground',
            beforeDraw: (chart) => {
                const ctx = chart.ctx;
                const theme = this.getChartTheme();
                ctx.save();
                ctx.fillStyle = theme.backgroundColor;
                ctx.fillRect(0, 0, chart.width, chart.height);
                ctx.restore();
            }
        });
    },

    observeThemeChanges(chartInstances) {
        const observer = new MutationObserver(() => {
            this.initializeDarkMode();
            Object.values(chartInstances).forEach(chart => {
                if (chart) chart.update();
            });
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class', 'data-theme']
        });
    }
};
