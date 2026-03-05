"""
经典监督学习：客户流失预测 (Churn Prediction)
适用场景：订阅服务、电商、SaaS、旅游平台
时间：25-30 分钟
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

# ============================================================================
# 1. 数据加载与探索 (5 min)
# ============================================================================

# 创建示例 CSV 数据（面试时会给你真实 CSV）
def create_sample_csv():
    """生成示例客户流失数据"""
    np.random.seed(42)
    n = 1000

    data = {
        'customer_id': range(1, n+1),
        'tenure_months': np.random.randint(1, 72, n),
        'monthly_charges': np.random.uniform(20, 150, n),
        'total_charges': np.random.uniform(100, 8000, n),
        'num_products': np.random.randint(1, 5, n),
        'num_support_calls': np.random.poisson(2, n),
        'contract_type': np.random.choice(['Month-to-month', 'One year', 'Two year'], n),
        'payment_method': np.random.choice(['Credit card', 'Bank transfer', 'Electronic check'], n),
        'age': np.random.randint(18, 75, n),
        'is_senior': np.random.binomial(1, 0.2, n),
    }

    df = pd.DataFrame(data)

    # 生成流失标签（业务逻辑）
    churn_prob = (
        0.1  # 基础流失率
        - 0.01 * (df['tenure_months'] / 12)  # 老客户更忠诚
        + 0.005 * (df['monthly_charges'] / 50)  # 高价格更易流失
        + 0.02 * (df['num_support_calls'] > 3)  # 频繁投诉
        + 0.15 * (df['contract_type'] == 'Month-to-month')  # 短期合约易流失
        + np.random.normal(0, 0.1, n)
    )
    df['churned'] = (churn_prob > 0.3).astype(int)

    # 保存 CSV
    df.to_csv('churn_data.csv', index=False)
    print("✓ 已创建 churn_data.csv")
    return df

# 加载数据
print("=" * 70)
print("客户流失预测 - 监督学习")
print("=" * 70)

# 如果没有 CSV，创建一个
try:
    df = pd.read_csv('churn_data.csv')
    print("\n✓ 已加载 churn_data.csv")
except FileNotFoundError:
    print("\n创建示例数据...")
    df = create_sample_csv()

# 基础探索
print(f"\n数据形状: {df.shape}")
print(f"流失率: {df['churned'].mean():.2%}")
print(f"\n前 5 行:")
print(df.head())

print(f"\n缺失值:")
print(df.isnull().sum())

print(f"\n数据类型:")
print(df.dtypes)

# ============================================================================
# 2. 特征工程 (5 min)
# ============================================================================

# 数值特征
df['avg_monthly_spend'] = df['total_charges'] / df['tenure_months'].replace(0, 1)
df['charges_per_product'] = df['monthly_charges'] / df['num_products']
df['is_high_support'] = (df['num_support_calls'] > 3).astype(int)

# 类别特征编码
df['is_month_to_month'] = (df['contract_type'] == 'Month-to-month').astype(int)
df['is_electronic_check'] = (df['payment_method'] == 'Electronic check').astype(int)

# 选择特征
feature_cols = [
    'tenure_months', 'monthly_charges', 'total_charges', 'num_products',
    'num_support_calls', 'age', 'is_senior',
    'avg_monthly_spend', 'charges_per_product', 'is_high_support',
    'is_month_to_month', 'is_electronic_check'
]

X = df[feature_cols]
y = df['churned']

print(f"\n特征数量: {len(feature_cols)}")

# ============================================================================
# 3. 模型训练 (5 min)
# ============================================================================

# 划分数据
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n训练集: {X_train.shape}, 测试集: {X_test.shape}")

# 标准化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 训练模型
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=20,
    random_state=42,
    class_weight='balanced'  # 处理不平衡
)

model.fit(X_train_scaled, y_train)

# 预测
y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

# ============================================================================
# 4. 模型评估 - 详细解释 Metrics (10 min)
# ============================================================================

print("\n" + "=" * 70)
print("模型评估 - Metrics 详解")
print("=" * 70)

# 混淆矩阵
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()

print(f"\n【混淆矩阵】")
print(f"              预测: 不流失  预测: 流失")
print(f"实际: 不流失      {tn:4d}      {fp:4d}  (FP = 误报)")
print(f"实际: 流失        {fn:4d}      {tp:4d}  (FN =漏报)")

# Metric 1: Accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"\n【1. Accuracy (准确率)】: {accuracy:.3f}")
print(f"   公式: (TP + TN) / (TP + TN + FP + FN)")
print(f"   含义: 所有预测中，正确的比例")
print(f"   ⚠️  局限: 数据不平衡时会误导（如 95% 不流失，全预测不流失也有 95% 准确率）")

# Metric 2: Precision
precision = precision_score(y_test, y_pred)
print(f"\n【2. Precision (精确率)】: {precision:.3f}")
print(f"   公式: TP / (TP + FP)")
print(f"   含义: 预测为流失的客户中，真正流失的比例")
print(f"   业务: 高 Precision → 减少误报，避免浪费挽留成本")
print(f"   例子: 预测 100 人流失，实际 {int(precision*100)} 人真流失")

# Metric 3: Recall (Sensitivity)
recall = recall_score(y_test, y_pred)
print(f"\n【3. Recall (召回率)】: {recall:.3f}")
print(f"   公式: TP / (TP + FN)")
print(f"   含义: 真正流失的客户中，被预测出来的比例")
print(f"   业务: 高 Recall → 减少漏报，不错过高价值客户")
print(f"   例子: 实际 100 人流失，成功识别 {int(recall*100)} 人")

# Metric 4: F1 Score
f1 = f1_score(y_test, y_pred)
print(f"\n【4. F1 Score (F1 分数)】: {f1:.3f}")
print(f"   公式: 2 × (Precision × Recall) / (Precision + Recall)")
print(f"   含义: Precision 和 Recall 的调和平均数")
print(f"   业务: 平衡精确率和召回率，适合不平衡数据")
print(f"   ⚠️  当 Precision 和 Recall 都重要时使用")

# Metric 5: AUC-ROC
auc = roc_auc_score(y_test, y_pred_proba)
print(f"\n【5. AUC-ROC (ROC 曲线下面积)】: {auc:.3f}")
print(f"   含义: 模型区分正负样本的能力")
print(f"   范围: [0.5, 1.0]，0.5 = 随机猜测，1.0 = 完美分类")
print(f"   业务: 衡量模型整体性能，不受阈值影响")
print(f"   解读:")
print(f"     - 0.9-1.0: 优秀")
print(f"     - 0.8-0.9: 良好")
print(f"     - 0.7-0.8: 一般")
print(f"     - 0.5-0.7: 较差")

# ============================================================================
# 5. 业务应用 (5 min)
# ============================================================================

print("\n" + "=" * 70)
print("业务应用建议")
print("=" * 70)

# 特征重要性
importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 5 流失预测因子:")
for i, row in importance.head(5).iterrows():
    print(f"  {row['feature']:25s}: {row['importance']:.3f}")

# 高风险客户识别
high_risk_threshold = 0.7
high_risk_customers = df.loc[X_test.index][y_pred_proba > high_risk_threshold]
print(f"\n高风险客户 (流失概率 > {high_risk_threshold}): {len(high_risk_customers)} 人")
print(f"建议: 优先挽留，提供折扣/升级服务")

print("\n" + "=" * 70)
print("面试要点总结")
print("=" * 70)
print("1. Metrics 选择:")
print("   - 不平衡数据: 用 Precision/Recall/F1，不用 Accuracy")
print("   - 业务优先级: 挽留成本低 → 高 Recall; 成本高 → 高 Precision")
print("   - 整体评估: AUC-ROC")
print("\n2. 阈值调整:")
print("   - 默认 0.5，可根据业务调整")
print("   - 降低阈值 → 提高 Recall（捕获更多流失）")
print("   - 提高阈值 → 提高 Precision（减少误报）")
print("\n3. 生产化:")
print("   - 定期重训练（月度）")
print("   - 监控 Precision/Recall 漂移")
print("   - A/B 测试挽留策略效果")
