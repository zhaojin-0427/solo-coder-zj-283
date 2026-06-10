<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="(stat, index) in stats" :key="index">
        <el-card class="stat-card" :body-style="{ padding: '24px' }">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="28" color="white"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">{{ stat.label }}</div>
              <div class="stat-value">{{ stat.formatter ? stat.formatter(stat.value) : stat.value }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="(stat, index) in orderStats" :key="'order-' + index">
        <el-card class="stat-card" :body-style="{ padding: '24px' }">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="28" color="white"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">{{ stat.label }}</div>
              <div class="stat-value">{{ stat.formatter ? stat.formatter(stat.value) : stat.value }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">近6个月材料成本趋势</span>
          </template>
          <div class="chart-container">
            <Line v-if="costChartData" :data="costChartData" :options="chartOptions" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">作品类型分布</span>
          </template>
          <div class="chart-container">
            <Doughnut v-if="typeChartData" :data="typeChartData" :options="doughnutOptions" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">闲置材料预警</span>
          </template>
          <el-table :data="idleMaterials" v-loading="loading" size="small">
            <el-table-column prop="name" label="材料名称" />
            <el-table-column prop="material_type" label="类型" width="100" />
            <el-table-column prop="remaining_length" label="剩余(米)" width="100">
              <template #default="{ row }">
                {{ row.remaining_length.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="days_idle" label="闲置天数" width="100">
              <template #default="{ row }">
                <el-tag :type="row.days_idle > 180 ? 'danger' : 'warning'">
                  {{ row.days_idle }}天
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">最新作品</span>
          </template>
          <el-table :data="recentProjects" v-loading="loading" size="small">
            <el-table-column prop="name" label="作品名称" />
            <el-table-column prop="project_type" label="类型" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : 'primary'">
                  {{ statusMap[row.status] }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="primary" link @click="goToProject(row.id)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span class="card-title">最新订单</span>
          </template>
          <el-table :data="recentOrders" v-loading="loading" size="small">
            <el-table-column prop="id" label="订单号" width="80" align="center" />
            <el-table-column prop="customer_name" label="客户姓名" width="120" />
            <el-table-column prop="project_name" label="关联作品">
              <template #default="{ row }">
                <span v-if="row.project_name">{{ row.project_name }}</span>
                <el-tag v-else type="info" size="small">未关联</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="报价" width="120" align="right">
              <template #default="{ row }">¥{{ row.quoted_price.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="delivery_date" label="交付日期" width="120" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.is_overdue ? '#f44336' : '' }">
                  {{ row.delivery_date || '-' }}
                </span>
                <el-tag v-if="row.is_overdue" type="danger" size="small" style="margin-left: 4px;">逾期</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="orderStatusType(row.status)" size="small">
                  {{ orderStatusMap[row.status] }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="交付风险" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="riskType(row.delivery_risk)" size="small">
                  {{ riskMap[row.delivery_risk] }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="primary" link @click="goToOrder(row.id)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { Line, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { statisticsApi, projectApi, orderApi } from '@/api'
import { Collection, Folder, Money, TrendCharts, Warning, Tickets, Wallet, ShoppingBag, Clock } from '@element-plus/icons-vue'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const router = useRouter()
const loading = ref(false)
const overview = ref({})
const orderOverview = ref({})
const idleMaterials = ref([])
const recentProjects = ref([])
const recentOrders = ref([])
const costChartData = ref(null)
const typeChartData = ref(null)

const statusMap = {
  'in_progress': '进行中',
  'completed': '已完成',
  'paused': '已暂停'
}

const orderStatusMap = {
  'pending': '待确认',
  'confirmed': '已确认',
  'in_progress': '制作中',
  'ready': '待交付',
  'completed': '已完成',
  'cancelled': '已取消'
}

const stats = [
  { label: '材料总数', value: 0, icon: Collection, color: '#e91e63' },
  { label: '作品总数', value: 0, icon: Folder, color: '#9c27b0' },
  { label: '库存总价值', value: 0, icon: Money, color: '#673ab7', formatter: (v) => `¥${v.toFixed(2)}` },
  { label: '平均利用率', value: 0, icon: TrendCharts, color: '#3f51b5', formatter: (v) => `${v}%` }
]

const orderStats = [
  { label: '订单总数', value: 0, icon: Tickets, color: '#ff9800' },
  { label: '总收入', value: 0, icon: Wallet, color: '#4caf50', formatter: (v) => `¥${v.toFixed(2)}` },
  { label: '待交付', value: 0, icon: Clock, color: '#ff5722' },
  { label: '利润率', value: 0, icon: ShoppingBag, color: '#795548', formatter: (v) => `${v}%` }
]

const riskMap = {
  'none': '无风险',
  'low': '低风险',
  'medium': '中风险',
  'high': '高风险'
}

const orderStatusType = (status) => {
  const map = {
    'pending': 'info',
    'confirmed': 'warning',
    'in_progress': 'primary',
    'ready': 'warning',
    'completed': 'success',
    'cancelled': 'info'
  }
  return map[status] || 'info'
}

const riskType = (risk) => {
  const map = {
    'none': 'success',
    'low': 'success',
    'medium': 'warning',
    'high': 'danger'
  }
  return map[risk] || 'info'
}

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { callback: (v) => `¥${v}` }
    }
  }
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right' }
  }
}

const colors = ['#e91e63', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3', '#00bcd4', '#4caf50', '#ff9800']

const fetchData = async () => {
  loading.value = true
  try {
    const [overviewRes, idleRes, projectsRes, costRes, typeRes, orderOverviewRes, ordersRes] = await Promise.all([
      statisticsApi.overview(),
      statisticsApi.idleMaterials({ days: 90 }),
      projectApi.list(),
      statisticsApi.costTrend(),
      statisticsApi.projectTypes(),
      statisticsApi.orderOverview(),
      orderApi.list()
    ])

    overview.value = overviewRes.data
    idleMaterials.value = idleRes.data.slice(0, 5)
    recentProjects.value = projectsRes.data.slice(0, 5)
    recentOrders.value = ordersRes.data.slice(0, 5)

    stats[0].value = overview.value.total_materials
    stats[1].value = overview.value.total_projects
    stats[2].value = overview.value.total_material_value
    stats[3].value = overview.value.avg_utilization

    orderOverview.value = orderOverviewRes.data
    orderStats[0].value = orderOverview.value.total_orders
    orderStats[1].value = orderOverview.value.total_revenue
    orderStats[2].value = orderOverview.value.pending_delivery
    orderStats[3].value = orderOverview.value.profit_rate

    costChartData.value = {
      labels: costRes.data.months,
      datasets: [{
        label: '材料成本',
        data: costRes.data.costs,
        borderColor: '#e91e63',
        backgroundColor: 'rgba(233, 30, 99, 0.1)',
        fill: true,
        tension: 0.4
      }]
    }

    typeChartData.value = {
      labels: typeRes.data.labels,
      datasets: [{
        data: typeRes.data.data,
        backgroundColor: colors.slice(0, typeRes.data.labels.length)
      }]
    }
  } finally {
    loading.value = false
  }
}

const goToProject = (id) => {
  router.push(`/projects/${id}`)
}

const goToOrder = (id) => {
  router.push(`/orders/${id}`)
}

onMounted(fetchData)
</script>

<style scoped>
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.card-title {
  font-weight: 600;
  color: #333;
}

.chart-container {
  height: 280px;
}
</style>
