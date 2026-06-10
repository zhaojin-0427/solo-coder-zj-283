<template>
  <div class="schedule-page">
    <el-row :gutter="20">
      <el-col :span="18">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title">排期日历</span>
              <div class="header-actions">
                <el-button-group>
                  <el-button @click="changeView('month')" :type="viewMode === 'month' ? 'primary' : ''">月视图</el-button>
                  <el-button @click="changeView('week')" :type="viewMode === 'week' ? 'primary' : ''">周视图</el-button>
                  <el-button @click="changeView('list')" :type="viewMode === 'list' ? 'primary' : ''">列表视图</el-button>
                </el-button-group>
                <el-button type="primary" @click="openTaskDialog">
                  <el-icon><Plus /></el-icon>
                  新建任务
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="viewMode === 'list'">
            <div class="filter-bar">
              <el-form :inline="true">
                <el-form-item label="状态">
                  <el-select v-model="filterStatus" @change="fetchTasks" clearable placeholder="全部">
                    <el-option label="待开始" value="pending" />
                    <el-option label="进行中" value="in_progress" />
                    <el-option label="已完成" value="completed" />
                    <el-option label="已延期" value="delayed" />
                    <el-option label="已取消" value="cancelled" />
                  </el-select>
                </el-form-item>
                <el-form-item label="优先级">
                  <el-select v-model="filterPriority" @change="fetchTasks" clearable placeholder="全部">
                    <el-option label="高" value="high" />
                    <el-option label="中" value="medium" />
                    <el-option label="低" value="low" />
                  </el-select>
                </el-form-item>
                <el-form-item label="负责人">
                  <el-input v-model="filterAssignee" @input="fetchTasks" placeholder="搜索负责人" clearable />
                </el-form-item>
              </el-form>
            </div>
            <el-table :data="tasks" v-loading="loading" border>
              <el-table-column prop="name" label="任务名称" min-width="150">
                <template #default="{ row }">
                  <div class="task-name-cell">
                    <el-tag :type="priorityType(row.priority)" size="small" style="margin-right: 8px;">
                      {{ priorityMap[row.priority] }}
                    </el-tag>
                    <span>{{ row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="stage" label="制作阶段" width="100" />
              <el-table-column label="关联项目" width="150">
                <template #default="{ row }">
                  <el-link v-if="row.project_id" type="primary" @click="goToProject(row.project_id)">
                    {{ row.project_name }}
                  </el-link>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="关联订单" width="150">
                <template #default="{ row }">
                  <el-link v-if="row.order_id" type="primary" @click="goToOrder(row.order_id)">
                    {{ row.order_customer }}
                  </el-link>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="预计时间" width="220">
                <template #default="{ row }">
                  <div v-if="row.estimated_start_date && row.estimated_end_date">
                    <div>{{ row.estimated_start_date }}</div>
                    <div class="text-muted">至 {{ row.estimated_end_date }}</div>
                  </div>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="工时" width="100" align="center">
                <template #default="{ row }">
                  <div>{{ row.actual_hours || 0 }} / {{ row.estimated_hours }}h</div>
                </template>
              </el-table-column>
              <el-table-column prop="assignee" label="负责人" width="100" />
              <el-table-column label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="statusType(row.status)" size="small">
                    {{ statusMap[row.status] }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="进度" width="120">
                <template #default="{ row }">
                  <el-progress :percentage="row.progress" :stroke-width="6" />
                </template>
              </el-table-column>
              <el-table-column label="风险" width="80" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.delay_risk === 'high'" type="danger" size="small">高</el-tag>
                  <el-tag v-else-if="row.delay_risk === 'medium'" type="warning" size="small">中</el-tag>
                  <el-tag v-else-if="row.delay_risk === 'low'" type="info" size="small">低</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="180" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button link size="small" @click="editTask(row)">编辑</el-button>
                  <el-button link size="small" type="primary" @click="updateTaskStatus(row)">
                    更新状态
                  </el-button>
                  <el-button link size="small" type="danger" @click="deleteTask(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="tasks.length === 0" description="暂无任务" />
          </div>

          <div v-else class="calendar-container">
            <div class="calendar-toolbar">
              <el-button-group>
                <el-button @click="prevPeriod">
                  <el-icon><ArrowLeft /></el-icon>
                </el-button>
                <el-button @click="goToToday">今天</el-button>
                <el-button @click="nextPeriod">
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </el-button-group>
              <span class="current-period">{{ currentPeriodText }}</span>
            </div>
            <div class="calendar-grid" v-if="viewMode === 'month'">
              <div class="calendar-weekdays">
                <div v-for="day in weekdays" :key="day" class="weekday">{{ day }}</div>
              </div>
              <div class="calendar-days">
                <div 
                  v-for="(day, index) in calendarDays" 
                  :key="index" 
                  class="calendar-day"
                  :class="{ 
                    'other-month': !day.isCurrentMonth,
                    'today': day.isToday,
                    'weekend': day.isWeekend
                  }"
                  @click="selectDate(day.date)"
                >
                  <div class="day-number">{{ day.day }}</div>
                  <div class="day-events">
                    <div 
                      v-for="event in day.events.slice(0, 3)" 
                      :key="event.id"
                      class="day-event"
                      :style="{ backgroundColor: event.color }"
                      @click.stop="viewTask(event)"
                    >
                      <span class="event-title">{{ event.title }}</span>
                    </div>
                    <div v-if="day.events.length > 3" class="more-events">
                      +{{ day.events.length - 3 }} 更多
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="calendar-week" v-else-if="viewMode === 'week'">
              <div class="week-header">
                <div 
                  v-for="day in weekDays" 
                  :key="day.date" 
                  class="week-day-header"
                  :class="{ 'today': day.isToday, 'weekend': day.isWeekend }"
                >
                  <div class="weekday-name">{{ day.weekday }}</div>
                  <div class="day-number">{{ day.day }}</div>
                </div>
              </div>
              <div class="week-body">
                <div 
                  v-for="day in weekDays" 
                  :key="day.date" 
                  class="week-day-column"
                  :class="{ 'today': day.isToday }"
                  @click="selectDate(day.date)"
                >
                  <div 
                    v-for="event in day.events" 
                    :key="event.id"
                    class="week-event"
                    :style="{ 
                      backgroundColor: event.color,
                      top: event.top + 'px',
                      height: event.height + 'px'
                    }"
                    @click.stop="viewTask(event)"
                  >
                    <div class="event-time">{{ event.timeText }}</div>
                    <div class="event-title">{{ event.title }}</div>
                    <div class="event-assignee">{{ event.assignee }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card style="margin-bottom: 20px;">
          <template #header>
            <span class="card-title">排期预警</span>
          </template>
          <el-alert 
            v-if="conflicts.length > 0"
            :title="`发现 ${conflicts.length} 个排期冲突`"
            type="error"
            show-icon
            style="margin-bottom: 12px;"
          />
          <div v-for="(conflict, index) in conflicts" :key="index" class="conflict-item">
            <el-icon color="#f44336"><Warning /></el-icon>
            <div class="conflict-content">
              <div class="conflict-message">{{ conflict.message }}</div>
              <div class="conflict-tasks">
                <el-tag size="small" type="danger">{{ conflict.task1.name }}</el-tag>
                <span class="conflict-vs">↔</span>
                <el-tag size="small" type="danger">{{ conflict.task2.name }}</el-tag>
              </div>
              <div class="conflict-days">重叠 {{ conflict.overlap_days }} 天</div>
            </div>
          </div>
          <el-empty v-if="conflicts.length === 0" description="暂无排期冲突" :image-size="60" />
        </el-card>

        <el-card style="margin-bottom: 20px;">
          <template #header>
            <span class="card-title">今日任务</span>
          </template>
          <div v-for="task in todayTasks" :key="task.id" class="today-task-item">
            <el-tag :type="statusType(task.status)" size="small" style="margin-right: 8px;">
              {{ statusMap[task.status] }}
            </el-tag>
            <span class="task-name">{{ task.name }}</span>
            <el-tag v-if="task.priority === 'high'" type="danger" size="small" style="margin-left: auto;">紧急</el-tag>
          </div>
          <el-empty v-if="todayTasks.length === 0" description="今日暂无任务" :image-size="60" />
        </el-card>

        <el-card>
          <template #header>
            <span class="card-title">本周待办</span>
            <el-tag type="primary" size="small">{{ weekTaskCount }} 个任务</el-tag>
          </template>
          <div class="week-stats">
            <div class="stat-item">
              <div class="stat-value pending">{{ pendingTaskCount }}</div>
              <div class="stat-label">待开始</div>
            </div>
            <div class="stat-item">
              <div class="stat-value progress">{{ inProgressTaskCount }}</div>
              <div class="stat-label">进行中</div>
            </div>
            <div class="stat-item">
              <div class="stat-value delayed">{{ delayedTaskCount }}</div>
              <div class="stat-label">已延期</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="taskDialogVisible" :title="isEdit ? '编辑任务' : '新建任务'" width="600px">
      <el-form :model="taskForm" :rules="taskRules" ref="taskFormRef" label-width="100px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="制作阶段" prop="stage">
              <el-select v-model="taskForm.stage" placeholder="请选择阶段" style="width: 100%;">
                <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="taskForm.priority" style="width: 100%;">
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="关联作品">
              <el-select v-model="taskForm.project_id" placeholder="请选择作品" style="width: 100%;" filterable clearable>
                <el-option 
                  v-for="p in availableProjects" 
                  :key="p.id" 
                  :label="`${p.name} (${p.project_type})`" 
                  :value="p.id" 
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联订单">
              <el-select v-model="taskForm.order_id" placeholder="请选择订单" style="width: 100%;" filterable clearable>
                <el-option 
                  v-for="o in availableOrders" 
                  :key="o.id" 
                  :label="`#${o.id} ${o.customer_name}`" 
                  :value="o.id" 
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="预计开始" prop="estimated_start_date">
              <el-date-picker v-model="taskForm.estimated_start_date" type="date" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计结束" prop="estimated_end_date">
              <el-date-picker v-model="taskForm.estimated_end_date" type="date" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="预计工时" prop="estimated_hours">
              <el-input-number v-model="taskForm.estimated_hours" :min="0" :step="0.5" style="width: 100%;" />
              <span class="form-hint">单位：小时</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实际工时">
              <el-input-number v-model="taskForm.actual_hours" :min="0" :step="0.5" style="width: 100%;" />
              <span class="form-hint">单位：小时</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="负责人">
              <el-input v-model="taskForm.assignee" placeholder="请输入负责人姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务状态" prop="status">
              <el-select v-model="taskForm.status" style="width: 100%;">
                <el-option label="待开始" value="pending" />
                <el-option label="进行中" value="in_progress" />
                <el-option label="已完成" value="completed" />
                <el-option label="已延期" value="delayed" />
                <el-option label="已取消" value="cancelled" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="taskForm.notes" type="textarea" :rows="3" placeholder="记录任务相关信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTask">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="statusDialogVisible" title="更新任务状态" width="400px">
      <div class="status-update-content">
        <div class="task-info">
          <span class="task-name">{{ editingTask?.name }}</span>
          <el-tag :type="statusType(editingTask?.status)" size="small">
            {{ statusMap[editingTask?.status] }}
          </el-tag>
        </div>
        <el-form label-width="100px" style="margin-top: 20px;">
          <el-form-item label="新状态">
            <el-select v-model="newStatus" style="width: 100%;">
              <el-option label="待开始" value="pending" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="已延期" value="delayed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </el-form-item>
          <el-form-item label="实际工时">
            <el-input-number v-model="newActualHours" :min="0" :step="0.5" style="width: 100%;" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="statusDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitStatusUpdate">确认更新</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { taskApi, projectApi, orderApi, formatDate } from '@/api'
import { 
  Plus, ArrowLeft, ArrowRight, Warning, Calendar 
} from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const viewMode = ref('month')
const currentDate = ref(new Date())

const tasks = ref([])
const calendarEvents = ref([])
const conflicts = ref([])
const availableProjects = ref([])
const availableOrders = ref([])

const taskDialogVisible = ref(false)
const statusDialogVisible = ref(false)
const taskFormRef = ref(null)
const isEdit = ref(false)
const editingTaskId = ref(null)
const editingTask = ref(null)
const newStatus = ref('')
const newActualHours = ref(0)

const filterStatus = ref('')
const filterPriority = ref('')
const filterAssignee = ref('')

const stages = ['设计稿', '裁剪', '缝纫', '熨烫', '装饰', '成品', '其他']
const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const statusMap = {
  'pending': '待开始',
  'in_progress': '进行中',
  'completed': '已完成',
  'delayed': '已延期',
  'cancelled': '已取消'
}

const priorityMap = {
  'high': '高',
  'medium': '中',
  'low': '低'
}

const statusType = (status) => {
  const map = {
    'pending': 'info',
    'in_progress': 'primary',
    'completed': 'success',
    'delayed': 'danger',
    'cancelled': 'info'
  }
  return map[status] || 'info'
}

const priorityType = (priority) => {
  const map = {
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return map[priority] || 'info'
}

const taskForm = reactive({
  name: '',
  stage: '',
  project_id: null,
  order_id: null,
  estimated_start_date: null,
  estimated_end_date: null,
  estimated_hours: 0,
  actual_hours: 0,
  assignee: '',
  priority: 'medium',
  status: 'pending',
  notes: ''
})

const taskRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  stage: [{ required: true, message: '请选择制作阶段', trigger: 'change' }]
}

const currentPeriodText = computed(() => {
  const d = currentDate.value
  if (viewMode.value === 'month') {
    return `${d.getFullYear()}年${d.getMonth() + 1}月`
  } else {
    const weekStart = new Date(d)
    weekStart.setDate(d.getDate() - d.getDay())
    const weekEnd = new Date(weekStart)
    weekEnd.setDate(weekStart.getDate() + 6)
    return `${weekStart.getMonth() + 1}月${weekStart.getDate()}日 - ${weekEnd.getMonth() + 1}月${weekEnd.getDate()}日`
  }
})

const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  const today = new Date()
  
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDay = new Date(firstDay)
  startDay.setDate(firstDay.getDate() - firstDay.getDay())
  
  const days = []
  for (let i = 0; i < 42; i++) {
    const d = new Date(startDay)
    d.setDate(startDay.getDate() + i)
    const dateStr = formatDate(d)
    
    const dayEvents = calendarEvents.value.filter(e => {
      if (!e.start || !e.end) return false
      return e.start <= dateStr && e.end >= dateStr
    })
    
    days.push({
      date: dateStr,
      day: d.getDate(),
      isCurrentMonth: d.getMonth() === month,
      isToday: formatDate(d) === formatDate(today),
      isWeekend: d.getDay() === 0 || d.getDay() === 6,
      events: dayEvents
    })
  }
  return days
})

