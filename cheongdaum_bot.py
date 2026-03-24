import requests
import json
import random  # 🎲 봇에게 랜덤 뽑기 능력을 부여하는 부품
from datetime import datetime
from supabase import create_client, Client

print("🤖 [청다움 봇] 시스템 가동을 시작합니다...")

# ==========================================
# 🔑 [1] 황금 열쇠 세팅 구역
# ==========================================
SUPABASE_URL = "https://imgyafnhzrketbjfpxdt.supabase.co" 
SUPABASE_KEY = "sb_publishable_mXPEUz8UITZRpC9Q8d11og_2D1WQAYU"         

NAVER_CLIENT_ID = "IfR2VKsvWWc2ZLDivsbO"
NAVER_CLIENT_SECRET = "9TFmWDXh7w"

YOUTUBE_API_KEY = "AIzaSyD5Pn7AHtK48UagHMxNssdCXGg6BWLOSk8"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 💎 [2] 대표님의 실전 키워드 보물상자
# ==========================================
KEYWORD_LIST = [
    "디저트", "앙금플라워", "떡케이크", "양갱", "산도", "고나시", "공방", 
    "개성주악", "선물포장방법", "보자기포장", "디저트트렌드", "화과자", 
    "공방 창업", "상견례선물", "결혼식답례", "어버이날선물", "다과", 
    "전통다과", "수제디저트", "전통디저트", "일본디저트", "대만디저트", 
    "홍콩디저트", "해외디저트", "유행디저트"
]

# ==========================================
# 🔎 [3] 청다움 트렌드 정보 수집 모듈
# ==========================================
def fetch_naver_news(keyword, display=3):
    print(f"   👉 [네이버 뉴스] '{keyword}' 검색 중...")
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": keyword, "display": display, "sort": "sim"}
    
    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        items = res.json().get('items', [])
        if not items: return "- 관련 최신 뉴스가 없습니다."
        
        news_list = []
        for item in items:
            title = item['title'].replace("<b>", "").replace("</b>", "").replace("&quot;", "'")
            link = item['link']
            news_list.append(f"- [{title}]({link})")
        return "\n".join(news_list)
    except Exception as e:
        print(f"   ❌ 네이버 뉴스 수집 실패: {e}")
        return "- 뉴스 데이터를 불러오지 못했습니다."

def fetch_youtube_trends(keyword, max_results=3):
    print(f"   👉 [유튜브 영상] '{keyword}' 검색 중...")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY
    }
    
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        items = res.json().get('items', [])
        if not items: return "- 관련 추천 영상이 없습니다."
        
        yt_list = []
        for item in items:
            title = item['snippet']['title'].replace("&quot;", "'").replace("&#39;", "'")
            video_id = item['id']['videoId']
            yt_list.append(f"- 📺 [{title}](https://www.youtube.com/watch?v={video_id})")
        return "\n".join(yt_list)
    except Exception as e:
        print(f"   ❌ 유튜브 수집 실패: {e}")
        return "- 유튜브 데이터를 불러오지 못했습니다."

# ==========================================
# ✍️ [4] 청다움 매거진 포장 및 송출 모듈
# ==========================================
def publish_magazine():
    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    
    # 🎲 보물상자에서 오늘의 키워드 2개를 무작위로 뽑습니다!
    today_keywords = random.sample(KEYWORD_LIST, 2)
    news_keyword = today_keywords[0]
    yt_keyword = today_keywords[1]
    
    print(f"\n📝 [청다움 라운지] {today_str} 매거진 원고 작성 중...")
    print(f"🎯 오늘의 당첨 키워드: 뉴스({news_keyword}), 유튜브({yt_keyword})")
    
    # 데이터 수집 실행
    news_data = fetch_naver_news(news_keyword)
    yt_data = fetch_youtube_trends(yt_keyword)
    
    # 매거진 제목에 오늘의 랜덤 키워드를 박아넣어 전광판에서 눈에 띄게 합니다.
    title = f"🌸 {today_str} 청다움 인사이트: [{news_keyword}] & [{yt_keyword}]"
    content = f"""
안녕하세요, 사장님! **[청다움 라운지]**입니다. 🍡
오늘도 매장에서 치열한 하루를 준비하시는 사장님을 위해, 따뜻하고 유용한 오늘의 트렌드를 전해드립니다.

### 📰 오늘의 디저트 뉴스 하이라이트 (키워드: {news_keyword})
{news_data}

### 🎥 영감을 주는 추천 영상 (키워드: {yt_keyword})
{yt_data}

---
💡 **청다움의 따뜻한 조언**
"유행은 빠르게 변하지만, 사장님이 빚어내는 디저트의 정성은 변하지 않습니다. 오늘의 정보가 사장님의 매출에 작지만 든든한 씨앗이 되길 바랍니다."
"""

    print("\n📡 [시스템] 수파베이스 서버로 전국 송출 시도 중...")
    try:
        supabase.table("magazine_db").insert({
            "제목": title,
            "내용": content.strip(),
            "작성일": datetime.now().strftime("%Y-%m-%d")
        }).execute()
        print("🎉 [송출 성공] 청다움 라운지에 새로운 매거진이 업데이트되었습니다!")
    except Exception as e:
        print(f"❌ [송출 실패] 데이터베이스 저장 중 오류 발생: {e}")

# ==========================================
# 🚀 [5] 로봇 실행 스위치
# ==========================================
if __name__ == "__main__":
    publish_magazine()
    print("\n🤖 [청다움 봇] 오늘의 트렌드 수집 및 발행 임무를 무사히 마쳤습니다!")
