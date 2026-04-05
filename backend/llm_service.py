# -*- coding: utf-8 -*-
"""
LLM服务封装 - 对话式推荐
使用Ollama本地部署的Qwen2.5-1.8B模型
"""

import json
import requests
from typing import Dict, List, Optional, Any
from collections import defaultdict


# Ollama配置
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:0.5b"  # 使用0.5B参数模型
MAX_HISTORY_LENGTH = 10  # 最大对话历史长度

# MIND数据集新闻类别（英文）
MIND_CATEGORIES = [
    "autos", "entertainment", "finance", "foodanddrink", "health",
    "kids", "lifestyle", "middleeast", "movies", "music",
    "news", "northamerica", "sports", "travel", "tv",
    "video", "weather"
]

# 中文到英文类别映射
CATEGORY_CN_TO_EN = {
    "汽车": "autos",
    "娱乐": "entertainment",
    "财经": "finance",
    "美食": "foodanddrink",
    "饮食": "foodanddrink",
    "健康": "health",
    "儿童": "kids",
    "生活": "lifestyle",
    "中东": "middleeast",
    "电影": "movies",
    "音乐": "music",
    "新闻": "news",
    "北美": "northamerica",
    "体育": "sports",
    "旅游": "travel",
    "电视": "tv",
    "视频": "video",
    "天气": "weather",
    "科技": "technology",  # 可能映射到news或其他
    "游戏": "entertainment",
    "教育": "lifestyle",
}


class LLMService:
    """LLM服务封装类"""
    
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.base_url = OLLAMA_BASE_URL
        # 每个用户的对话历史
        self.chat_history: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    
    def is_ollama_running(self) -> bool:
        """检查Ollama服务是否运行"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_model_available(self) -> bool:
        """检查模型是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(self.model in m.get("name", "") for m in models)
            return False
        except Exception:
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用LLM生成回答（关闭思考模式）"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 512  # 限制输出长度
                    },
                    # removed think param
                },
                timeout=60
            )
            if response.status_code == 200:
                content = response.json().get("message", {}).get("content", "")
                if not content:
                    return "生成内容为空，请确保Ollama服务正常运行。"
                import re
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
                return content.strip()
            return f"LLM请求失败({response.status_code}): {response.text[:80]}"
        except requests.exceptions.Timeout:
            return "生成超时，请稍后重试。"
        except requests.exceptions.ConnectionError:
            return "无法连接到LLM服务，请确保Ollama已启动。"
        except Exception as e:
            return f"服务错误: {str(e)[:80]}"
    
    def chat(self, user_id: str, message: str, system_prompt: Optional[str] = None) -> str:
        """带上下文的对话"""
        history = self.chat_history[user_id]
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息
        messages.extend(history[-MAX_HISTORY_LENGTH:])
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=60
            )
            if response.status_code == 200:
                reply = response.json().get("message", {}).get("content", "")
                # 保存对话历史
                self.chat_history[user_id].append({"role": "user", "content": message})
                self.chat_history[user_id].append({"role": "assistant", "content": reply})
                # 限制历史长度
                if len(self.chat_history[user_id]) > MAX_HISTORY_LENGTH * 2:
                    self.chat_history[user_id] = self.chat_history[user_id][-MAX_HISTORY_LENGTH:]
                return reply
            return f"Error: {response.status_code}"
        except requests.exceptions.Timeout:
            return "抱歉，生成超时，请稍后重试。"
        except Exception as e:
            return f"抱歉，服务暂时不可用: {str(e)}"
    
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None):
        """流式生成 - yield每个token"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True
                },
                timeout=120,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'message' in data and 'content' in data['message']:
                                content = data['message']['content']
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
            else:
                yield f"[Error: {response.status_code}]"
        except requests.exceptions.Timeout:
            yield "抱歉，生成超时，请稍后重试。"
        except Exception as e:
            yield f"抱歉，服务暂时不可用: {str(e)}"
    
    def chat_stream(self, user_id: str, message: str, system_prompt: Optional[str] = None):
        """带上下文的流式对话"""
        history = self.chat_history[user_id]
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息
        messages.extend(history[-MAX_HISTORY_LENGTH:])
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        full_reply = ""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True
                },
                timeout=120,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'message' in data and 'content' in data['message']:
                                content = data['message']['content']
                                if content:
                                    full_reply += content
                                    yield content
                        except json.JSONDecodeError:
                            continue
                
                # 保存对话历史
                self.chat_history[user_id].append({"role": "user", "content": message})
                self.chat_history[user_id].append({"role": "assistant", "content": full_reply})
                # 限制历史长度
                if len(self.chat_history[user_id]) > MAX_HISTORY_LENGTH * 2:
                    self.chat_history[user_id] = self.chat_history[user_id][-MAX_HISTORY_LENGTH:]
            else:
                yield f"[Error: {response.status_code}]"
        except requests.exceptions.Timeout:
            yield "抱歉，生成超时，请稍后重试。"
        except Exception as e:
            yield f"抱歉，服务暂时不可用: {str(e)}"
    
    def clear_history(self, user_id: str):
        """清除用户对话历史"""
        if user_id in self.chat_history:
            del self.chat_history[user_id]
    
    def parse_intent(self, user_message: str) -> Dict[str, Any]:
        """
        解析用户推荐意图（使用LLM，关闭思考模式）
        返回: {category, keywords, time_preference, intent_summary}
        """
        categories_hint = ", ".join(MIND_CATEGORIES)
        
        prompt = f"""分析用户新闻需求，返回JSON：