const weekDays = computed(() => {
  const d = currentDate.value
  const weekStart = new Date(d)
  weekStart.setDate(d.getDate() - d.getDay())
  const today = new Date()
  
  const days = []
  for (let i = 0; i < 7; i++) {
    const day = new Date(weekStart)
    day.setDate(weekStart.getDate() + i)
    const dateStr = formatDate(day)
    
    const dayEvents = calendarEvents.value.filter(e => {
      if (!e.start || !e.end) return false
      return e.start <= dateStr && e.end >= dateStr
    }).map(e => {
      const hoursPerDay = 8
      const event = { ...e }
      const startDate = new Date(e.start)
      const endDate = new Date(e.end)
      const totalDays = (endDate - startDate) / (1000 * 60 * 60 * 24) + 1
      const totalHours = e.extendedProps?.estimated_hours || 8
      
      event.top = 0
      event.height = Math.min(200, (totalHours / totalDays / hoursPerDay) * 400)
      event.timeText = `${e.extendedProps?.estimated_hours || 0}h`
      return event
    })
    
    days.push({
      date: dateStr,
      day: day.getDate(),
      weekday: weekdays[i],
      isToday: formatDate(day) === formatDate(today),
      isWeekend: day.getDay() === 0 || day.getDay() === 6,
      events: dayEvents
    })
  }
  return days
})

