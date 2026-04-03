import json
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from backend.models import (
    RecommendRequest, ClassifyRequest, ClickRequest,
    RecommendResponse, ClassifyResponse, ClickResponse, HistoryResponse, HistoryListResponse,
    UserProfileResponse, ExampleUsersResponse,
    RegisterRequest, LoginRequest, AuthResponse, ChangePasswordRequest,
    UploadNewsRequest, UploadNewsResponse,
    EventRequest, EventResponse, UserEventsResponse,
    AdminNewsListResponse, AdminNewsUpdateRequest, AdminNewsUpdateResponse,
    AdminStatsOverviewResponse, AdminStatsTrendsResponse,
    NewsDetailResponse, NewsSearchResponse,
    UserClusterResponse, AdminClusterRebuildResponse,
    ClusterGraphResponse,
    LLMProfileResponse,
)
from backend.services import RecommendationService
from backend.auth import verify_password, hash_password, create_token, get_user_from_token
from backend.db import get_connection
from backend.llm_service import get_llm_service, check_llm_available

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


@app.patch("/api/user/password")
async def change_password(req: ChangePasswordRequest, current=Depends(get_current_user)):
    username = current["username"]
    row = _get_user_from_db(username)
    if not row:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not verify_password(req.current_password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="当前密码错误")
    new_hash = hash_password(req.new_password)
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="数据库不可用")
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET password_hash = %s WHERE username = %s", (new_hash, username))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "message": "密码修改成功"}


# ---------- 推荐与分类（user_id 由前端传入；每次请求都按当前用户历史重新计算推荐） ----------
@app.post("/api/recommend/initial", response_model=RecommendResponse)
@app.post("/api/recommend", response_model=RecommendResponse)  # 与 initial 同一逻辑，命名更通用
async def get_recommendations(req: RecommendRequest):
    """获取推荐列表。首次加载与点击刷新均调用此接口，后端每次按当前用户历史重新计算。"""
    recommendations = service.get_initial_recommendations(req.user_id, with_reasons=req.with_reasons)
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


@app.get("/api/user/profile/llm", response_model=LLMProfileResponse)
async def get_llm_user_profile(user_id: str, current=Depends(get_current_user)):
    """获取LLM生成的文字版用户画像"""
    from datetime import datetime
    
    # 检查LLM服务是否可用
    llm_status = check_llm_available()
    if not llm_status.get("ready"):
        raise HTTPException(status_code=503, detail="LLM服务暂不可用")
    
    # 获取用户画像
    profile = service.get_user_profile(user_id)
    
    # 获取最近浏览历史（包含标题和摘要）
    history_items = service.get_user_history_items(user_id, limit=15)
    
    # 获取用户行为事件（点赞、收藏、不感兴趣等）
    user_events = service.get_user_events(user_id, limit=100)
    
    # 统计用户行为 - 需要取每条新闻的最新状态
    # 先按新闻ID分组，记录每条新闻的最新状态
    news_latest_state = {}  # {news_id: {"like": bool, "favorite": bool, "dislike": bool, "not_interested": bool}}
    
    # 事件是按时间倒序的，所以需要反向遍历来获取最新状态
    for event in reversed(user_events):
        event_type = event.get("event_type", "")
        news_id = event.get("news_id", "")
        
        if news_id not in news_latest_state:
            news_latest_state[news_id] = {
                "like": False,
                "favorite": False,
                "dislike": False,
                "not_interested": False
            }
        
        # 更新状态
        if event_type == "like":
            news_latest_state[news_id]["like"] = True
        elif event_type == "unlike":
            news_latest_state[news_id]["like"] = False
        elif event_type == "favorite":
            news_latest_state[news_id]["favorite"] = True
        elif event_type == "unfavorite":
            news_latest_state[news_id]["favorite"] = False
        elif event_type == "dislike":
            news_latest_state[news_id]["dislike"] = True
        elif event_type == "undislike":
            news_latest_state[news_id]["dislike"] = False
        elif event_type == "not_interested":
            news_latest_state[news_id]["not_interested"] = True
        elif event_type == "remove_not_interested":
            news_latest_state[news_id]["not_interested"] = False
    
    # 构建行为统计
    behavior_stats = {
        "liked": [],
        "favorited": [],
        "disliked": [],
        "not_interested": []
    }
    
    # 根据最新状态收集新闻标题
    for news_id, state in news_latest_state.items():
        news_info = service.news_info.get(news_id) or service.rec.news_data.get(news_id, {})
        title = news_info.get("title", news_id)
        if isinstance(title, list):
            title = " ".join(title) if title else news_id
        
        if state["like"] and len(behavior_stats["liked"]) < 5:
            behavior_stats["liked"].append(title[:50] if title else news_id)
        if state["favorite"] and len(behavior_stats["favorited"]) < 5:
            behavior_stats["favorited"].append(title[:50] if title else news_id)
        if state["dislike"] and len(behavior_stats["disliked"]) < 3:
            behavior_stats["disliked"].append(title[:50] if title else news_id)
        if state["not_interested"] and len(behavior_stats["not_interested"]) < 3:
            behavior_stats["not_interested"].append(title[:50] if title else news_id)
    
    # 调用LLM生成画像
    llm = get_llm_service()
    llm_profile = llm.generate_user_profile_text(profile, history_items, behavior_stats)
    
    return LLMProfileResponse(
        user_id=user_id,
        llm_profile=llm_profile,
        generated_at=datetime.utcnow().isoformat() + "Z"
    )


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
        body=req.body,
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


