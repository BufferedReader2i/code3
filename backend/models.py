from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Literal

# ----- 认证 -----
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class AuthResponse(BaseModel):
    token: str
    username: str
    role: str

# ----- 推荐等 -----
class RecommendRequest(BaseModel):
    user_id: str
    with_reasons: bool = False  # 是否生成推荐理由

class ClassifyRequest(BaseModel):
    text: str

class ClickRequest(BaseModel):
    user_id: str
    news_id: str

class EventRequest(BaseModel):
    user_id: str
    news_id: str
    event_type: Literal["click", "like", "unlike", "dislike", "undislike", "not_interested", "remove_not_interested", "favorite", "unfavorite", "dwell"]
    ts: Optional[int] = None  # ms timestamp; server fills if omitted
    dwell_ms: int = 0
    extra: Optional[Dict[str, Any]] = None

class EventItem(BaseModel):
    id: int
    user_id: str
    news_id: str
    event_type: str
    ts: int
    dwell_ms: int = 0
    extra: Dict[str, Any] = {}

class EventResponse(BaseModel):
    ok: bool = True
    saved: bool = True  # 是否已写入数据库（False 表示数据库不可用等）

class UserEventsResponse(BaseModel):
    user_id: str
    items: List[EventItem]

class NewsItem(BaseModel):
    id: str
    title: str
    category: str
    abstract: str
    score: Optional[float] = None
    tag: str = ""
    reason: str = ""  # LLM生成的推荐理由

class RecommendResponse(BaseModel):
    user_id: str
    recommendations: List[NewsItem]

class ClassifyResponse(BaseModel):
    category: str
    confidence: float
    all_scores: Dict[str, float]

class ClickResponse(BaseModel):
    clicked_news: Dict
    recommendations: List[NewsItem]

class HistoryResponse(BaseModel):
    user_id: str
    history: List[str]

class HistoryListResponse(BaseModel):
    user_id: str
    items: List["NewsItem"]  # 带标题等完整信息的列表


class CategoryItem(BaseModel):
    name: str
    score: float
    relative: Optional[float] = None  # 相对全局比例，>1 表示高于平均
    strength: Optional[str] = None    # strong / weak


class UserProfileResponse(BaseModel):
    user_id: str
    categories: List[CategoryItem]
    subcategories: List[CategoryItem] = []
    history_count: int


class LLMProfileResponse(BaseModel):
    """LLM生成的用户画像响应"""
    user_id: str
    llm_profile: str
    generated_at: str


class EnhancedLLMProfileResponse(BaseModel):
    """增强版LLM用户画像响应，包含推理"""
    user_id: str
    summary: str
    click_reasons: List[str] = []
    potential_needs: List[str] = []
    generated_at: str


class NewsReasonRequest(BaseModel):
    """按需生成推荐理由请求"""
    user_id: str
    news_id: str


class NewsReasonResponse(BaseModel):
    """按需生成推荐理由响应"""
    news_id: str
    title: str
    reason: str
    generated_at: str


class ExampleUsersResponse(BaseModel):
    user_ids: List[str]


class UploadNewsRequest(BaseModel):
    title: str
    abstract: str = ""
    body: str = ""
    category: str = ""
    subcategory: str = ""


class UploadNewsResponse(BaseModel):
    news_id: str
    message: str

class AdminNewsItem(BaseModel):
    news_id: str
    title: str
    category: str
    subcategory: str
    status: str = "active"
    created_at: Optional[str] = None
    abstract: str = ""
    body: str = ""

class AdminNewsListResponse(BaseModel):
    items: List[AdminNewsItem]

class AdminNewsUpdateRequest(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    status: Optional[Literal["active", "inactive"]] = None

class AdminNewsUpdateResponse(BaseModel):
    ok: bool = True

class DailyStat(BaseModel):
    date: str
    value: int


class AdminStatsOverviewResponse(BaseModel):
    dau: int
    events_24h: int
    dau_trend: List[DailyStat] = []
    events_trend: List[DailyStat] = []
    top_categories_7d: List[Dict[str, Any]]
    top_news_7d: List[Dict[str, Any]]

class AdminStatsTrendsPoint(BaseModel):
    day: str
    events: int

class AdminStatsTrendsResponse(BaseModel):
    points: List[AdminStatsTrendsPoint]

class NewsDetailResponse(BaseModel):
    news_id: str
    title: str
    abstract: str
    category: str
    subcategory: str
    url: str = ""
    entity_ids: List[str] = []
    like_count: int = 0
    user_liked: bool = False

class NewsSearchItem(BaseModel):
    news_id: str
    title: str
    abstract: str
    category: str
    subcategory: str

class NewsSearchResponse(BaseModel):
    items: List[NewsSearchItem]

class UserClusterResponse(BaseModel):
    user_id: str
    cluster_id: Optional[int] = None
    cluster_name: str = ""
    updated_at: Optional[str] = None

class AdminClusterRebuildResponse(BaseModel):
    ok: bool = True
    users: int = 0
    clusters: int = 0


class ClusterGraphNode(BaseModel):
    id: str
    name: str
    category: int  # 0=当前用户 1=兴趣群 2=同群用户


class ClusterGraphLink(BaseModel):
    source: str
    target: str


class ClusterGraphResponse(BaseModel):
    nodes: List[ClusterGraphNode]
    links: List[ClusterGraphLink]


# 解析前向引用
HistoryListResponse.model_rebuild()
