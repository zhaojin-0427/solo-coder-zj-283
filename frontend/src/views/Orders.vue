<template>
  <div class="orders-page">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable @change="fetchOrders">
            <el-option v-for="(label, value) in statusMap" :key="value" :label="label" :value="value" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filters.search" placeholder="客户姓名/需求" clearable @keyup.enter="fetchOrders" style="width: 200px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="openDialog">
            <el-icon><Plus /></el-icon>
            新建订单
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="orders" v-loading="loading" border style="margin-top: 16px;">
      <el-table-column prop="id" label="订单号" width="80" align="center" />
      <el-table-column prop="customer_name" label="客户姓名" width="120" />
      <el-table-column prop="contact_info" label="联系方式" width="160" />
      <el-table-column prop="order_source" label="订单来源" width="100" />
      <el-table-column label="关联作品" width="160">
        <template #default="{ row }">
          <span v-if="row.project_name">{{ row.project_name }}</span>
          <el-tag v-else type="info" size="small">未关联</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="制作进度" width="140">
        <template #default="{ row }">
          <el-progress 
            v-if="row.project_id"
            :percentage="row.project_progress" 
            :stroke-width="6"
            :color="row.project_status === 'completed' ? '#67c23a' : '#e91e63'"
          />
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="报价" width="110" align="right">
        <template #default="{ row }">¥{{ row.quoted_price.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="定金" width="100" align="right">
        <template #default="{ row }">¥{{ row.deposit.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="交付日期" width="120" align="center">
        <template #default="{ row }">
          <span :style="{ color: row.is_overdue ? '#f44336' : '' }">
            {{ row.delivery_date || '-' }}
          </span>
          <el-tag v-if="row.is_overdue" type="danger" size="small" style="margin-left: 4px;">逾期</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="交付风险" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="riskType(row.delivery_risk)" size="small">
            {{ riskMap[row.delivery_risk] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">
            {{ statusMap[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="goToDetail(row.id)">
            详情
          </el-button>
          <el-button type="primary" link size="small" @click="editOrder(row)">
            编辑
          </el-button>
          <el-button type="danger" link size="small" @click="deleteOrder(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && orders.length === 0" description="暂无订单数据" style="margin-top: 40px;" />

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑订单' : '新建订单'" width="700px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户姓名" prop="customer_name">
              <el-input v-model="form.customer_name" placeholder="请输入客户姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系方式" prop="contact_info">
              <el-input v-model="form.contact_info" placeholder="电话/微信" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="订单来源">
              <el-select v-model="form.order_source" placeholder="请选择来源" style="width: 100%;" clearable>
                <el-option v-for="s in orderSources" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="交付日期" prop="delivery_date">
              <el-date-picker v-model="form.delivery_date" type="date" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="作品需求" prop="requirement">
          <el-input v-model="form.requirement" type="textarea" :rows="3" placeholder="描述客户的作品需求" />
        </el-form-item>
        <el-form-item label="关联作品">
          <el-radio-group v-model="linkType" @change="handleLinkTypeChange">
            <el-radio value="none">暂不关联</el-radio>
            <el-radio value="existing">关联已有作品</el-radio>
            <el-radio value="new">新建作品</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="linkType === 'existing'" label="选择作品" prop="project_id">
          <el-select v-model="form.project_id" placeholder="请选择作品" style="width: 100%;" filterable @change="handleProjectChange">
            <el-option 
              v-for="p in availableProjects" 
              :key="p.id" 
              :label="`${p.name} (${p.project_type})`" 
              :value="p.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="linkType === 'new'" label="作品名称" prop="project_name">
          <el-input v-model="form.project_name" placeholder="请输入作品名称" />
        </el-form-item>
        <el-form-item v-if="linkType === 'new'" label="作品类型">
          <el-select v-model="form.project_type" style="width: 100%;">
            <el-option v-for="t in projectTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="linkType === 'new'" label="目标数量">
          <el-input-number v-model="form.target_quantity" :min="1" style="width: 100%;" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="报价" prop="quoted_price">
              <el-input-number 
                v-model="form.quoted_price" 
                :min="0" 
                :precision="2" 
                style="width: 100%;" 
              />
              <div v-if="suggestedPrice > 0" class="price-hint">
                <el-icon color="#67c23a"><Lightbulb /></el-icon>
                建议报价 ¥{{ suggestedPrice.toFixed(2) }}
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="定金" prop="deposit">
              <el-input-number v-model="form.deposit" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="尾款" prop="balance">
              <el-input-number v-model="form.balance" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="订单状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio value="pending">待确认</el-radio>
            <el-radio value="confirmed">已确认</el-radio>
            <el-radio value="in_progress">制作中</el-radio>
            <el-radio value="ready">待交付</el-radio>
            <el-radio value="completed">已完成</el-radio>
            <el-radio value="cancelled">已取消</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="其他备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">{{ isEdit ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { orderApi, projectApi, formatDate } from '@/api'
import { Plus, Lightbulb } from '@element-plus/icons-vue'

const router = useRouter()
const orders = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const editingId = ref(null)
const linkType = ref('none')
const suggestedPrice = ref(0)
const availableProjects = ref([])

const filters = reactive({
  status: '',
  search: ''
})

const orderSources = ['微信', '淘宝', '闲鱼', '抖音', '线下门店', '朋友介绍', '其他']
const projectTypes = ['服装', '包包', '家居装饰', '玩偶', '拼布', '刺绣', '其他']

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

const form = reactive({
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

const rules = {
  customer_name: [{ required: true, message: '请输入客户姓名', trigger: 'blur' }],
  contact_info: [{ required: true, message: '请输入联系方式', trigger: 'blur' }],
  delivery_date: [{ required: true, message: '请选择交付日期', trigger: 'change' }],
  quoted_price: [{ required: true, message: '请输入报价', trigger: 'blur' }],
  deposit: [{ required: true, message: '请输入定金', trigger: 'blur' }],
  balance: [{ required: true, message: '请输入尾款', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const fetchOrders = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.search) params.search = filters.search
    const res = await orderApi.list(params)
    orders.value = res.data
  } catch (err) {
    ElMessage.error('获取订单列表失败')
  } finally {
    loading.value = false
  }
}

const fetchProjects = async () => {
  try {
    const res = await projectApi.list()
    availableProjects.value = res.data
  } catch (err) {
    console.error('获取作品列表失败', err)
  }
}

const fetchSuggestedPrice = async (orderId) => {
  try {
    const res = await orderApi.getSuggestedPrice(orderId)
    suggestedPrice.value = res.data.suggested_price
  } catch (err) {
    console.error('获取建议报价失败', err)
  }
}

const handleLinkTypeChange = () => {
  if (linkType.value === 'none') {
    form.project_id = null
    form.project_name = ''
    suggestedPrice.value = 0
  } else if (linkType.value === 'existing') {
    form.project_name = ''
  }
}

const handleProjectChange = async () => {
  if (isEdit.value && editingId.value && form.project_id) {
    await fetchSuggestedPrice(editingId.value)
  } else if (form.project_id) {
    try {
      const projectRes = await projectApi.get(form.project_id)
      const materialCost = projectRes.data.total_material_cost || 0
      if (materialCost > 0) {
        if (materialCost < 100) {
          suggestedPrice.value = materialCost * 2.5
        } else if (materialCost < 500) {
          suggestedPrice.value = materialCost * 2.0
        } else {
          suggestedPrice.value = materialCost * 1.8
        }
      } else {
        suggestedPrice.value = 0
      }
    } catch (err) {
      console.error('获取项目材料成本失败', err)
    }
  } else {
    suggestedPrice.value = 0
  }
}

const openDialog = () => {
  isEdit.value = false
  editingId.value = null
  linkType.value = 'none'
  suggestedPrice.value = 0
  Object.assign(form, {
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
  dialogVisible.value = true
  fetchProjects()
}

const editOrder = (row) => {
  isEdit.value = true
  editingId.value = row.id
  suggestedPrice.value = row.suggested_price
  if (row.project_id) {
    linkType.value = 'existing'
  } else {
    linkType.value = 'none'
  }
  Object.assign(form, {
    customer_name: row.customer_name,
    contact_info: row.contact_info,
    order_source: row.order_source || '',
    requirement: row.requirement || '',
    delivery_date: row.delivery_date ? new Date(row.delivery_date) : null,
    quoted_price: row.quoted_price,
    deposit: row.deposit,
    balance: row.balance,
    status: row.status,
    notes: row.notes || '',
    project_id: row.project_id,
    project_name: '',
    project_type: '其他',
    target_quantity: 1
  })
  dialogVisible.value = true
  fetchProjects()
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  
  const data = {
    customer_name: form.customer_name,
    contact_info: form.contact_info,
    order_source: form.order_source || null,
    requirement: form.requirement || null,
    delivery_date: form.delivery_date ? formatDate(form.delivery_date) : null,
    quoted_price: form.quoted_price,
    deposit: form.deposit,
    balance: form.balance,
    status: form.status,
    notes: form.notes || null,
    project_id: linkType.value === 'existing' ? form.project_id : null
  }
  
  if (linkType.value === 'new') {
    data.create_new_project = true
    data.project_name = form.project_name
    data.project_type = form.project_type
    data.target_quantity = form.target_quantity
    data.requirement = form.requirement
  }
  
  try {
    if (isEdit.value && editingId.value) {
      await orderApi.update(editingId.value, data)
      ElMessage.success('保存成功')
    } else {
      const res = await orderApi.create(data)
      ElMessage.success('创建成功')
      if (linkType.value === 'existing' || linkType.value === 'new') {
        router.push(`/orders/${res.data.id}`)
      }
    }
    dialogVisible.value = false
    fetchOrders()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '操作失败')
  }
}

const deleteOrder = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除客户"${row.customer_name}"的订单吗？`, '提示', {
      type: 'warning'
    })
    await orderApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchOrders()
  } catch {}
}

const goToDetail = (id) => {
  router.push(`/orders/${id}`)
}

onMounted(() => {
  fetchOrders()
  fetchProjects()
})
</script>

<style scoped>
.filter-card {
  margin-bottom: 16px;
}

.price-hint {
  font-size: 12px;
  color: #67c23a;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
