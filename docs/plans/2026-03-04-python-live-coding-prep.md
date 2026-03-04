# Python Live Coding 训练系统 - 2周建立绝对信心

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 2 周内建立 Python live coding 绝对信心，针对 DE/MLE 面试场景

**Architecture:** 混合训练系统 (70% 基础语法肌肉记忆 + 30% 实战场景)。Week 1 通过 LeetCode Easy 建立语言基础，Week 2 通过实战项目巩固工程能力。所有训练零 AI 辅助，强调手写 + 限时 + 口述。

**Tech Stack:** Python 3.x, LeetCode, VS Code, pytest, pandas, FastAPI, sentence-transformers, Docker, SQLite

---

## Task 1: 建立基础设施 (Day 1)

**Files:**
- Create: `drills/python_syntax_cheatsheet.md`
- Create: `drills/progress.db`
- Create: `drills/patterns.md`
- Create: `drills/gotchas.md`
- Create: `scripts/drill_tracker.py`
- Create: `drills/leetcode_easy/.gitkeep`
- Create: `drills/de_mle_projects/.gitkeep`
- Create: `drills/mock_interviews/.gitkeep`

**Step 1: 创建目录结构**

```bash
mkdir -p drills/leetcode_easy drills/de_mle_projects drills/mock_interviews
touch drills/leetcode_easy/.gitkeep drills/de_mle_projects/.gitkeep drills/mock_interviews/.gitkeep
```

**Step 2: 手写 Python 核心语法速查表**

创建 `drills/python_syntax_cheatsheet.md`，手写以下内容 (1 页 A4 纸)：

```markdown
# Python 核心语法速查表

## List 操作
- `list.append(x)` - 末尾添加
- `list.extend(iterable)` - 批量添加
- `list.insert(i, x)` - 指定位置插入
- `list.pop([i])` - 删除并返回
- `list[start:end:step]` - 切片
- `[x for x in iterable if condition]` - 列表推导式

## Dict 操作
- `dict.get(key, default)` - 安全获取
- `dict.setdefault(key, default)` - 获取或设置默认值
- `dict.update(other)` - 合并字典
- `{k: v for k, v in items if condition}` - 字典推导式

## String 操作
- `str.split(sep)` - 分割
- `str.join(iterable)` - 连接
- `str.strip()` - 去除首尾空白
- `str.replace(old, new)` - 替换
- `str.startswith(prefix)` / `str.endswith(suffix)`

## 常用内置函数
- `enumerate(iterable, start=0)` - 带索引遍历
- `zip(*iterables)` - 并行遍历
- `map(func, iterable)` - 映射
- `filter(func, iterable)` - 过滤
- `sorted(iterable, key=None, reverse=False)` - 排序
- `any(iterable)` / `all(iterable)` - 逻辑判断

## 高级特性
- `*args, **kwargs` - 可变参数
- `@decorator` - 装饰器
- `yield` - 生成器
- `with` - 上下文管理器

## 常见坑
- Mutable default args: `def f(x=[]):` ❌ → `def f(x=None): x = x or []` ✅
- Shallow vs deep copy: `list2 = list1` ❌ → `list2 = list1.copy()` ✅
- `is` vs `==`: `is` 比较身份，`==` 比较值
```

**Step 3: 初始化进度追踪数据库**

创建 `drills/progress.db` (SQLite)：

```python
import sqlite3

conn = sqlite3.connect('drills/progress.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,  -- 'leetcode' or 'project'
    item_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    time_spent INTEGER,  -- seconds
    passed BOOLEAN,
    notes TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()
```

**Step 4: 创建进度追踪 CLI 工具**

创建 `scripts/drill_tracker.py`：