用户: {user_message}
可用类别: {categories_hint}

返回格式(仅JSON):
{{"category": "英文类别或null", "keywords": ["关键词"], "intent_summary": "需求总结"}}

规则: category必须是可用类别之一，体育->sports，娱乐->entertainment，财经->finance等。"""

        result = self.generate(prompt)
        
        try:
            import re
            json_match = re.search(r'\{[^{}]*\}', result)
            if json_match:
                parsed = json.loads(json_match.group())
                category = parsed.get("category")
                
                if category and category not in MIND_CATEGORIES:
                    category = CATEGORY_CN_TO_EN.get(category)
                
                return {
                    "category": category if category in MIND_CATEGORIES else None,
                    "keywords": parsed.get("keywords", []),
                    "time_preference": parsed.get("time_preference"),
                    "intent_summary": parsed.get("intent_summary", user_message)
                }
        except Exception:
            pass
        
        return {
            "category": None,
            "keywords": [],
            "time_preference": None,
            "intent_summary": user_message
        }
    
    def generate_response(self, user_intent: Dict, news_titles: List[str]) -> str:
        """生成推荐回复（使用LLM，关闭思考模式）"""
        intent_summary = user_intent.get("intent_summary", "")
        
        if not news_titles:
            prompt = f"""用户想看: {intent_summary}
但没有找到相关新闻。
请用简短友好的一句话回复，建议换个搜索词。"""
        else:
            titles_str = "\n".join([f"- {t}" for t in news_titles[:5]])
            prompt = f"""用户想看: {intent_summary}
推荐新闻:
{titles_str}

