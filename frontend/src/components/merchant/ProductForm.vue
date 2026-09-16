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
  detail_content: '',
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
  form.detail_content = ''
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
          :rows="2"
          placeholder="简短描述商品的主要特点和适用场景"
        />
      </el-form-item>
      <el-form-item label="功能介绍与使用说明">
        <el-input
          v-model="form.detail_content"
          type="textarea"
          :rows="8"
          placeholder="详细的功能介绍、使用方法、售后政策等。这些内容将作为AI客服的知识库依据,用户提问时AI会基于此内容进行介绍和推荐。&#10;&#10;建议包含:&#10;1. 核心功能介绍(各功能详细说明)&#10;2. 使用方法与注意事项&#10;3. 售后政策(退换货规则、保修期限等)&#10;4. 常见问题解答&#10;&#10;示例:&#10;【功能】支持NFC公交/门禁模拟,可绑定多张卡&#10;【使用】长按侧键3秒开机,下载APP绑定设备&#10;【售后】7天无理由退换,1年质保&#10;【注意】游泳时可佩戴,但不要热水浴"
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
.form-card { background: var(--bg-surface); border-radius: var(--radius-md); border: 1px solid var(--border-base); }
.header-title { font-weight: 700; font-size: 15px; color: var(--text-primary); }
</style>
