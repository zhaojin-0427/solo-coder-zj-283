<template>
  <div class="project-detail">
    <el-page-header @back="goBack" :content="project?.name" class="page-header">
      <template #extra>
        <el-button @click="openEditDialog">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button type="danger" @click="deleteProject">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </template>
    </el-page-header>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-tabs v-model="activeTab" class="detail-tabs">
          <el-tab-pane label="材料清单" name="materials">
            <div class="tab-header">
              <el-button type="primary" @click="openMaterialDialog">
                <el-icon><Plus /></el-icon>
                添加材料
              </el-button>
              <div class="cost-summary">
                <span>总材料成本：</span>
                <span class="cost-total">¥{{ project?.total_material_cost?.toFixed(2) || '0.00' }}</span>
              </div>
            </div>
            <el-table :data="project?.material_usages || []" v-loading="loading" border>
              <el-table-column prop="material_name" label="材料名称" />
              <el-table-column prop="material_type" label="类型" width="100" />
              <el-table-column prop="color_code" label="色号" width="100">
                <template #default="{ row }">#{{ row.color_code }}</template>
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
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row }">
                  <el-button type="danger" link size="small" @click="removeMaterial(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="过程记录" name="photos">
            <div class="tab-header">
              <el-button type="primary" @click="openPhotoDialog">
                <el-icon><Plus /></el-icon>
                上传过程照
              </el-button>
            </div>
            <el-timeline v-if="project?.process_photos?.length" class="photo-timeline">
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
                    <div class="photo-actions">
                      <el-button link size="small" @click="editPhoto(photo)">
                        <el-icon><Edit /></el-icon>
                      </el-button>
                      <el-button type="danger" link size="small" @click="removePhoto(photo)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
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
        </el-tabs>
      </el-col>

      <el-col :span="8">
        <el-card class="info-card">
          <template #header>
            <span class="card-title">作品信息</span>
          </template>
          <div class="info-item" v-if="project">
            <div class="info-label">作品状态</div>
            <el-tag :type="statusType(project.status)">{{ statusMap[project.status] }}</el-tag>
          </div>
          <div class="info-item" v-if="project">
            <div class="info-label">作品类型</div>
            <div class="info-value">{{ project.project_type }}</div>
          </div>
          <div class="info-item" v-if="project">
            <div class="info-label">开始日期</div>
            <div class="info-value">{{ project.start_date }}</div>
          </div>
          <div class="info-item" v-if="project?.end_date">
            <div class="info-label">完成日期</div>
            <div class="info-value">{{ project.end_date }}</div>
          </div>
          <div class="info-item" v-if="project">
            <div class="info-label">制作进度</div>
            <div class="info-value">
              {{ project.completed_quantity }} / {{ project.target_quantity }} 件
              <el-tag v-if="project.is_over_target" size="small" type="danger" style="margin-left: 8px;">超额</el-tag>
            </div>
          </div>
          <div class="info-item" v-if="project">
            <div class="info-label">完成比例</div>
            <div class="info-value">
              <el-progress 
                :percentage="project.progress_percentage" 
                :stroke-width="8"
                :color="project.is_over_target ? '#f44336' : '#e91e63'"
                style="width: 200px;"
              />
            </div>
          </div>
          <div class="info-item" v-if="project">
            <div class="info-label">单件材料成本</div>
            <div class="info-value price">¥{{ project.unit_material_cost?.toFixed(2) || '0.00' }}</div>
          </div>
          <div class="info-item" v-if="project?.description">
            <div class="info-label">作品描述</div>
            <div class="info-value">{{ project.description }}</div>
          </div>
          <div class="info-item" v-if="project?.notes">
            <div class="info-label">备注</div>
            <div class="info-value">{{ project.notes }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="materialDialogVisible" title="添加材料" width="500px">
      <el-form :model="materialForm" :rules="materialRules" ref="materialFormRef" label-width="100px">
        <el-form-item label="选择材料" prop="material_id">
          <el-select v-model="materialForm.material_id" placeholder="请选择材料" style="width: 100%;" filterable>
            <el-option 
              v-for="m in availableMaterials" 
              :key="m.id" 
              :label="`${m.name} (剩余${m.remaining_length.toFixed(2)}m, ¥${m.unit_price}/m)`" 
              :value="m.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="使用长度(米)" prop="used_length">
          <el-input-number v-model="materialForm.used_length" :min="0.01" :step="0.01" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="裁剪损耗(米)">
          <el-input-number v-model="materialForm.cutting_loss" :min="0" :step="0.01" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="materialForm.notes" type="textarea" :rows="2" placeholder="记录使用情况" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="materialDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitMaterial">添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="photoDialogVisible" title="上传过程照片" width="500px">
      <el-form :model="photoForm" :rules="photoRules" ref="photoFormRef" label-width="100px">
        <el-form-item label="制作阶段" prop="stage">
          <el-select v-model="photoForm.stage" placeholder="请选择阶段" style="width: 100%;">
            <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="阶段顺序" prop="stage_order">
          <el-input-number v-model="photoForm.stage_order" :min="0" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="照片" prop="photo">
          <el-upload
            drag
            :auto-upload="false"
            :show-file-list="false"
            accept="image/*"
            @change="handlePhotoChange"
          >
            <div v-if="photoPreviewUrl" class="preview-wrapper">
              <img :src="photoPreviewUrl" alt="" />
            </div>
            <div v-else class="upload-area">
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div>点击或拖拽上传照片</div>
            </div>
          </el-upload>
        </el-form-item>
        <el-form-item label="过程描述">
          <el-input v-model="photoForm.description" type="textarea" :rows="2" placeholder="描述当前阶段" />
        </el-form-item>
        <el-form-item label="制作经验">
          <el-input v-model="photoForm.experience" type="textarea" :rows="3" placeholder="记录制作心得和技巧" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="photoDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPhoto">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editPhotoDialogVisible" title="编辑照片信息" width="500px">
      <el-form :model="editPhotoForm" ref="editPhotoFormRef" label-width="100px">
        <el-form-item label="制作阶段">
          <el-select v-model="editPhotoForm.stage" style="width: 100%;">
            <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="阶段顺序">
          <el-input-number v-model="editPhotoForm.stage_order" :min="0" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="过程描述">
          <el-input v-model="editPhotoForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="制作经验">
          <el-input v-model="editPhotoForm.experience" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editPhotoDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEditPhoto">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑作品" width="500px">
      <el-form :model="editForm" :rules="rules" ref="editFormRef" label-width="100px">
        <el-form-item label="作品名称" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="作品类型" prop="project_type">
          <el-select v-model="editForm.project_type" style="width: 100%;">
            <el-option v-for="t in projectTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="editForm.status">
            <el-radio value="in_progress">进行中</el-radio>
            <el-radio value="completed">已完成</el-radio>
            <el-radio value="paused">已暂停</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="目标数量" prop="target_quantity">
              <el-input-number 
                v-model="editForm.target_quantity" 
                :min="1" 
                style="width: 100%;"
                @change="validateEditQuantity"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="已完成数" prop="completed_quantity">
              <el-input-number 
                v-model="editForm.completed_quantity" 
                :min="0" 
                :max="editForm.target_quantity"
                style="width: 100%;"
                @change="validateEditQuantity"
              />
              <div v-if="editForm.completed_quantity > editForm.target_quantity" class="quantity-hint">
                <el-icon color="#f44336"><Warning /></el-icon>
                已完成数不能超过目标数量
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="作品描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
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
import { projectApi, materialApi, materialUsageApi, processPhotoApi, getImageUrl } from '@/api'
import { Plus, Edit, Delete, UploadFilled, Warning } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => parseInt(route.params.id))

