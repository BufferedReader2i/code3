<template>
  <div class="bar-chart-container">
    <div ref="chartRef" class="bar-chart"></div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

const COLORS = [
  '#6366f1', '#818cf8', '#a5b4fc', '#c7d2fe', '#e0e7ff',
  '#f59e0b', '#fbbf24', '#fcd34d', '#fde68a', '#fef3c7'
]

export default {
  name: 'BarChart',
  props: {
    data: { type: Array, default: () => [] },
    title: { type: String, default: '' },
    nameKey: { type: String, default: 'title' },
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
      // 取前10条数据并反转顺序（让最大的在顶部）
      const list = [...this.data].slice(0, 10).reverse()
      const names = list.map(d => {
        const name = d[this.nameKey] || ''
        return name.length > 12 ? name.substring(0, 12) + '...' : name
      })
      const values = list.map(d => d[this.valueKey])
      const colors = list.map((_, i) => COLORS[i % COLORS.length])
      
      this.chart.setOption({
        title: {
          text: this.title,
          left: 'center',
          top: 8,
          textStyle: { fontSize: 14, fontWeight: 600, color: '#1e293b', fontFamily: 'Inter, system-ui, sans-serif' }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(99, 102, 241, 0.1)' } },
          backgroundColor: 'rgba(30, 41, 59, 0.9)',
          borderColor: 'transparent',
          borderRadius: 8,
          padding: [10, 14],
          textStyle: { color: '#fff', fontSize: 12 }
        },
        grid: { left: 130, right: 24, top: 40, bottom: 24 },
        xAxis: {
          type: 'value',
          axisLine: { show: false },
          splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
          axisLabel: { color: '#64748b', fontSize: 11 }
        },
        yAxis: {
          type: 'category',
          data: names,
          axisLine: { lineStyle: { color: '#e2e8f0', width: 1 } },
          axisTick: { show: false },
          axisLabel: { color: '#64748b', fontSize: 11 }
        },
        series: [{
          type: 'bar',
          data: values.map((v, i) => ({
            value: v,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: colors[i] },
                { offset: 1, color: colors[i] + 'cc' }
              ]),
              borderRadius: [0, 4, 4, 0]
            }
          })),
          barWidth: '55%',
          label: {
            show: true,
            position: 'right',
            color: '#64748b',
            fontSize: 11,
            distance: 8
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 15,
              shadowColor: 'rgba(99, 102, 241, 0.3)'
            }
          },
          animationDuration: 1200,
          animationEasing: 'cubicOut'
        }]
      })
    }
  }
}
</script>

<style scoped>
.bar-chart-container {
  position: relative;
  padding: 16px 16px 8px;
}

.bar-chart {
  width: 100%;
  height: 280px;
}
</style>