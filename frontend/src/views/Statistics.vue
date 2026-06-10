<template>
  <div class="statistics-page">
    <el-row :gutter="20">
      <el-col :span="4" v-for="(stat, index) in overviewStats" :key="index">
        <el-card class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="24" color="white"><component :is="stat.icon" /></el-icon>
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
      <el-col :span="4" v-for="(stat, index) in orderStats" :key="'order-' + index">
        <el-card class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="24" color="white"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">{{ stat.label }}</div>
              <div class="stat-value">{{ stat.formatter ? stat.formatter(stat.value) : stat.value }}</div>
              <div v-if="stat.subLabel" class="stat-sublabel">{{ stat.subLabel }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">本月各类型材料消耗速度</span>
            <el-tag type="info" size="small">单位：米</el-tag>
          </template>
          <div class="chart-container">
            <Bar v-if="consumptionChartData" :data="consumptionChartData" :options="barOptions" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">各类型面料利用率</span>
            <el-tag type="info" size="small">单位：%</el-tag>
          </template>
          <div class="chart-container">
            <Bar v-if="utilizationChartData" :data="utilizationChartData" :options="utilizationOptions" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">作品类型分布</span>
          </template>
          <div class="chart-container">
            <Pie v-if="typeChartData" :data="typeChartData" :options="pieOptions" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">近6个月材料成本趋势</span>
          </template>
          <div class="chart-container">
            <Line v-if="costChartData" :data="costChartData" :options="lineOptions" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span class="card-title">近6个月订单收入趋势</span>
            <el-tag type="success" size="small">单位：元</el-tag>
          </template>
          <div class="chart-container">
            <Line v-if="revenueChartData" :data="revenueChartData" :options="revenueOptions" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title">订单预警</span>
        </div>
      </template>
      <el-alert 
        v-if="overdueOrders.length > 0 || highRiskOrders.length > 0" 
        :title="`发现 ${overdueOrders.length} 个逾期订单，${highRiskOrders.length} 个高风险订单，请及时处理`" 
        type="error" 
        show-icon 
        style="margin-bottom: 16px;"
      />
      <el-tabs v-model="orderAlertTab">
        <el-tab-pane label="逾期订单" name="overdue">
          <el-table :data="overdueOrders" v-loading="loading" border>
            <el-table-column prop="order_id" label="订单号" width="80" align="center" />
            <el-table-column prop="customer_name" label="客户姓名" width="120" />
            <el-table-column prop="project_name" label="关联作品" />
            <el-table-column prop="days_overdue" label="逾期天数" width="100" align="center">
              <template #default="{ row }">
                <el-tag type="danger">{{ row.days_overdue }} 天</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="goToOrder(row.order_id)">
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="overdueOrders.length === 0" description="暂无逾期订单" />
        </el-tab-pane>
        <el-tab-pane label="高风险订单" name="high_risk">
          <el-table :data="highRiskOrders" v-loading="loading" border>
            <el-table-column prop="order_id" label="订单号" width="80" align="center" />
            <el-table-column prop="customer_name" label="客户姓名" width="120" />
            <el-table-column prop="project_name" label="关联作品" />
            <el-table-column prop="days_until_delivery" label="剩余天数" width="100" align="center">
              <template #default="{ row }">
                <el-tag type="warning">{{ row.days_until_delivery }} 天</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="goToOrder(row.order_id)">
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="highRiskOrders.length === 0" description="暂无高风险订单" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title">长期闲置材料预警</span>
          <div class="filter-group">
            <el-form :inline="true">
              <el-form-item label="闲置天数">
                <el-select v-model="idleDays" @change="fetchIdleMaterials" style="width: 120px;">
                  <el-option label="30天" :value="30" />
                  <el-option label="60天" :value="60" />
                  <el-option label="90天" :value="90" />
                  <el-option label="180天" :value="180" />
                </el-select>
              </el-form-item>
              <el-form-item label="剩余不少于">
                <el-input-number v-model="minRemaining" :min="0.1" :step="0.1" @change="fetchIdleMaterials" style="width: 100px;" />
                <span style="margin-left: 4px;">米</span>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </template>
      <el-alert 
        v-if="idleMaterials.length > 0" 
        :title="`发现 ${idleMaterials.length} 种长期闲置材料，请及时处理或利用`" 
        type="warning" 
        show-icon 
        style="margin-bottom: 16px;"
      />
      <el-table :data="idleMaterials" v-loading="loading" border>
        <el-table-column label="材料照片" width="100" align="center">
          <template #default="{ row }">
            <img v-if="row.photo" :src="getImageUrl(row.photo)" class="thumb-image" />
            <el-icon v-else :size="32" color="#ccc"><Picture /></el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="材料名称" />
        <el-table-column prop="material_type" label="类型" width="100" />
        <el-table-column prop="color_code" label="色号" width="100">
          <template #default="{ row }">#{{ row.color_code || '-' }}</template>
        </el-table-column>
        <el-table-column prop="remaining_length" label="剩余(米)" width="100" align="right">
          <template #default="{ row }">{{ row.remaining_length.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="库存价值" width="120" align="right">
          <template #default="{ row }">¥{{ row.total_value.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="闲置天数" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.days_idle > 180 ? 'danger' : row.days_idle > 90 ? 'warning' : 'info'">
              {{ row.days_idle }} 天
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后使用" width="120" align="center">
          <template #default="{ row }">
            {{ row.last_used || '从未使用' }}
          </template>
        </el-table-column>
        <el-table-column label="采购日期" width="120" align="center">
          <template #default="{ row }">{{ row.purchase_date }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Bar, Pie, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { useRouter } from 'vue-router'
import { statisticsApi, getImageUrl } from '@/api'
import { Collection, Folder, Money, TrendCharts, Warning, Picture, Tickets, Wallet, ShoppingBag, Clock } from '@element-plus/icons-vue'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
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
const idleDays = ref(90)
const minRemaining = ref(1)
const orderAlertTab = ref('overdue')
const overdueOrders = ref([])
const highRiskOrders = ref([])

const consumptionChartData = ref(null)
const utilizationChartData = ref(null)
const typeChartData = ref(null)
const costChartData = ref(null)
const revenueChartData = ref(null)

const colors = ['#e91e63', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3', '#00bcd4', '#4caf50', '#ff9800', '#795548', '#607d8b']

const overviewStats = [
  { label: '材料总数', value: 0, icon: Collection, color: '#e91e63' },
  { label: '作品总数', value: 0, icon: Folder, color: '#9c27b0' },
  { label: '库存总价值', value: 0, icon: Money, color: '#673ab7', formatter: (v) => `¥${v.toFixed(2)}` },
  { label: '平均利用率', value: 0, icon: TrendCharts, color: '#3f51b5', formatter: (v) => `${v}%` }
]

const orderStats = [
  { label: '订单总数', value: 0, icon: Tickets, color: '#ff9800' },
  { label: '总收入', value: 0, icon: Wallet, color: '#4caf50', formatter: (v) => `¥${v.toFixed(2)}` },
  { label: '总利润', value: 0, icon: ShoppingBag, color: '#00bcd4', formatter: (v) => `¥${v.toFixed(2)}` },
  { label: '利润率', value: 0, icon: TrendCharts, color: '#795548', formatter: (v) => `${v}%` },
  { label: '待交付', value: 0, icon: Clock, color: '#ff5722' },
  { label: '逾期订单', value: 0, icon: Warning, color: '#f44336' }
]

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    y: { beginAtZero: true }
  }
}