const todayTasks = computed(() => {
  const today = formatDate(new Date())
  return tasks.value.filter(t => 
    t.estimated_start_date <= today && t.estimated_end_date >= today && t.status !== 'cancelled'
  )
})

const weekTaskCount = computed(() => {
  const today = new Date()
  const weekStart = new Date(today)
  weekStart.setDate(today.getDate() - today.getDay())
  const weekEnd = new Date(weekStart)
  weekEnd.setDate(weekStart.getDate() + 6)
  const weekStartStr = formatDate(weekStart)
  const weekEndStr = formatDate(weekEnd)
  
  return tasks.value.filter(t => 
    t.status !== 'cancelled' && 
    t.estimated_start_date >= weekStartStr && 
    t.estimated_start_date <= weekEndStr
  ).length
})

const pendingTaskCount = computed(() => tasks.value.filter(t => t.status === 'pending').length)
const inProgressTaskCount = computed(() => tasks.value.filter(t => t.status === 'in_progress').length)
const delayedTaskCount = computed(() => tasks.value.filter(t => t.status === 'delayed').length)

const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    if (filterPriority.value) params.priority = filterPriority.value
    if (filterAssignee.value) params.assignee = filterAssignee.value
    
    const [tasksRes, calendarRes, conflictsRes] = await Promise.all([
      taskApi.list(params),
      taskApi.getCalendar(),
      taskApi.getConflicts()
    ])
    
    tasks.value = tasksRes.data
    calendarEvents.value = calendarRes.data
    conflicts.value = conflictsRes.data
  } finally {
    loading.value = false
  }
}

