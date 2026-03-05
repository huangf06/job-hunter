"""
简化版：动态定价转化率预测 (20-25 分钟)
核心：预测 P(Conversion | Price) → 优化 Expected Revenue
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

# ============================================================================
# 1. 生成数据 (5 min)
# ============================================================================
np.random.seed(42)
n = 5000

# 基础特征
data = {
    'price': np.random.uniform(50, 200, n),
    'competitor_price': np.random.uniform(60, 180, n),
    'days_advance': np.random.exponential(14, n),
    'capacity_left': np.random.uniform(0, 1, n),
    'is_weekend': np.random.randint(0, 2, n),
}
df = pd.DataFrame(data)

# 生成转化率：价格越高 → 转化越低，紧迫性 + 稀缺性 → 转化越高
price_effect = -2.0 * (df['price'] - df['competitor_price']) / df['competitor_price']
urgency = 1.5 * np.exp(-df['days_advance'] / 7)
scarcity = 1.0 * (1 - df['capacity_left'])
weekend = 0.3 * df['is_weekend']

logit = 1.0 + price_effect + urgency + scarcity + weekend + np.random.normal(0, 0.5, n)
df['converted'] = (1 / (1 + np.exp(-logit)) > 0.5).astype(int)

print(f"数据: {df.shape}, 转化率: {df['converted'].mean():.2%}")

# ============================================================================
# 2. 特征工程 (5 min)
# ============================================================================
df['price_vs_comp'] = (df['price'] - df['competitor_price']) / df['competitor_price']
df['urgency'] = np.exp(-df['days_advance'] / 7)
df['scarcity'] = 1 - df['capacity_left']

# ============================================================================
# 3. 训练模型 (5 min)
# ============================================================================
features = ['price', 'competitor_price', 'days_advance', 'capacity_left',
            'is_weekend', 'price_vs_comp', 'urgency', 'scarcity']
X = df[features]
y = df['converted']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
model.fit(X_train_scaled, y_train)

y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
auc = roc_auc_score(y_test, y_pred_proba)
print(f"\nTest AUC: {auc:.3f}")

# 特征重要性
importance = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
print("\n特征重要性:")
print(importance.head(5))

# ============================================================================
# 4. 优化价格 (5 min)
# ============================================================================
# 场景：周末，7 天后，20% 容量，竞争对手 $120
test_case = pd.DataFrame([{
    'price': 100,  # 待优化
    'competitor_price': 120,
    'days_advance': 7,
    'capacity_left': 0.2,
    'is_weekend': 1,
}])

# 遍历价格找最优
prices = np.arange(80, 160, 5)
revenues = []

for p in prices:
    test_case['price'] = p
    test_case['price_vs_comp'] = (p - 120) / 120
    test_case['urgency'] = np.exp(-7 / 7)
    test_case['scarcity'] = 1 - 0.2

    X_test = test_case[features]
    X_scaled = scaler.transform(X_test)
    prob = model.predict_proba(X_scaled)[0, 1]

    revenue = p * prob
    revenues.append(revenue)

optimal_idx = np.argmax(revenues)
optimal_price = prices[optimal_idx]
max_revenue = revenues[optimal_idx]

print(f"\n场景: 周末, 7天后, 20%容量, 竞争对手$120")
print(f"最优价格: ${optimal_price:.0f}")
print(f"期望收入: ${max_revenue:.2f}")

print("\n✓ 完成! 核心要点:")
print("1. 特征工程: price_vs_comp, urgency, scarcity")
print("2. GradientBoosting 捕捉非线性")
print("3. 优化目标: max(Price × P(Conversion))")
