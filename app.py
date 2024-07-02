import streamlit as st
import folium
from streamlit_folium import folium_static
from openai import OpenAI
import google.generativeai as genai
import json
import re
import logging
import random
import base64
from PIL import Image

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# Streamlit secrets에서 OpenAI API 키 가져오기
OPENAI_API_KEY = st.secrets["OPENAI"]["api_key"]
GOOGLE_API_KEY = st.secrets["GOOGLE"]["api_key"]

# OpenAI 클라이언트 설정
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Google Gemini 설정
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-pro')

# 페이지 설정
st.set_page_config(page_title="도쿄 맛집 추천 서비스", layout="wide")

# 배경 이미지 함수
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return f"data:image/png;base64,{encoded_string.decode()}"

# 사이드바 배경 이미지 설정
sidebar_bg = add_bg_from_local('sidebar_bg.jpg')  # 이미지 경로를 실제 경로로 변경하세요

# 사이드바 배경 이미지 및 스타일 적용
st.markdown(
    f"""
    <style>
    [data-testid="stSidebar"] > div:first-child {{
        background-image: url("{sidebar_bg}");
        background-position: center;
        background-repeat: no-repeat;
        background-size: cover;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(0,0,0,0);
    }}
    [data-testid="stSidebar"] > div:first-child > div:first-child {{
        background-color: rgba(255, 255, 255, 0.1);
    }}
    .small-font {{
        font-size: 14px !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# 위치와 메뉴 데이터 정의
locations = {
    "신주쿠": "shinjuku", "시부야": "shibuya", "긴자": "ginza",
    "롯폰기": "roppongi", "우에노": "ueno", "아사쿠사": "asakusa",
    "아키하바라": "akihabara"
}

menus = {
    "스시": "sushi", "라멘": "ramen", "야키토리": "yakitori",
    "텐푸라": "tempura", "우동": "udon", "소바": "soba",
    "돈카츠": "tonkatsu"
}

latitudes = {
    "신주쿠": 35.6938, "시부야": 35.6580, "긴자": 35.6721,
    "롯폰기": 35.6628, "우에노": 35.7089, "아사쿠사": 35.7147,
    "아키하바라": 35.7022
}

longitudes = {
    "신주쿠": 139.7034, "시부야": 139.7016, "긴자": 139.7666,
    "롯폰기": 139.7315, "우에노": 139.7741, "아사쿠사": 139.7967,
    "아키하바라": 139.7741
}

def extract_json(text):
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return match.group()
    return None

def call_openai_api(location, menu):
    prompt = f"""tabelog.com 사이트를 기반으로 도쿄의 {location} 지역에 위치한 현재 영업 중인 {menu} 맛집을 추천해주세요. 
    별점 5점에 가까운 랭킹 1위~5위 맛집을 선정하고, 각 맛집에 대해 다음 정보를 포함해 주세요:
    - 가게 이름
    - 별점 (5점 만점)
    - 리뷰 수
    - 가게 리뷰 요약
    - 상세 정보 (특징, 추천 메뉴 등)
    - 가게 정보 (주소, 전화번호, 영업시간, 가격대)
    - 추천 이유
 
    반드시 다음과 같은 유효한 JSON 형식으로 응답해주세요:
    [
      {{
        "name": "레스토랑 이름",
        "rating": 4.5,
        "reviews": 100,
        "review_summary": "리뷰 요약",
        "details": "상세 정보",
        "address": "주소",
        "phone": "전화번호",
        "hours": "영업시간",
        "price_range": "가격대",
        "reason": "추천 이유"
      }},
      ...
    ]
    """

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 도쿄 레스토랑 추천 전문가입니다."},
            {"role": "user", "content": prompt}
        ]
    )
    
    logging.info(f"OpenAI API 원본 응답: {response.choices[0].message.content}")
    
    json_str = extract_json(response.choices[0].message.content)
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"JSON 파싱 오류: {str(e)}")
            return None
    else:
        logging.error("응답에서 JSON을 찾을 수 없습니다.")
        return None

def call_gemini_api(location, menu):
    prompt = f"""tabelog.com 사이트를 기반으로 도쿄의 {location} 지역에 위치한 현재 영업 중인 {menu} 맛집을 추천해주세요. 
    별점 5점에 가까운 랭킹 1위~5위 맛집을 선정하고, 각 맛집에 대해 다음 정보를 포함해 주세요:
    - 가게 이름
    - 별점 (5점 만점)
    - 리뷰 수
    - 가게 리뷰 요약
    - 상세 정보 (특징, 추천 메뉴 등)
    - 가게 정보 (주소, 전화번호, 영업시간, 가격대)
    - 추천 이유
    
    반드시 다음과 같은 유효한 JSON 형식으로 응답해주세요:
    [
      {{
        "name": "레스토랑 이름",
        "rating": 4.5,
        "reviews": 100,
        "review_summary": "리뷰 요약",
        "details": "상세 정보",
        "address": "주소",
        "phone": "전화번호",
        "hours": "영업시간",
        "price_range": "가격대",
        "reason": "추천 이유"
      }},
      ...
    ]
    """

    response = gemini_model.generate_content(prompt)
    
    logging.info(f"Gemini API 원본 응답: {response.text}")
    
    json_str = extract_json(response.text)
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"JSON 파싱 오류: {str(e)}")
            return None
    else:
        logging.error("응답에서 JSON을 찾을 수 없습니다.")
        return None

# SNS 공유 버튼을 위한 HTML 추가
def add_sns_buttons():
    st.markdown("""
    <div class="sns-share">
        <a href="https://www.facebook.com/sharer/sharer.php?u=" target="_blank" class="facebook" id="facebook-share">
            <i class="fab fa-facebook-f"></i>
        </a>
        <a href="https://twitter.com/intent/tweet?url=" target="_blank" class="twitter" id="twitter-share">
            <i class="fab fa-twitter"></i>
        </a>
        <a href="https://www.instagram.com/" target="_blank" class="instagram" id="instagram-share">
            <i class="fab fa-instagram"></i>
        </a>
    </div>
    """, unsafe_allow_html=True)

# 제목과 로고 추가
col1, col2 = st.columns([1, 4])
with col1:
    logo = Image.open('logo.png')  # 로고 이미지 파일 경로를 지정하세요
    st.image(logo, width=369)

# 앱 설명 (메인 영역으로 이동, 작은 폰트로 설정)
st.markdown('<div class="small-font">  이 앱은 도쿄의 맛집을 추천해주는 서비스입니다.<br> '
            '  원하는 지역과 메뉴를 선택한 후 \'OpenAI GPT\' 또는 \'Google Gemini\' AI모델을 선택하여 '
            '  맛집 추천을 받으세요.</div>', unsafe_allow_html=True)

# 사이드바 설정
st.sidebar.header("검색 옵션")

# 위치 선택
location = st.sidebar.selectbox("도쿄 내 관광지 선택", list(locations.keys()), key="location_select")

# 메뉴 선택
menu = st.sidebar.selectbox("도쿄 대표 메뉴 선택", list(menus.keys()), key="menu_select")

# API 선택
api_choice = st.sidebar.radio("AI 모델 선택", ["OpenAI GPT", "Google Gemini"], key="api_choice_radio")

# 검색 버튼
if st.sidebar.button("맛집 검색", key="search_button"):
    lat, lon = latitudes[location], longitudes[location]

    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat, lon], popup=location, icon=folium.Icon(color='red', icon='info-sign')).add_to(m)

    # API 호출 및 결과 표시
    try:
        with st.spinner('로컬 맛집 정보와 지도를 가져오는 중 입니다...'):
            if api_choice == "OpenAI GPT":
                recommendations = call_openai_api(location, menu)
            else:
                recommendations = call_gemini_api(location, menu)
        
        if recommendations is None:
            st.error("맛집 정보를 가져오는 데 실패했습니다. 다시 시도해 주세요.")
        elif isinstance(recommendations, list):
            for idx, restaurant in enumerate(recommendations):
                restaurant_lat = lat + random.uniform(-0.005, 0.005)
                restaurant_lon = lon + random.uniform(-0.005, 0.005)
                
                tooltip_content = f"""
                <div style="font-size: 14px;">
                <b>{restaurant.get('name', 'Unknown')}</b><br>
                평점: {restaurant.get('rating', 'N/A')}<br>
                리뷰 수: {restaurant.get('reviews', 'N/A')}<br>
                가격대: {restaurant.get('price_range', 'N/A')}<br>
                </div>
                """

                popup_content = f"""
                <div style="font-size: 16px;">
                <b>{restaurant.get('name', 'Unknown')}</b><br>
                평점: {restaurant.get('rating', 'N/A')}<br>
                리뷰 수: {restaurant.get('reviews', 'N/A')}<br>
                리뷰 요약: {restaurant.get('review_summary', 'N/A')}<br>
                주소: {restaurant.get('address', 'N/A')}<br>
                전화번호: {restaurant.get('phone', 'N/A')}<br>
                영업시간: {restaurant.get('hours', 'N/A')}<br>
                가격대: {restaurant.get('price_range', 'N/A')}<br>
                추천 이유: {restaurant.get('reason', 'N/A')}
                </div>
                """

                folium.Marker(
                    [restaurant_lat, restaurant_lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=folium.Tooltip(tooltip_content),
                    icon=folium.Icon(color='green', icon='cutlery', prefix='fa')
                ).add_to(m)

            st.subheader(f"{location}의 {menu} 맛집 지도")
            folium_static(m, width=800, height=500)

            # 맛집 정보 표시
            for idx, restaurant in enumerate(recommendations):
                with st.expander(f"{restaurant.get('name', 'Unknown')}", key=f"restaurant_{idx}"):
                    st.write(f"평점: {restaurant.get('rating', 'N/A')}")
                    st.write(f"리뷰 수: {restaurant.get('reviews', 'N/A')}")
                    st.write(f"리뷰 요약: {restaurant.get('review_summary', 'N/A')}")
                    st.write(f"주소: {restaurant.get('address', 'N/A')}")
                    st.write(f"전화번호: {restaurant.get('phone', 'N/A')}")
                    st.write(f"영업시간: {restaurant.get('hours', 'N/A')}")
                    st.write(f"가격대: {restaurant.get('price_range', 'N/A')}")
                    st.write(f"추천 이유: {restaurant.get('reason', 'N/A')}")

            # SNS 공유 버튼 추가
            add_sns_buttons()

        else:
            st.error("예상치 못한 응답 형식입니다. 다시 시도해 주세요.")
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")

# CSS 스타일 추가
st.markdown("""
<style>
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css');
    
    body {
        font-family: 'Noto Sans JP', sans-serif;
        background-color: #f0f2f6;
    }
    
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    h1 {
        color: #333;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .sns-share {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    
    .sns-share a {
        margin: 0 10px;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        text-decoration: none;
        transition: all 0.3s ease;
    }
    
    .sns-share a:hover {
        transform: scale(1.1);
    }
    
    .facebook { background-color: #3b5998; }
    .twitter { background-color: #1da1f2; }
    .instagram { background-color: #e1306c; }
    
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        transition-duration: 0.4s;
        cursor: pointer;
        border-radius: 5px;
    }
    
    .stButton>button:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)

# JavaScript 추가
st.markdown("""
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
<script>
    $(document).ready(function() {
        $('.sns-share a').click(function(e) {
            e.preventDefault();
            var url = $(this).attr('href');
            var shareUrl = encodeURIComponent(window.location.href);
            var title = encodeURIComponent(document.title);
            
            if (url.includes('facebook')) {
                url += shareUrl;
            } else if (url.includes('twitter')) {
                url += 'text=' + title + '&url=' + shareUrl;
            } else if (url.includes('instagram')) {
                alert('Instagram sharing is not supported. Please copy the link manually.');
                return;
            }
            
            window.open(url, '_blank', 'width=600,height=400');
        });
    });
</script>
""", unsafe_allow_html=True)

# 푸터
st.markdown("---")
st.markdown("© 2024 도쿄 맛집 추천 서비스. All rights reserved.")