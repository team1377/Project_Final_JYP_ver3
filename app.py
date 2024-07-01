import streamlit as st
import folium
from streamlit_folium import folium_static
import random
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="도쿄 맛집 추천 서비스", layout="wide")

# 제목과 로고 추가
col1, col2 = st.columns([1, 4])
with col1:
    logo = Image.open('logo.png')  # 로고 이미지 파일 경로를 지정하세요
    st.image(logo, width=369)

# 앱 설명
st.markdown('<div style="font-size: 14px;">이 앱은 도쿄의 맛집을 추천해주는 서비스입니다.<br>'
            '원하는 지역과 메뉴를 선택하여 맛집 추천을 받으세요.</div>', unsafe_allow_html=True)

# 사이드바 설정
st.sidebar.header("검색 옵션")

# 위치 선택
locations = {
    "신주쿠": "shinjuku",
    "시부야": "shibuya",
    "긴자": "ginza",
    "롯폰기": "roppongi",
    "우에노": "ueno",
    "아사쿠사": "asakusa",
    "아키하바라": "akihabara"
}
location = st.sidebar.selectbox("도쿄 내 관광지 선택", list(locations.keys()), key="location_select")

# 메뉴 선택
menus = {
    "스시": "sushi",
    "라멘": "ramen",
    "야키토리": "yakitori",
    "텐푸라": "tempura",
    "우동": "udon",
    "소바": "soba",
    "돈카츠": "tonkatsu"
}
menu = st.sidebar.selectbox("도쿄 대표 메뉴 선택", list(menus.keys()), key="menu_select")

# 맛집 정보 생성 함수
def generate_restaurant_info(location, menu):
    restaurants = [
        {
            "name": f"{location} {menu} 맛집 {i}",
            "rating": round(random.uniform(3.5, 5.0), 1),
            "reviews": random.randint(10, 500),
            "address": f"{location} {random.randint(1, 30)}-{random.randint(1, 20)}",
            "price_range": f"¥{random.randint(1000, 10000)}~¥{random.randint(11000, 30000)}",
        } for i in range(1, 6)
    ]
    return restaurants

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

    # 맛집 정보 생성 및 표시
    restaurants = generate_restaurant_info(location, menu)
    for restaurant in restaurants:
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
        주소: {restaurant['address']}<br>
        가격대: {restaurant['price_range']}<br>
        </div>
        """

        folium.Marker(
            [restaurant_lat, restaurant_lon],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=folium.Tooltip(tooltip_content),
            icon=folium.Icon(color='green', icon='cutlery', prefix='fa')
        ).add_to(m)

    # 지도 표시
    st.subheader(f"{location}의 {menu} 맛집 지도")
    folium_static(m, width=800, height=500)

    # 맛집 목록 표시
    st.subheader("추천 맛집 목록")
    for restaurant in restaurants:
        st.write(f"**{restaurant['name']}** - 평점: {restaurant['rating']}, 리뷰 수: {restaurant['reviews']}")

# 푸터
st.markdown("---")
st.markdown("© 2024 도쿄 맛집 추천 서비스. All rights reserved.")