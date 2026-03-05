"""
Customer Segmentation for Pricing Strategy - Unsupervised Learning
===================================================================
Scenario: Segment customers by booking behavior and price sensitivity
to enable targeted pricing strategies.

Time: 30-40 minutes
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================================
# PART 1: Data Generation (5 min)
# ============================================================================

def generate_customer_data(n_customers=1000, random_state=42):
    """
    Generate synthetic customer booking history.

    Customer segments:
    1. Budget Travelers: Price-sensitive, book early, low spend
    2. Premium Seekers: Price-insensitive, last-minute, high spend
    3. Value Hunters: Moderate price sensitivity, compare options
    4. Spontaneous Bookers: Mixed behavior, impulse purchases
    """
    np.random.seed(random_state)

    # Generate 4 distinct customer segments
    segment_sizes = [300, 200, 300, 200]
    segments = []

    # Segment 1: Budget Travelers
    budget = pd.DataFrame({
        'avg_booking_value': np.random.normal(80, 15, segment_sizes[0]),
        'booking_frequency': np.random.normal(2, 0.5, segment_sizes[0]),
        'avg_days_advance': np.random.normal(25, 5, segment_sizes[0]),
        'price_sensitivity': np.random.normal(0.8, 0.1, segment_sizes[0]),
        'weekend_ratio': np.random.normal(0.3, 0.1, segment_sizes[0]),
        'cancellation_rate': np.random.normal(0.15, 0.05, segment_sizes[0]),
        'true_segment': 'Budget'
    })
    segments.append(budget)

    # Segment 2: Premium Seekers
    premium = pd.DataFrame({
        'avg_booking_value': np.random.normal(180, 25, segment_sizes[1]),
        'booking_frequency': np.random.normal(4, 1, segment_sizes[1]),
        'avg_days_advance': np.random.normal(5, 2, segment_sizes[1]),
        'price_sensitivity': np.random.normal(0.2, 0.1, segment_sizes[1]),
        'weekend_ratio': np.random.normal(0.7, 0.1, segment_sizes[1]),
        'cancellation_rate': np.random.normal(0.05, 0.03, segment_sizes[1]),
        'true_segment': 'Premium'
    })
    segments.append(premium)

    # Segment 3: Value Hunters
    value = pd.DataFrame({
        'avg_booking_value': np.random.normal(120, 20, segment_sizes[2]),
        'booking_frequency': np.random.normal(3, 0.8, segment_sizes[2]),
        'avg_days_advance': np.random.normal(15, 4, segment_sizes[2]),
        'price_sensitivity': np.random.normal(0.5, 0.1, segment_sizes[2]),
        'weekend_ratio': np.random.normal(0.5, 0.1, segment_sizes[2]),
        'cancellation_rate': np.random.normal(0.10, 0.04, segment_sizes[2]),
        'true_segment': 'Value'
    })
    segments.append(value)

    # Segment 4: Spontaneous Bookers
    spontaneous = pd.DataFrame({
        'avg_booking_value': np.random.normal(140, 30, segment_sizes[3]),
        'booking_frequency': np.random.normal(1.5, 0.5, segment_sizes[3]),
        'avg_days_advance': np.random.normal(3, 1, segment_sizes[3]),
        'price_sensitivity': np.random.normal(0.4, 0.15, segment_sizes[3]),
        'weekend_ratio': np.random.normal(0.6, 0.15, segment_sizes[3]),
        'cancellation_rate': np.random.normal(0.20, 0.08, segment_sizes[3]),
        'true_segment': 'Spontaneous'
    })
    segments.append(spontaneous)

    df = pd.concat(segments, ignore_index=True)

    # Clip values to realistic ranges
    df['avg_booking_value'] = df['avg_booking_value'].clip(50, 250)
    df['booking_frequency'] = df['booking_frequency'].clip(1, 10)
    df['avg_days_advance'] = df['avg_days_advance'].clip(0, 60)
    df['price_sensitivity'] = df['price_sensitivity'].clip(0, 1)
    df['weekend_ratio'] = df['weekend_ratio'].clip(0, 1)
    df['cancellation_rate'] = df['cancellation_rate'].clip(0, 0.5)

    return df


# ============================================================================
# PART 2: Feature Engineering (5 min)
# ============================================================================

def engineer_customer_features(df):
    """
    Create derived features for customer segmentation.
    """
    df = df.copy()

    # Behavioral features
    df['total_lifetime_value'] = df['avg_booking_value'] * df['booking_frequency']
    df['booking_urgency'] = np.exp(-df['avg_days_advance'] / 10)
    df['reliability_score'] = 1 - df['cancellation_rate']

    # Composite scores
    df['premium_score'] = (
        (df['avg_booking_value'] / 250) * 0.4 +
        (df['booking_frequency'] / 10) * 0.3 +
        (1 - df['price_sensitivity']) * 0.3
    )

    df['spontaneity_score'] = (
        df['booking_urgency'] * 0.6 +
        df['weekend_ratio'] * 0.4
    )

    return df


# ============================================================================
# PART 3: Clustering (10 min)
# ============================================================================

def find_optimal_clusters(X_scaled, max_k=10):
    """
    Use elbow method and silhouette score to find optimal k.
    """
    inertias = []
    silhouette_scores = []
    K_range = range(2, max_k + 1)

    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        inertias.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(X_scaled, labels))

    # Plot elbow curve
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(K_range, inertias, marker='o', linewidth=2)
    ax1.set_xlabel('Number of Clusters (k)', fontsize=12)
    ax1.set_ylabel('Inertia', fontsize=12)
    ax1.set_title('Elbow Method', fontsize=14, fontweight='bold')
    ax1.grid(alpha=0.3)

    ax2.plot(K_range, silhouette_scores, marker='o', linewidth=2, color='orange')
    ax2.set_xlabel('Number of Clusters (k)', fontsize=12)
    ax2.set_ylabel('Silhouette Score', fontsize=12)
    ax2.set_title('Silhouette Analysis', fontsize=14, fontweight='bold')
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('cluster_optimization.png', dpi=150)
    print("✓ Saved: cluster_optimization.png")

    # Recommend k
    optimal_k = K_range[np.argmax(silhouette_scores)]
    print(f"\nRecommended k: {optimal_k} (highest silhouette score: {max(silhouette_scores):.3f})")

    return optimal_k


def perform_clustering(X_scaled, n_clusters=4):
    """
    Perform K-Means clustering and evaluate.
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    labels = kmeans.fit_predict(X_scaled)

    # Evaluation metrics
    silhouette = silhouette_score(X_scaled, labels)
    davies_bouldin = davies_bouldin_score(X_scaled, labels)

    print(f"\nClustering Metrics:")
    print(f"  Silhouette Score: {silhouette:.3f} (higher is better, range [-1, 1])")
    print(f"  Davies-Bouldin Index: {davies_bouldin:.3f} (lower is better)")

    return kmeans, labels


