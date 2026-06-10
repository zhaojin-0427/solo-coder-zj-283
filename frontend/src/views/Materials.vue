<template>
  <div class="materials-page">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input v-model="filters.search" placeholder="名称/色号" clearable @input="fetchMaterials" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable @change="fetchMaterials">
            <el-option v-for="t in materialTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="openDialog">
            <el-icon><Plus /></el-icon>
            新增材料
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="6" v-for="material in materials" :key="material.id">
        <el-card class="material-card" :body-style="{ padding: 0 }">
          <div class="material-photo">
            <img v-if="material.photo" :src="getImageUrl(material.photo)" alt="" />
            <div v-else class="photo-placeholder">
              <el-icon :size="48" color="#ccc"><Picture /></el-icon>
            </div>
            <div class="material-badge" :class="{ low: material.remaining_length < 1 }">
              {{ material.remaining_length.toFixed(1) }}m
            </div>
          </div>
          <div class="material-info">
            <div class="material-name">{{ material.name }}</div>
            <div class="material-meta">
              <el-tag size="small" type="info">{{ material.material_type }}</el-tag>
              <span v-if="material.color_code" class="color-code">#{{ material.color_code }}</span>
            </div>
            <div class="material-details">
              <div class="detail-item">
                <span class="label">幅宽</span>
                <span class="value">{{ material.width }}m</span>
              </div>
              <div class="detail-item">
                <span class="label">单价</span>
                <span class="value">¥{{ material.unit_price }}/m</span>
              </div>
              <div class="detail-item">
                <span class="label">总价</span>
                <span class="value">¥{{ material.total_value.toFixed(2) }}</span>
              </div>
            </div>
            <el-progress 
              :percentage="(material.usage_rate * 100).toFixed(0)" 
              :stroke-width="6"
              :color="material.usage_rate > 0.8 ? '#e91e63' : '#4caf50'"
            />
            <div class="material-actions">
              <el-button type="primary" link @click="editMaterial(material)">编辑</el-button>
              <el-button type="danger" link @click="deleteMaterial(material)">删除</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑材料' : '新增材料'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="材料名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入材料名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="材料类型" prop="material_type">
              <el-select v-model="form.material_type" placeholder="请选择类型" style="width: 100%;">
                <el-option v-for="t in materialTypes" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="色号">
              <el-input v-model="form.color_code" placeholder="如：FF0000" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="幅宽(米)" prop="width">
              <el-input-number v-model="form.width" :min="0.1" :step="0.1" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="总长度(米)" prop="total_length">
              <el-input-number v-model="form.total_length" :min="0.1" :step="0.1" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单价(元/米)" prop="unit_price">
              <el-input-number v-model="form.unit_price" :min="0" :step="0.01" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="供应商">
              <el-input v-model="form.supplier" placeholder="请输入供应商" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="采购日期" prop="purchase_date">
              <el-date-picker v-model="form.purchase_date" type="date" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="材料照片">
          <el-upload
            drag
            :auto-upload="false"
            :show-file-list="false"
            accept="image/*"
            @change="handlePhotoChange"
          >
            <div v-if="previewUrl" class="preview-wrapper">
              <img :src="previewUrl" alt="" />
            </div>
            <div v-else class="upload-area">
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div>点击或拖拽上传照片</div>
            </div>
          </el-upload>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="输入备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { materialApi, getImageUrl } from '@/api'
import { Plus, Picture, UploadFilled } from '@element-plus/icons-vue'

const loading = ref(false)
const materials = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)
const photoFile = ref(null)
const previewUrl = ref('')

const filters = reactive({
  search: '',
  type: ''
})

const materialTypes = ['纯棉', '亚麻', '丝绸', '化纤', '混纺', '牛仔', '灯芯绒', '蕾丝', '不织布', '其他']

const form = reactive({
  name: '',
  material_type: '',
  color_code: '',
  width: 1.5,
  total_length: 1,
  unit_price: 0,
  supplier: '',
  purchase_date: new Date(),
  notes: ''
})

const rules = {
  name: [{ required: true, message: '请输入材料名称', trigger: 'blur' }],
  material_type: [{ required: true, message: '请选择材料类型', trigger: 'change' }],
  width: [{ required: true, message: '请输入幅宽', trigger: 'blur' }],
  total_length: [{ required: true, message: '请输入总长度', trigger: 'blur' }],
  unit_price: [{ required: true, message: '请输入单价', trigger: 'blur' }],
  purchase_date: [{ required: true, message: '请选择采购日期', trigger: 'change' }]
}

const fetchMaterials = async () => {
  loading.value = true
  try {
    const res = await materialApi.list(filters)
    materials.value = res.data
  } finally {
    loading.value = false
  }
}

const openDialog = () => {
  isEdit.value = false
  editId.value = null
  photoFile.value = null
  previewUrl.value = ''
  Object.assign(form, {
    name: '',
    material_type: '',
    color_code: '',
    width: 1.5,
    total_length: 1,
    unit_price: 0,
    supplier: '',
    purchase_date: new Date(),
    notes: ''
  })
  dialogVisible.value = true
}

const editMaterial = (material) => {
  isEdit.value = true
  editId.value = material.id
  photoFile.value = null
  previewUrl.value = material.photo ? getImageUrl(material.photo) : ''
  Object.assign(form, {
    name: material.name,
    material_type: material.material_type,
    color_code: material.color_code || '',
    width: material.width,
    total_length: material.total_length,
    unit_price: material.unit_price,
    supplier: material.supplier || '',
    purchase_date: new Date(material.purchase_date),
    notes: material.notes || ''
  })
  dialogVisible.value = true
}

const deleteMaterial = async (material) => {
  try {
    await ElMessageBox.confirm(`确定删除材料"${material.name}"吗？`, '提示', {
      type: 'warning'
    })
    await materialApi.delete(material.id)
    ElMessage.success('删除成功')
    fetchMaterials()
  } catch {}
}

const handlePhotoChange = (uploadFile) => {
  photoFile.value = uploadFile.raw
  previewUrl.value = URL.createObjectURL(uploadFile.raw)
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  
  const formData = new FormData()
  Object.keys(form).forEach(key => {
    if (form[key] !== null && form[key] !== undefined) {
      if (key === 'purchase_date') {
        formData.append(key, form[key].toISOString().split('T')[0])
      } else {
        formData.append(key, form[key])
      }
    }
  })
  if (photoFile.value) {
    formData.append('photo', photoFile.value)
  }

  try {
    if (isEdit.value) {
      await materialApi.update(editId.value, formData)
      ElMessage.success('更新成功')
    } else {
      await materialApi.create(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchMaterials()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '操作失败')
  }
}

onMounted(fetchMaterials)
</script>

<style scoped>
.filter-card {
  margin-bottom: 16px;
}

.material-card {
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.material-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.material-photo {
  position: relative;
  height: 160px;
  background: #f5f5f5;
  overflow: hidden;
}

.material-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.material-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: #4caf50;
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.material-badge.low {
  background: #f44336;
}

.material-info {
  padding: 16px;
}

.material-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.material-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.color-code {
  font-size: 12px;
  color: #999;
}

.material-details {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.detail-item {
  text-align: center;
}

.detail-item .label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 2px;
}

.detail-item .value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.material-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
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
</style>