请用简短友好的一句话介绍推荐结果(不超过50字)。"""
        
        return self.generate(prompt)
    
    def generate_followup_suggestions(self, user_intent: Dict) -> List[str]:
        """生成追问建议"""
        category = user_intent.get("category", "")
        keywords = user_intent.get("keywords", [])
        
        suggestions = []
        if category:
            suggestions.append(f"有没有关于{category}的最新消息？")
        if keywords:
            suggestions.append(f"能推荐一些{keywords[0]}相关的吗？")
        else:
            suggestions.append("给我推荐一些热门新闻")
            suggestions.append("有没有体育类的新闻？")
        
        return suggestions[:3]
    
    def generate_user_profile_text(self, user_profile: Dict, recent_history: List[Dict], behavior_stats: Dict = None) -> str:
        """
        根据用户画像、历史记录和行为数据生成文字版用户画像
        
        参数:
            user_profile: 用户画像数据，包含categories, subcategories, history_count
            recent_history: 最近浏览的新闻列表，包含title, category, abstract
            behavior_stats: 用户行为统计，包含liked, favorited, disliked, not_interested
        
        返回:
            文字版用户画像描述
        """
        # 构建兴趣类别信息
        categories = user_profile.get("categories", [])
        cat_info = []
        for cat in categories[:5]:
            name = cat.get("name", "未知")
            score = cat.get("score", 0)
            if score > 0:
                cat_info.append(f"{name}({int(score * 100)}%)")
        
        # 构建最近关注的子类别
        subcategories = user_profile.get("subcategories", [])
        subcat_names = [s.get("name", "") for s in subcategories[:5] if s.get("name")]
        
        if not cat_info:
            return "您还没有足够的阅读记录，多浏览一些新闻后我们可以更好地了解您的兴趣。"
        
        # 构建最近浏览的新闻标题和摘要（最多5条）
        recent_titles = []
        recent_abstracts = []
        for item in recent_history[:5]:
            title = item.get("title", "")
            abstract = item.get("abstract", "")
            category = item.get("category", "")
            if title:
                recent_titles.append(f"《{title[:30]}》[{category}]")
            if abstract and len(abstract) > 20:
                recent_abstracts.append(abstract[:80])
        
        # 构建用户行为信息
        behavior_info = []
        if behavior_stats:
            liked = behavior_stats.get("liked", [])
            favorited = behavior_stats.get("favorited", [])
            disliked = behavior_stats.get("disliked", [])
            not_interested = behavior_stats.get("not_interested", [])
            
            if liked:
                behavior_info.append(f"点赞过的内容: {', '.join(liked[:3])}")
            if favorited:
                behavior_info.append(f"收藏过的内容: {', '.join(favorited[:3])}")
            if disliked:
                behavior_info.append(f"不感兴趣的内容: {', '.join(disliked[:2])}")
            if not_interested:
                behavior_info.append(f"标记过不喜欢的: {', '.join(not_interested[:2])}")
        
        # 构建更全面的prompt - 用于LLM分析，但不直接输出新闻标题
        prompt = f"""根据用户的阅读数据，生成一段用户阅读画像描述（60-100字）。

用户兴趣分布: {', '.join(cat_info)}
最近关注的话题: {', '.join(subcat_names[:4]) if subcat_names else '暂无'}
点赞收藏的内容类型: {'; '.join([t[:20] for t in (behavior_stats.get('liked', []) + behavior_stats.get('favorited', []))[:4]]) if behavior_stats and (behavior_stats.get('liked') or behavior_stats.get('favorited')) else '暂无'}
不感兴趣的内容类型: {'; '.join([t[:20] for t in (behavior_stats.get('disliked', []) + behavior_stats.get('not_interested', []))[:2]]) if behavior_stats and (behavior_stats.get('disliked') or behavior_stats.get('not_interested')) else '暂无'}

要求：
1. 用简洁自然的语言概括用户的兴趣领域和偏好
2. 简单告诉用户我们认为您的偏好是什么
3. 可提及用户的内容偏好特点（如偏好深度分析、娱乐资讯等）
4. 不要提及具体新闻标题、不要列举文章名
5. 不要提及用户性别、阅读数量
6. 输出纯文本，不要markdown格式
7. 只输出画像描述，不要其他内容
8. 不要输出用户兴趣分布占比"""

        result = self.generate(prompt)
        
        # 清理可能存在的markdown格式
        import re
        # 移除markdown标题
        result = re.sub(r'^#{1,6}\s*', '', result, flags=re.MULTILINE)
        # 移除markdown粗体
        result = re.sub(r'\*\*(.+?)\*\*', r'\1', result)
        result = re.sub(r'__(.+?)__', r'\1', result)
        # 移除markdown列表符号
        result = re.sub(r'^\s*[-*+]\s+', '', result, flags=re.MULTILINE)
        result = re.sub(r'^\s*\d+\.\s+', '', result, flags=re.MULTILINE)
        # 移除多余的空行
        result = re.sub(r'\n{3,}', '\n\n', result)
        # 移除开头的### 或 ##
        result = re.sub(r'^\s*#+\s*', '', result)
        result = result.strip()
        
        # 限制输出长度
        if len(result) > 400:
            result = result[:400] + "..."
        return result
    
    def generate_recommend_reason(self, news: Dict, user_profile: Dict) -> str:
        """
        根据用户画像为推荐新闻生成推荐理由
        
        参数:
            news: 新闻信息，包含title, category, abstract
            user_profile: 用户画像数据
        
        返回:
            推荐理由（简短一句话）
        """
        news_title = news.get("title", "")[:50]
        news_category = news.get("category", "综合")
        
        # 获取用户兴趣类别
        categories = user_profile.get("categories", [])
        user_interests = [cat.get("name", "") for cat in categories[:3] if cat.get("score", 0) > 0.05]
        
        # 检查新闻类别是否在用户兴趣中
        category_match = news_category in user_interests
        
        if category_match:
            prompt = f"""用户对{news_category}很感兴趣，请用简短一句话（20字以内）说明为什么推荐这条新闻：
