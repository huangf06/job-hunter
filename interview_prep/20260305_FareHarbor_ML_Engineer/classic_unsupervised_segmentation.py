"""
经典无监督学习：客户细分 (Customer Segmentation)
适用场景：电商、零售、旅游、SaaS
时间：25-30 分钟
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

# ============================================================================
# 1. 数据加载与探索 (5 min)
# ============================================================================

# 创建示例 CSV 数据（面试时会给你真实 CSV）
def create_sample_csv():
    """生成示例客户 RFM 数据"""
    np.random.seed(42)
    n = 500

    # 生成 4 类客户
    segments = []

    # Segment 1: VIP (高价值)
    vip = pd.DataFrame({
        'customer_id': range(1, 126),
        'recency_days': np.random.randint(1, 30, 125),  # 最近购买
        'frequency': np.random.randint(10, 30, 125),  # 高频
        'monetary': np.random.uniform(5000, 15000, 125),  # 高消费
        'avg_order_value': np.random.uniform(200, 500, 125),
        'tenure_months': np.random.randint(24, 60, 125),
    })
    segments.append(vip)

    # Segment 2: Loyal (忠诚但中等消费)
    loyal = pd.DataFrame({
        'customer_id': range(126, 251),
        'recency_days': np.random.randint(1, 60, 125),
        'frequency': np.random.randint(5, 15, 125),
        'monetary': np.random.uniform(1000, 5000, 125),
        'avg_order_value': np.random.uniform(80, 200, 125),
        'tenure_months': np.random.randint(12, 48, 125),
    })
    segments.append(loyal)

    # Segment 3: At-Risk (曾经活跃，现在沉默)
    at_risk = pd.DataFrame({
        'customer_id': range(251, 376),
        'recency_days': np.random.randint(90, 365, 125),  # 很久没买
        'frequency': np.random.randint(3, 10, 125),
        'monetary': np.random.uniform(500, 3000, 125),
        'avg_order_value': np.random.uniform(50, 150, 125),
        'tenure_months': np.random.randint(6, 36, 125),
    })
    segments.append(at_risk)

    # Segment 4: New/Low-Value (新客户或低价值)
    new_low = pd.DataFrame({
        'customer_id': range(376, 501),
        'recency_days': np.random.randint(30, 180, 125),
        'frequency': np.random.randint(1, 5, 125),
        'monetary': np.random.uniform(50, 1000, 125),
        'avg_order_value': np.random.uniform(20, 100, 125),
        'tenure_months': np.random.randint(1, 12, 125),
    })
    segments.append(new_low)

    df = pd.concat(segments, ignore_index=True)

    # 保存 CSV
    df.to_csv('customer_data.csv', index=False)
    print("✓ 已创建 customer_data.csv")
    return df

# 加载数据
print("=" * 70)
print("客户细分 - 无监督学习")
print("=" * 70)

# 如果没有 CSV，创建一个
try:
    df = pd.read_csv('customer_data.csv')
    print("\n✓ 已加载 customer_data.csv")
except FileNotFoundError:
    print("\n创建示例数据...")
    df = create_sample_csv()

# 基础探索
print(f"\n数据形状: {df.shape}")
print(f"\n前 5 行:")
print(df.head())

print(f"\n描述性统计:")
print(df.describe())

print(f"\n缺失值:")
print(df.isnull().sum())

# ============================================================================
# 2. 特征工程 (5 min)
# ============================================================================

# RFM 特征（Recency, Frequency, Monetary）
df['recency_score'] = 1 / (df['recency_days'] + 1)  # 越近越好，取倒数
df['frequency_score'] = df['frequency']
df['monetary_score'] = df['monetary']

# 复合特征
df['customer_lifetime_value'] = df['monetary']
df['engagement_score'] = df['frequency'] / (df['tenure_months'] + 1)
df['avg_purchase_interval'] = df['recency_days'] / (df['frequency'] + 1)

# 选择聚类特征
feature_cols = [
    'recency_days', 'frequency', 'monetary', 'avg_order_value',
    'tenure_months', 'recency_score', 'engagement_score'
]

X = df[feature_cols]

print(f"\n聚类特征: {len(feature_cols)} 个")

# ============================================================================
# 3. 聚类 (5 min)
# ============================================================================

# 标准化（必须！）
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"\n标准化后的数据形状: {X_scaled.shape}")

# 寻找最优 k（Elbow Method）
print("\n寻找最优聚类数...")
inertias = []
silhouette_scores = []
K_range = range(2, 8)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    inertias.append(kmeans.inertia_)
    silhouette_scores.append(silhouette_score(X_scaled, labels))

# 选择最优 k
optimal_k = K_range[np.argmax(silhouette_scores)]
print(f"推荐聚类数: {optimal_k} (Silhouette Score 最高)")

# 使用最优 k 聚类
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=20)
labels = kmeans.fit_predict(X_scaled)

df['cluster'] = labels

# ============================================================================
# 4. 聚类评估 - 详细解释 Metrics (10 min)
# ============================================================================

print("\n" + "=" * 70)
print("聚类评估 - Metrics 详解")
print("=" * 70)

# Metric 1: Inertia (惯性)
inertia = kmeans.inertia_
print(f"\n【1. Inertia (簇内平方和)】: {inertia:.2f}")
print(f"   公式: Σ (样本到其簇中心的距离²)")
print(f"   含义: 簇内紧密度，越小越好")
print(f"   ⚠️  局限: 随 k 增大单调递减，需结合 Elbow Method")
print(f"   用途: 画 Elbow 曲线找拐点")

# Metric 2: Silhouette Score
silhouette = silhouette_score(X_scaled, labels)
print(f"\n【2. Silhouette Score (轮廓系数)】: {silhouette:.3f}")
print(f"   公式: (b - a) / max(a, b)")
print(f"     a = 样本到同簇其他点的平均距离（簇内距离）")
print(f"     b = 样本到最近其他簇的平均距离（簇间距离）")
print(f"   范围: [-1, 1]")
print(f"   含义: 衡量样本与自己簇的匹配度")
print(f"   解读:")
print(f"     - 接近 +1: 样本离自己簇很近，离其他簇很远（好）")
print(f"     - 接近  0: 样本在簇边界上（模糊）")
print(f"     - 接近 -1: 样本可能分错簇了（差）")
print(f"   业务: 越高越好，通常 > 0.5 为良好聚类")

# Metric 3: Davies-Bouldin Index
davies_bouldin = davies_bouldin_score(X_scaled, labels)
print(f"\n【3. Davies-Bouldin Index (DB 指数)】: {davies_bouldin:.3f}")
print(f"   公式: (1/k) × Σ max[(σᵢ + σⱼ) / d(cᵢ, cⱼ)]")
print(f"     σᵢ = 簇 i 内样本到中心的平均距离")
print(f"     d(cᵢ, cⱼ) = 簇中心 i 和 j 的距离")
print(f"   含义: 簇内离散度 / 簇间距离")
print(f"   范围: [0, +∞)，越小越好")
print(f"   解读:")
print(f"     - 接近 0: 簇紧密且分离（好）")
print(f"     - 大于 2: 簇重叠严重（差）")
print(f"   业务: 衡量簇的分离度，越低越好")

# Metric 4: Calinski-Harabasz Index (方差比)
calinski = calinski_harabasz_score(X_scaled, labels)
print(f"\n【4. Calinski-Harabasz Index (CH 指数)】: {calinski:.2f}")
print(f"   公式: (簇间方差 / 簇内方差) × [(n - k) / (k - 1)]")
print(f"   含义: 簇间分离度 vs 簇内紧密度的比值")
print(f"   范围: [0, +∞)，越大越好")
print(f"   解读:")
print(f"     - 高值: 簇分离清晰，内部紧密（好）")
print(f"     - 低值: 簇边界模糊（差）")
print(f"   业务: 快速评估聚类质量，越高越好")

# ============================================================================
# 5. 业务分析 (5 min)
# ============================================================================

print("\n" + "=" * 70)
print("客群画像与策略")
print("=" * 70)

for cluster_id in sorted(df['cluster'].unique()):
    cluster_data = df[df['cluster'] == cluster_id]

    print(f"\n--- Cluster {cluster_id} (n={len(cluster_data)}, {len(cluster_data)/len(df):.1%}) ---")
    print(f"  Recency (最近购买):  {cluster_data['recency_days'].mean():.0f} 天")
    print(f"  Frequency (购买频次): {cluster_data['frequency'].mean():.1f} 次")
    print(f"  Monetary (总消费):   ${cluster_data['monetary'].mean():.0f}")
    print(f"  平均订单价值:        ${cluster_data['avg_order_value'].mean():.0f}")
    print(f"  客户生命周期:        {cluster_data['tenure_months'].mean():.0f} 月")

    # 客群定义
    avg_recency = cluster_data['recency_days'].mean()
    avg_frequency = cluster_data['frequency'].mean()
    avg_monetary = cluster_data['monetary'].mean()

    if avg_recency < 60 and avg_frequency > 10 and avg_monetary > 5000:
        segment_name = "VIP 客户"
        strategy = "专属服务、优先支持、高端产品推荐"
    elif avg_frequency > 5 and avg_monetary > 1000:
        segment_name = "忠诚客户"
        strategy = "会员计划、积分奖励、交叉销售"
    elif avg_recency > 90 and avg_frequency > 3:
        segment_name = "流失风险客户"
        strategy = "挽回邮件、限时折扣、问卷调查"
    else:
        segment_name = "新客户/低价值"
        strategy = "新手引导、首单优惠、培养忠诚度"

    print(f"  → 客群: {segment_name}")
    print(f"  → 策略: {strategy}")

# ============================================================================
# 6. Metrics 对比总结
# ============================================================================

print("\n" + "=" * 70)
print("Metrics 对比总结")
print("=" * 70)

print(f"\n{'Metric':<30} {'当前值':<15} {'越大越好/越小越好'}")
print("-" * 70)
print(f"{'Inertia':<30} {inertia:<15.2f} {'越小越好 (但看 Elbow)'}")
print(f"{'Silhouette Score':<30} {silhouette:<15.3f} {'越大越好 (>0.5 良好)'}")
print(f"{'Davies-Bouldin Index':<30} {davies_bouldin:<15.3f} {'越小越好 (<1.0 良好)'}")
print(f"{'Calinski-Harabasz Index':<30} {calinski:<15.2f} {'越大越好'}")

print("\n" + "=" * 70)
print("面试要点总结")
print("=" * 70)
print("1. 为什么要标准化?")
print("   - 不同特征量纲不同（天数 vs 金额）")
print("   - K-Means 基于欧氏距离，大数值特征会主导聚类")
print("   - StandardScaler: (x - mean) / std")
print("\n2. 如何选择 k?")
print("   - Elbow Method: Inertia 曲线找拐点")
print("   - Silhouette Score: 选最高的 k")
print("   - 业务可操作性: 4-6 个客群最实用")
print("\n3. Metrics 选择:")
print("   - 快速评估: Silhouette Score (最常用)")
print("   - 簇分离度: Davies-Bouldin Index")
print("   - 综合质量: Calinski-Harabasz Index")
print("   - 找最优 k: Elbow Method (Inertia)")
print("\n4. 生产化:")
print("   - 定期重聚类（季度）")
print("   - 监控簇大小变化（客群漂移）")
print("   - 新客户分配: kmeans.predict(new_data)")
print("   - A/B 测试不同策略效果")