```python
#!/usr/bin/env python3
"""
Drill Tracker - 追踪 Python live coding 训练进度

Usage:
    python scripts/drill_tracker.py --log leetcode 001_reverse_string 1 480 True "卡在边界条件"
    python scripts/drill_tracker.py --stats
    python scripts/drill_tracker.py --next
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "drills" / "progress.db"

def log_progress(item_type, item_id, attempt, time_spent, passed, notes):
    """记录一次训练"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO progress (item_type, item_id, attempt_number, time_spent, passed, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (item_type, item_id, attempt, time_spent, passed == 'True', notes))
    conn.commit()
    conn.close()
    print(f"✅ Logged: {item_type}/{item_id} attempt {attempt}")

def show_stats():
    """显示统计信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 总体统计
    cursor.execute('SELECT COUNT(DISTINCT item_id) FROM progress WHERE item_type = "leetcode"')
    leetcode_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT item_id) FROM progress WHERE item_type = "project"')
    project_count = cursor.fetchone()[0]

    # 今日统计
    cursor.execute('''
        SELECT COUNT(*) FROM progress
        WHERE DATE(timestamp) = DATE('now')
    ''')
    today_count = cursor.fetchone()[0]

    print(f"\n📊 训练统计")
    print(f"LeetCode 题目: {leetcode_count}/60")
    print(f"实战项目: {project_count}/5")
    print(f"今日训练次数: {today_count}")

    # 最近 5 次训练
    cursor.execute('''
        SELECT item_type, item_id, attempt_number, time_spent, passed, timestamp
        FROM progress
        ORDER BY timestamp DESC
        LIMIT 5
    ''')
    recent = cursor.fetchall()

    if recent:
        print(f"\n🕐 最近训练:")
        for r in recent:
            status = "✅" if r[4] else "❌"
            print(f"  {status} {r[0]}/{r[1]} (attempt {r[2]}) - {r[3]}s - {r[5]}")

    conn.close()

def suggest_next():
    """推荐下一个训练项目"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查今天完成了多少题
    cursor.execute('''
        SELECT COUNT(DISTINCT item_id) FROM progress
        WHERE item_type = "leetcode" AND DATE(timestamp) = DATE('now')
    ''')
    today_leetcode = cursor.fetchone()[0]

    print(f"\n💡 今日已完成 {today_leetcode}/10 道 LeetCode 题")

    if today_leetcode < 10:
        print(f"建议: 继续 LeetCode Easy 训练 (还需 {10 - today_leetcode} 道)")
    else:
        print(f"建议: 今日 LeetCode 目标已完成，可以提前进入实战项目或休息")

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: drill_tracker.py [--log|--stats|--next]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "--log":
        if len(sys.argv) != 8:
            print("Usage: --log <type> <id> <attempt> <time_spent> <passed> <notes>")
            sys.exit(1)
        log_progress(sys.argv[2], sys.argv[3], int(sys.argv[4]),
                    int(sys.argv[5]), sys.argv[6], sys.argv[7])
    elif command == "--stats":
        show_stats()
    elif command == "--next":
        suggest_next()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
```

**Step 5: 创建模式和坑点文件**

创建 `drills/patterns.md`:

```markdown
# 通用模式提炼

## Two Pointers
- 场景: 有序数组，查找配对
- 模板:
```python
left, right = 0, len(arr) - 1
while left < right:
    if condition:
        # found
    elif arr[left] + arr[right] < target:
        left += 1
    else:
        right -= 1
```

## Sliding Window
- 场景: 子数组/子串问题
- 模板:
```python
left = 0
for right in range(len(arr)):
    # 扩展窗口
    window.add(arr[right])

    # 收缩窗口
    while not valid(window):
        window.remove(arr[left])
        left += 1

    # 更新结果
    result = max(result, right - left + 1)
```

(后续从训练中补充)
```

创建 `drills/gotchas.md`:

```markdown
# 踩过的坑

(从训练中记录)
```

**Step 6: 配置 VS Code (关闭 AI 插件)**

创建 `.vscode/settings.json` (如果不存在):

```json
{
  "github.copilot.enable": false,
  "editor.quickSuggestions": false,
  "editor.suggestOnTriggerCharacters": false,
  "editor.wordBasedSuggestions": false,
  "editor.parameterHints.enabled": false
}
```

