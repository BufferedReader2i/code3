<template>
  <div class="line-chart-container">
    <div ref="chartRef" class="line-chart"></div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'LineChart',
  props: {
    data: { type: Array, default: () => [] },
    title: { type: String, default: '' },
    color: { type: String, default: '#0d9488' },
    valueKey: { type: String, default: 'value' },
    dateKey: { type: String, default: 'date' }
  },
  data() {
    return { chart: null }
  },
  watch: {
    data: {
      handler() { this.updateChart() },
      deep: true
    }
  },
  mounted() {
    this.chart = echarts.init(this.$refs.chartRef)
    this.updateChart()
    window.addEventListener('resize', () => this.chart?.resize())
  },
  beforeUnmount() {
    this.chart?.dispose()
  },
  methods: {
    updateChart() {
      if (!this.chart) return
      const dates = this.data.map(d => d[this.dateKey])
      const values = this.data.map(d => d[this.valueKey])
      this.chart.setOption({
        title: {
          text: this.title,
          left: 'center',
          textStyle: { fontSize: 14, fontWeight: 600, color: '#1e293b', fontFamily: 'Inter, system-ui, sans-serif' }
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(30, 41, 59, 0.9)',
          borderColor: 'transparent',
          borderRadius: 8,
          padding: [10, 14],
          textStyle: { color: '#fff', fontSize: 12 },
          axisPointer: { type: 'cross', crossStyle: { color: '#cbd5e1' } }
        },
        grid: { left: 50, right: 20, top: 45, bottom: 35 },
        xAxis: {
          type: 'category',
          data: dates,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#e2e8f0', width: 1 } },
          axisTick: { show: false },
          axisLabel: { color: '#64748b', fontSize: 11, margin: 12 }
        },
        yAxis: {
          type: 'value',
          axisLine: { show: false },
          splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
          axisLabel: { color: '#64748b', fontSize: 11 }
        },
        series: [{
          data: values,
          type: 'line',
          smooth: 0.4,
          symbol: 'circle',
          symbolSize: 8,
          symbolKeepAspect: true,
          lineStyle: {
            color: this.color,
            width: 3,
            shadowColor: this.color + '40',
            shadowBlur: 8
          },
          itemStyle: {
            color: this.color,
            borderColor: '#fff',
            borderWidth: 2,
            shadowColor: this.color + '30',
            shadowBlur: 6
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: this.color + '50' },
              { offset: 0.5, color: this.color + '20' },
              { offset: 1, color: this.color + '05' }
            ])
          },
          emphasis: {
            scale: 1.5,
            itemStyle: {
              shadowColor: this.color + '60',
              shadowBlur: 15
            }
          },
          animationDuration: 1500,
          animationEasing: 'cubicOut'
        }]
      })
    }
  }
}
</script>

<style scoped>
.line-chart-container {
  position: relative;
  padding: 16px 16px 8px;
}

.line-chart {
  width: 100%;
  height: 240px;
}

.line-chart::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--chart-color, #0d9488), transparent);
  opacity: 0.3;
}
</style>