新闻标题: {news_title}
要求：只输出推荐理由，不要引号和其他内容。例如："符合您对体育的关注" """
        else:
            prompt = f"""请用简短一句话（20字以内）说明为什么推荐这条新闻：
新闻标题: {news_title}
用户兴趣: {', '.join(user_interests) if user_interests else '综合'}
要求：只输出推荐理由，不要引号和其他内容。例如："热门推荐"或"新内容推荐" """

        result = self.generate(prompt)
        # 清理输出
        result = result.strip().strip('"').strip('"').strip()
        if len(result) > 30:
            result = result[:30]
        return result
    
    def generate_batch_reasons(self, news_list: List[Dict], user_profile: Dict) -> List[str]:
        """
        批量生成推荐理由（更高效）
        
        参数:
            news_list: 新闻列表
            user_profile: 用户画像数据
        
        返回:
            推荐理由列表
        """
        reasons = []
        for news in news_list:
            reason = self.generate_recommend_reason(news, user_profile)
            reasons.append(reason)
        return reasons
    
    def generate_enhanced_user_profile(self, user_profile: Dict, recent_history: List[Dict], behavior_stats: Dict = None) -> Dict:
        """
        生成增强版用户画像，包含画像概述、点击原因推理和潜在需求推理
        """
        import re
        
        categories = user_profile.get("categories", [])
        cat_info = []
        for cat in categories[:5]:
            name = cat.get("name", "未知")
            score = cat.get("score", 0)
            if score > 0:
                cat_info.append(f"{name}({int(score * 100)}%)")
        
        subcategories = user_profile.get("subcategories", [])
        subcat_names = [s.get("name", "") for s in subcategories[:5] if s.get("name")]
        
        if not cat_info:
            return {"summary": "您还没有足够的阅读记录，多浏览一些新闻后我们可以更好地了解您的兴趣。", "click_reasons": [], "potential_needs": []}
        
        recent_titles_with_cat = []
        for item in recent_history[:8]:
            title = item.get("title", "")
            category = item.get("category", "")
            if title:
                recent_titles_with_cat.append(f"《{title[:25]}》[{category}]")
        
        liked_titles = []
        favorited_titles = []
        if behavior_stats:
            liked_titles = [t[:25] for t in behavior_stats.get("liked", [])[:3]]
            favorited_titles = [t[:25] for t in behavior_stats.get("favorited", [])[:3]]
        
        prompt = f"""根据用户的阅读数据，分析并生成结构化的用户画像。

用户兴趣分布: {', '.join(cat_info)}
最近关注的话题: {', '.join(subcat_names[:4]) if subcat_names else '暂无'}
最近浏览的新闻: {'; '.join(recent_titles_with_cat[:5]) if recent_titles_with_cat else '暂无'}
点赞过的内容: {'; '.join(liked_titles) if liked_titles else '暂无'}
收藏过的内容: {'; '.join(favorited_titles) if favorited_titles else '暂无'}

请按以下格式输出（纯文本，不要markdown）：

【画像概述】
用30-50字概括用户的主要兴趣领域和阅读偏好

【点击原因推理】
分析用户点击某些新闻的深层原因，1-2条
格式：用户点击这篇[类别]新闻，是因为[具体原因]，而不是[表面原因]

【潜在需求推理】
基于连续行为推断用户可能的潜在需求，1-2条
格式：用户[行为描述]，可能[潜在需求]