const loading = ref(false)
const project = ref(null)
const activeTab = ref('materials')
const availableMaterials = ref([])

const materialDialogVisible = ref(false)
const photoDialogVisible = ref(false)
const editPhotoDialogVisible = ref(false)
const editDialogVisible = ref(false)

const materialFormRef = ref(null)
const photoFormRef = ref(null)
const editPhotoFormRef = ref(null)
const editFormRef = ref(null)

const photoFile = ref(null)
const photoPreviewUrl = ref('')
const editingPhotoId = ref(null)

const stages = ['设计稿', '裁剪', '缝纫', '熨烫', '装饰', '成品', '其他']
const projectTypes = ['服装', '包包', '家居装饰', '玩偶', '拼布', '刺绣', '其他']
const timelineColors = ['primary', 'success', 'warning', 'danger', 'info']

const statusMap = {
  'in_progress': '进行中',
  'completed': '已完成',
  'paused': '已暂停'
}

const statusType = (status) => {
  const map = { 'in_progress': 'primary', 'completed': 'success', 'paused': 'info' }
  return map[status] || 'info'
}

const sortedPhotos = computed(() => {
  if (!project.value?.process_photos) return []
  return [...project.value.process_photos].sort((a, b) => a.stage_order - b.stage_order)
})

const materialForm = reactive({
  material_id: null,
  used_length: 0.1,
  cutting_loss: 0,
  notes: ''
})

const photoForm = reactive({
  stage: '',
  stage_order: 0,
  photo: null,
  description: '',
  experience: ''
})

const editPhotoForm = reactive({
  stage: '',
  stage_order: 0,
  description: '',
  experience: ''
})

const editForm = reactive({
  name: '',
  project_type: '',
  description: '',
  target_quantity: 1,
  completed_quantity: 0,
  status: 'in_progress',
  notes: ''
})

const validateEditCompletedQuantity = (rule, value, callback) => {
  if (value > editForm.target_quantity) {
    callback(new Error('已完成数量不能超过目标数量'))
  } else {
    callback()
  }
}

