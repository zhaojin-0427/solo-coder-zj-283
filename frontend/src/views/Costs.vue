<template>
  <div class="costs-page">
    <el-card v-if="anomaliesData && anomaliesData.total_count > 0" class="anomalies-card">
      <template #header>
        <div class="anomalies-header">
          <div class="anomalies-title">
            <el-icon :size="20" color="#f44336"><Warning /></el-icon>
            <span>异常数据提示区（共发现 {{ anomaliesData.total_count }} 个问题）</span>
          </div>
          <div class="anomalies-tabs">
            <el-tag 
              v-for="(count, key) in anomaliesData.summary" 
              :key="key"
              :type="count > 0 ? 'danger' : 'info'"
              :effect="count > 0 ? 'light' : 'plain'"
              class="anomaly-tag"
            >
              {{ anomalyLabels[key] }}: {{ count }}
            </el-tag>
          </div>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :span="12" v-if="anomaliesData.anomalies.insufficient_stock.length > 0">
          <div class="anomaly-section">
            <h4 class="anomaly-section-title">
              <el-icon color="#ff9800"><Warning /></el-icon>
              库存不足
            </h4>
            <div 
              v-for="item in anomaliesData.anomalies.insufficient_stock" 
              :key="`stock-${item.material_id}`"
              class="anomaly-item"
            >
              <span class="anomaly-message">{{ item.message }}</span>
              <el-button type="primary" link size="small" @click="goToMaterial(item.material_id)">
                查看材料
              </el-button>
            </div>
          </div>
        </el-col>
        <el-col :span="12" v-if="anomaliesData.anomalies.over_target.length > 0">
          <div class="anomaly-section">
            <h4 class="anomaly-section-title">
              <el-icon color="#f44336"><Warning /></el-icon>
              进度超额
            </h4>
            <div 
              v-for="item in anomaliesData.anomalies.over_target" 
              :key="`target-${item.project_id}`"
              class="anomaly-item"
            >
              <span class="anomaly-message">{{ item.message }}</span>
              <el-button type="primary" link size="small" @click="goToProject(item.project_id)">
                查看作品
              </el-button>
            </div>
          </div>
        </el-col>
        <el-col :span="12" v-if="anomaliesData.anomalies.material_conflicts.length > 0">
          <div class="anomaly-section">
            <h4 class="anomaly-section-title">
              <el-icon color="#e91e63"><Warning /></el-icon>
              材料引用冲突
            </h4>
            <div 
              v-for="item in anomaliesData.anomalies.material_conflicts" 
              :key="`conflict-${item.material_id}`"
              class="anomaly-item"
            >
              <span class="anomaly-message">{{ item.message }}</span>
              <div class="anomaly-actions">
                <el-button type="primary" link size="small" @click="goToMaterial(item.material_id)">
                  查看材料
                </el-button>
                <el-button 
                  v-for="p in item.used_by_projects" 
                  :key="p.project_id"
                  type="warning" 
                  link 
                  size="small" 
                  @click="goToProject(p.project_id)"
                >
                  作品: {{ p.project_name }}
                </el-button>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="12" v-if="anomaliesData.anomalies.negative_inventory.length > 0">
          <div class="anomaly-section">
            <h4 class="anomaly-section-title">
              <el-icon color="#9c27b0"><Warning /></el-icon>
              负库存
            </h4>
            <div 
              v-for="item in anomaliesData.anomalies.negative_inventory" 
              :key="`negative-${item.material_id}`"
              class="anomaly-item"
            >
              <span class="anomaly-message">{{ item.message }}</span>
              <el-button type="primary" link size="small" @click="goToMaterial(item.material_id)">
                查看材料
              </el-button>
            </div>
          </div>
        </el-col>
        <el-col :span="12" v-if="anomaliesData.anomalies.over_usage_rate.length > 0">
          <div class="anomaly-section">
            <h4 class="anomaly-section-title">
              <el-icon color="#673ab7"><Warning /></el-icon>
              使用率超过100%
            </h4>
            <div 
              v-for="item in anomaliesData.anomalies.over_usage_rate" 
              :key="`usage-${item.material_id}`"
              class="anomaly-item"
            >
              <span class="anomaly-message">{{ item.message }}</span>
              <el-button type="primary" link size="small" @click="goToMaterial(item.material_id)">
                查看材料
              </el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

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
import { Warning } from '@element-plus/icons-vue'

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
const anomaliesData = ref(null)

const anomalyLabels = {
  insufficient_stock: '库存不足',
  over_target: '进度超额',
  material_conflicts: '引用冲突',
  negative_inventory: '负库存',
  over_usage_rate: '使用率超限'
}

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
    const [projectsRes, overviewRes, costRes, anomaliesRes] = await Promise.all([
      projectApi.list(),
      statisticsApi.overview(),
      statisticsApi.costTrend(),
      statisticsApi.anomalies()
    ])
    
    anomaliesData.value = anomaliesRes.data
    
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

const goToMaterial = (id) => {
  router.push({ path: '/materials', query: { highlight: id } })
}

const goToProject = (id) => {
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

.anomalies-card {
  margin-bottom: 20px;
  border: 1px solid #f44336;
}

.anomalies-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.anomalies-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #f44336;
}

.anomalies-tabs {
  display: flex;
  gap: 8px;
}

.anomaly-tag {
  cursor: default;
}

.anomaly-section {
  padding: 12px;
  background: #fff8f8;
  border-radius: 8px;
  margin-bottom: 12px;
}

.anomaly-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #333;
}

.anomaly-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  margin-bottom: 8px;
  border-left: 3px solid #f44336;
}

.anomaly-item:last-child {
  margin-bottom: 0;
}

.anomaly-message {
  font-size: 13px;
  color: #666;
  flex: 1;
}

.anomaly-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
  margin-left: 12px;
}
</style>