const fetchOptions = async () => {
  try {
    const [projectsRes, ordersRes] = await Promise.all([
      projectApi.list(),
      orderApi.list()
    ])
    availableProjects.value = projectsRes.data
    availableOrders.value = ordersRes.data
  } catch (err) {
    console.error('获取选项失败', err)
  }
}

const changeView = (mode) => {
  viewMode.value = mode
  if (mode === 'list') {
    fetchTasks()
  }
}

const prevPeriod = () => {
  const d = new Date(currentDate.value)
  if (viewMode.value === 'month') {
    d.setMonth(d.getMonth() - 1)
  } else {
    d.setDate(d.getDate() - 7)
  }
  currentDate.value = d
}

const nextPeriod = () => {
  const d = new Date(currentDate.value)
  if (viewMode.value === 'month') {
    d.setMonth(d.getMonth() + 1)
  } else {
    d.setDate(d.getDate() + 7)
  }
  currentDate.value = d
}

const goToToday = () => {
  currentDate.value = new Date()
}

const selectDate = (date) => {
  taskForm.estimated_start_date = new Date(date)
  taskForm.estimated_end_date = new Date(date)
  openTaskDialog()
}

const openTaskDialog = () => {
  isEdit.value = false
  editingTaskId.value = null
  Object.assign(taskForm, {
    name: '',
    stage: '',
    project_id: null,
    order_id: null,
    estimated_start_date: null,
    estimated_end_date: null,
    estimated_hours: 0,
    actual_hours: 0,
    assignee: '',
    priority: 'medium',
    status: 'pending',
    notes: ''
  })
  taskDialogVisible.value = true
}

