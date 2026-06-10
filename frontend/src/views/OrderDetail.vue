<template>
  <div class="order-detail">
    <el-page-header @back="goBack" :content="`订单 #${order?.id}`" class="page-header">
      <template #extra>
        <el-button @click="openEditDialog">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button type="danger" @click="deleteOrder">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </template>
    </el-page-header>

    <el-row :gutter="20" style="margin-top: 20px;" v-loading="loading">
      <el-col :span="16">
        <el-alert 
          v-if="order?.delivery_risk === 'high'" 
          type="error" 
          show-icon 
          style="margin-bottom: 16px;"
        >
          <template #title>
            <span>交付风险高！</span>
            <span v-if="order?.is_overdue">订单已逾期 {{ -order.days_until_delivery }} 天</span>
            <span v-else>仅剩 {{ order?.days_until_delivery }} 天交付时间</span>
          </template>
        </el-alert>
        <el-alert 
          v-else-if="order?.delivery_risk === 'medium'" 
          type="warning" 
          show-icon 
          style="margin-bottom: 16px;"
        >
          <template #title>交付风险中等，请留意制作进度</template>
        </el-alert>

        <el-card class="info-card" style="margin-bottom: 16px;">
          <template #header>
            <div class="card-header">
              <span class="card-title">客户信息</span>
            </div>
          </template>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">客户姓名</div>
                <div class="info-value">{{ order?.customer_name }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">联系方式</div>
                <div class="info-value">{{ order?.contact_info }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">订单来源</div>
                <div class="info-value">{{ order?.order_source || '-' }}</div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <el-card class="info-card" style="margin-bottom: 16px;">
          <template #header>
            <div class="card-header">
              <span class="card-title">作品需求</span>
              <el-tag :type="statusType(order?.status)" size="small">{{ statusMap[order?.status] }}</el-tag>
            </div>
          </template>
          <div class="info-item" v-if="order?.requirement">
            <div class="info-label">需求描述</div>
            <div class="info-value">{{ order.requirement }}</div>
          </div>
          <el-row :gutter="20" style="margin-top: 12px;">
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">关联作品</div>
                <div class="info-value">
                  <el-link v-if="order?.project_id" type="primary" @click="goToProject">
                    {{ order.project_name }}
                  </el-link>
                  <span v-else>-</span>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">交付日期</div>
                <div class="info-value" :style="{ color: order?.is_overdue ? '#f44336' : '' }">
                  {{ order?.delivery_date || '-' }}
                  <el-tag v-if="order?.is_overdue" type="danger" size="small" style="margin-left: 4px;">逾期</el-tag>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">交付风险</div>
                <div class="info-value">
                  <el-tag :type="riskType(order?.delivery_risk)" size="small">
                    {{ riskMap[order?.delivery_risk] }}
                  </el-tag>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <el-tabs v-model="activeTab" class="detail-tabs">
          <el-tab-pane label="制作进度" name="progress">
            <div class="tab-header">
              <span class="section-title">制作进度</span>
              <el-progress 
                v-if="order?.project_id"
                :percentage="order.project_progress" 
                :stroke-width="12"
                :color="order?.project_status === 'completed' ? '#67c23a' : '#e91e63'"
                style="width: 300px;"
              />
              <el-tag v-if="order?.project_status" :type="projectStatusType(order?.project_status)" size="small">
                {{ projectStatusMap[order?.project_status] }}
              </el-tag>
            </div>
            <el-timeline v-if="order?.process_photos?.length" class="photo-timeline">
              <el-timeline-item
                v-for="(photo, index) in sortedPhotos"
                :key="photo.id"
                :timestamp="photo.created_at"
                placement="top"
                :type="timelineColors[index % timelineColors.length]"
              >
                <el-card class="photo-card">
                  <div class="photo-header">
                    <el-tag :type="timelineColors[index % timelineColors.length]" size="small">
                      {{ photo.stage }}
                    </el-tag>
                  </div>
                  <div class="photo-content">
                    <img :src="getImageUrl(photo.photo)" alt="" class="process-image" />
                  </div>
                  <div class="photo-meta" v-if="photo.description">
                    <div class="meta-label">描述</div>
                    <div class="meta-content">{{ photo.description }}</div>
                  </div>
                  <div class="photo-meta" v-if="photo.experience">
                    <div class="meta-label">制作经验</div>
                    <div class="meta-content experience">{{ photo.experience }}</div>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无过程照片" />
          </el-tab-pane>

          <el-tab-pane label="材料成本" name="materials">
            <div class="tab-header">
              <span class="section-title">材料清单</span>
              <div class="cost-summary">
                <span>总材料成本：</span>
                <span class="cost-total">¥{{ order?.material_cost?.toFixed(2) || '0.00' }}</span>
              </div>
            </div>
            <el-table :data="order?.material_usages || []" border>
              <el-table-column prop="material_name" label="材料名称" />
              <el-table-column prop="material_type" label="类型" width="100" />
              <el-table-column prop="color_code" label="色号" width="100">
                <template #default="{ row }">#{{ row.color_code || '-' }}</template>
              </el-table-column>
              <el-table-column prop="used_length" label="用料(米)" width="100" align="right">
                <template #default="{ row }">{{ row.used_length.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="cutting_loss" label="损耗(米)" width="100" align="right">
                <template #default="{ row }">{{ row.cutting_loss.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column label="利用率" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.utilization_rate >= 0.9 ? 'success' : row.utilization_rate >= 0.7 ? 'warning' : 'danger'">
                    {{ (row.utilization_rate * 100).toFixed(1) }}%
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="unit_price" label="单价" width="100" align="right">
                <template #default="{ row }">¥{{ row.unit_price.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="total_cost" label="成本" width="100" align="right">
                <template #default="{ row }">¥{{ row.total_cost.toFixed(2) }}</template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="利润分析" name="profit">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-card class="stat-card">
                  <div class="stat-icon" style="background-color: #67c23a;">
                    <el-icon :size="24" color="white"><Money /></el-icon>
                  </div>
                  <div class="stat-label">报价</div>
                  <div class="stat-value">¥{{ order?.quoted_price?.toFixed(2) || '0.00' }}</div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card class="stat-card">
                  <div class="stat-icon" style="background-color: #e91e63;">
                    <el-icon :size="24" color="white"><ShoppingBag /></el-icon>
                  </div>
                  <div class="stat-label">材料成本</div>
                  <div class="stat-value">¥{{ order?.material_cost?.toFixed(2) || '0.00' }}</div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card class="stat-card">
                  <div class="stat-icon" style="background-color: #ff9800;">
                    <el-icon :size="24" color="white"><Wallet /></el-icon>
                  </div>
                  <div class="stat-label">预估利润</div>
                  <div class="stat-value" :style="{ color: order?.profit_estimate >= 0 ? '#67c23a' : '#f44336' }">
                    ¥{{ order?.profit_estimate?.toFixed(2) || '0.00' }}
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card class="stat-card">
                  <div class="stat-icon" style="background-color: #2196f3;">
                    <el-icon :size="24" color="white"><TrendCharts /></el-icon>
                  </div>
                  <div class="stat-label">利润率</div>
                  <div class="stat-value" :style="{ color: order?.profit_margin >= 30 ? '#67c23a' : order?.profit_margin >= 15 ? '#ff9800' : '#f44336' }">
                    {{ order?.profit_margin?.toFixed(2) || '0.00' }}%
                  </div>
                </el-card>
              </el-col>
            </el-row>
            <el-card style="margin-top: 20px;">
              <template #header>
                <span class="card-title">建议报价参考</span>
                <el-tag type="success" size="small">基于材料成本自动计算</el-tag>
              </template>
              <el-row :gutter="20">
                <el-col :span="12">
                  <div class="info-item">
                    <div class="info-label">材料成本</div>
                    <div class="info-value">¥{{ order?.material_cost?.toFixed(2) || '0.00' }}</div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="info-item">
                    <div class="info-label">建议报价</div>
                    <div class="info-value price">¥{{ order?.suggested_price?.toFixed(2) || '0.00' }}</div>
                  </div>
                </el-col>
              </el-row>
              <el-alert 
                v-if="order && order.quoted_price > 0 && order.quoted_price < order.suggested_price" 
                type="warning" 
                show-icon 
                style="margin-top: 16px;"
              >
                当前报价低于建议报价，利润率可能偏低
              </el-alert>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </el-col>

      <el-col :span="8">
        <el-card class="info-card" style="margin-bottom: 16px;">
          <template #header>
            <span class="card-title">订单状态</span>
          </template>
          <el-form label-width="100px">
            <el-form-item label="当前状态">
              <el-tag :type="statusType(order?.status)" size="large">{{ statusMap[order?.status] }}</el-tag>
            </el-form-item>
            <el-form-item label="更新状态">
              <el-select v-model="newStatus" placeholder="选择新状态" style="width: 100%;" @change="updateStatus">
                <el-option v-for="(label, value) in statusMap" :key="value" :label="label" :value="value" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="info-card" style="margin-bottom: 16px;">
          <template #header>
            <span class="card-title">收款信息</span>
          </template>
          <div class="info-item">
            <div class="info-label">报价</div>
            <div class="info-value price">¥{{ order?.quoted_price?.toFixed(2) || '0.00' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">已收定金</div>
            <div class="info-value">¥{{ order?.deposit?.toFixed(2) || '0.00' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">应收尾款</div>
            <div class="info-value">¥{{ order?.balance?.toFixed(2) || '0.00' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">实收合计</div>
            <div class="info-value">¥{{ ((order?.deposit || 0) + (order?.balance || 0)).toFixed(2) }}</div>
          </div>
        </el-card>

        <el-card class="info-card" v-if="order?.notes">
          <template #header>
            <span class="card-title">备注</span>
          </template>
          <div class="info-value">{{ order.notes }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="editDialogVisible" title="编辑订单" width="700px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户姓名" prop="customer_name">
              <el-input v-model="editForm.customer_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系方式" prop="contact_info">
              <el-input v-model="editForm.contact_info" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="订单来源">
              <el-select v-model="editForm.order_source" placeholder="请选择来源" style="width: 100%;" clearable>
                <el-option v-for="s in orderSources" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="交付日期" prop="delivery_date">
              <el-date-picker v-model="editForm.delivery_date" type="date" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="作品需求" prop="requirement">
          <el-input v-model="editForm.requirement" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="关联作品">
          <el-radio-group v-model="editLinkType">
            <el-radio value="none">暂不关联</el-radio>
            <el-radio value="existing">关联已有作品</el-radio>
            <el-radio value="new">新建作品</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="editLinkType === 'existing'" label="选择作品">
          <el-select v-model="editForm.project_id" placeholder="请选择作品" style="width: 100%;" filterable>
            <el-option 
              v-for="p in availableProjects" 
              :key="p.id" 
              :label="`${p.name} (${p.project_type})`" 
              :value="p.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editLinkType === 'new'" label="作品名称">
          <el-input v-model="editForm.project_name" placeholder="请输入作品名称" />
        </el-form-item>
        <el-form-item v-if="editLinkType === 'new'" label="作品类型">
          <el-select v-model="editForm.project_type" style="width: 100%;">
            <el-option v-for="t in projectTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editLinkType === 'new'" label="目标数量">
          <el-input-number v-model="editForm.target_quantity" :min="1" style="width: 100%;" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="报价" prop="quoted_price">
              <el-input-number v-model="editForm.quoted_price" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="定金" prop="deposit">
              <el-input-number v-model="editForm.deposit" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="尾款" prop="balance">
              <el-input-number v-model="editForm.balance" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="订单状态" prop="status">
          <el-radio-group v-model="editForm.status">
            <el-radio value="pending">待确认</el-radio>
            <el-radio value="confirmed">已确认</el-radio>
            <el-radio value="in_progress">制作中</el-radio>
            <el-radio value="ready">待交付</el-radio>
            <el-radio value="completed">已完成</el-radio>
            <el-radio value="cancelled">已取消</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { orderApi, projectApi, getImageUrl, formatDate } from '@/api'
import { Edit, Delete, Money, Wallet, TrendCharts, ShoppingBag } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const orderId = computed(() => parseInt(route.params.id))

const loading = ref(false)
const order = ref(null)
const activeTab = ref('progress')
const newStatus = ref('')
const availableProjects = ref([])

const editDialogVisible = ref(false)
const editFormRef = ref(null)
const editLinkType = ref('none')

const orderSources = ['微信', '淘宝', '闲鱼', '抖音', '线下门店', '朋友介绍', '其他']
const projectTypes = ['服装', '包包', '家居装饰', '玩偶', '拼布', '刺绣', '其他']
const timelineColors = ['primary', 'success', 'warning', 'danger', 'info']

const statusMap = {
  'pending': '待确认',
  'confirmed': '已确认',
  'in_progress': '制作中',
  'ready': '待交付',
  'completed': '已完成',
  'cancelled': '已取消'
}

const statusType = (status) => {
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

const projectStatusMap = {
  'in_progress': '进行中',
  'completed': '已完成',
  'paused': '已暂停'
}

const projectStatusType = (status) => {
  const map = { 'in_progress': 'primary', 'completed': 'success', 'paused': 'info' }
  return map[status] || 'info'
}

const riskMap = {
  'none': '无风险',
  'low': '低风险',
  'medium': '中风险',
  'high': '高风险'
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

const sortedPhotos = computed(() => {
  if (!order.value?.process_photos) return []
  return [...order.value.process_photos].sort((a, b) => a.stage_order - b.stage_order)
})

const editForm = reactive({
  customer_name: '',
  contact_info: '',
  order_source: '',
  requirement: '',
  delivery_date: null,
  quoted_price: 0,
  deposit: 0,
  balance: 0,
  status: 'pending',
  notes: '',
  project_id: null,
  project_name: '',
  project_type: '其他',
  target_quantity: 1
})

const editRules = {
  customer_name: [{ required: true, message: '请输入客户姓名', trigger: 'blur' }],
  contact_info: [{ required: true, message: '请输入联系方式', trigger: 'blur' }],
  delivery_date: [{ required: true, message: '请选择交付日期', trigger: 'change' }],
  quoted_price: [{ required: true, message: '请输入报价', trigger: 'blur' }],
  deposit: [{ required: true, message: '请输入定金', trigger: 'blur' }],
  balance: [{ required: true, message: '请输入尾款', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const [orderRes, projectsRes] = await Promise.all([
      orderApi.get(orderId.value),
      projectApi.list()
    ])
    order.value = orderRes.data
    newStatus.value = order.value.status
    availableProjects.value = projectsRes.data
  } finally {
    loading.value = false
  }
}

const updateStatus = async () => {
  if (!order.value || newStatus.value === order.value.status) return
  
  try {
    await orderApi.update(orderId.value, { status: newStatus.value })
    ElMessage.success('状态更新成功')
    fetchData()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '更新失败')
  }
}

const openEditDialog = () => {
  if (!order.value) return
  editLinkType.value = order.value.project_id ? 'existing' : 'none'
  Object.assign(editForm, {
    customer_name: order.value.customer_name,
    contact_info: order.value.contact_info,
    order_source: order.value.order_source || '',
    requirement: order.value.requirement || '',
    delivery_date: order.value.delivery_date ? new Date(order.value.delivery_date) : null,
    quoted_price: order.value.quoted_price,
    deposit: order.value.deposit,
    balance: order.value.balance,
    status: order.value.status,
    notes: order.value.notes || '',
    project_id: order.value.project_id,
    project_name: '',
    project_type: '其他',
    target_quantity: 1
  })
  editDialogVisible.value = true
}

const submitEdit = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate()
  
  const data = {
    customer_name: editForm.customer_name,
    contact_info: editForm.contact_info,
    order_source: editForm.order_source || null,
    requirement: editForm.requirement || null,
    delivery_date: editForm.delivery_date ? formatDate(editForm.delivery_date) : null,
    quoted_price: editForm.quoted_price,
    deposit: editForm.deposit,
    balance: editForm.balance,
    status: editForm.status,
    notes: editForm.notes || null,
    project_id: editLinkType.value === 'existing' ? editForm.project_id : null
  }
  
  if (editLinkType.value === 'new') {
    data.create_new_project = true
    data.project_name = editForm.project_name
    data.project_type = editForm.project_type
    data.target_quantity = editForm.target_quantity
    data.requirement = editForm.requirement
  }
  
  try {
    await orderApi.update(orderId.value, data)
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    fetchData()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '保存失败')
  }
}

const deleteOrder = async () => {
  try {
    await ElMessageBox.confirm(`确定删除该订单吗？此操作不可恢复。`, '提示', {
      type: 'danger',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    await orderApi.delete(orderId.value)
    ElMessage.success('删除成功')
    router.push('/orders')
  } catch {}
}

const goBack = () => {
  router.push('/orders')
}

const goToProject = () => {
  if (order.value?.project_id) {
    router.push(`/projects/${order.value.project_id}`)
  }
}

onMounted(fetchData)
</script>

<style scoped>
.page-header {
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  color: #333;
}

.detail-tabs {
  background: white;
  padding: 16px;
  border-radius: 8px;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.cost-summary {
  font-size: 14px;
  color: #666;
}

.cost-total {
  font-size: 20px;
  font-weight: 600;
  color: #e91e63;
  margin-left: 8px;
}

.info-card {
  border-radius: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: #999;
  flex-shrink: 0;
  margin-right: 16px;
}

.info-value {
  font-size: 14px;
  color: #333;
  text-align: right;
  flex: 1;
}

.info-value.price {
  font-size: 18px;
  font-weight: 600;
  color: #e91e63;
}

.photo-timeline {
  padding-left: 20px;
}

.photo-card {
  margin-bottom: 16px;
}

.photo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.photo-content {
  margin-bottom: 12px;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
}

.process-image {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  display: block;
}

.photo-meta {
  margin-bottom: 8px;
}

.meta-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.meta-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}

.meta-content.experience {
  background: #fff8e1;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #ff9800;
}

.stat-card {
  border-radius: 12px;
  text-align: center;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #333;
}
</style>
