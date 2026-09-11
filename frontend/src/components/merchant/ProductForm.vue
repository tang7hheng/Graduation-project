<script setup lang="ts">
import { reactive, ref } from 'vue'
import {
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElButton,
  ElCard,
  type FormInstance,
  type FormRules,
} from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useMerchantProductsStore } from '@/stores/merchantProducts'
import type { ProductCreate } from '@/api/client'

const store = useMerchantProductsStore()
const formRef = ref<FormInstance>()

const form = reactive<ProductCreate>({
  name: '',
  description: '',
  price: '',
  specs: '',
  stock: 0,
  image_url: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
}

function reset() {
  form.name = ''
  form.description = ''
  form.price = ''
  form.specs = ''
  form.stock = 0
  form.image_url = ''
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await store.add({ ...form })
      reset()
    } catch {
      /* error already toasted */
    }
  })
}
</script>

<template>
  <el-card class="form-card" shadow="never">
    <template #header>
      <span class="header-title">上架新商品</span>
    </template>
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="90px"
      label-position="right"
    >
      <el-form-item label="商品名称" prop="name">
        <el-input v-model="form.name" placeholder="如:智能云音箱 Pro" />
      </el-form-item>
      <el-form-item label="商品描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="商品的主要功能、特点、适用场景等(将作为客服检索依据)"
        />
      </el-form-item>
      <el-form-item label="规格参数">
        <el-input
          v-model="form.specs"
          type="textarea"
          :rows="3"
          placeholder="如:尺寸 150×90×90mm;功率 30W;Wi-Fi 5G"
        />
      </el-form-item>
      <el-form-item label="价格">
        <el-input v-model="form.price" placeholder="如:499.00 元">
          <template #append>元</template>
        </el-input>
      </el-form-item>
      <el-form-item label="库存">
        <el-input-number v-model="form.stock" :min="0" :step="10" />
      </el-form-item>
      <el-form-item label="图片 URL">
        <el-input v-model="form.image_url" placeholder="https://... (可选)" />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          :icon="Plus"
          :loading="store.submitting"
          @click="submit"
        >
          上架商品
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<style scoped>
.form-card {
  background: #fff;
}
.header-title {
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
}
</style>