const editTask = (task) => {
  isEdit.value = true
  editingTaskId.value = task.id
  Object.assign(taskForm, {
    name: task.name,
    stage: task.stage,
    project_id: task.project_id,
    order_id: task.order_id,
    estimated_start_date: task.estimated_start_date ? new Date(task.estimated_start_date) : null,
    estimated_end_date: task.estimated_end_date ? new Date(task.estimated_end_date) : null,
    estimated_hours: task.estimated_hours,
    actual_hours: task.actual_hours || 0,
    assignee: task.assignee || '',
    priority: task.priority,
    status: task.status,
    notes: task.notes || ''
  })
  taskDialogVisible.value = true
}

const viewTask = (event) => {
  if (event.extendedProps) {
    editTask(event.extendedProps)
  }
}

const submitTask = async () => {
  if (!taskFormRef.value) return
  await taskFormRef.value.validate()
  
  const data = {
    ...taskForm,
    estimated_start_date: taskForm.estimated_start_date ? formatDate(taskForm.estimated_start_date) : null,
    estimated_end_date: taskForm.estimated_end_date ? formatDate(taskForm.estimated_end_date) : null
  }
  
  try {
    if (isEdit.value) {
      await taskApi.update(editingTaskId.value, data)
      ElMessage.success('更新成功')
    } else {
      await taskApi.create(data)
      ElMessage.success('创建成功')
    }
    taskDialogVisible.value = false
    fetchTasks()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '保存失败')
  }
}