要求：推理要有依据，语言简洁，如果数据不足以推理某项输出'数据不足'"""

        result = self.generate(prompt)
        # 清理所有markdown标记
        result = re.sub(r'^#{1,6}\s*', '', result, flags=re.MULTILINE)  # 标题#
        result = re.sub(r'\*\*(.+?)\*\*', r'\1', result)  # 加粗**
        result = re.sub(r'\*(.+?)\*', r'\1', result)  # 斜体*
        result = re.sub(r'~~(.+?)~~', r'\1', result)  # 删除线~~
        result = re.sub(r'`(.+?)`', r'\1', result)  # 行内代码`
        result = re.sub(r'^\s*[-*+]\s+', '', result, flags=re.MULTILINE)  # 列表项
        result = re.sub(r'^\s*\d+\.\s+', '', result, flags=re.MULTILINE)  # 数字列表
        result = result.strip()
        
        summary = ""
        click_reasons = []
        potential_needs = []
        
        lines = result.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 跳过可能的标题关键词行
            if any(kw in line for kw in ['画像概述', '点击原因', '潜在需求']) and len(line) < 15:
                if '画像概述' in line:
                    if current_section == 'summary' and current_content:
                        summary = ' '.join(current_content).strip()
                    current_section = 'summary'
                    current_content = []
                elif '点击原因' in line:
                    if current_section == 'summary' and current_content:
                        summary = ' '.join(current_content).strip()
                    elif current_section == 'click' and current_content:
                        click_reasons.append(' '.join(current_content).strip())
                    current_section = 'click'
                    current_content = []
                elif '潜在需求' in line:
                    if current_section == 'click' and current_content:
                        click_reasons.append(' '.join(current_content).strip())
                    current_section = 'potential'
                    current_content = []
                continue
            # 处理内容行
            if current_section and '数据不足' not in line and len(line) > 5:
                current_content.append(line)
        
        if current_section == 'potential' and current_content:
            potential_needs.append(' '.join(current_content).strip())
        elif current_section == 'summary' and current_content:
            summary = ' '.join(current_content).strip()
        
        # 限制长度
        if len(summary) > 100:
            summary = summary[:100] + "..."
        
        # 过滤无效内容
        click_reasons = [r for r in click_reasons if len(r) > 10 and '数据不足' not in r][:2]
        potential_needs = [r for r in potential_needs if len(r) > 10 and '数据不足' not in r][:2]
        
        return {
            "summary": summary or "根据您的阅读记录，您对多个领域都有所关注。",
            "click_reasons": click_reasons,
            "potential_needs": potential_needs
        }
    
    def generate_on_demand_reason(self, news: Dict, user_profile: Dict) -> str:
        """按需生成单个新闻的推荐理由"""
        news_title = news.get("title", "")[:50]
        news_category = news.get("category", "综合")
        news_abstract = news.get("abstract", "")[:100]
        
        categories = user_profile.get("categories", [])
        user_interests = [cat.get("name", "") for cat in categories[:3] if cat.get("score", 0) > 0.05]
        subcategories = user_profile.get("subcategories", [])
        user_topics = [s.get("name", "") for s in subcategories[:3] if s.get("name")]
        
        category_match = news_category in user_interests
        
        if category_match:
            prompt = f"""用户对{news_category}很感兴趣，请用简短一句话（15-25字）说明为什么推荐这条新闻：
新闻标题: {news_title}
要求：只输出推荐理由，不要引号。例如："符合您对体育赛事的关注" """
        else:
            prompt = f"""请用简短一句话（15-25字）说明为什么推荐这条新闻：
新闻标题: {news_title}
用户兴趣: {', '.join(user_interests) if user_interests else '综合'}
用户关注话题: {', '.join(user_topics[:3]) if user_topics else '暂无'}
要求：只输出推荐理由，不要引号。例如："热门推荐"或"为您推荐新内容" """

        result = self.generate(prompt)
        result = result.strip().strip('"').strip('"').strip()
        if len(result) > 35:
            result = result[:35]
        return result


# 全局LLM服务实例
llm_service = LLMService()


# 便捷函数
def get_llm_service() -> LLMService:
    """获取LLM服务实例"""
    return llm_service


def check_llm_available() -> Dict[str, Any]:
    """检查LLM服务状态"""
    service = get_llm_service()
    ollama_running = service.is_ollama_running()
    model_available = service.check_model_available() if ollama_running else False
    
    return {
        "ollama_running": ollama_running,
        "model_available": model_available,
        "model": service.model if model_available else None,
        "ready": ollama_running and model_available
    }