**Step 7: 验证基础设施**

```bash
python scripts/drill_tracker.py --stats
```

Expected output:
```
📊 训练统计
LeetCode 题目: 0/60
实战项目: 0/5
今日训练次数: 0
```

**Step 8: Commit**

```bash
git add drills/ scripts/drill_tracker.py .vscode/settings.json
git commit -m "feat: initialize Python live coding training infrastructure"
```

---

## Task 2: Week 1 训练 - LeetCode Easy (Day 2-7)

**Files:**
- Create: `drills/leetcode_easy/day2_string/*.py` (10 files)
- Create: `drills/leetcode_easy/day3_array/*.py` (10 files)
- Create: `drills/leetcode_easy/day4_hash_table/*.py` (10 files)
- Create: `drills/leetcode_easy/day5_stack_queue/*.py` (10 files)
- Create: `drills/leetcode_easy/day6_linked_list/*.py` (10 files)
- Create: `drills/leetcode_easy/day7_misc/*.py` (10 files)
- Modify: `drills/patterns.md` (每日补充)

**每日训练流程 (Day 2-7，每天 10 题)**

### Step 1: 在 LeetCode 选题 (5 分钟)

Day 2: LeetCode → Problems → Difficulty: Easy → Tags: String → 选 10 道
Day 3: Tags: Array → 选 10 道
Day 4: Tags: Hash Table → 选 10 道
Day 5: Tags: Stack, Queue → 各选 5 道
Day 6: Tags: Linked List → 选 10 道
Day 7: Tags: Recursion, Tree → 各选 5 道

推荐题目 (如果不知道选哪些):
- String: 344, 387, 242, 125, 28, 14, 58, 709, 680, 520
- Array: 26, 27, 88, 66, 283, 1, 121, 122, 217, 219
- Hash Table: 1, 217, 219, 242, 349, 350, 383, 389, 409, 496
- Stack: 20, 155, 232, 496, 682
- Queue: 225, 346, 933, 622, 641
- Linked List: 21, 83, 141, 160, 203, 206, 234, 237, 876, 1290
- Recursion/Tree: 70, 509, 104, 226, 617

### Step 2: 第 1 遍 - 在 LeetCode 提交 (60 分钟，每题 6 分钟)

对每道题:
1. 读题 → 手写伪代码 (纸笔，2 分钟)
2. 在 LeetCode 编辑器写代码 (3 分钟)
3. 提交 → 通过 (1 分钟)
4. 如果卡壳超过 10 分钟，可以看 1 个 hint (但不能看完整题解)

### Step 3: 复制到本地 (10 分钟)

为每道题创建本地文件，例如 `drills/leetcode_easy/day2_string/001_reverse_string.py`:

```python
"""
LeetCode 344. Reverse String
https://leetcode.com/problems/reverse-string/

Write a function that reverses a string. The input string is given as an array of characters s.

Example:
Input: s = ["h","e","l","l","o"]
Output: ["o","l","l","e","h"]
"""

def reverse_string(s):
    # Attempt 1: 2026-03-05 10:30 - LeetCode submission
    # Attempt 2: (待填写)
    pass


if __name__ == "__main__":
    # Test cases
    s1 = ["h","e","l","l","o"]
    reverse_string(s1)
    assert s1 == ["o","l","l","e","h"]

    s2 = ["H","a","n","n","a","H"]
    reverse_string(s2)
    assert s2 == ["h","a","n","n","a","H"]

    print("All tests passed!")
```

### Step 4: 第 2 遍 - 本地限时重写 (40 分钟，每题 4 分钟)

对每道题:
1. 删除或注释掉第 1 遍的代码
2. 设置计时器 4 分钟
3. 不看 LeetCode 代码，重新手写一遍
4. **边写边口述思路** (录音或对着镜子说)
5. 运行测试: `python 001_reverse_string.py`
6. 记录时间和卡壳点到注释