# ===================== LLM对话式推荐 API =====================

# LLM请求/响应模型
class LLMChatRequest(BaseModel):
    message: str
    user_id: str
    history: List[Dict[str, str]] = []

class LLMChatResponse(BaseModel):
    reply: str
    recommendations: List[Dict[str, Any]] = []
    parsed_intent: Dict[str, Any] = {}
    suggestions: List[str] = []

class LLMStatusResponse(BaseModel):
    ollama_running: bool
    model_available: bool
    model: Optional[str] = None
    ready: bool


@app.get("/api/llm/status", response_model=LLMStatusResponse)
async def llm_status():
    """检查LLM服务状态"""
    status = check_llm_available()
    return LLMStatusResponse(**status)


@app.post("/api/llm/chat", response_model=LLMChatResponse)
async def llm_chat(req: LLMChatRequest, current: dict = Depends(get_current_user)):
    """
    LLM对话式推荐核心接口（新增）
    1. 解析用户意图
    2. 调用推荐服务获取推荐
    3. 生成自然语言回复
    """
    llm = get_llm_service()
    user_id = current["username"]
    
    # 检查LLM服务可用性
    llm_status = check_llm_available()
    if not llm_status.get("ready"):
        return LLMChatResponse(
            reply="抱歉，LLM服务暂不可用。请确保Ollama服务已启动，并已下载 qwen2.5:1.8b 模型。",
            recommendations=[],
            parsed_intent={},
            suggestions=[]
        )
    
    # 1. 解析用户意图（新增LLM功能）
    intent = llm.parse_intent(req.message)
    
    # 2. 获取推荐结果（使用现有search_news方法）
    recommendations = []
    try:
        category = intent.get("category")
        keywords = intent.get("keywords", [])
        
        # 使用现有的search_news方法获取推荐
        search_results = service.search_news(
            q=" ".join(keywords) if keywords else None,
            category=category,
            limit=10
        )
        
        # 转换为推荐结果格式
        recommendations = [
            {
                "id": str(item.get("id", "")),
                "title": item.get("title", "")[:100] if item.get("title") else "无标题",
                "category": item.get("category", ""),
                "abstract": (item.get("abstract") or "")[:100]
            }
            for item in search_results
        ]
    except Exception as e:
        print(f"推荐服务调用失败: {e}")
    
    # 3. 生成回复（新增LLM功能）
    news_titles = [r.get("title", "") for r in recommendations]
    reply = llm.generate_response(intent, news_titles)
    
    # 4. 生成追问建议（新增LLM功能）
    suggestions = llm.generate_followup_suggestions(intent)
    
    return LLMChatResponse(
        reply=reply,
        recommendations=recommendations,
        parsed_intent=intent,
        suggestions=suggestions
    )


@app.post("/api/llm/chat/stream")
async def llm_chat_stream(req: LLMChatRequest, current: dict = Depends(get_current_user)):
    """
    LLM流式对话推荐接口
    返回SSE格式: data: {"type": "token", "content": "..."}
    """
    llm = get_llm_service()
    user_id = current["username"]
    
    # 检查LLM服务可用性
    llm_status = check_llm_available()
    if not llm_status.get("ready"):
        def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'content': 'LLM服务暂不可用'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")
    
    async def generate():
        try:
            # 1. 快速解析意图（先用LLM解析）
            intent = llm.parse_intent(req.message)
            
            # 发送意图信息
            yield f"data: {json.dumps({'type': 'intent', 'content': intent}, ensure_ascii=False)}\n\n"
            
            # 2. 获取推荐结果
            recommendations = []
            try:
                category = intent.get("category")
                keywords = intent.get("keywords", [])
                
                search_results = service.search_news(
                    q=" ".join(keywords) if keywords else None,
                    category=category,
                    limit=10
                )
                
                recommendations = [
                    {
                        "id": str(item.get("id", "")),
                        "title": item.get("title", "")[:100] if item.get("title") else "无标题",
                        "category": item.get("category", ""),
                        "abstract": (item.get("abstract") or "")[:100]
                    }
                    for item in search_results
                ]
            except Exception as e:
                print(f"推荐服务调用失败: {e}")
            
            # 发送推荐结果
            yield f"data: {json.dumps({'type': 'recommendations', 'content': recommendations}, ensure_ascii=False)}\n\n"
            
            # 3. 流式生成回复
            news_titles = [r.get("title", "") for r in recommendations]
            reply_prompt = f"""用户需求: {intent.get('intent_summary', '')}

为您推荐的新闻:
{chr(10).join(['- ' + t for t in news_titles[:10]]) if news_titles else '暂无符合条件的新闻'}

请用友好自然的语气回复用户，简要说明推荐理由。如果无新闻，建议用户换个搜索词。"""
            
            for token in llm.generate_stream(reply_prompt):
                yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/llm/chat/clear")
async def llm_clear_history(current: dict = Depends(get_current_user)):
    """清除对话历史"""
    llm = get_llm_service()
    user_id = current["username"]
    llm.clear_history(user_id)
    return {"ok": True, "message": "对话历史已清除"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
