import matplotlib.pyplot as plt
import numpy as np

# ===================== 硬编码你的实验数据 =====================
epochs = [1, 2, 3, 4, 5]

train_loss = [0.8778, 0.6456, 0.6456, 0.6408, 0.6373]
test_loss  = [0.6509, 0.6474, 0.6425, 0.6345, 0.6381]
precision = [0.1192, 0.1215, 0.1217, 0.1225, 0.1220]
recall    = [0.4779, 0.4881, 0.4874, 0.4913, 0.4903]
ndcg      = [0.3573, 0.3644, 0.3629, 0.3650, 0.3656]
auc       = [0.6651, 0.6753, 0.6788, 0.6773, 0.6797]
mrr       = [0.3822, 0.3880, 0.3852, 0.3874, 0.3886]

# ===================== 论文风格绘图（不重叠、高清、正式） =====================
plt.rcParams['figure.dpi'] = 300            # 高清
plt.rcParams['font.size'] = 11              # 统一字号
plt.rcParams['axes.linewidth'] = 0.8        # 边框粗细
plt.rcParams['font.sans-serif'] = ['Times New Roman']  # 论文字体
plt.rcParams['axes.unicode_minus'] = False

# 大图尺寸，避免拥挤
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()

# 颜色（论文常用配色）
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

# 1 Loss
axes[0].plot(epochs, train_loss, marker='o', color=colors[0], linewidth=1.5, markersize=4, label='Train Loss')
axes[0].plot(epochs, test_loss, marker='s', color=colors[1], linewidth=1.5, markersize=4, label='Test Loss')
axes[0].set_title('Loss', fontsize=12, pad=8)
axes[0].legend(frameon=False)
axes[0].grid(True, alpha=0.2)

# 2 Precision@5
axes[1].plot(epochs, precision, marker='o', color=colors[2], linewidth=1.5, markersize=4)
axes[1].set_title('Precision@5', fontsize=12, pad=8)
axes[1].grid(True, alpha=0.2)

# 3 Recall@5
axes[2].plot(epochs, recall, marker='o', color=colors[3], linewidth=1.5, markersize=4)
axes[2].set_title('Recall@5', fontsize=12, pad=8)
axes[2].grid(True, alpha=0.2)

# 4 NDCG@5
axes[3].plot(epochs, ndcg, marker='o', color=colors[4], linewidth=1.5, markersize=4)
axes[3].set_title('NDCG@5', fontsize=12, pad=8)
axes[3].grid(True, alpha=0.2)

# 5 AUC
axes[4].plot(epochs, auc, marker='o', color=colors[5], linewidth=1.5, markersize=4)
axes[4].set_title('AUC', fontsize=12, pad=8)
axes[4].grid(True, alpha=0.2)

# 6 MRR
axes[5].plot(epochs, mrr, marker='o', color='#e377c2', linewidth=1.5, markersize=4)
axes[5].set_title('MRR', fontsize=12, pad=8)
axes[5].grid(True, alpha=0.2)

# 统一 X 轴
for ax in axes:
    ax.set_xticks(epochs)
    ax.set_xlabel('Epoch', labelpad=3)

# 整体标题
fig.suptitle('Training Performance of News Recommendation Model', fontsize=14, y=0.98)

# 绝对不重叠
plt.tight_layout()
plt.subplots_adjust(top=0.93)

# 保存高清图片
plt.savefig('training_metrics_paper_style.png', dpi=600, bbox_inches='tight')
plt.show()