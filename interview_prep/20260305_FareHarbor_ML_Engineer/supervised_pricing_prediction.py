"""
Dynamic Pricing Conversion Prediction - Supervised Learning
============================================================
Scenario: Predict conversion probability at different price points
to optimize revenue for tour/activity bookings.

Time: 30-40 minutes
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt


# ============================================================================
# PART 1: Data Generation (5 min)
# ============================================================================

def generate_pricing_data(n_samples=5000, random_state=42):
    """
    Generate synthetic booking data with realistic pricing dynamics.

    Key patterns:
    - Higher prices → lower conversion
    - Last-minute bookings → less price sensitive
    - Low capacity → higher willingness to pay
    - Weekends → higher conversion
    """
    np.random.seed(random_state)

    data = {
        'base_price': np.random.uniform(50, 200, n_samples),
        'day_of_week': np.random.randint(0, 7, n_samples),
        'days_until_booking': np.random.exponential(14, n_samples),
        'capacity_remaining': np.random.uniform(0, 1, n_samples),
        'competitor_avg_price': np.random.uniform(60, 180, n_samples),
        'season': np.random.binomial(1, 0.4, n_samples),  # 40% high season
    }

    df = pd.DataFrame(data)

    # Generate conversion based on realistic pricing logic
    price_sensitivity = (df['base_price'] - df['competitor_avg_price']) / df['competitor_avg_price']
    urgency_factor = np.exp(-df['days_until_booking'] / 7)  # Last-minute urgency
    scarcity_factor = 1 - df['capacity_remaining']  # Low capacity → higher conversion
    weekend_boost = (df['day_of_week'] >= 5).astype(float) * 0.3
    season_boost = df['season'] * 0.2

    # Logistic conversion probability
    logit = (
        2.0  # Base conversion
        - 3.0 * price_sensitivity  # Price vs competitor
        + 1.5 * urgency_factor  # Urgency
        + 1.0 * scarcity_factor  # Scarcity
        + weekend_boost
        + season_boost
        + np.random.normal(0, 0.5, n_samples)  # Noise
    )

    df['converted'] = (1 / (1 + np.exp(-logit)) > 0.5).astype(int)

    return df


# ============================================================================
# PART 2: Feature Engineering (5 min)
# ============================================================================

def engineer_features(df):
    """
    Create domain-specific features for pricing optimization.
    """
    df = df.copy()

    # Price features
    df['price_vs_competitor'] = (df['base_price'] - df['competitor_avg_price']) / df['competitor_avg_price']
    df['price_per_capacity'] = df['base_price'] * (1 - df['capacity_remaining'])

    # Time features
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_last_minute'] = (df['days_until_booking'] < 3).astype(int)
    df['booking_urgency'] = np.exp(-df['days_until_booking'] / 7)

    # Scarcity features
    df['is_low_capacity'] = (df['capacity_remaining'] < 0.3).astype(int)
    df['scarcity_score'] = 1 - df['capacity_remaining']

    # Interaction features
    df['price_x_urgency'] = df['price_vs_competitor'] * df['booking_urgency']
    df['scarcity_x_season'] = df['scarcity_score'] * df['season']

    return df


# ============================================================================
# PART 3: Model Training (10 min)
# ============================================================================

def train_conversion_model(X_train, y_train, X_test, y_test):
    """
    Train gradient boosting model for conversion prediction.
    """
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train model
    model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=4,
        min_samples_split=50,
        random_state=42
    )

    model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    y_pred = (y_pred_proba > 0.5).astype(int)

    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"Test AUC: {auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nTop 10 Features:")
    print(feature_importance.head(10))

    return model, scaler, feature_importance


# ============================================================================
# PART 4: Revenue Optimization (10 min)
# ============================================================================

def optimize_price(model, scaler, sample_features, price_range=(50, 200)):
    """
    Find optimal price that maximizes expected revenue.

    Expected Revenue = Price × P(Conversion | Price)
    """
    prices = np.linspace(price_range[0], price_range[1], 100)
    expected_revenues = []

    for price in prices:
        # Update price in features
        features = sample_features.copy()
        features['base_price'] = price

        # Re-engineer features with new price
        features_df = pd.DataFrame([features])
        features_df = engineer_features(features_df)

        # Predict conversion probability
        X = features_df[model.feature_names_in_]
        X_scaled = scaler.transform(X)
        conversion_prob = model.predict_proba(X_scaled)[0, 1]

        # Calculate expected revenue
        expected_revenue = price * conversion_prob
        expected_revenues.append(expected_revenue)

    optimal_idx = np.argmax(expected_revenues)
    optimal_price = prices[optimal_idx]
    max_revenue = expected_revenues[optimal_idx]

    return optimal_price, max_revenue, prices, expected_revenues


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Dynamic Pricing Conversion Prediction")
    print("=" * 70)

    # 1. Generate data
    print("\n[1/4] Generating synthetic booking data...")
    df = generate_pricing_data(n_samples=5000)
    print(f"Dataset shape: {df.shape}")
    print(f"Conversion rate: {df['converted'].mean():.2%}")

    # 2. Feature engineering
    print("\n[2/4] Engineering features...")
    df_features = engineer_features(df)

    # Prepare train/test split
    feature_cols = [col for col in df_features.columns if col != 'converted']
    X = df_features[feature_cols]
    y = df_features['converted']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Train model
    print("\n[3/4] Training conversion model...")
    model, scaler, feature_importance = train_conversion_model(
        X_train, y_train, X_test, y_test
    )

    # 4. Optimize pricing for sample scenario
    print("\n[4/4] Optimizing price for sample booking...")
    sample_scenario = {
        'base_price': 100,  # Will be optimized
        'day_of_week': 5,  # Saturday
        'days_until_booking': 7,
        'capacity_remaining': 0.2,  # Low capacity
        'competitor_avg_price': 120,
        'season': 1  # High season
    }

    optimal_price, max_revenue, prices, revenues = optimize_price(
        model, scaler, sample_scenario
    )

    print(f"\nScenario: Weekend booking, 7 days out, 20% capacity left, high season")
    print(f"Competitor avg price: ${sample_scenario['competitor_avg_price']}")
    print(f"Optimal price: ${optimal_price:.2f}")
    print(f"Expected revenue: ${max_revenue:.2f}")

    # Visualize price-revenue curve
    plt.figure(figsize=(10, 6))
    plt.plot(prices, revenues, linewidth=2)
    plt.axvline(optimal_price, color='r', linestyle='--', label=f'Optimal: ${optimal_price:.2f}')
    plt.axvline(sample_scenario['competitor_avg_price'], color='g', linestyle='--',
                label=f'Competitor: ${sample_scenario["competitor_avg_price"]}')
    plt.xlabel('Price ($)', fontsize=12)
    plt.ylabel('Expected Revenue ($)', fontsize=12)
    plt.title('Price vs Expected Revenue', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('price_optimization_curve.png', dpi=150)
    print("\n✓ Saved visualization: price_optimization_curve.png")

    print("\n" + "=" * 70)
    print("INTERVIEW TALKING POINTS:")
    print("=" * 70)
    print("1. Feature engineering: price_vs_competitor, booking_urgency, scarcity_score")
    print("2. Model choice: GradientBoosting for non-linear interactions")
    print("3. Business metric: Expected Revenue = Price × P(Conversion)")
    print("4. Production considerations: A/B test price changes, monitor conversion drift")
    print("5. Extensions: Multi-armed bandit for online learning, segment-specific models")
