from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from backend.models import (
    RecommendRequest, ClassifyRequest, ClickRequest,
    RecommendResponse, ClassifyResponse, ClickResponse, HistoryResponse, HistoryListResponse,
    UserProfileResponse, ExampleUsersResponse,
    RegisterRequest, LoginRequest, AuthResponse,
    UploadNewsRequest, UploadNewsResponse,
    EventRequest, EventResponse, UserEventsResponse,
    AdminNewsListResponse, AdminNewsUpdateRequest, AdminNewsUpdateResponse,
    AdminStatsOverviewResponse, AdminStatsTrendsResponse,
    NewsDetailResponse, NewsSearchResponse,
    UserClusterResponse, AdminClusterRebuildResponse,
    ClusterGraphResponse,
)
from backend.services import RecommendationService
from backend.auth import verify_password, hash_password, create_token, get_user_from_token
from backend.db import get_connection

app = FastAPI(title="News Recommendation System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = RecommendationService()


def _get_user_from_db(username: str):
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username, password_hash, role FROM users WHERE username = %s", (username,))
            return cur.fetchone()
    finally:
        conn.close()


async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或 token 无效")
    token = authorization.replace("Bearer ", "").strip()
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return {"username": user[0], "role": user[1]}


async def get_admin(current: dict = Depends(get_current_user)):
    if current.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current


# ---------- 认证 ----------
@app.post("/api/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    existing = _get_user_from_db(req.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="数据库不可用")
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'user')",
                (req.username.strip(), hash_password(req.password)),
            )
        conn.commit()
    finally:
        conn.close()
    token = create_token(req.username, "user")
    return AuthResponse(token=token, username=req.username, role="user")


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    row = _get_user_from_db(req.username)
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(row["username"], row["role"])
    return AuthResponse(token=token, username=row["username"], role=row["role"])


# ---------- 推荐与分类（user_id 由前端传入；每次请求都按当前用户历史重新计算推荐） ----------
@app.post("/api/recommend/initial", response_model=RecommendResponse)
@app.post("/api/recommend", response_model=RecommendResponse)  # 与 initial 同一逻辑，命名更通用
async def get_recommendations(req: RecommendRequest):
    """获取推荐列表。首次加载与点击刷新均调用此接口，后端每次按当前用户历史重新计算。"""
    recommendations = service.get_initial_recommendations(req.user_id)
    return RecommendResponse(user_id=req.user_id, recommendations=recommendations)


@app.post("/api/classify", response_model=ClassifyResponse)
async def classify(req: ClassifyRequest):
    category, confidence, all_scores = service.classify_text(req.text)
    return ClassifyResponse(category=category, confidence=confidence, all_scores=all_scores)


@app.post("/api/click", response_model=ClickResponse)
async def click_news(req: ClickRequest):
    clicked_info, recommendations = service.click_news(req.user_id, req.news_id)
    return ClickResponse(clicked_news=clicked_info, recommendations=recommendations)

@app.post("/api/event", response_model=EventResponse)
async def post_event(req: EventRequest):
    saved = service.record_event(
        user_id=req.user_id,
        news_id=req.news_id,
        event_type=req.event_type,
        ts=req.ts,
        dwell_ms=req.dwell_ms,
        extra=req.extra,
    )
    return EventResponse(ok=True, saved=saved)

@app.get("/api/user/events", response_model=UserEventsResponse)
async def get_user_events(user_id: str, limit: int = 200):
    items = service.get_user_events(user_id, limit=limit)
    return UserEventsResponse(user_id=user_id, items=items)


@app.get("/api/user/history", response_model=HistoryResponse)
async def get_history(user_id: str):
    history = service.get_user_history(user_id)
    return HistoryResponse(user_id=user_id, history=history)


@app.get("/api/user/history/list", response_model=HistoryListResponse)
async def get_history_list(user_id: str):
    items = service.get_user_history_items(user_id)
    return HistoryListResponse(user_id=user_id, items=items)


