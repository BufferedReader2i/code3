<template>
  <div class="pie-chart-container">
    <div ref="chartRef" class="pie-chart"></div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

const COLORS = [
  '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b',
  '#10b981', '#06b6d4', '#3b82f6', '#14b8a6', '#a855f7'
]

export default {
  name: 'PieChart',
  props: {
    data: { type: Array, default: () => [] },
    title: { type: String, default: '' },
    nameKey: { type: String, default: 'name' },
    valueKey: { type: String, default: 'count' }
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
      const chartData = this.data.map((d, i) => ({
        name: d[this.nameKey],
        value: d[this.valueKey],
        itemStyle: {
          color: COLORS[i % COLORS.length],
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2
        }
      }))
      
      const total = this.data.reduce((sum, d) => sum + (d[this.valueKey] || 0), 0)
      
      this.chart.setOption({
        title: {
          text: this.title,
          left: 'center',
          top: 8,
          textStyle: { fontSize: 14, fontWeight: 600, color: '#1e293b', fontFamily: 'Inter, system-ui, sans-serif' }
        },
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(30, 41, 59, 0.9)',
          borderColor: 'transparent',
          borderRadius: 8,
          padding: [10, 14],
          textStyle: { color: '#fff', fontSize: 12 },
          formatter: (params) => {
            return `<div style="display:flex;align-items:center;gap:8px;">
              <span style="width:10px;height:10px;border-radius:50%;background:${params.color};display:inline-block;"></span>
              <span>${params.name}:</span>
              <strong>${params.value}</strong>
              <span style="color:#94a3b8;">(${params.percent}%)</span>
            </div>`
          }
        },
        legend: {
          orient: 'vertical',
          right: 8,
          top: 'center',
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 8,
          textStyle: { color: '#64748b', fontSize: 11, padding: [0, 0, 0, 4] },
          icon: 'circle'
        },
        series: [{
          type: 'pie',
          name: this.title,
          radius: ['45%', '72%'],
          center: ['35%', '52%'],
          avoidLabelOverlap: true,
          itemRadius: 6,
          hoverOffset: 12,
          stillShowZeroSum: false,
          label: { show: false },
          emphasis: {
            scale: true,
            scaleSize: 8,
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(0, 0, 0, 0.15)'
            }
          },
          labelLine: { show: false },
          data: chartData,
          animationType: 'scale',
          animationDuration: 800,
          animationEasing: 'elasticOut'
        }]
      })
    }
  }
}
</script>

<style scoped>
.pie-chart-container {
  position: relative;
  padding: 16px 16px 8px;
}

.pie-chart {
  width: 100%;
  height: 240px;
}
</style>