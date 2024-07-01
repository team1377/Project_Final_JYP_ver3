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
locations = {
    "신주쿠": "shinjuku",
    "시부야": "shibuya",
    "긴자": "ginza",
    "롯폰기": "roppongi",
    "우에노": "ueno",
    "아사쿠사": "asakusa",
    "아키하바라": "akihabara"
}

location = st.sidebar.selectbox("도쿄 내 관광지 선택", list(locations.keys()))

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
menu = st.sidebar.selectbox("도쿄 대표 메뉴 선택", list(menus.keys()))

# API 선택
api_choice = st.sidebar.radio("AI 모델 선택", ["OpenAI GPT", "Google Gemini"])

# 기존 함수들
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

# 새로운 기능: 데이터베이스에서 레스토랑 정보 가져오기
def get_restaurants_from_db(location, menu):
    db = RestaurantDatabase('tokyo_restaurants.db')
    restaurants = db.get_restaurants_by_location_and_menu(location, menu)
    db.close()
    return restaurants

# 새로운 기능: 데이터 시각화
def visualize_restaurant_data():
    visualizer = RestaurantVisualizer('tokyo_restaurants.db')
    fig = visualizer.visualize_data()
    visualizer.close()
    return fig

# 메인 앱 로직 (이전 코드와 동일)
if st.sidebar.button("맛집 검색"):
    # 지도 표시
    latitudes = {
        "신주쿠": 35.6938,
        "시부야": 35.6580,
        "긴자": 35.6721,
        "롯폰기": 35.6628,
        "우에노": 35.7089
    }
    longitudes = {
        "신주쿠": 139.7034,
        "시부야": 139.7016,
        "긴자": 139.7666,
        "롯폰기": 139.7315,
        "우에노": 139.7741
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
if st.sidebar.checkbox("관리자 모드"):
    st.sidebar.subheader("데이터 업데이트")
    if st.sidebar.button("데이터 업데이트 실행"):
        with st.spinner("데이터 업데이트 중..."):
            try:
                # 스크래핑
                scraper = TabelogScraper()
                for location in locations.values():
                    for menu in menus.values():
                        restaurants = scraper.scrape_area(location, menu, num_pages=2)
                        scraper.save_to_json(restaurants, f'latest_{location}_{menu}_restaurants.json')

                # 데이터 통합
                integrator = RestaurantDataIntegrator()
                for location in locations.values():
                    for menu in menus.values():
                        integrator.load_data(f'latest_{location}_{menu}_restaurants.json')
                integrator.deduplicate()
                integrator.merge_data()
                integrator.save_integrated_data('integrated_tokyo_restaurants.json')

                # 데이터베이스 업데이트
                db = RestaurantDatabase('tokyo_restaurants.db')
                db.load_from_json('integrated_tokyo_restaurants.json')
                db.close()

                st.sidebar.success("데이터 업데이트가 완료되었습니다.")
            except Exception as e:
                st.sidebar.error(f"데이터 업데이트 중 오류 발생: {str(e)}")

    # 데이터베이스 통계
    st.sidebar.subheader("데이터베이스 통계")
    db = RestaurantDatabase('tokyo_restaurants.db')
    total_restaurants = db.get_total_restaurants()
    st.sidebar.write(f"총 레스토랑 수: {total_restaurants}")
    db.close()

# 메인 앱 로직
if st.sidebar.button("맛집 검색"):
    # 맛집 검색 관련 코드
    # (이 부분의 코드는 그대로 유지)
    ...
    
# 추가 기능: 전체 데이터 통계
if st.checkbox("전체 데이터 통계 보기"):
    st.subheader("도쿄 레스토랑 전체 통계")
    
    # 데이터베이스에서 통계 정보 가져오기
    db = RestaurantDatabase('tokyo_restaurants.db')
    stats = db.get_restaurant_stats()
    total_restaurants = db.get_total_restaurants()
    location_dist = db.get_location_distribution()
    menu_dist = db.get_menu_distribution()
    db.close()

    # 통계 정보 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 레스토랑 수", total_restaurants)
    with col2:
        st.metric("평균 평점", f"{stats['avg_rating']:.2f}")
    with col3:
        st.metric("평균 리뷰 수", f"{stats['avg_reviews']:.0f}")

    # 지역별 레스토랑 분포
    st.subheader("지역별 레스토랑 분포")
    fig, ax = plt.subplots()
    ax.bar(location_dist.keys(), location_dist.values())
    ax.set_xlabel("지역")
    ax.set_ylabel("레스토랑 수")
    ax.set_title("지역별 레스토랑 분포")
    st.pyplot(fig)

    # 메뉴별 레스토랑 분포
    st.subheader("메뉴별 레스토랑 분포")
    fig, ax = plt.subplots()
    ax.pie(menu_dist.values(), labels=menu_dist.keys(), autopct='%1.1f%%')
    ax.set_title("메뉴별 레스토랑 분포")
    st.pyplot(fig)

# 푸터
st.markdown("---")
st.markdown("© 2024 도쿄 맛집 추천 서비스. All rights reserved.")