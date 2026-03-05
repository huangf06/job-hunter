"""
简化版：客户聚类与定价策略 (20-25 分钟)
核心：K-Means 分群 → 识别价格敏感度 → 差异化定价
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# ============================================================================
# 1. 生成数据 (5 min)
# ============================================================================
np.random.seed(42)

# 4 类客户：Budget, Premium, Value, Spontaneous
segments = []

# Budget: 低消费, 提前订, 高价格敏感
budget = pd.DataFrame({
    'avg_spend': np.random.normal(80, 15, 300),
    'frequency': np.random.normal(2, 0.5, 300),
    'days_advance': np.random.normal(25, 5, 300),
    'price_sensitivity': np.random.normal(0.8, 0.1, 300),
})
segments.append(budget)

# Premium: 高消费, 临时订, 低价格敏感
premium = pd.DataFrame({
    'avg_spend': np.random.normal(180, 25, 200),
    'frequency': np.random.normal(4, 1, 200),
    'days_advance': np.random.normal(5, 2, 200),
    'price_sensitivity': np.random.normal(0.2, 0.1, 200),
})
segments.append(premium)

# Value: 中等消费, 中等提前, 中等敏感
value = pd.DataFrame({
    'avg_spend': np.random.normal(120, 20, 300),
    'frequency': np.random.normal(3, 0.8, 300),
    'days_advance': np.random.normal(15, 4, 300),
    'price_sensitivity': np.random.normal(0.5, 0.1, 300),
})
segments.append(value)

# Spontaneous: 高消费, 极临时, 中低敏感
spontaneous = pd.DataFrame({
    'avg_spend': np.random.normal(140, 30, 200),
    'frequency': np.random.normal(1.5, 0.5, 200),
    'days_advance': np.random.normal(3, 1, 200),
    'price_sensitivity': np.random.normal(0.4, 0.15, 200),
})
segments.append(spontaneous)

df = pd.concat(segments, ignore_index=True)
print(f"数据: {df.shape}")

# ============================================================================
# 2. 特征工程 (5 min)
# ============================================================================
df['lifetime_value'] = df['avg_spend'] * df['frequency']
df['urgency'] = np.exp(-df['days_advance'] / 10)

# ============================================================================
# 3. 聚类 (5 min)
# ============================================================================
features = ['avg_spend', 'frequency', 'days_advance', 'price_sensitivity',
            'lifetime_value', 'urgency']
X = df[features]

# 标准化
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# K-Means
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
labels = kmeans.fit_predict(X_scaled)

# 评估
silhouette = silhouette_score(X_scaled, labels)
print(f"\nSilhouette Score: {silhouette:.3f} (越高越好)")

# ============================================================================
# 4. 分析客群 (5 min)
# ============================================================================
df['cluster'] = labels

print("\n客群画像:")
for i in range(4):
    cluster_data = df[df['cluster'] == i]
    print(f"\n--- Cluster {i} (n={len(cluster_data)}) ---")
    print(f"  平均消费: ${cluster_data['avg_spend'].mean():.0f}")
    print(f"  频率: {cluster_data['frequency'].mean():.1f} 次/年")
    print(f"  提前天数: {cluster_data['days_advance'].mean():.0f} 天")
    print(f"  价格敏感: {cluster_data['price_sensitivity'].mean():.2f}")
    print(f"  LTV: ${cluster_data['lifetime_value'].mean():.0f}")

    # 推荐策略
    avg_sens = cluster_data['price_sensitivity'].mean()
    avg_advance = cluster_data['days_advance'].mean()

    if avg_sens > 0.6 and avg_advance > 15:
        print(f"  → 策略: 早鸟折扣, 捆绑优惠")
    elif avg_sens < 0.3:
        print(f"  → 策略: 溢价定价, VIP 体验")
    elif avg_advance < 5:
        print(f"  → 策略: 动态定价, 限时促销")
    else:
        print(f"  → 策略: 竞争性定价, 透明价值")

print("\n✓ 完成! 核心要点:")
print("1. 特征: lifetime_value, urgency")
print("2. 标准化必须 (不同量纲)")
print("3. Silhouette Score 验证聚类质量")
print("4. 每个簇对应明确的定价策略")
