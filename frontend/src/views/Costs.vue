<template>
  <div class="costs-page">
    <el-card class="summary-card">
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="summary-item">
            <div class="summary-label">总材料成本</div>
            <div class="summary-value primary">¥{{ overview?.total_material_cost?.toFixed(2) || '0.00' }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="summary-item">
            <div class="summary-label">已完成作品</div>
            <div class="summary-value success">{{ overview?.completed_projects || 0 }} 件</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="summary-item">
            <div class="summary-label">平均面料利用率</div>
            <div class="summary-value warning">{{ overview?.avg_utilization || 0 }}%</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="14">
        <el-card>
          <template #header>
            <span class="card-title">作品成本明细</span>
          </template>
          <el-table :data="projects" v-loading="loading" border>
            <el-table-column prop="name" label="作品名称" />
            <el-table-column prop="project_type" label="类型" width="100" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : 'primary'">{{ statusMap[row.status] }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="材料种类" width="100" align="center">
              <template #default="{ row }">{{ row.material_count }}</template>
            </el-table-column>
            <el-table-column label="完成数量" width="100" align="center">
              <template #default="{ row }">{{ row.completed_quantity }}</template>
            </el-table-column>
            <el-table-column label="总成本" width="120" align="right">
              <template #default="{ row }">
                <span class="cost-text">¥{{ row.total_material_cost.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="单件成本" width="120" align="right">
              <template #default="{ row }">
                <span class="cost-text highlight">¥{{ row.unit_material_cost.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="goToDetail(row.id)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header>
            <span class="card-title">成本趋势</span>
          </template>
          <div class="chart-container">
            <Line v-if="costChartData" :data="costChartData" :options="chartOptions" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span class="card-title">材料使用成本分析</span>
      </template>
      <el-table :data="materialCosts" border>
        <el-table-column prop="material_name" label="材料名称" />
        <el-table-column prop="material_type" label="类型" width="100" />
        <el-table-column label="总使用量(米)" width="120" align="right">
          <template #default="{ row }">{{ row.total_used.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="总损耗(米)" width="120" align="right">
          <template #default="{ row }">{{ row.total_loss.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="平均利用率" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.avg_utilization >= 0.9 ? 'success' : row.avg_utilization >= 0.7 ? 'warning' : 'danger'">
              {{ (row.avg_utilization * 100).toFixed(1) }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="总成本" width="120" align="right">
          <template #default="{ row }">
            <span class="cost-text">¥{{ row.total_cost.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="使用次数" width="100" align="center">
          <template #default="{ row }">{{ row.usage_count }} 次</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { projectApi, statisticsApi, materialApi } from '@/api'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const router = useRouter()
const loading = ref(false)
const projects = ref([])
const overview = ref({})
const costChartData = ref(null)
const materialCosts = ref([])

const statusMap = {
  'in_progress': '进行中',
  'completed': '已完成',
  'paused': '已暂停'
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

const fetchData = async () => {
  loading.value = true
  try {
    const [projectsRes, overviewRes, costRes] = await Promise.all([
      projectApi.list(),
      statisticsApi.overview(),
      statisticsApi.costTrend()
    ])
    
    projects.value = projectsRes.data.filter(p => p.material_count > 0)
    overview.value = overviewRes.data
    
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

    await calculateMaterialCosts()
  } finally {
    loading.value = false
  }
}

const calculateMaterialCosts = async () => {
  const usageMap = {}
  
  for (const project of projects.value) {
    const detailRes = await projectApi.get(project.id)
    for (const usage of detailRes.data.material_usages) {
      if (!usageMap[usage.material_id]) {
        usageMap[usage.material_id] = {
          material_id: usage.material_id,
          material_name: usage.material_name,
          material_type: usage.material_type,
          total_used: 0,
          total_loss: 0,
          total_cost: 0,
          usage_count: 0,
          utilizations: []
        }
      }
      usageMap[usage.material_id].total_used += usage.used_length
      usageMap[usage.material_id].total_loss += usage.cutting_loss
      usageMap[usage.material_id].total_cost += usage.total_cost
      usageMap[usage.material_id].usage_count += 1
      usageMap[usage.material_id].utilizations.push(usage.utilization_rate)
    }
  }
  
  materialCosts.value = Object.values(usageMap).map(item => ({
    ...item,
    avg_utilization: item.utilizations.reduce((a, b) => a + b, 0) / item.utilizations.length
  })).sort((a, b) => b.total_cost - a.total_cost)
}

const goToDetail = (id) => {
  router.push(`/projects/${id}`)
}

onMounted(fetchData)
</script>

<style scoped>
.summary-card {
  margin-bottom: 20px;
}

.summary-item {
  text-align: center;
  padding: 12px;
}

.summary-label {
  font-size: 14px;
  color: #999;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 28px;
  font-weight: 600;
}

.summary-value.primary {
  color: #e91e63;
}

.summary-value.success {
  color: #4caf50;
}

.summary-value.warning {
  color: #ff9800;
}

.card-title {
  font-weight: 600;
  color: #333;
}

.cost-text {
  font-family: monospace;
  font-weight: 500;
}

.cost-text.highlight {
  color: #e91e63;
  font-weight: 600;
}

.chart-container {
  height: 300px;
}
</style>
