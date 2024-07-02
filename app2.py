import streamlit as st
import folium
from streamlit_folium import folium_static
from openai import OpenAI
import google.generativeai as genai
import json
import re
import logging
import random
from PIL import Image
from folium.plugins import MarkerCluster
import base64

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

# 제목과 로고 추가
col1, col2 = st.columns([1, 4])
with col1:
    logo = Image.open('logo.png')  # 로고 이미지 파일 경로를 지정하세요
    st.image(logo, width=369)

# 앱 설명
st.markdown('<div style="font-size: 14px;">이 앱은 도쿄의 맛집을 추천해주는 서비스입니다.<br>'
            '원하는 지역과 메뉴를 선택한 후 \'OpenAI GPT\' 또는 \'Google Gemini\' AI모델을 선택하여 '
            '맛집 추천을 받으세요.</div>', unsafe_allow_html=True)

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

# API 선택
api_choice = st.sidebar.radio("AI 모델 선택", ["OpenAI GPT", "Google Gemini"], key="api_choice_radio")

def extract_json(text):
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return match.group()
    return None

# call_openai_api와 call_gemini_api 함수 내의 프롬프트 수정
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
    - SNS 공유 URL (가상의 URL로 대체)

    반드시 5개의 맛집을 추천하고, 다음과 같은 유효한 JSON 형식으로 응답해주세요:
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
        "reason": "추천 이유",
        "share_url": "https://example.com/share/restaurant_name"
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
    - SNS 공유 URL (가상의 URL로 대체)

    반드시 5개의 맛집을 추천하고, 다음과 같은 유효한 JSON 형식으로 응답해주세요:
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
        "reason": "추천 이유",
        "share_url": "https://example.com/share/restaurant_name"
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

# SNS 공유 URL 생성 함수
def get_sns_share_urls(restaurant_name, restaurant_url):
    encoded_name = base64.b64encode(restaurant_name.encode('utf-8')).decode('utf-8')
    encoded_url = base64.b64encode(restaurant_url.encode('utf-8')).decode('utf-8')
    return {
        'twitter': f"https://twitter.com/intent/tweet?text={encoded_name}&url={encoded_url}",
        'facebook': f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}",
        'instagram': f"https://www.instagram.com/"  # Instagram은 직접 공유 URL이 없으므로 기본 페이지로 연결
    }

# 팝업 내용 생성 함수
def create_popup_content(idx, restaurant):
    share_urls = get_sns_share_urls(restaurant['name'], "http://localhost:8501")  # 로컬 서버 주소
    return f"""
    <div style="font-size: 16px; font-family: Arial, sans-serif;">
        <h3>{idx}. {restaurant['name']}</h3>
        <p><strong>평점:</strong> {restaurant['rating']} ⭐ ({restaurant['reviews']} 리뷰)</p>
        <p><strong>주소:</strong> {restaurant['address']}</p>
        <p><strong>전화번호:</strong> {restaurant['phone']}</p>
        <p><strong>영업시간:</strong> {restaurant['hours']}</p>
        <p><strong>가격대:</strong> {restaurant['price_range']}</p>
        <p><strong>추천 이유:</strong> {restaurant['reason']}</p>
        <p><strong>공유하기:</strong></p>
        <a href="{share_urls['twitter']}" target="_blank" style="margin-right: 10px;">
            <img src="https://img.icons8.com/color/48/000000/twitter.png" width="30" height="30" alt="Twitter">
        </a>
        <a href="{share_urls['facebook']}" target="_blank" style="margin-right: 10px;">
            <img src="https://img.icons8.com/color/48/000000/facebook-new.png" width="30" height="30" alt="Facebook">
        </a>
        <a href="{share_urls['instagram']}" target="_blank">
            <img src="https://img.icons8.com/color/48/000000/instagram-new.png" width="30" height="30" alt="Instagram">
        </a>
        <p><small>* SNS 공유 기능은 로컬 환경에서 제한될 수 있습니다.</small></p>
    </div>
    """

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
        with st.spinner('맛집 정보를 가져오는 중입니다...'):
            if api_choice == "OpenAI GPT":
                recommendations = call_openai_api(location, menu)
            else:
                recommendations = call_gemini_api(location, menu)
        
        if recommendations is None or len(recommendations) == 0:
            st.error("맛집 정보를 가져오는 데 실패했습니다. 다시 시도해 주세요.")
        else:
            for idx, restaurant in enumerate(recommendations, 1):
                restaurant_lat = lat + random.uniform(-0.005, 0.005)
                restaurant_lon = lon + random.uniform(-0.005, 0.005)
                
                popup_content = create_popup_content(idx, restaurant)

                folium.Marker(
                    [restaurant_lat, restaurant_lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{idx}. {restaurant['name']}",
                    icon=folium.Icon(color='green', icon='cutlery', prefix='fa')
                ).add_to(m)

            # 지도 표시
            st.subheader(f"{location}의 {menu} 맛집 지도")
            folium_static(m, width=800, height=500)

    except Exception as e:
        st.error(f"오류 발생: {str(e)}")

# 푸터
st.markdown("---")
st.markdown("© 2024 도쿄 맛집 추천 서비스. All rights reserved.")