### Step 5: 记录进度 (5 分钟)

```bash
python scripts/drill_tracker.py --log leetcode 001_reverse_string 2 240 True "第2遍顺利"
```

### Step 6: 提炼模式 (20 分钟)

每天结束后，回顾 10 道题，提炼通用模式到 `drills/patterns.md`。

例如，Day 2 (String) 可能提炼出:
- Two pointers for palindrome
- Hash table for anagram
- Sliding window for substring

### Step 7: 每日 Commit

```bash
git add drills/leetcode_easy/day2_string/ drills/patterns.md
git commit -m "feat: complete Day 2 - 10 String problems (2 attempts each)"
```

**重复 Step 1-7，完成 Day 3-7**

---

## Task 3: Week 2 实战项目 1 - JSON 搜索引擎 (Day 8)

**Files:**
- Create: `drills/de_mle_projects/01_json_search_engine/*`

(详细步骤见 Task 3 完整版，包含: README, solution.py, Dockerfile, 2 遍实现)

---

## Task 4: Week 2 实战项目 2-5 (Day 9-12)

**项目 2: CSV 数据清洗工具 (Day 9)**

**Files:**
- Create: `drills/de_mle_projects/02_csv_data_cleaner/*`

**需求**:
- 读取 CSV (包含缺失值、重复行、异常值)
- 实现清洗: 删除重复、填充缺失值、移除异常值 (IQR)
- 用 pandas 实现，<50 行代码

**验收**: 给定测试 CSV，输出符合预期

---

**项目 3: REST API CRUD (Day 10)**

**Files:**
- Create: `drills/de_mle_projects/03_fastapi_crud/*`

**需求**:
- FastAPI 实现 TODO API
- 端点: GET/POST/PUT/DELETE `/todos`
- pydantic 数据验证

**验收**: curl 测试所有端点通过

---

**项目 4: 简单 ETL Pipeline (Day 11)**

**Files:**
- Create: `drills/de_mle_projects/04_simple_etl/*`

**需求**:
- 读 CSV (用户行为日志)
- 转换: 计算每用户总访问次数、平均停留时间
- 加载: 写入 SQLite

**验收**: 数据库有正确聚合结果

---

**项目 5: 文本相似度匹配 (Day 12)**

**Files:**
- Create: `drills/de_mle_projects/05_text_similarity/*`

**需求**:
- 实现 3 种相似度: Jaccard, Cosine (TF-IDF), Semantic (sentence-transformers)
- 返回 top-k 相似文本

**验收**: 3 种算法都返回正确结果，能解释区别

---

**每个项目的执行流程**:
1. 创建 README (需求 + 验收标准)
2. 第 1 遍实现 (2-3 小时)
3. 测试验证
4. 记录进度: `drill_tracker.py --log project <name> 1 <time> True <notes>`
5. 第 2 遍限时重写 (1-1.5 小时)
6. 记录进度: `drill_tracker.py --log project <name> 2 <time> True <notes>`
7. Commit

---

## Task 5: Week 2 模拟面试 (Day 13-14)

**Files:**
- Create: `drills/mock_interviews/2026-03-06_mock_01.md`
- Create: `drills/mock_interviews/2026-03-06_mock_02.md`
- Create: `drills/mock_interviews/2026-03-07_mock_01.md`
- Create: `drills/mock_interviews/2026-03-07_mock_02.md`

**每场模拟流程 (45 分钟)**

### Step 1: 准备录屏工具

安装 OBS Studio 或使用系统录屏 (Windows: Win+G)

### Step 2: 热身 (5 分钟)

随机抽 1 道 Week 1 的 Easy 题，口述思路 (不写代码)

### Step 3: 主题 (30 分钟)

随机抽 1 个实战项目的变种题:

