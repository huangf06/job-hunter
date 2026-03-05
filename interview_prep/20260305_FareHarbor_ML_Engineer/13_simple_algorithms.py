"""
简单算法实现 - 以防万一
只准备最可能考的 3 个算法

时间: 每个算法 10 分钟
难度: Easy
"""

import numpy as np
from collections import Counter

# ============================================================================
# 算法 1: KNN 分类器 (最可能考)
# ============================================================================

def knn_predict(X_train, y_train, X_test, k=3):
    """
    K-Nearest Neighbors 分类器

    参数:
    - X_train: 训练特征 (n_samples, n_features)
    - y_train: 训练标签 (n_samples,)
    - X_test: 测试特征 (m_samples, n_features)
    - k: 最近邻数量

    返回:
    - predictions: 预测标签 (m_samples,)

    时间复杂度: O(m * n * d) - m 测试样本, n 训练样本, d 特征维度
    空间复杂度: O(m) - 存储预测结果
    """
    predictions = []

    for x_test in X_test:
        # 计算测试样本到所有训练样本的距离
        # 欧氏距离: sqrt(sum((x1 - x2)^2))
        distances = np.sqrt(np.sum((X_train - x_test) ** 2, axis=1))

        # 找到最近的 k 个样本的索引
        nearest_indices = np.argsort(distances)[:k]

        # 获取这 k 个样本的标签
        nearest_labels = y_train[nearest_indices]

        # 投票: 选择出现最多的标签
        most_common = Counter(nearest_labels).most_common(1)[0][0]
        predictions.append(most_common)

    return np.array(predictions)


# 测试
if __name__ == "__main__":
    print("=" * 80)
    print("算法 1: KNN 分类器")
    print("=" * 80)

    # 简单数据集
    X_train = np.array([
        [1, 2],
        [2, 3],
        [3, 4],
        [6, 7],
        [7, 8],
        [8, 9]
    ])
    y_train = np.array([0, 0, 0, 1, 1, 1])  # 两个类别

    X_test = np.array([
        [2, 2],   # 应该预测为 0 (靠近前 3 个点)
        [7, 7]    # 应该预测为 1 (靠近后 3 个点)
    ])

    predictions = knn_predict(X_train, y_train, X_test, k=3)
    print(f"\n测试样本: {X_test}")
    print(f"预测结果: {predictions}")
    print(f"期望结果: [0, 1]")


# ============================================================================
# 算法 2: K-Means 聚类 (第二可能)
# ============================================================================

def kmeans(X, k, max_iters=100, random_state=42):
    """
    K-Means 聚类算法

    参数:
    - X: 数据 (n_samples, n_features)
    - k: 簇的数量
    - max_iters: 最大迭代次数
    - random_state: 随机种子

    返回:
    - labels: 每个样本的簇标签 (n_samples,)
    - centers: 簇中心 (k, n_features)

    时间复杂度: O(n * k * d * iters) - n 样本, k 簇, d 特征, iters 迭代次数
    空间复杂度: O(n + k*d) - 存储标签和中心点
    """
    np.random.seed(random_state)

    # 1. 随机初始化 k 个中心点
    n_samples = len(X)
    random_indices = np.random.choice(n_samples, k, replace=False)
    centers = X[random_indices].copy()

    for iteration in range(max_iters):
        # 2. 分配每个样本到最近的中心
        # 计算每个样本到每个中心的距离
        distances = np.zeros((n_samples, k))
        for i in range(k):
            distances[:, i] = np.sqrt(np.sum((X - centers[i]) ** 2, axis=1))

        # 找到最近的中心
        labels = np.argmin(distances, axis=1)

        # 3. 更新中心点为簇内样本的均值
        new_centers = np.zeros((k, X.shape[1]))
        for i in range(k):
            cluster_points = X[labels == i]
            if len(cluster_points) > 0:
                new_centers[i] = cluster_points.mean(axis=0)
            else:
                # 如果簇为空，保持原中心
                new_centers[i] = centers[i]

        # 4. 检查收敛 (中心点不再变化)
        if np.allclose(centers, new_centers):
            print(f"收敛于第 {iteration + 1} 次迭代")
            break

        centers = new_centers

    return labels, centers