const utilizationOptions = {
  ...barOptions,
  scales: {
    y: {
      beginAtZero: true,
      max: 100,
      ticks: { callback: (v) => `${v}%` }
    }
  }
}

const pieOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right' }
  }
}

const lineOptions = {
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

const revenueOptions = {
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

const fetchData = async () => {
  loading.value = true
  try {
    const [overviewRes, consumptionRes, utilizationRes, typeRes, costRes, orderOverviewRes, orderTrendRes, anomaliesRes] = await Promise.all([
      statisticsApi.overview(),
      statisticsApi.consumption(),
      statisticsApi.utilization(),
      statisticsApi.projectTypes(),
      statisticsApi.costTrend(),
      statisticsApi.orderOverview(),
      statisticsApi.orderTrend(),
      statisticsApi.anomalies()
    ])

    overview.value = overviewRes.data
    
    overviewStats[0].value = overview.value.total_materials
    overviewStats[1].value = overview.value.total_projects
    overviewStats[2].value = overview.value.total_material_value
    overviewStats[3].value = overview.value.avg_utilization

    consumptionChartData.value = {
      labels: consumptionRes.data.labels,
      datasets: [{
        label: '消耗量',
        data: consumptionRes.data.data,
        backgroundColor: colors.slice(0, consumptionRes.data.labels.length)
      }]
    }

    utilizationChartData.value = {
      labels: utilizationRes.data.labels,
      datasets: [{
        label: '利用率',
        data: utilizationRes.data.data,
        backgroundColor: colors.slice(0, utilizationRes.data.labels.length).map(c => c + 'cc')
      }]
    }

    typeChartData.value = {
      labels: typeRes.data.labels,
      datasets: [{
        data: typeRes.data.data,
        backgroundColor: colors.slice(0, typeRes.data.labels.length)
      }]
    }

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

    orderOverview.value = orderOverviewRes.data
    orderStats[0].value = orderOverview.value.total_orders
    orderStats[1].value = orderOverview.value.total_revenue
    orderStats[2].value = orderOverview.value.total_profit
    orderStats[3].value = orderOverview.value.profit_rate
    orderStats[4].value = orderOverview.value.pending_delivery
    orderStats[5].value = orderOverview.value.overdue_orders

    revenueChartData.value = {
      labels: orderTrendRes.data.months,
      datasets: [{
        label: '订单收入',
        data: orderTrendRes.data.revenues,
        borderColor: '#4caf50',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        fill: true,
        tension: 0.4
      }]
    }

    overdueOrders.value = anomaliesRes.data.anomalies?.overdue_orders || []
    highRiskOrders.value = anomaliesRes.data.anomalies?.high_risk_orders || []

    await fetchIdleMaterials()
  } finally {
    loading.value = false
  }
}

const fetchIdleMaterials = async () => {
  try {
    const res = await statisticsApi.idleMaterials({
      days: idleDays.value,
      min_remaining: minRemaining.value
    })
    idleMaterials.value = res.data
  } catch (err) {
    console.error('获取闲置材料失败', err)
  }
}

const goToOrder = (orderId) => {
  router.push(`/orders/${orderId}`)
}

onMounted(fetchData)
</script>

<style scoped>
.stat-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.stat-sublabel {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.card-title {
  font-weight: 600;
  color: #333;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
}

.thumb-image {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
}
</style>