**Day 13 Mock 1**: "实现一个 API，输入 CSV URL，返回清洗后的数据"
**Day 13 Mock 2**: "实现一个简单的用户认证系统 (JWT)"
**Day 14 Mock 1**: "实现一个日志聚合工具 (读多个 log 文件 → 统计)"
**Day 14 Mock 2**: "实现一个简单的推荐系统 (基于文本相似度)"

**关键规则**:
- 录屏全程
- 边写边口述
- 严格限时 30 分钟

### Step 4: 复盘 (10 分钟)

创建复盘笔记，例如 `drills/mock_interviews/2026-03-06_mock_01.md`:

```markdown
# Mock Interview 1 - 2026-03-06

## 题目
实现一个 API，输入 CSV URL，返回清洗后的数据

## 时间分配
- 理解需求: 3 分钟
- 设计方案: 5 分钟
- 编码: 18 分钟
- 测试: 4 分钟

## 卡壳点
1. pandas read_csv 从 URL 的语法忘了 (花了 2 分钟查文档)
2. FastAPI 返回 DataFrame 的序列化方式不确定

## 口述质量
- 前 10 分钟: 清晰
- 后 20 分钟: 有点慌，说话不流畅

## 改进点
1. 提前复习 pandas I/O API
2. 练习在压力下保持冷静
3. 测试用例应该提前想好

## 录屏文件
`mock_01_recording.mp4`
```

### Step 5: 回看录屏 (可选)

观看自己的录屏，记录:
- 哪里停顿太久
- 哪里说话不清楚
- 哪里代码写得乱

### Step 6: 记录进度

```bash
python scripts/drill_tracker.py --log mock mock_01 1 2700 True "第1场模拟，有点紧张"
```

### Step 7: 每日 Commit

```bash
git add drills/mock_interviews/
git commit -m "feat: complete Day 13 mock interviews (2 sessions)"
```

---

## Task 6: 最终复盘与总结 (Day 14 晚上)

**Files:**
- Create: `drills/final_review.md`

**Step 1: 查看统计**

```bash
python scripts/drill_tracker.py --stats
```

Expected output:
```
📊 训练统计
LeetCode 题目: 60/60
实战项目: 5/5
今日训练次数: 4
```

**Step 2: 写最终复盘**

创建 `drills/final_review.md`:

```markdown
# 2 周 Python Live Coding 训练 - 最终复盘

## 完成情况
- ✅ LeetCode Easy: 60/60 (每题 2 遍)
- ✅ 实战项目: 5/5 (每个 2 遍)
- ✅ 模拟面试: 4/4

## 最大收获
1. (填写)
2. (填写)
3. (填写)

## 仍需改进
1. (填写)
2. (填写)

## 下一步计划
- 继续每周 5 道 LeetCode Easy 保持手感
- 每周 1 场模拟面试
- 面试前 1 天复习 `python_syntax_cheatsheet.md` 和 `patterns.md`
```

**Step 3: 最终 Commit**

```bash
git add drills/final_review.md
git commit -m "docs: complete 2-week Python live coding training program"
```

---

## 附录: 关键原则

1. **零 AI 辅助** - 关闭所有智能补全
2. **手写优先** - 纸笔写伪代码再敲代码
3. **限时压力** - 第 2 遍必须限时
4. **口述练习** - 边写边说，模拟面试
5. **反馈循环** - 每次记录卡壳点
6. **质量 > 数量** - 不要速通，要深度练习
7. **每日 Commit** - 建立进度感

## 附录: 紧急救援

如果某天实在完成不了目标:
- **最低标准**: 5 道 LeetCode (而非 10 道)
- **调整策略**: 延长 1-2 天完成 Week 1
- **不要放弃**: 即使进度慢，也比不练强 100 倍

## 附录: 面试前 24 小时 Checklist

- [ ] 复习 `python_syntax_cheatsheet.md`
- [ ] 复习 `patterns.md`
- [ ] 随机抽 3 道 Easy 题，限时 30 分钟完成
- [ ] 睡个好觉

---

**Plan complete. Ready for execution.**
