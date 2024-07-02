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
import urllib.parse
from folium.plugins import MarkerCluster

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# API 키 설정
OPENAI_API_KEY = st.secrets["OPENAI"]["api_key"]
GOOGLE_API_KEY = st.secrets["GOOGLE"]["api_key"]

# OpenAI 및 Google Gemini 클라이언트 설정
openai_client = OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-pro')

# 페이지 설정
st.set_page_config(page_title="도쿄 맛집 추천 서비스", layout="wide")

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

# 유틸리티 함수
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return f"data:image/png;base64,{encoded_string.decode()}"

def extract_json(text):
    match = re.search(r'\[.*\]', text, re.DOTALL)
    return match.group() if match else None

# API 호출 함수
def call_openai_api(location, menu):
    prompt = f"""tabelog.com 사이트를 기반으로 도쿄의 {location} 지역에 위치한 현재 영업 중인 {menu} 맛집을 추천해주세요. 
    별점 5점에 가까운 랭킹 1위~5위 맛집을 선정하고, 각 맛집에 대해 다음 정보를 포함해 주세요:
    - 가게 이름
    - 별점 (5점 만점)
    - 리뷰 수
    - 가게 리뷰 요약
    - 상세 정보 (특징, 추천 메뉴 등)
    - 가게 정보 (주소, 전화번호, 영업시간, 가격대)
    - 가게 웹사이트 URL (없는 경우 "https://tabelog.com/tokyo/"로 설정)
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
        "website": "https://restaurant-website.com"
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
    json_str = extract_json(response.choices[0].message.content)
    return json.loads(json_str) if json_str else None

def call_gemini_api(location, menu):
    prompt = f"""tabelog.com 사이트를 기반으로 도쿄의 {location} 지역에 위치한 현재 영업 중인 {menu} 맛집을 추천해주세요. 
    별점 5점에 가까운 랭킹 1위~5위 맛집을 선정하고, 각 맛집에 대해 다음 정보를 포함해 주세요:
    - 가게 이름
    - 별점 (5점 만점)
    - 리뷰 수
    - 가게 리뷰 요약
    - 상세 정보 (특징, 추천 메뉴 등)
    - 가게 정보 (주소, 전화번호, 영업시간, 가격대)
    - 가게 웹사이트 URL (없는 경우 "https://tabelog.com/tokyo/"로 설정)
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
        "website": "https://restaurant-website.com"
      }},
      ...
    ]
    """
    response = gemini_model.generate_content(prompt)
    json_str = extract_json(response.text)
    return json.loads(json_str) if json_str else None

def get_share_urls(restaurant_name, location, menu):
    base_url = "https://your-streamlit-app-url.com"  # 실제 앱 URL로 변경해야 함
    text = urllib.parse.quote(f"도쿄 {location}의 {menu} 맛집 '{restaurant_name}'을 추천합니다!")
    url = urllib.parse.quote(base_url)
    return {
        "instagram": f"https://www.instagram.com/"  # Instagram은 직접 공유 URL을 제공하지 않습니다
        "twitter": f"https://twitter.com/intent/tweet?text={text}&url={url}",
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={url}",
    }

# SNS 공유 관련 함수
def create_popup_content(restaurant, location, menu):
    share_urls = get_share_urls(restaurant.get('name', 'Unknown'), location, menu)
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 300px;">
        <h3 style="color: #1a1a1a; margin-bottom: 10px;">{restaurant.get('name', 'Unknown')}</h3>
        <p style="color: #4a4a4a; margin-bottom: 5px;">
            <strong>평점:</strong> {restaurant.get('rating', 'N/A')} 
            <span style="color: #ffa500;">{'★' * int(float(restaurant.get('rating', 0)))}</span>
            (리뷰 {restaurant.get('reviews', 'N/A')}개)
        </p>
        <p style="color: #4a4a4a; margin-bottom: 5px;"><strong>리뷰 요약:</strong> {restaurant.get('review_summary', 'N/A')}</p>
        <p style="color: #4a4a4a; margin-bottom: 5px;"><strong>주소:</strong> {restaurant.get('address', 'N/A')}</p>
        <p style="color: #4a4a4a; margin-bottom: 5px;"><strong>전화번호:</strong> {restaurant.get('phone', 'N/A')}</p>
        <p style="color: #4a4a4a; margin-bottom: 5px;"><strong>영업시간:</strong> {restaurant.get('hours', 'N/A')}</p>
        <p style="color: #4a4a4a; margin-bottom: 5px;"><strong>가격대:</strong> {restaurant.get('price_range', 'N/A')}</p>
        <p style="margin-bottom: 15px;">
            <a href="{restaurant.get('website', 'https://tabelog.com/tokyo/')}" target="_blank" style="color: #007bff; text-decoration: none;">로컬 사이트 방문</a>
        </p>
        <div style="text-align: center; margin-top: 15px;">
            <p style="color: #4a4a4a; margin-bottom: 10px;"><strong>SNS 공유</strong></p>
            <div style="display: flex; justify-content: center; align-items: center;">
                <a href="#" onclick="alert('Instagram에 공유하려면 이 페이지의 URL을 복사하여 Instagram 앱에서 공유해주세요.'); return false;" style="color: #C13584; text-decoration: none; margin: 0 10px;">
                    <img src="https://img.icons8.com/color/48/000000/instagram-new.png" width="40" height="40" alt="Instagram">
                
                <a href="{share_urls['twitter']}" target="_blank" style="color: #1DA1F2; text-decoration: none; margin: 0 10px;">
                    <img src="https://img.icons8.com/color/48/000000/twitter.png" width="40" height="40" alt="Twitter">
                </a>
                <a href="{share_urls['facebook']}" target="_blank" style="color: #4267B2; text-decoration: none; margin: 0 10px;">
                    <img src="https://img.icons8.com/color/48/000000/facebook-new.png" width="40" height="40" alt="Facebook">
                </a>
            </div>
        </div>
    </div>
    """