# ============================================================================
# PART 4: Segment Analysis & Pricing Strategy (10 min)
# ============================================================================

def analyze_segments(df, labels):
    """
    Profile each cluster and recommend pricing strategies.
    """
    df = df.copy()
    df['cluster'] = labels

    print("\n" + "=" * 70)
    print("SEGMENT PROFILES")
    print("=" * 70)

    for cluster_id in sorted(df['cluster'].unique()):
        cluster_data = df[df['cluster'] == cluster_id]

        print(f"\n--- Cluster {cluster_id} (n={len(cluster_data)}) ---")
        print(f"Avg Booking Value:    ${cluster_data['avg_booking_value'].mean():.2f}")
        print(f"Booking Frequency:    {cluster_data['booking_frequency'].mean():.2f} times/year")
        print(f"Avg Days Advance:     {cluster_data['avg_days_advance'].mean():.1f} days")
        print(f"Price Sensitivity:    {cluster_data['price_sensitivity'].mean():.2f}")
        print(f"Weekend Ratio:        {cluster_data['weekend_ratio'].mean():.2%}")
        print(f"Cancellation Rate:    {cluster_data['cancellation_rate'].mean():.2%}")
        print(f"Lifetime Value:       ${cluster_data['total_lifetime_value'].mean():.2f}")

        # Infer segment type
        avg_value = cluster_data['avg_booking_value'].mean()
        avg_sensitivity = cluster_data['price_sensitivity'].mean()
        avg_advance = cluster_data['avg_days_advance'].mean()

        if avg_sensitivity > 0.6 and avg_advance > 15:
            segment_type = "Budget Travelers"
            strategy = "Early-bird discounts, bundle deals, loyalty rewards"
        elif avg_value > 150 and avg_sensitivity < 0.3:
            segment_type = "Premium Seekers"
            strategy = "Premium pricing, VIP experiences, last-minute availability"
        elif avg_advance < 5:
            segment_type = "Spontaneous Bookers"
            strategy = "Dynamic pricing, flash sales, urgency messaging"
        else:
            segment_type = "Value Hunters"
            strategy = "Competitive pricing, transparent value, comparison tools"

        print(f"\nSegment Type:         {segment_type}")
        print(f"Pricing Strategy:     {strategy}")