const rules = {
  name: [{ required: true, message: '请输入作品名称', trigger: 'blur' }],
  project_type: [{ required: true, message: '请选择作品类型', trigger: 'change' }],
  target_quantity: [{ required: true, message: '请输入目标数量', trigger: 'blur' }],
  completed_quantity: [
    { required: true, message: '请输入已完成数量', trigger: 'blur' },
    { validator: validateEditCompletedQuantity, trigger: 'change' }
  ],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const validateEditQuantity = () => {
  if (editFormRef.value) {
    editFormRef.value.validateField('completed_quantity')
  }
}

const materialRules = {
  material_id: [{ required: true, message: '请选择材料', trigger: 'change' }],
  used_length: [{ required: true, message: '请输入使用长度', trigger: 'blur' }]
}

const photoRules = {
  stage: [{ required: true, message: '请选择制作阶段', trigger: 'change' }],
  photo: [{ required: true, message: '请上传照片', trigger: 'change' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const [projectRes, materialsRes] = await Promise.all([
      projectApi.get(projectId.value),
      materialApi.list()
    ])
    project.value = projectRes.data
    availableMaterials.value = materialsRes.data.filter(m => m.remaining_length > 0)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/projects')
}

const openMaterialDialog = () => {
  Object.assign(materialForm, {
    material_id: null,
    used_length: 0.1,
    cutting_loss: 0,
    notes: ''
  })
  materialDialogVisible.value = true
}

const submitMaterial = async () => {
  if (!materialFormRef.value) return
  await materialFormRef.value.validate()
  
  try {
    await projectApi.addMaterial(projectId.value, materialForm)
    ElMessage.success('添加成功')
    materialDialogVisible.value = false
    fetchData()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '添加失败')
  }
}

const removeMaterial = async (usage) => {
  try {
    await ElMessageBox.confirm(`确定移除该材料吗？`, '提示', { type: 'warning' })
    await materialUsageApi.delete(usage.id)
    ElMessage.success('移除成功')
    fetchData()
  } catch {}
}

const openPhotoDialog = () => {
  photoFile.value = null
  photoPreviewUrl.value = ''
  Object.assign(photoForm, {
    stage: '',
    stage_order: project.value?.process_photos?.length || 0,
    photo: null,
    description: '',
    experience: ''
  })
  photoDialogVisible.value = true
}

const handlePhotoChange = (uploadFile) => {
  photoFile.value = uploadFile.raw
  photoForm.photo = uploadFile.raw
  photoPreviewUrl.value = URL.createObjectURL(uploadFile.raw)
}

const submitPhoto = async () => {
  if (!photoFormRef.value) return
  await photoFormRef.value.validate()
  
  const formData = new FormData()
  formData.append('stage', photoForm.stage)
  formData.append('stage_order', photoForm.stage_order)
  formData.append('description', photoForm.description || '')
  formData.append('experience', photoForm.experience || '')
  if (photoFile.value) {
    formData.append('photo', photoFile.value)
  }

  try {
    await projectApi.addPhoto(projectId.value, formData)
    ElMessage.success('上传成功')
    photoDialogVisible.value = false
    fetchData()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '上传失败')
  }
}

const editPhoto = (photo) => {
  editingPhotoId.value = photo.id
  Object.assign(editPhotoForm, {
    stage: photo.stage,
    stage_order: photo.stage_order,
    description: photo.description || '',
    experience: photo.experience || ''
  })
  editPhotoDialogVisible.value = true
}

const submitEditPhoto = async () => {
  try {
    await processPhotoApi.update(editingPhotoId.value, editPhotoForm)
    ElMessage.success('保存成功')
    editPhotoDialogVisible.value = false
    fetchData()
  } catch (err) {
    ElMessage.error('保存失败')
  }
}

const removePhoto = async (photo) => {
  try {
    await ElMessageBox.confirm(`确定删除该照片吗？`, '提示', { type: 'warning' })
    await processPhotoApi.delete(photo.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const openEditDialog = () => {
  Object.assign(editForm, {
    name: project.value.name,
    project_type: project.value.project_type,
    description: project.value.description || '',
    target_quantity: project.value.target_quantity,
    completed_quantity: project.value.completed_quantity,
    status: project.value.status,
    notes: project.value.notes || ''
  })
  editDialogVisible.value = true
}

const submitEdit = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate()
  
  try {
    await projectApi.update(projectId.value, editForm)
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    fetchData()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '保存失败')
  }
}

const deleteProject = async () => {
  try {
    await ElMessageBox.confirm(`确定删除作品"${project.value.name}"吗？此操作不可恢复。`, '提示', {
      type: 'danger',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    await projectApi.delete(projectId.value)
    ElMessage.success('删除成功')
    router.push('/projects')
  } catch {}
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

.card-title {
  font-weight: 600;
  color: #333;
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

.photo-actions {
  display: flex;
  gap: 8px;
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

.upload-area {
  padding: 24px;
  text-align: center;
  color: #999;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 8px;
  color: #e91e63;
}

.preview-wrapper {
  text-align: center;
}

.preview-wrapper img {
  max-width: 200px;
  max-height: 200px;
  object-fit: contain;
}

.quantity-hint {
  font-size: 12px;
  color: #f44336;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