const updateTaskStatus = (task) => {
  editingTask.value = task
  newStatus.value = task.status
  newActualHours.value = task.actual_hours || 0
  statusDialogVisible.value = true
}

const submitStatusUpdate = async () => {
  if (!editingTask.value) return
  
  try {
    await taskApi.update(editingTask.value.id, {
      status: newStatus.value,
      actual_hours: newActualHours.value
    })
    ElMessage.success('状态更新成功')
    statusDialogVisible.value = false
    fetchTasks()
  } catch (err) {
    ElMessage.error('更新失败')
  }
}

const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(`确定删除任务"${task.name}"吗？`, '提示', { type: 'warning' })
    await taskApi.delete(task.id)
    ElMessage.success('删除成功')
    fetchTasks()
  } catch {}
}

const goToProject = (projectId) => {
  router.push(`/projects/${projectId}`)
}

const goToOrder = (orderId) => {
  router.push(`/orders/${orderId}`)
}

onMounted(() => {
  fetchTasks()
  fetchOptions()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-bar {
  margin-bottom: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.task-name-cell {
  display: flex;
  align-items: center;
}

.text-muted {
  color: #999;
  font-size: 12px;
}

.calendar-container {
  min-height: 600px;
}

.calendar-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.current-period {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-bottom: 1px solid #f0f0f0;
}

.weekday {
  padding: 12px;
  text-align: center;
  font-weight: 500;
  color: #666;
  background: #fafafa;
}

.calendar-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-left: 1px solid #f0f0f0;
}

.calendar-day {
  min-height: 100px;
  padding: 8px;
  border-right: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.2s;
}

.calendar-day:hover {
  background-color: #f5f5f5;
}

.calendar-day.other-month {
  background-color: #fafafa;
  color: #ccc;
}

.calendar-day.today {
  background-color: #fff3f7;
}

.calendar-day.weekend {
  background-color: #fafafa;
}

.day-number {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.calendar-day.today .day-number {
  display: inline-block;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  background-color: #e91e63;
  color: white;
  border-radius: 50%;
}

.day-events {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.day-event {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  color: white;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-events {
  font-size: 11px;
  color: #999;
  padding: 2px 6px;
}

.calendar-week {
  min-height: 600px;
}

.week-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-bottom: 2px solid #f0f0f0;
}

.week-day-header {
  padding: 12px;
  text-align: center;
  background: #fafafa;
}

.week-day-header.today {
  background: #fff3f7;
}

.weekday-name {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.week-day-header.today .weekday-name {
  color: #e91e63;
}

.week-day-header .day-number {
  font-size: 20px;
  font-weight: 600;
}

.week-body {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  min-height: 500px;
  position: relative;
}

.week-day-column {
  border-right: 1px solid #f0f0f0;
  position: relative;
  min-height: 500px;
  cursor: pointer;
}

.week-day-column.today {
  background: #fff3f7;
}

.week-event {
  position: absolute;
  left: 4px;
  right: 4px;
  padding: 8px;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  overflow: hidden;
}

.event-time {
  font-size: 11px;
  opacity: 0.9;
  margin-bottom: 2px;
}

.event-title {
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 2px;
}

.event-assignee {
  font-size: 11px;
  opacity: 0.9;
}

.conflict-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #fff1f0;
  border-radius: 8px;
  margin-bottom: 8px;
}

.conflict-content {
  flex: 1;
}

.conflict-message {
  font-size: 13px;
  color: #333;
  margin-bottom: 6px;
}

.conflict-tasks {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.conflict-vs {
  color: #f44336;
  font-size: 12px;
}

.conflict-days {
  font-size: 12px;
  color: #f44336;
}

.today-task-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.today-task-item:last-child {
  border-bottom: none;
}

.task-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.week-stats {
  display: flex;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 4px;
}

.stat-value.pending {
  color: #909399;
}

.stat-value.progress {
  color: #409eff;
}

.stat-value.delayed {
  color: #f56c6c;
}

.stat-label {
  font-size: 12px;
  color: #999;
}

.status-update-content {
  padding: 12px 0;
}

.task-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 8px;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}
</style>
