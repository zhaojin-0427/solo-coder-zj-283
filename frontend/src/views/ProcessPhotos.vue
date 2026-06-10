<template>
  <div class="photos-page">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="所属作品">
          <el-select v-model="filters.project_id" placeholder="全部作品" clearable @change="fetchPhotos" style="width: 200px;">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="photos-grid" v-if="photos.length">
      <div v-for="photo in photos" :key="photo.id" class="photo-item">
        <el-card :body-style="{ padding: 0 }" class="photo-card">
          <div class="photo-wrapper">
            <img :src="getImageUrl(photo.photo)" alt="" @click="previewPhoto(photo)" />
            <div class="photo-overlay">
              <el-tag size="small" type="primary">{{ photo.stage }}</el-tag>
            </div>
          </div>
          <div class="photo-info">
            <div class="photo-project">{{ photo.project_name }}</div>
            <div class="photo-date">{{ photo.created_at }}</div>
            <div class="photo-desc" v-if="photo.description">{{ photo.description }}</div>
          </div>
        </el-card>
      </div>
    </div>
    <el-empty v-else description="暂无过程照片" />

    <el-dialog v-model="previewVisible" width="800px" class="preview-dialog">
      <div class="preview-content" v-if="currentPhoto">
        <img :src="getImageUrl(currentPhoto.photo)" alt="" />
        <div class="preview-meta">
          <div class="meta-row">
            <el-tag type="primary" size="large">{{ currentPhoto.stage }}</el-tag>
            <span class="project-name">{{ currentPhoto.project_name }}</span>
          </div>
          <div class="meta-date">{{ currentPhoto.created_at }}</div>
          <div class="meta-section" v-if="currentPhoto.description">
            <div class="meta-label">过程描述</div>
            <div class="meta-content">{{ currentPhoto.description }}</div>
          </div>
          <div class="meta-section experience" v-if="currentPhoto.experience">
            <div class="meta-label">制作经验</div>
            <div class="meta-content">{{ currentPhoto.experience }}</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { processPhotoApi, projectApi, getImageUrl } from '@/api'

const photos = ref([])
const projects = ref([])
const previewVisible = ref(false)
const currentPhoto = ref(null)

const filters = reactive({
  project_id: ''
})

const fetchPhotos = async () => {
  try {
    const params = filters.project_id ? { project_id: filters.project_id } : {}
    const res = await processPhotoApi.list(params)
    photos.value = res.data
  } catch (err) {
    console.error('获取照片失败', err)
  }
}

const fetchProjects = async () => {
  try {
    const res = await projectApi.list()
    projects.value = res.data
  } catch (err) {
    console.error('获取作品失败', err)
  }
}

const previewPhoto = (photo) => {
  currentPhoto.value = photo
  previewVisible.value = true
}

onMounted(() => {
  fetchPhotos()
  fetchProjects()
})
</script>

<style scoped>
.filter-card {
  margin-bottom: 20px;
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.photo-card {
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.photo-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.photo-wrapper {
  position: relative;
  height: 200px;
  overflow: hidden;
  cursor: pointer;
}

.photo-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.photo-wrapper:hover img {
  transform: scale(1.05);
}

.photo-overlay {
  position: absolute;
  top: 12px;
  left: 12px;
}

.photo-info {
  padding: 12px 16px;
}

.photo-project {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.photo-date {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.photo-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.preview-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.preview-content {
  display: flex;
  max-height: 600px;
}

.preview-content img {
  width: 60%;
  object-fit: contain;
  background: #f5f5f5;
}

.preview-meta {
  width: 40%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.meta-date {
  font-size: 13px;
  color: #999;
}

.meta-section {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
}

.meta-section.experience {
  background: #fff8e1;
  border-left: 3px solid #ff9800;
}

.meta-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 6px;
}

.meta-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}
</style>