@app.get("/api/user/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: str):
    profile = service.get_user_profile(user_id)
    return UserProfileResponse(**profile)

@app.delete("/api/user/profile/subcategory/{subcategory_name}")
async def delete_user_subcategory(subcategory_name: str, user_id: str, current=Depends(get_current_user)):
    service.delete_user_subcategory(current["username"], subcategory_name)
    return {"ok": True}

@app.get("/api/users/examples", response_model=ExampleUsersResponse)
async def get_example_users():
    user_ids = service.get_example_users()
    return ExampleUsersResponse(user_ids=user_ids)

# ---------- Search & explore ----------
@app.get("/api/news/categories")
async def get_news_categories():
    categories = service.get_all_categories()
    return {"categories": categories}

@app.get("/api/news/search", response_model=NewsSearchResponse)
async def search_news(q: str = "", category: str = "", subcategory: str = "", limit: int = 50):
    items = service.search_news(
        q=q.strip() or None,
        category=category.strip() or None,
        subcategory=subcategory.strip() or None,
        limit=limit,
    )
    return NewsSearchResponse(items=items)

@app.get("/api/news/{news_id}", response_model=NewsDetailResponse)
async def get_news_detail(news_id: str, user_id: str = None):
    data = service.get_news_detail(news_id, user_id=user_id)
    if not data:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return NewsDetailResponse(**data)

@app.get("/api/news/{news_id}/similar", response_model=NewsSearchResponse)
async def similar_news(news_id: str, limit: int = 12):
    items = service.similar_news(news_id, limit=limit)
    return NewsSearchResponse(items=items)

@app.get("/api/user/cluster", response_model=UserClusterResponse)
async def get_user_cluster(user_id: str):
    data = service.get_user_cluster(user_id)
    return UserClusterResponse(**data)

@app.get("/api/user/cluster/graph", response_model=ClusterGraphResponse)
async def get_user_cluster_graph(user_id: str, limit: int = 30):
    data = service.get_cluster_graph(user_id, same_cluster_limit=limit)
    return ClusterGraphResponse(**data)

@app.get("/api/user/favorites", response_model=HistoryListResponse)
async def get_user_favorites(user_id: str, limit: int = 100):
    items = service.get_user_favorites(user_id, limit=limit)
    return HistoryListResponse(user_id=user_id, items=items)


# ---------- 管理员上传新闻 ----------
@app.post("/api/admin/news", response_model=UploadNewsResponse)
async def admin_upload_news(req: UploadNewsRequest, admin=Depends(get_admin)):
    news_id = service.add_news(
        title=req.title,
        abstract=req.abstract or "",
        body=req.body or "",
        category=req.category or "N/A",
        subcategory=req.subcategory or "N/A",
    )
    return UploadNewsResponse(news_id=news_id, message="上传成功")

@app.get("/api/admin/news", response_model=AdminNewsListResponse)
async def admin_list_news(q: str = "", category: str = "", status: str = "", limit: int = 100, admin=Depends(get_admin)):
    items = service.admin_list_news(
        q=q.strip() or None,
        category=category.strip() or None,
        status=status.strip() or None,
        limit=limit,
    )
    return AdminNewsListResponse(items=items)

@app.get("/api/admin/news/flagged", response_model=AdminNewsListResponse)
async def admin_list_flagged_news(limit: int = 100, admin=Depends(get_admin)):
    items = service.admin_list_flagged_news(limit=limit)
    return AdminNewsListResponse(items=items)

@app.patch("/api/admin/news/{news_id}", response_model=AdminNewsUpdateResponse)
async def admin_update_news(news_id: str, req: AdminNewsUpdateRequest, admin=Depends(get_admin)):
    service.admin_update_news(
        news_id=news_id,
        title=req.title,
        abstract=req.abstract,
        category=req.category,
        subcategory=req.subcategory,
        status=req.status,
    )
    return AdminNewsUpdateResponse(ok=True)

@app.delete("/api/admin/news/{news_id}", response_model=AdminNewsUpdateResponse)
async def admin_delete_news(news_id: str, admin=Depends(get_admin)):
    service.admin_delete_news(news_id=news_id)
    return AdminNewsUpdateResponse(ok=True)

@app.get("/api/admin/stats/overview", response_model=AdminStatsOverviewResponse)
async def admin_stats_overview(admin=Depends(get_admin)):
    data = service.admin_stats_overview()
    return AdminStatsOverviewResponse(**data)

@app.get("/api/admin/stats/trends", response_model=AdminStatsTrendsResponse)
async def admin_stats_trends(days: int = 14, admin=Depends(get_admin)):
    points = service.admin_stats_trends(days=days)
    return AdminStatsTrendsResponse(points=points)

@app.post("/api/admin/cluster/rebuild", response_model=AdminClusterRebuildResponse)
async def admin_cluster_rebuild(k: int = 6, user_limit: int = 3000, admin=Depends(get_admin)):
    out = service.rebuild_user_clusters(k=k, user_limit=user_limit)
    return AdminClusterRebuildResponse(ok=True, users=int(out.get("users") or 0), clusters=int(out.get("clusters") or 0))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
