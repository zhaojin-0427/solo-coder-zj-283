<template>
  <div class="projects-page">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable @change="fetchProjects">
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已暂停" value="paused" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable @change="fetchProjects">
            <el-option v-for="t in projectTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="openDialog">
            <el-icon><Plus /></el-icon>
            新建作品
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="8" v-for="project in projects" :key="project.id">
        <el-card class="project-card" hoverable @click="goToDetail(project.id)">
          <div class="project-header">
            <el-tag :type="statusType(project.status)" size="small">{{ statusMap[project.status] }}</el-tag>
            <span class="project-type">{{ project.project_type }}</span>
          </div>
          <div class="project-name">{{ project.name }}</div>
          <div class="project-desc" v-if="project.description">{{ project.description }}</div>
          <div class="project-stats">
            <div class="stat-item">
              <el-icon color="#e91e63"><Collection /></el-icon>
              <span>{{ project.material_count }} 种材料</span>
            </div>
            <div class="stat-item">
              <el-icon color="#9c27b0"><Picture /></el-icon>
              <span>{{ project.photo_count }} 张照片</span>
            </div>
            <div class="stat-item">
              <el-icon color="#673ab7"><Money /></el-icon>
              <span>¥{{ project.unit_material_cost.toFixed(2) }}/件</span>
            </div>
          </div>
          <div class="project-progress">
            <div class="progress-label">
              <span>进度</span>
              <span>{{ project.completed_quantity }} / {{ project.target_quantity }} 件</span>
            </div>
            <el-progress 
              :percentage="Math.round(project.completed_quantity / project.target_quantity * 100)" 
              :stroke-width="8"
              color="#e91e63"
            />
          </div>
          <div class="project-footer">
            <span class="date">开始于 {{ project.start_date }}</span>
            <el-button type="primary" link size="small" @click.stop="goToDetail(project.id)">
              查看详情 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" title="新建作品" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="作品名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入作品名称" />
        </el-form-item>
        <el-form-item label="作品类型" prop="project_type">
          <el-select v-model="form.project_type" placeholder="请选择类型" style="width: 100%;">
            <el-option v-for="t in projectTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="作品描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述作品内容" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker v-model="form.start_date" type="date" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="完成日期">
              <el-date-picker v-model="form.end_date" type="date" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="目标数量" prop="target_quantity">
              <el-input-number v-model="form.target_quantity" :min="1" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="已完成数" prop="completed_quantity">
              <el-input-number v-model="form.completed_quantity" :min="0" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio value="in_progress">进行中</el-radio>
            <el-radio value="completed">已完成</el-radio>
            <el-radio value="paused">已暂停</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { projectApi, formatDate } from '@/api'
import { Plus, Collection, Picture, Money, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()
const projects = ref([])
const dialogVisible = ref(false)
const formRef = ref(null)

const filters = reactive({
  status: '',
  type: ''
})

const projectTypes = ['服装', '包包', '家居装饰', '玩偶', '拼布', '刺绣', '其他']

const statusMap = {
  'in_progress': '进行中',
  'completed': '已完成',
  'paused': '已暂停'
}

const statusType = (status) => {
  const map = { 'in_progress': 'primary', 'completed': 'success', 'paused': 'info' }
  return map[status] || 'info'
}

const form = reactive({
  name: '',
  project_type: '',
  description: '',
  start_date: new Date(),
  end_date: null,
  target_quantity: 1,
  completed_quantity: 0,
  status: 'in_progress',
  notes: ''
})

const rules = {
  name: [{ required: true, message: '请输入作品名称', trigger: 'blur' }],
  project_type: [{ required: true, message: '请选择作品类型', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  target_quantity: [{ required: true, message: '请输入目标数量', trigger: 'blur' }],
  completed_quantity: [{ required: true, message: '请输入已完成数量', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const fetchProjects = async () => {
  try {
    const res = await projectApi.list(filters)
    projects.value = res.data
  } catch (err) {
    ElMessage.error('获取作品列表失败')
  }
}

const openDialog = () => {
  Object.assign(form, {
    name: '',
    project_type: '',
    description: '',
    start_date: new Date(),
    end_date: null,
    target_quantity: 1,
    completed_quantity: 0,
    status: 'in_progress',
    notes: ''
  })
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  
  const data = {
    ...form,
    start_date: formatDate(form.start_date),
    end_date: form.end_date ? formatDate(form.end_date) : null
  }
  
  try {
    const res = await projectApi.create(data)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    fetchProjects()
    router.push(`/projects/${res.data.id}`)
  } catch (err) {
    ElMessage.error('创建失败')
  }
}

const goToDetail = (id) => {
  router.push(`/projects/${id}`)
}

onMounted(fetchProjects)
</script>

<style scoped>
.filter-card {
  margin-bottom: 16px;
}

.project-card {
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-bottom: 16px;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.project-type {
  font-size: 12px;
  color: #999;
}

.project-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.project-desc {
  font-size: 13px;
  color: #666;
  margin-bottom: 16px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}

.project-progress {
  margin-bottom: 12px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}

.project-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.date {
  font-size: 12px;
  color: #999;
}
</style>