def visualize_segments(df, labels, X_scaled):
    """
    Visualize clusters in 2D using PCA.
    """
    # PCA for visualization
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    df_viz = df.copy()
    df_viz['cluster'] = labels
    df_viz['PC1'] = X_pca[:, 0]
    df_viz['PC2'] = X_pca[:, 1]

    # Scatter plot
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(
        df_viz['PC1'],
        df_viz['PC2'],
        c=df_viz['cluster'],
        cmap='viridis',
        s=50,
        alpha=0.6,
        edgecolors='k',
        linewidth=0.5
    )
    plt.colorbar(scatter, label='Cluster')
    plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)', fontsize=12)
    plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)', fontsize=12)
    plt.title('Customer Segments (PCA Projection)', fontsize=14, fontweight='bold')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('customer_segments_pca.png', dpi=150)
    print("\n✓ Saved: customer_segments_pca.png")

    # Feature importance heatmap
    feature_cols = ['avg_booking_value', 'booking_frequency', 'avg_days_advance',
                    'price_sensitivity', 'weekend_ratio', 'cancellation_rate']

    cluster_profiles = df_viz.groupby('cluster')[feature_cols].mean()

    plt.figure(figsize=(10, 6))
    sns.heatmap(cluster_profiles.T, annot=True, fmt='.2f', cmap='RdYlGn', cbar_kws={'label': 'Value'})
    plt.xlabel('Cluster', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.title('Cluster Feature Profiles', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('cluster_heatmap.png', dpi=150)
    print("✓ Saved: cluster_heatmap.png")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Customer Segmentation for Pricing Strategy")
    print("=" * 70)

    # 1. Generate data
    print("\n[1/4] Generating customer booking history...")
    df = generate_customer_data(n_customers=1000)
    print(f"Dataset shape: {df.shape}")

    # 2. Feature engineering
    print("\n[2/4] Engineering customer features...")
    df_features = engineer_customer_features(df)

    # Prepare features for clustering
    feature_cols = ['avg_booking_value', 'booking_frequency', 'avg_days_advance',
                    'price_sensitivity', 'weekend_ratio', 'cancellation_rate',
                    'total_lifetime_value', 'booking_urgency', 'reliability_score',
                    'premium_score', 'spontaneity_score']

    X = df_features[feature_cols]

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Find optimal k and cluster
    print("\n[3/4] Finding optimal number of clusters...")
    optimal_k = find_optimal_clusters(X_scaled, max_k=8)

    print("\nPerforming clustering...")
    kmeans, labels = perform_clustering(X_scaled, n_clusters=optimal_k)

    # 4. Analyze segments
    print("\n[4/4] Analyzing customer segments...")
    analyze_segments(df_features, labels)

    # Visualize
    print("\nGenerating visualizations...")
    visualize_segments(df_features, labels, X_scaled)

    print("\n" + "=" * 70)
    print("INTERVIEW TALKING POINTS:")
    print("=" * 70)
    print("1. Feature engineering: LTV, urgency, reliability, composite scores")
    print("2. Clustering validation: Silhouette score, Davies-Bouldin index, elbow method")
    print("3. Business value: Segment-specific pricing strategies, targeted marketing")
    print("4. Production considerations: Periodic re-clustering, segment drift monitoring")
    print("5. Extensions: Hierarchical clustering, DBSCAN for outliers, RFM analysis")