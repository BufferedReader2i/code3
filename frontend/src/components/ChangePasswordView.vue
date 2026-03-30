<template>
  <main class="change-password-page">
    <div class="password-card">
      <div class="card-header">
        <button type="button" class="btn-back" @click="$emit('back')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          返回
        </button>
        <h2>修改密码</h2>
      </div>
      
      <div class="card-body">
        <div class="form-group">
          <label>当前密码</label>
          <input v-model="passwordForm.currentPassword" type="password" class="form-input" placeholder="请输入当前密码">
        </div>
        <div class="form-group">
          <label>新密码</label>
          <input v-model="passwordForm.newPassword" type="password" class="form-input" placeholder="请输入新密码">
        </div>
        <div class="form-group">
          <label>确认新密码</label>
          <input v-model="passwordForm.confirmPassword" type="password" class="form-input" placeholder="请再次输入新密码">
        </div>
        
        <div v-if="passwordError" class="error-message">{{ passwordError }}</div>
        <div v-if="passwordSuccess" class="success-message">{{ passwordSuccess }}</div>
        
        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="$emit('back')">取消</button>
          <button type="button" class="btn-save" @click="handleChangePassword" :disabled="passwordLoading">
            {{ passwordLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<script>
export default {
  name: 'ChangePasswordView',
  emits: ['back', 'password-changed'],
  data() {
    return {
      passwordForm: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      passwordError: '',
      passwordSuccess: '',
      passwordLoading: false
    }
  },
  methods: {
    handleChangePassword() {
      this.passwordError = '';
      this.passwordSuccess = '';
      
      if (!this.passwordForm.currentPassword) {
        this.passwordError = '请输入当前密码';
        return;
      }
      if (!this.passwordForm.newPassword) {
        this.passwordError = '请输入新密码';
        return;
      }
      if (this.passwordForm.newPassword.length < 6) {
        this.passwordError = '新密码长度至少6位';
        return;
      }
      if (this.passwordForm.newPassword !== this.passwordForm.confirmPassword) {
        this.passwordError = '两次输入的新密码不一致';
        return;
      }
      
      this.passwordLoading = true;
      this.$api.changePassword(this.passwordForm.currentPassword, this.passwordForm.newPassword)
        .then(() => {
          this.passwordSuccess = '密码修改成功';
          this.passwordForm = { currentPassword: '', newPassword: '', confirmPassword: '' };
          setTimeout(() => {
            this.$emit('back');
          }, 1500);
        })
        .catch(err => {
          this.passwordError = err.response?.data?.detail || err.message || '修改密码失败';
        })
        .finally(() => {
          this.passwordLoading = false;
        });
    }
  }
}
</script>

<style scoped>
.change-password-page {
  min-height: calc(100vh - 64px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background-color: #f5f7fa;
}

.password-card {
  width: 100%;
  max-width: 420px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  background-color: #fafafa;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #666;
  font-size: 14px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.btn-back svg {
  width: 16px;
  height: 16px;
}

.btn-back:hover {
  background-color: #f0f0f0;
  color: #333;
}

.card-body {
  padding: 24px 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  font-size: 14px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
  transition: border-color 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #4a7ab5;
}

.error-message {
  padding: 10px 12px;
  margin-bottom: 16px;
  background-color: #fef0f0;
  border: 1px solid #fecaca;
  border-radius: 4px;
  color: #dc2626;
  font-size: 14px;
}

.success-message {
  padding: 10px 12px;
  margin-bottom: 16px;
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 4px;
  color: #16a34a;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-cancel,
.btn-save {
  flex: 1;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel {
  background-color: #f5f5f5;
  color: #666;
}

.btn-cancel:hover {
  background-color: #e8e8e8;
}

.btn-save {
  background-color: #4a7ab5;
  color: #ffffff;
}

.btn-save:hover {
  background-color: #3d6aa3;
}

.btn-save:disabled {
  background-color: #a0aec0;
  cursor: not-allowed;
}
</style>