# 메인 앱 로직
def main():
    # 사이드바 배경 이미지 설정
    sidebar_bg = add_bg_from_local('sidebar_bg.jpg')
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

    # 제목과 로고 추가
    col1, col2 = st.columns([1, 4])
    with col1:
        logo = Image.open('logo.png')
        st.image(logo, width=369)

    # 앱 설명
    st.markdown('<div class="small-font">이 앱은 도쿄의 맛집을 추천해주는 서비스입니다.<br>'
                '도쿄 관광지와 메뉴를 선택한 후 \'OpenAI GPT\' 또는 \'Google Gemini\' AI 모델을 선택하여 ' 
                '맛집 추천을 받으세요.</div>', unsafe_allow_html=True)

    # 사이드바 설정
    st.sidebar.header("검색 옵션")
    location = st.sidebar.selectbox("도쿄 내 관광지 선택", list(locations.keys()), key="location_select")
    menu = st.sidebar.selectbox("도쿄 대표 메뉴 선택", list(menus.keys()), key="menu_select")
    api_choice = st.sidebar.radio("AI 모델 선택", ["OpenAI GPT", "Google Gemini"], key="api_choice_radio")

    # 검색 버튼
    if st.sidebar.button("맛집 검색", key="search_button"):
        lat, lon = latitudes[location], longitudes[location]
        m = folium.Map(location=[lat, lon], zoom_start=15)
        marker_cluster = MarkerCluster().add_to(m)

        try:
            with st.spinner('로컬 맛집 정보와 지도를 가져오는 중 입니다...'):
                recommendations = call_openai_api(location, menu) if api_choice == "OpenAI GPT" else call_gemini_api(location, menu)
            
            if recommendations:
                for restaurant in recommendations:
                    restaurant_lat = lat + random.uniform(-0.005, 0.005)
                    restaurant_lon = lon + random.uniform(-0.005, 0.005)
                    
                    popup_content = create_popup_content(restaurant, location, menu)
                    iframe = folium.IFrame(html=popup_content, width=350, height=450)
                    popup = folium.Popup(iframe, max_width=350)

                    folium.Marker(
                        [restaurant_lat, restaurant_lon],
                        popup=popup,
                        tooltip=restaurant.get('name', 'Unknown'),
                        icon=folium.Icon(color='green', icon='cutlery', prefix='fa')
                    ).add_to(marker_cluster)

                st.subheader(f"{location}의 {menu} 맛집 지도")
                folium_static(m, width=800, height=500)

            else:
                st.error("맛집 정보를 가져오는 데 실패했습니다. 다시 시도해 주세요.")
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main()

# 푸터
st.markdown("---")
st.markdown("© 2024 도쿄로컬맛집. All rights reserved.")