"""
Structured output models for all agents.

Using Pydantic models ensures consistent, parseable output from every agent,
improving data quality for downstream aggregation by the final predictor.
"""
from pydantic import BaseModel, Field


class RecentAnalysis(BaseModel):
    """Agent 1: Recent Performance Analysis output."""
    home_momentum: str = Field(description="Home team momentum assessment: Rising / Stable / Declining")
    away_momentum: str = Field(description="Away team momentum assessment: Rising / Stable / Declining")
    home_recent_record: str = Field(description="Home team recent W-L record, e.g. '4-1'")
    away_recent_record: str = Field(description="Away team recent W-L record, e.g. '2-3'")
    home_avg_points: float = Field(description="Home team average points per game in recent games")
    away_avg_points: float = Field(description="Away team average points per game in recent games")
    key_insight: str = Field(description="One-sentence key insight about form comparison")
    advantage: str = Field(description="Which team has the edge based on recent form: home / away / even")
    summary: str = Field(description="Brief analysis report within 200 words")


class HistoryAnalysis(BaseModel):
    """Agent 2: Historical Matchup Analysis output."""
    historical_record: str = Field(description="Head-to-head record summary, e.g. 'Lakers lead 3-1 in last 4'")
    style_matchup: str = Field(description="How the teams' playing styles interact")
    key_factor: str = Field(description="The single most important factor from historical matchups")
    tactical_trend: str = Field(description="Predicted tactical trend for this game")
    advantage: str = Field(description="Which team has historical advantage: home / away / even")
    summary: str = Field(description="Professional tactical analysis report within 200 words")


class NewsAnalysis(BaseModel):
    """Agent 3: News and Injury Report output."""
    home_injuries: list[str] = Field(description="List of injured/questionable players for home team")
    away_injuries: list[str] = Field(description="List of injured/questionable players for away team")
    major_news: str = Field(description="Most impactful news item affecting this matchup")
    injury_impact: str = Field(description="How injuries shift the balance: favors_home / favors_away / neutral")
    preliminary_prediction: str = Field(description="Preliminary prediction based on news intelligence")
    summary: str = Field(description="News investigation report within 200 words")


class OddsAnalysis(BaseModel):
    """Agent 4: Odds and Market Analysis output."""
    favorite: str = Field(description="Which team is the betting favorite")
    underdog: str = Field(description="Which team is the underdog")
    spread: str = Field(description="Point spread, e.g. '-5.5'")
    spread_implication: str = Field(description="What the spread implies about expected competitiveness")
    public_trend: str = Field(description="Public betting trend if available")
    market_confidence: str = Field(description="Market confidence level: High / Medium / Low")
    summary: str = Field(description="Market analysis report within 150 words")


class StrategyAnalysis(BaseModel):
    """Agent 5: Strategy and Matchup Analysis output."""
    key_matchup: str = Field(description="Most critical player-vs-player matchup")
    home_strength: str = Field(description="Home team's biggest tactical advantage")
    away_strength: str = Field(description="Away team's biggest tactical advantage")
    bench_advantage: str = Field(description="Which team has better bench depth: home / away / even")
    tactical_recommendation: str = Field(description="Key tactical factor that will decide the game")
    summary: str = Field(description="Tactical matchup analysis report within 150 words")


class GamePrediction(BaseModel):
    """Agent 6: Final Prediction output."""
    winner: str = Field(description="Full name of the predicted winning team")
    win_probability: float = Field(description="Win probability between 0 and 100")
    score_prediction: str = Field(description="Predicted score range, e.g., '110-105'")
    confidence_level: str = Field(description="Confidence level: High / Medium / Low")
    key_factors: list[str] = Field(description="Top 3 key factors determining the outcome")
    risk_warning: str = Field(description="Biggest uncertainty factor (e.g., player absence)")
    agent_agreement: str = Field(description="How many of the 5 expert agents agree on the winner: e.g. '4/5'")
    summary: str = Field(description="Final comprehensive analysis summary within 300 words")
