"""
Structured output models for all agents.

Using Pydantic models ensures consistent, parseable output from every agent,
improving data quality for downstream aggregation by the final predictor.
"""
from pydantic import BaseModel, Field


class RecentAnalysis(BaseModel):
    """Agent 1: 近期表现分析输出"""
    home_momentum: str = Field(description="主队势头评估：上升 / 稳定 / 下滑")
    away_momentum: str = Field(description="客队势头评估：上升 / 稳定 / 下滑")
    home_recent_record: str = Field(description="主队近期胜负记录，如 '4胜1负'")
    away_recent_record: str = Field(description="客队近期胜负记录，如 '2胜3负'")
    home_avg_points: float = Field(description="主队近期场均得分")
    away_avg_points: float = Field(description="客队近期场均得分")
    key_insight: str = Field(description="一句话概括两队状态对比的核心发现")
    advantage: str = Field(description="基于近期表现哪队占优：主队 / 客队 / 持平")
    summary: str = Field(description="中文分析报告，200字以内")


class HistoryAnalysis(BaseModel):
    """Agent 2: 历史对战分析输出"""
    historical_record: str = Field(description="交手记录摘要，如 '湖人近4次交锋3胜1负'")
    style_matchup: str = Field(description="两队打法风格的互相影响分析")
    key_factor: str = Field(description="历史交锋中最关键的单一因素")
    tactical_trend: str = Field(description="本场比赛的战术走势预测")
    advantage: str = Field(description="历史数据中哪队占优：主队 / 客队 / 持平")
    summary: str = Field(description="中文战术分析报告，200字以内")


class NewsAnalysis(BaseModel):
    """Agent 3: 伤病新闻分析输出"""
    home_injuries: list[str] = Field(description="主队伤病/存疑球员列表")
    away_injuries: list[str] = Field(description="客队伤病/存疑球员列表")
    major_news: str = Field(description="影响本场比赛的最重要新闻")
    injury_impact: str = Field(description="伤病对天平的影响：利好主队 / 利好客队 / 中性")
    preliminary_prediction: str = Field(description="基于新闻情报的初步预判")
    summary: str = Field(description="中文新闻调查报告，200字以内")


class OddsAnalysis(BaseModel):
    """Agent 4: 赔率市场分析输出"""
    favorite: str = Field(description="博彩热门球队名称")
    underdog: str = Field(description="博彩冷门球队名称")
    spread: str = Field(description="盘口让分，如 '-5.5'")
    spread_implication: str = Field(description="盘口数据隐含的两队实力差距分析")
    public_trend: str = Field(description="公众投注趋势（如有）")
    market_confidence: str = Field(description="市场信心水平：高 / 中 / 低")
    summary: str = Field(description="中文市场分析报告，150字以内")


class StrategyAnalysis(BaseModel):
    """Agent 5: 战术对位分析输出"""
    key_matchup: str = Field(description="最关键的球员对位")
    home_strength: str = Field(description="主队最大的战术优势")
    away_strength: str = Field(description="客队最大的战术优势")
    bench_advantage: str = Field(description="哪队替补阵容更有深度：主队 / 客队 / 持平")
    tactical_recommendation: str = Field(description="决定比赛走向的关键战术因素")
    summary: str = Field(description="中文战术对位分析报告，150字以内")


class GamePrediction(BaseModel):
    """Agent 6: 最终预测输出"""
    winner: str = Field(description="预测获胜球队的全名")
    win_probability: float = Field(description="胜率，0到100之间的数字")
    score_prediction: str = Field(description="预测比分，如 '110-105'")
    confidence_level: str = Field(description="置信度：高 / 中 / 低")
    key_factors: list[str] = Field(description="决定比赛结果的3个关键因素（中文）")
    risk_warning: str = Field(description="最大的不确定性因素（如球员缺阵），用中文描述")
    agent_agreement: str = Field(description="5位专家Agent中多少个同意此预测，如 '4/5'")
    summary: str = Field(description="中文综合分析总结，300字以内")
