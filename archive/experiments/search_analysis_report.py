# =============================================================================
# 搜索策略分析报告
# =============================================================================

ANALYSIS = """
问题诊断:
==========

1. 当前配置的问题:
   - 5个策略 × 8职位 = 40职位
   - 复杂布尔语法可能不被LinkedIn完全支持
   - 策略间隔30秒，总时间约5-8分钟
   - 风险: 中高（可能触发反爬）

2. LinkedIn的限制:
   - 未登录用户: 约100职位/天限制
   - 频繁请求: 可能要求登录或验证码
   - 复杂搜索: 结果可能不准确

3. 最佳实践（基于经验）:
   - 简单关键词 > 复杂布尔
   - 少策略+深挖掘 > 多策略+浅挖掘
   - 间隔 > 速度

我的建议方案:
==============

方案: "3+2" 策略

LinkedIn (3个策略):
  1. "quantitative researcher" - 8职位
  2. "machine learning engineer" - 8职位  
  3. "data engineer" - 8职位
  间隔: 30秒
  预计: 24职位, 3-4分钟

IamExpat (2个策略):
  1. "data" - 10职位
  2. "machine learning" - 10职位
  间隔: 20秒
  预计: 20职位, 2-3分钟

总计: 44职位/天, 6-8分钟
风险: 中低

优化建议:
==========

1. 关键词优化:
   - 去掉复杂布尔语法
   - 使用2-3个词的简单短语
   - 优先职位title中的关键词

2. 时间优化:
   - 上午9点或下午2点运行
   - 避开周一早上和周五下午
   - 周末不运行

3. 反爬优化:
   - headless=false（显示浏览器）
   - 随机化间隔时间（±5秒）
   - 限制每日总量 < 50

4. 监控指标:
   - 每个策略的有效职位率
   - 重复职位比例
   - 被封频率

测试计划:
==========

第1周: 测试简化方案
  - 每天运行1次
  - 记录成功率和时间
  - 观察是否被封

第2周: 优化调整
  - 根据结果调整关键词
  - 优化间隔时间
  - 增加/减少策略

第3周: 稳定运行
  - 确定最终配置
  - 接入自动化调度
"""

print(ANALYSIS)

# 推荐配置
RECOMMENDED_CONFIG = {
    "linkedin": {
        "enabled": True,
        "strategies": [
            {"name": "quant", "term": "quantitative researcher", "max": 8},
            {"name": "ml", "term": "machine learning engineer", "max": 8},
            {"name": "data", "term": "data engineer", "max": 8},
        ],
        "interval": 30,
        "time_range": "r86400",
        "headless": False
    },
    "iamexpat": {
        "enabled": True,
        "strategies": [
            {"name": "data", "term": "data", "max": 10},
            {"name": "ml", "term": "machine learning", "max": 10},
        ],
        "interval": 20,
        "headless": False
    },
    "daily_total": 44,
    "estimated_time": "6-8 minutes",
    "risk_level": "MEDIUM-LOW"
}

print("\n" + "="*60)
print("推荐配置:")
print("="*60)
import json
print(json.dumps(RECOMMENDED_CONFIG, indent=2))
