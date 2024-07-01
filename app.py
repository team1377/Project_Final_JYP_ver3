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
import matplotlib.pyplot as plt

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

# 새로 추가된 함수들
def call_openai_api(location, menu):
    return generate_mock_data(location, menu)

def call_gemini_api(location, menu):
    return generate_mock_data(location, menu)

def generate_mock_data(location, menu):
    return [
        {
            "name": f"{location} {menu} 맛집 {i}",
            "rating": round(random.uniform(3.5, 5.0), 1),
            "reviews": random.randint(10, 500),
            "review_summary": "맛있는 음식과 좋은 분위기",
            "address": f"{location} {i}번지",
            "phone": f"03-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "hours": "11:00-22:00",
            "price_range": f"¥{random.randint(1000, 10000)}~",
            "reason": "높은 평점과 많은 리뷰 수"
        } for i in range(1, 6)
    ]

def get_restaurants_from_db(location, menu):
    return generate_mock_data(location, menu)

def visualize_restaurant_data():
    fig, ax = plt.subplots()
    ax.bar(['A', 'B', 'C', 'D'], [random.randint(1, 10) for _ in range(4)])
    ax.set_title("레스토랑 데이터 시각화 (더미)")
    return fig

# 배경 이미지 함수
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return f"data:image/png;base64,{encoded_string.decode()}"

# 사이드바 배경 이미지 설정
sidebar_bg = add_bg_from_local('sidebar_bg.jpg')

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

# 제목과 로고 추가
col1, col2 = st.columns([1, 4])
with col1:
    logo = Image.open('logo.png')
    st.image(logo, width=369)

# 앱 설명
st.markdown('<div class="small-font">이 앱은 도쿄의 맛집을 추천해주는 서비스입니다.<br>'
            '원하는 지역과 메뉴를 선택한 후 \'OpenAI GPT\' 또는 \'Google Gemini\' AI모델을 선택하여 '
            '맛집 추천을 받으세요.</div>', unsafe_allow_html=True)

# 사이드바 설정
st.sidebar.header("검색 옵션")

# 위치 선택
locations = {
    "신주쿠": "shinjuku", "시부야": "shibuya", "긴자": "ginza",
    "롯폰기": "roppongi", "우에노": "ueno", "아사쿠사": "asakusa",
    "아키하바라": "akihabara"
}
location = st.sidebar.selectbox("도쿄 내 관광지 선택", list(locations.keys()), key="location_select")

# 메뉴 선택
menus = {
    "스시": "sushi", "라멘": "ramen", "야키토리": "yakitori",
    "텐푸라": "tempura", "우동": "udon", "소바": "soba",
    "돈카츠": "tonkatsu"
}
menu = st.sidebar.selectbox("도쿄 대표 메뉴 선택", list(menus.keys()), key="menu_select")

# API 선택
api_choice = st.sidebar.radio("AI 모델 선택", ["OpenAI GPT", "Google Gemini"], key="api_choice_radio")

# 검색 버튼
if st.sidebar.button("맛집 검색", key="search_button"):
    # 지도 표시
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
            for restaurant in recommendations:
                restaurant_lat = lat + random.uniform(-0.005, 0.005)
                restaurant_lon = lon + random.uniform(-0.005, 0.005)
                
                tooltip_content = f"""
                <div style="font-size: 14px;">
                <b>{restaurant['name']}</b><br>
                평점: {restaurant['rating']}<br>
                리뷰 수: {restaurant['reviews']}<br>
                가격대: {restaurant['price_range']}<br>
                </div>
                """

                popup_content = f"""
                <div style="font-size: 16px;">
                <b>{restaurant['name']}</b><br>
                평점: {restaurant['rating']}<br>
                리뷰 수: {restaurant['reviews']}<br>
                리뷰 요약: {restaurant['review_summary']}<br>
                주소: {restaurant['address']}<br>
                전화번호: {restaurant['phone']}<br>
                영업시간: {restaurant['hours']}<br>
                가격대: {restaurant['price_range']}<br>
                추천 이유: {restaurant['reason']}
                </div>
                """

                folium.Marker(
                    [restaurant_lat, restaurant_lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=folium.Tooltip(tooltip_content),
                    icon=folium.Icon(color='green', icon='cutlery', prefix='fa')
                ).add_to(m)

        else:
            st.error("예상치 못한 응답 형식입니다. 다시 시도해 주세요.")
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")

    # 지도 표시
    st.subheader(f"{location}의 {menu} 맛집 지도")
    folium_static(m, width=800, height=500)

    # 데이터베이스에서 레스토랑 정보 가져오기
    db_restaurants = get_restaurants_from_db(locations[location], menus[menu])
    if db_restaurants:
        st.subheader("데이터베이스에 저장된 레스토랑 정보")
        st.table(db_restaurants)

    # 데이터 시각화
    st.subheader("레스토랑 데이터 시각화")
    fig = visualize_restaurant_data()
    st.pyplot(fig)

# 데이터 업데이트 기능 (관리자용)
if st.sidebar.checkbox("관리자 모드", key="admin_mode_checkbox"):
    st.sidebar.subheader("데이터 관리")
    
    if st.sidebar.button("데이터 업데이트", key="update_data_button"):
        st.sidebar.success("데이터 업데이트가 시뮬레이션되었습니다.")
    
    # 간단한 통계 표시
    st.sidebar.subheader("간단한 통계")
    st.sidebar.write(f"등록된 지역 수: {len(locations)}")
    st.sidebar.write(f"등록된 메뉴 수: {len(menus)}")
    total_restaurants = random.randint(50, 200)  # 임의의 레스토랑 수
    st.sidebar.write(f"총 레스토랑 수: {total_restaurants}")

# 푸터
st.markdown("---")
st.markdown("© 2024 도쿄 맛집 추천 서비스. All rights reserved.")