# 测试
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("算法 2: K-Means 聚类")
    print("=" * 80)

    # 创建两个明显的簇
    cluster1 = np.random.randn(20, 2) + np.array([0, 0])
    cluster2 = np.random.randn(20, 2) + np.array([5, 5])
    X = np.vstack([cluster1, cluster2])

    labels, centers = kmeans(X, k=2, random_state=42)

    print(f"\n数据形状: {X.shape}")
    print(f"簇标签: {labels}")
    print(f"簇中心:\n{centers}")
    print(f"\n簇 0 的样本数: {np.sum(labels == 0)}")
    print(f"簇 1 的样本数: {np.sum(labels == 1)}")


# ============================================================================
# 算法 3: 线性回归 (第三可能)
# ============================================================================

def linear_regression(X, y):
    """
    线性回归 (正规方程法)

    参数:
    - X: 特征矩阵 (n_samples, n_features)
    - y: 目标值 (n_samples,)

    返回:
    - theta: 参数 (n_features + 1,) - 包含截距

    公式: θ = (X^T X)^(-1) X^T y

    时间复杂度: O(n * d^2 + d^3) - n 样本, d 特征
    空间复杂度: O(d^2) - 存储 X^T X
    """
    # 添加截距项 (bias)
    n_samples = len(X)
    X_b = np.c_[np.ones((n_samples, 1)), X]  # 在第一列添加 1

    # 正规方程: θ = (X^T X)^(-1) X^T y
    theta = np.linalg.inv(X_b.T @ X_b) @ X_b.T @ y

    return theta


def predict_linear(X, theta):
    """
    用训练好的参数预测

    参数:
    - X: 特征矩阵 (n_samples, n_features)
    - theta: 参数 (n_features + 1,)

    返回:
    - predictions: 预测值 (n_samples,)
    """
    n_samples = len(X)
    X_b = np.c_[np.ones((n_samples, 1)), X]
    return X_b @ theta


# 测试
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("算法 3: 线性回归")
    print("=" * 80)

    # 创建简单的线性数据: y = 2x + 3 + noise
    np.random.seed(42)
    X = np.random.rand(100, 1) * 10
    y = 2 * X.squeeze() + 3 + np.random.randn(100) * 0.5

    # 训练
    theta = linear_regression(X, y)
    print(f"\n学到的参数: {theta}")
    print(f"期望参数: [3, 2] (截距=3, 斜率=2)")

    # 预测
    X_test = np.array([[0], [5], [10]])
    predictions = predict_linear(X_test, theta)
    print(f"\n测试输入: {X_test.squeeze()}")
    print(f"预测输出: {predictions}")
    print(f"期望输出: [3, 13, 23] (大约)")


# ============================================================================
# 面试中如何回答
# ============================================================================

interview_tips = """
===============================================================================
面试中如何回答 "请实现 KNN"
===============================================================================

第 1 步: 说出思路 (30 秒)
"KNN 的核心思想是找到测试样本最近的 k 个训练样本，然后用这 k 个样本的标签投票。
具体步骤是:
1. 计算测试样本到所有训练样本的距离 (欧氏距离)
2. 找到距离最小的 k 个样本
3. 统计这 k 个样本的标签，选择出现最多的"

第 2 步: 写代码 (5-8 分钟)
- 边写边说: "我现在计算距离..."
- 处理边界: "如果 k > n_samples，我会..."
- 测试: "让我用简单例子测试一下"

第 3 步: 分析复杂度 (1 分钟)
"时间复杂度是 O(m * n * d):
- m 个测试样本
- 每个测试样本要和 n 个训练样本计算距离
- 每次距离计算是 O(d) (d 个特征)
- 排序是 O(n log n)，但被 O(m*n*d) 主导

空间复杂度是 O(m)，存储预测结果"

第 4 步: 讨论优化 (如果有时间)
"可以用 KD-Tree 或 Ball-Tree 优化到 O(m * log(n) * d)，
但实现复杂，通常用 sklearn 的 KDTree"

===============================================================================
关键要点
===============================================================================

✅ 做到的:
1. 先说思路再写代码
2. 代码简洁清晰 (不超过 20 行)
3. 处理边界情况
4. 测试代码
5. 分析复杂度

⚠️ 避免:
1. 直接写代码不解释
2. 过度优化 (面试不需要 KD-Tree)
3. 忘记测试
4. 不分析复杂度

💡 加分项:
1. 主动讨论距离度量 (欧氏 vs 曼哈顿 vs 余弦)
2. 讨论 k 的选择 (奇数避免平局)
3. 提到 sklearn 的实现 (KNeighborsClassifier)
"""

print(interview_tips)
