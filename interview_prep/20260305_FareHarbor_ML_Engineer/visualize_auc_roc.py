"""
AUC-ROC 可视化演示
帮助直观理解 ROC 曲线和 AUC 的含义
"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score

# 设置中文字体（如果需要）
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

print("=" * 70)
print("AUC-ROC 可视化演示")
print("=" * 70)

# ============================================================================
# 示例 1: 完美模型 vs 随机模型 vs 良好模型
# ============================================================================

# 真实标签（10 个样本：5 个正样本，5 个负样本）
y_true = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])

# 模型 1: 完美模型（所有正样本分数 > 所有负样本分数）
y_perfect = np.array([0.9, 0.85, 0.8, 0.75, 0.7, 0.4, 0.3, 0.2, 0.15, 0.1])

# 模型 2: 随机模型（分数随机）
y_random = np.array([0.6, 0.3, 0.7, 0.4, 0.5, 0.8, 0.2, 0.9, 0.1, 0.55])

# 模型 3: 良好模型（大部分正样本分数 > 负样本分数）
y_good = np.array([0.85, 0.75, 0.65, 0.55, 0.45, 0.5, 0.35, 0.25, 0.15, 0.1])

# 计算 ROC 和 AUC
fpr_perfect, tpr_perfect, _ = roc_curve(y_true, y_perfect)
auc_perfect = roc_auc_score(y_true, y_perfect)

fpr_random, tpr_random, _ = roc_curve(y_true, y_random)
auc_random = roc_auc_score(y_true, y_random)

fpr_good, tpr_good, _ = roc_curve(y_true, y_good)
auc_good = roc_auc_score(y_true, y_good)

# 画图
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# 左图：ROC 曲线对比
ax1 = axes[0]
ax1.plot(fpr_perfect, tpr_perfect, 'g-', linewidth=3, label=f'Perfect Model (AUC={auc_perfect:.2f})')
ax1.plot(fpr_good, tpr_good, 'b-', linewidth=3, label=f'Good Model (AUC={auc_good:.2f})')
ax1.plot(fpr_random, tpr_random, 'orange', linewidth=3, label=f'Random Model (AUC={auc_random:.2f})')
ax1.plot([0, 1], [0, 1], 'k--', linewidth=2, label='Random Guess (AUC=0.50)')

# 填充 AUC 区域
ax1.fill_between(fpr_good, tpr_good, alpha=0.2, color='blue')

ax1.set_xlabel('False Positive Rate (FPR)', fontsize=14, fontweight='bold')
ax1.set_ylabel('True Positive Rate (TPR)', fontsize=14, fontweight='bold')
ax1.set_title('ROC Curves Comparison', fontsize=16, fontweight='bold')
ax1.legend(loc='lower right', fontsize=12)
ax1.grid(alpha=0.3)
ax1.set_xlim([0, 1])
ax1.set_ylim([0, 1])

# 标注关键点
ax1.annotate('Perfect: All positives\nranked higher', xy=(0, 1), xytext=(0.3, 0.8),
            fontsize=11, color='green', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='green', lw=2))

ax1.annotate('Random: 50% chance', xy=(0.5, 0.5), xytext=(0.6, 0.3),
            fontsize=11, color='red', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='red', lw=2))

# 右图：分数分布
ax2 = axes[1]

# 正样本和负样本的分数分布
pos_scores_good = y_good[y_true == 1]
neg_scores_good = y_good[y_true == 0]

ax2.hist(neg_scores_good, bins=10, alpha=0.6, color='red', label='Negative Samples', edgecolor='black')
ax2.hist(pos_scores_good, bins=10, alpha=0.6, color='green', label='Positive Samples', edgecolor='black')

ax2.axvline(0.5, color='black', linestyle='--', linewidth=2, label='Threshold = 0.5')
ax2.set_xlabel('Predicted Score', fontsize=14, fontweight='bold')
ax2.set_ylabel('Count', fontsize=14, fontweight='bold')
ax2.set_title('Score Distribution (Good Model)', fontsize=16, fontweight='bold')
ax2.legend(fontsize=12)
ax2.grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('auc_roc_comparison.png', dpi=150, bbox_inches='tight')
print("\n✓ 已保存: auc_roc_comparison.png")

# ============================================================================
# 示例 2: 阈值变化对 TPR/FPR 的影响
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 使用良好模型的数据
thresholds_demo = [0.8, 0.6, 0.4, 0.2]

for idx, threshold in enumerate(thresholds_demo):
    ax = axes[idx // 2, idx % 2]

    # 根据阈值分类
    y_pred = (y_good >= threshold).astype(int)

    # 计算混淆矩阵
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    tn = np.sum((y_true == 0) & (y_pred == 0))

    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    # 画分数分布
    ax.hist(neg_scores_good, bins=10, alpha=0.6, color='red', label='Negative', edgecolor='black')
    ax.hist(pos_scores_good, bins=10, alpha=0.6, color='green', label='Positive', edgecolor='black')
    ax.axvline(threshold, color='black', linestyle='--', linewidth=3, label=f'Threshold={threshold}')

    # 标注结果
    ax.text(0.05, 0.95, f'TPR = {tpr:.2f}\nFPR = {fpr:.2f}\n\nTP={tp}, FP={fp}\nFN={fn}, TN={tn}',
            transform=ax.transAxes, fontsize=12, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax.set_xlabel('Predicted Score', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax.set_title(f'Threshold = {threshold}', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('threshold_effect.png', dpi=150, bbox_inches='tight')
print("✓ 已保存: threshold_effect.png")

# ============================================================================
# 示例 3: AUC 的直观含义（排序能力）
# ============================================================================

fig, ax = plt.subplots(figsize=(14, 6))

# 按分数排序
sorted_indices = np.argsort(y_good)[::-1]
sorted_scores = y_good[sorted_indices]
sorted_labels = y_true[sorted_indices]

# 画柱状图
colors = ['green' if label == 1 else 'red' for label in sorted_labels]
bars = ax.bar(range(len(sorted_scores)), sorted_scores, color=colors, edgecolor='black', linewidth=1.5)

# 标注
for i, (score, label) in enumerate(zip(sorted_scores, sorted_labels)):
    ax.text(i, score + 0.03, f'{score:.2f}', ha='center', fontsize=10, fontweight='bold')
    ax.text(i, -0.08, 'P' if label == 1 else 'N', ha='center', fontsize=12,
            fontweight='bold', color='green' if label == 1 else 'red')

ax.set_xlabel('Samples (Ranked by Score)', fontsize=14, fontweight='bold')
ax.set_ylabel('Predicted Score', fontsize=14, fontweight='bold')
ax.set_title('AUC Intuition: Good Model Ranks Positives Higher', fontsize=16, fontweight='bold')
ax.set_ylim([-0.15, 1.0])
ax.grid(alpha=0.3, axis='y')

# 添加说明
ax.text(0.5, 0.5, f'AUC = {auc_good:.2f}\n\nMeaning: {auc_good*100:.0f}% chance that\na random positive is ranked\nhigher than a random negative',
        transform=ax.transAxes, fontsize=14, ha='center',
        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

# 图例
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='green', label='Positive (Churned)'),
                   Patch(facecolor='red', label='Negative (Not Churned)')]
ax.legend(handles=legend_elements, loc='upper right', fontsize=12)

plt.tight_layout()
plt.savefig('auc_ranking_intuition.png', dpi=150, bbox_inches='tight')
print("✓ 已保存: auc_ranking_intuition.png")

# ============================================================================
# 打印总结
# ============================================================================

print("\n" + "=" * 70)
print("总结")
print("=" * 70)

print(f"\n【模型对比】")
print(f"  Perfect Model: AUC = {auc_perfect:.2f} (所有正样本分数 > 所有负样本)")
print(f"  Good Model:    AUC = {auc_good:.2f} (大部分正样本分数 > 负样本)")
print(f"  Random Model:  AUC = {auc_random:.2f} (随机猜测)")

print(f"\n【AUC 直观含义】")
print(f"  AUC = {auc_good:.2f} 意味着:")
print(f"  → 随机抽一个正样本和一个负样本")
print(f"  → 有 {auc_good*100:.0f}% 的概率，模型给正样本的分数更高")

print(f"\n【阈值影响】")
print(f"  阈值 ↑ → TPR ↓, FPR ↓ (更保守)")
print(f"  阈值 ↓ → TPR ↑, FPR ↑ (更激进)")
print(f"  AUC 评估所有阈值下的平均表现，不受单一阈值影响")

print(f"\n【面试金句】")
print(f"  'AUC 衡量的是排序能力，不是分类准确性'")
print(f"  'AUC 0.8+ 为良好模型，0.9+ 为优秀模型'")
print(f"  'AUC 不受阈值和类别不平衡影响，是评估分类模型的金标准'")

print("\n" + "=" * 70)
print("可视化文件已生成:")
print("  1. auc_roc_comparison.png - ROC 曲线对比")
print("  2. threshold_effect.png - 阈值对 TPR/FPR 的影响")
print("  3. auc_ranking_intuition.png - AUC 排序能力直观展示")
print("=" * 70)
