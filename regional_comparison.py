# 지표별 지역 비교

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import tkinter.messagebox
from utils import create_styled_frame, create_styled_button
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm
import numpy as np
import geopandas as gpd
import pandas as pd
from PIL import Image, ImageTk
import threading
import os
import warnings
import traceback
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches

# 경고 메시지 숨기기
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


class RegionalComparisonPage:
    def __init__(self, parent):
        self.parent = parent
        self.setup_styles()

        # 기본 지역명 매핑 정의 (load_geodata에서 덮어쓸 수 있음)
        self.region_mapping = {
            "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
            "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
            "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
            "강원특별자치도": "강원", "강원도": "강원", "충청북도": "충북",
            "충청남도": "충남", "전북특별자치도": "전북", "전라북도": "전북",
            "전라남도": "전남", "경상북도": "경북", "경상남도": "경남",
            "제주특별자치도": "제주"
        }

        # 표시명 매핑 (UI에서 보이는 이름 -> 실제 데이터 키)
        self.indicator_display_names = {
            "자살률(10만명당)": "65세이상_평균자살률",
            "노령화지수": "평균노령화지수",
            "기초연금 수급률": "기초연금 수급률",
            "복지시설률": "복지시설률",
            "독거노인가구비율": "독거노인가구비율"
        }

        # 역매핑 (실제 데이터 키 -> UI 표시명)
        self.indicator_reverse_mapping = {v: k for k, v in self.indicator_display_names.items()}

        # 지역 체크박스 변수들을 먼저 정의
        self.regions = ["강원", "경기", "경남", "경북", "광주", "대구", "대전", "부산",
                        "서울", "세종", "울산", "인천", "전남", "전북", "제주", "충남", "충북"]
        self.region_vars = {}
        for region in self.regions:
            self.region_vars[region] = tk.BooleanVar()

        # 전체 선택 변수
        self.select_all_var = tk.BooleanVar()

        # 기본 선택 지역
        # 기본 선택 지역 - 전국
        for region in self.regions:
            self.region_vars[region].set(True)
        # 전체 선택 체크박스도 선택
        self.select_all_var.set(True)

        # 현재 선택된 지표
        self.current_indicator = "65세이상_평균자살률"

        self.setup_data()
        self.load_geodata()
        self.create_interface()

    def setup_styles(self):
        self.title_font = tkFont.Font(family="맑은 고딕", size=16, weight="bold")
        self.subtitle_font = tkFont.Font(family="맑은 고딕", size=14, weight="bold")
        self.label_font = tkFont.Font(family="맑은 고딕", size=11)
        self.checkbox_font = tkFont.Font(family="맑은 고딕", size=10)
        self.button_font = tkFont.Font(family="맑은 고딕", size=11, weight="bold")

    def load_geodata(self):
        """지도 데이터 로드 - 여러 인코딩 시도"""
        encodings_to_try = ['utf-8', 'euc-kr', 'cp949', 'latin1']

        for encoding in encodings_to_try:
            try:
                print(f"인코딩 {encoding}으로 시도 중...")
                self.gdf = gpd.read_file("데이터셋/경계데이터/bnd_sido_00_2024_2Q.shp", encoding=encoding)
                print(f"지도 데이터 로드 성공 (인코딩: {encoding})")
                print("컬럼:", self.gdf.columns.tolist())

                # 지역명 컬럼 찾기
                possible_columns = ['SIDO_NM', 'CTP_KOR_NM', 'NAME', 'SIDONM']
                self.지역컬럼 = None

                for col in possible_columns:
                    if col in self.gdf.columns:
                        self.지역컬럼 = col
                        break

                if self.지역컬럼 is None:
                    # 첫 번째 문자열 컬럼을 사용
                    for col in self.gdf.columns:
                        if self.gdf[col].dtype == 'object':
                            self.지역컬럼 = col
                            break

                print(f"사용할 지역 컬럼: {self.지역컬럼}")
                if self.지역컬럼:
                    print("지역명들:", self.gdf[self.지역컬럼].tolist()[:5])

                # 지역명이 제대로 읽혔는지 확인
                if self.지역컬럼 and len(self.gdf[self.지역컬럼].iloc[0]) > 0:
                    first_region = self.gdf[self.지역컬럼].iloc[0]
                    if any(ord(char) > 127 for char in first_region if char.isalpha()):
                        print(f"한글 지역명 확인됨: {first_region}")
                        break
                    else:
                        print(f"지역명이 깨져 보임: {first_region}")
                        continue
                else:
                    continue

            except Exception as e:
                print(f"인코딩 {encoding} 실패: {e}")
                continue

        # 모든 인코딩이 실패한 경우
        if not hasattr(self, 'gdf') or self.gdf is None:
            print("모든 인코딩 시도 실패. SIDO_CD 컬럼을 사용하여 매핑합니다.")
            try:
                self.gdf = gpd.read_file("데이터셋/경계데이터/bnd_sido_00_2024_2Q.shp")
                self.지역컬럼 = 'SIDO_CD'
                self.use_code_mapping = True
            except Exception as e:
                print(f"최종 로드 실패: {e}")
                self.gdf = None
                self.지역컬럼 = None
                return
        else:
            self.use_code_mapping = False

        # 지역명 매핑 설정 - 더 포괄적으로 수정
        if self.use_code_mapping:
            self.region_mapping = {
                '11': '서울',
                '26': '부산',
                '27': '대구',
                '28': '인천',
                '29': '광주',
                '30': '대전',
                '31': '울산',
                '36': '세종',
                '41': '경기',
                '42': '강원',
                '43': '충북',
                '44': '충남',
                '45': '전북',
                '46': '전남',
                '47': '경북',
                '48': '경남',
                '50': '제주'
            }
        else:
            # 더 포괄적인 매핑 추가
            self.region_mapping = {
                "서울특별시": "서울",
                "서울시": "서울",
                "서울": "서울",
                "부산광역시": "부산",
                "부산시": "부산",
                "부산": "부산",
                "대구광역시": "대구",
                "대구시": "대구",
                "대구": "대구",
                "인천광역시": "인천",
                "인천시": "인천",
                "인천": "인천",
                "광주광역시": "광주",
                "광주시": "광주",
                "광주": "광주",
                "대전광역시": "대전",
                "대전시": "대전",
                "대전": "대전",
                "울산광역시": "울산",
                "울산시": "울산",
                "울산": "울산",
                "세종특별자치시": "세종",
                "세종시": "세종",
                "세종": "세종",
                "경기도": "경기",
                "경기": "경기",
                "강원특별자치도": "강원",
                "강원도": "강원",
                "강원": "강원",
                "충청북도": "충북",
                "충북": "충북",
                "충청남도": "충남",
                "충남": "충남",
                "전북특별자치도": "전북",
                "전라북도": "전북",
                "전북": "전북",
                "전라남도": "전남",
                "전남": "전남",
                "경상북도": "경북",
                "경북": "경북",
                "경상남도": "경남",
                "경남": "경남",
                "제주특별자치도": "제주",
                "제주도": "제주",
                "제주": "제주"
            }

        # 역매핑 생성
        self.reverse_mapping = {v: k for k, v in self.region_mapping.items()}
        print("지도 데이터 로드 완료")

    def setup_data(self):
        """실제 데이터셋에서 데이터 로드"""
        try:
            # 여러 인코딩 시도
            encodings = ['utf-8', 'cp949', 'euc-kr']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv("데이터셋/통합_시도별_데이터셋.csv", encoding=encoding)
                    print(f"{encoding} 인코딩으로 데이터 로드 성공")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"데이터 로드 오류: {e}")
                    continue

            if df is None:
                raise Exception("모든 인코딩으로 데이터 로드 실패")

            # 컬럼명 확인 및 정리
            print("원본 컬럼명:", df.columns.tolist())

            # 시도명 컬럼 찾기
            region_col = None
            for col in df.columns:
                if '시도' in col or '지역' in col:
                    region_col = col
                    break

            if region_col is None:
                region_col = df.columns[0]  # 첫 번째 컬럼을 시도명으로 가정

            print(f"시도명 컬럼으로 '{region_col}' 사용")

            # 데이터 사전 초기화
            self.data = {
                "65세이상_평균자살률": {},
                "평균노령화지수": {},
                "기초연금 수급률": {},
                "복지시설률": {},
                "독거노인가구비율": {}
            }

            # 컬럼 매핑 (CSV 컬럼명과 앱에서 사용하는 지표명 매핑)
            column_mapping = {
                '65세이상_평균자살률': '65세이상_평균자살률',
                '평균노령화지수': '평균노령화지수',
                '수급률': '기초연금 수급률',
                '복지시설률': '복지시설률',
                '독거노인가구비율': '독거노인가구비율'
            }

            # 데이터 채우기
            for _, row in df.iterrows():
                region = row[region_col].strip()

                # 시도명 정리 (특별시, 광역시, 도 등 제거)
                region_short = None
                for full, short in self.region_mapping.items():
                    if region in full or full in region:
                        region_short = short
                        break

                # 매핑된 지역명이 없으면 원래 이름 사용
                if region_short is None:
                    # 시도명에서 '특별시', '광역시', '도' 등 제거
                    region_short = region.replace('특별시', '').replace('광역시', '').replace('도', '').replace('특별자치시',
                                                                                                         '').replace(
                        '특별자치도', '').strip()
                    print(f"매핑되지 않은 지역명: {region} -> {region_short}")

                # 각 지표별로 데이터 추출
                for csv_col, indicator in column_mapping.items():
                    for col in df.columns:
                        if csv_col.lower() in col.lower():
                            try:
                                value = float(row[col])
                                self.data[indicator][region_short] = value
                                break
                            except (ValueError, TypeError):
                                continue

            # 데이터 확인
            print("로드된 데이터:")
            for indicator, values in self.data.items():
                print(f"{indicator}: {len(values)} 지역")
                if len(values) > 0:
                    print(f"  샘플: {list(values.items())[:3]}")

            # 누락된 데이터가 있는지 확인하고 더미 데이터로 채우기
            for indicator in self.data:
                for region in self.regions:
                    if region not in self.data[indicator]:
                        if indicator == "복지시설률":
                            self.data[indicator][region] = 5.0
                        elif indicator == "65세이상_평균자살률":
                            self.data[indicator][region] = 50.0
                        elif indicator == "평균노령화지수":
                            self.data[indicator][region] = 400.0
                        elif indicator == "기초연금 수급률":
                            self.data[indicator][region] = 65.0
                        else:  # 독거노인가구비율
                            self.data[indicator][region] = 10.0

        except Exception as e:
            print(f"데이터 로드 중 오류 발생: {e}")
            print(f"오류 상세: {traceback.format_exc()}")

            # 오류 발생 시 더미 데이터 사용
            print("더미 데이터로 대체합니다.")

            # 더미 데이터 - 정확한 값으로 수정
            self.data = {
                "65세이상_평균자살률": {
                    "강원": 67.2, "경기": 49.0, "경남": 46.0, "경북": 43.6, "광주": 53.6,
                    "대구": 39.9, "대전": 56.6, "부산": 48.0, "서울": 45.3, "세종": 48.8,
                    "울산": 43.4, "인천": 46.5, "전남": 42.9, "전북": 42.7, "제주": 41.9,
                    "충남": 72.2, "충북": 56.4
                },
                "평균노령화지수": {
                    "강원": 641.6, "경기": 256.3, "경남": 852.5, "경북": 949.1, "광주": 295.5,
                    "대구": 402.9, "대전": 259.2, "부산": 404.1, "서울": 253.2, "세종": 288.1,
                    "울산": 259.6, "인천": 326.9, "전남": 795.8, "전북": 751.4, "제주": 778.4,
                    "충남": 829.6, "충북": 214.3
                },
                "기초연금 수급률": {
                    "강원": 67.5, "경기": 61.08, "경남": 71.66, "경북": 73.68, "광주": 65.33,
                    "대구": 69.59, "대전": 63.87, "부산": 70.74, "서울": 53.94, "세종": 53.15,
                    "울산": 63.96, "인천": 70.54, "전남": 71.05, "전북": 73.15, "제주": 69.5,
                    "충남": 77.48, "충북": 60.24
                },
                "복지시설률": {
                    "강원": 8.71, "경기": 9.48, "경남": 3.75, "경북": 6.74, "광주": 4.2,
                    "대구": 5.38, "대전": 5.76, "부산": 1.58, "서울": 2.75, "세종": 4.56,
                    "울산": 2.96, "인천": 9.19, "전남": 7.54, "전북": 5.79, "제주": 5.63,
                    "충남": 6.74, "충북": 8.5
                },
                "독거노인가구비율": {
                    "강원": 13.1, "경기": 7.4, "경남": 12.0, "경북": 13.6, "광주": 8.9,
                    "대구": 10.6, "대전": 8.3, "부산": 11.9, "서울": 8.1, "세종": 4.9,
                    "울산": 8.1, "인천": 9.3, "전남": 11.1, "전북": 13.5, "제주": 8.5,
                    "충남": 15.5, "충북": 11.0
                }
            }

    def create_interface(self):
        # 메인 컨테이너
        main_container = tk.Frame(self.parent, bg='#E3F2FD')
        main_container.pack(fill='both', expand=True)

        # 콘텐츠 영역
        content_frame = tk.Frame(main_container, bg='#E3F2FD')
        content_frame.pack(fill='both', expand=True, padx=40, pady=(40, 40))

        # 왼쪽 패널 - 지역 선택
        left_panel = self.create_region_panel(content_frame)
        left_panel.pack(side='left', fill='y', padx=(0, 20))

        # 오른쪽 패널 - 시각화 (지도 + 차트)
        right_panel = tk.Frame(content_frame, bg='#E3F2FD')
        right_panel.pack(side='right', fill='both', expand=True)

        # 지도 패널 (위쪽)
        map_panel = self.create_map_panel(right_panel)
        map_panel.pack(fill='both', expand=True, pady=(0, 20))

        # 차트 패널 (아래쪽)
        chart_panel = self.create_chart_panel(right_panel)
        chart_panel.pack(fill='both', expand=True)

    def create_region_panel(self, parent):
        # 지역 선택 패널
        panel_frame = tk.Frame(
            parent,
            bg='white',
            relief='solid',
            bd=1,
            width=280,
            height=500
        )
        panel_frame.pack_propagate(False)

        # 패널 제목
        title_label = tk.Label(
            panel_frame,
            text="지역 선택",
            font=self.subtitle_font,
            bg='white',
            fg='#333333'
        )
        title_label.pack(pady=(20, 10))

        # 전체 선택 체크박스
        select_all_frame = tk.Frame(panel_frame, bg='white')
        select_all_frame.pack(fill='x', padx=15, pady=(0, 5))

        select_all_checkbox = tk.Checkbutton(
            select_all_frame,
            text="전체 선택",
            variable=self.select_all_var,
            font=self.checkbox_font,
            bg='white',
            command=self.toggle_all_regions
        )
        select_all_checkbox.pack(side='left')

        # 구분선
        separator = ttk.Separator(panel_frame, orient='horizontal')
        separator.pack(fill='x', padx=15, pady=5)

        # 체크박스 컨테이너
        checkbox_container = tk.Frame(panel_frame, bg='white')
        checkbox_container.pack(fill='both', expand=True, padx=15, pady=(0, 10))

        # 체크박스들을 3열로 배치
        for i, region in enumerate(self.regions):
            row = i // 3
            col = i % 3

            checkbox = tk.Checkbutton(
                checkbox_container,
                text=region,
                variable=self.region_vars[region],
                font=self.checkbox_font,
                bg='white',
                command=self.update_select_all_state
            )
            checkbox.grid(row=row, column=col, sticky='w', padx=8, pady=2)

            # 그리드 열 가중치 설정
            checkbox_container.grid_columnconfigure(col, weight=1)

        # 비교하기 버튼
        compare_button = tk.Button(
            panel_frame,
            text="비교하기",
            font=self.button_font,
            bg='#1976D2',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.update_visualizations
        )
        compare_button.pack(pady=(10, 20))

        return panel_frame

    def toggle_all_regions(self):
        """전체 선택/해제 토글"""
        is_checked = self.select_all_var.get()
        for region in self.regions:
            self.region_vars[region].set(is_checked)

    def update_select_all_state(self):
        """개별 지역 선택 상태에 따라 전체 선택 체크박스 상태 업데이트"""
        all_selected = all(self.region_vars[region].get() for region in self.regions)
        self.select_all_var.set(all_selected)

    def create_chart_panel(self, parent):
        # 차트 패널
        panel_frame = tk.Frame(parent, bg='#E3F2FD')

        # 차트 영역
        chart_frame = tk.Frame(
            panel_frame,
            bg='white',
            relief='solid',
            bd=1,
            width=500,
            height=240
        )
        chart_frame.pack()
        chart_frame.pack_propagate(False)

        # matplotlib 차트 생성
        self.create_chart(chart_frame)

        # 지표 선택 드롭다운
        indicator_frame = tk.Frame(panel_frame, bg='#E3F2FD')
        indicator_frame.pack(pady=(15, 0))

        tk.Label(
            indicator_frame,
            text="지표 선택:",
            font=self.label_font,
            bg='#E3F2FD',
            fg='#333333'
        ).pack(side='left', padx=(0, 10))

        self.indicator_var = tk.StringVar(value=self.indicator_reverse_mapping[self.current_indicator])
        indicator_combo = ttk.Combobox(
            indicator_frame,
            textvariable=self.indicator_var,
            values=list(self.indicator_display_names.keys()),  # 표시명 사용
            state="readonly",
            width=15,
            font=self.label_font
        )
        indicator_combo.pack(side='left')
        indicator_combo.bind('<<ComboboxSelected>>', self.on_indicator_change)

        return panel_frame

    def create_map_panel(self, parent):
        # 지도 패널
        panel_frame = tk.Frame(parent, bg='#E3F2FD')

        # 지도 영역
        map_frame = tk.Frame(
            panel_frame,
            bg='white',
            relief='solid',
            bd=1,
            width=500,
            height=260
        )
        map_frame.pack()
        map_frame.pack_propagate(False)

        # 지도 생성
        self.create_map(map_frame)

        return panel_frame

    def create_chart(self, parent):
        # matplotlib figure 생성
        self.fig, self.ax = plt.subplots(figsize=(5, 2))
        self.fig.patch.set_facecolor('white')

        # 초기 차트 그리기
        self.update_chart()

        # tkinter에 차트 임베드
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

    def create_map(self, parent):
        # 지도 컨테이너
        map_container = tk.Frame(parent, bg='white')
        map_container.pack(expand=True, fill='both', padx=10, pady=10)

        # 로딩 라벨
        self.map_loading_label = tk.Label(
            map_container,
            text="지도 로딩 중...",
            font=self.label_font,
            bg='white',
            fg='#666666'
        )
        self.map_loading_label.pack(expand=True)

        # 지도 이미지 라벨 (초기에는 숨김)
        self.map_label = tk.Label(map_container, bg='white')

        # 초기 지도 생성
        self.update_map()

    def update_chart(self):
        # 선택된 지역들 가져오기
        selected_regions = [region for region, var in self.region_vars.items() if var.get()]

        if not selected_regions:
            # 선택된 지역이 없으면 빈 차트
            self.ax.clear()
            self.ax.text(0.5, 0.5, '지역을 선택해주세요',
                         horizontalalignment='center', verticalalignment='center',
                         transform=self.ax.transAxes, fontsize=12)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
        else:
            # 차트 데이터 준비
            values = [self.data[self.current_indicator][region] for region in selected_regions]

            # 차트 그리기
            self.ax.clear()
            bars = self.ax.bar(selected_regions, values, color='#4285F4', alpha=0.8)

            # 차트 스타일링
            self.ax.set_ylabel(self.indicator_reverse_mapping[self.current_indicator], fontsize=10)
            self.ax.tick_params(axis='x', rotation=45, labelsize=9)
            self.ax.tick_params(axis='y', labelsize=9)

            # Y축 포맷팅
            if self.current_indicator == "복지시설률":
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
            elif self.current_indicator == "독거노인가구비율":
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}'))
            else:
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}'))

            # 막대 위에 값 표시
            for bar, value in zip(bars, values):
                height = bar.get_height()
                if self.current_indicator == "평균노령화지수":
                    label = f'{value:.1f}'
                elif self.current_indicator == "복지시설률":
                    label = f'{value:.2f}'
                else:
                    label = f'{value:.1f}'

                self.ax.text(bar.get_x() + bar.get_width() / 2., height + max(values) * 0.01,
                             label, ha='center', va='bottom', fontsize=8)

            # 여백 조정
            self.ax.set_ylim(0, max(values) * 1.15 if values else 1)
            plt.tight_layout()

        # 차트 업데이트
        if hasattr(self, 'canvas'):
            self.canvas.draw()

    def update_map(self):
        """지표별 색상 지도 업데이트 - 선택된 지역만 색상 표시"""
        if self.gdf is None or self.지역컬럼 is None:
            self.map_loading_label.config(text="지도 데이터를 찾을 수 없습니다")
            return

        self.map_loading_label.config(text="지도 생성 중...")
        print(f"지도 업데이트 시작 - 현재 지표: {self.current_indicator}")

        def generate_map():
            try:
                print("지도 생성 함수 시작")

                # 선택된 지역들 가져오기
                selected_regions = [region for region, var in self.region_vars.items() if var.get()]
                print(f"선택된 지역들: {selected_regions}")

                # 지도 데이터 복사
                gdf_copy = self.gdf.copy()
                print(f"GeoDataFrame 복사 완료, 행 수: {len(gdf_copy)}")

                # 현재 지표의 데이터 가져오기
                indicator_data = self.data[self.current_indicator]

                # 지도 데이터에 지표 값 매핑 (선택된 지역만)
                gdf_copy['indicator_value'] = np.nan
                gdf_copy['is_selected'] = False

                # 매핑 성공 카운터
                mapping_success = 0

                # 모든 지역에 대해 매핑 시도 (선택 여부와 관계없이)
                for idx, row in gdf_copy.iterrows():
                    region_name = None

                    if self.use_code_mapping:
                        region_code = str(row[self.지역컬럼])
                        region_name = self.region_mapping.get(region_code)
                        print(f"코드 매핑: {region_code} -> {region_name}")
                    else:
                        region_full_name = str(row[self.지역컬럼])
                        print(f"지역명 매핑 시도: {region_full_name}")

                        # 직접 매핑 시도
                        if region_full_name in self.region_mapping:
                            region_name = self.region_mapping[region_full_name]
                        else:
                            # 부분 매칭 시도
                            for full_name, short_name in self.region_mapping.items():
                                if full_name in region_full_name or region_full_name in full_name:
                                    region_name = short_name
                                    break

                        print(f"매핑 결과: {region_full_name} -> {region_name}")

                    # 매핑된 지역이 있으면 데이터 설정 (선택 여부와 관계없이)
                    if region_name:
                        # 선택된 지역인지 확인
                        is_selected = region_name in selected_regions
                        gdf_copy.at[idx, 'is_selected'] = is_selected

                        # 데이터 값 설정 (선택 여부와 관계없이)
                        if region_name in indicator_data:
                            gdf_copy.at[idx, 'indicator_value'] = indicator_data[region_name]
                            mapping_success += 1
                            print(f"매핑 성공: {region_name} = {indicator_data[region_name]}")

                print(f"총 {mapping_success}개 지역 매핑 성공")

                # 모든 지역의 값들 가져오기 (선택 여부와 관계없이)
                all_values = gdf_copy['indicator_value'].dropna()

                if len(all_values) > 0:
                    vmin, vmax = all_values.min(), all_values.max()
                    print(f"값 범위: {vmin} ~ {vmax}")

                    # 지도 생성
                    fig, ax = plt.subplots(figsize=(5, 4))

                    # 색상 맵 설정
                    if self.current_indicator == "65세이상_평균자살률":
                        cmap = plt.cm.Reds
                    elif self.current_indicator == "복지시설률":
                        cmap = plt.cm.Blues
                    elif self.current_indicator == "독거노인가구비율":
                        cmap = plt.cm.Greens
                    elif self.current_indicator == "기초연금 수급률":
                        cmap = plt.cm.Oranges
                    else:  # 평균노령화지수
                        cmap = plt.cm.Purples

                    # 먼저 모든 지역을 회색으로 그리기
                    gdf_copy.plot(ax=ax, color='#f0f0f0', edgecolor='black', linewidth=0.5)

                    # 선택된 지역만 색상으로 그리기
                    selected_gdf = gdf_copy[gdf_copy['is_selected'] == True]
                    if len(selected_gdf) > 0:
                        selected_gdf.plot(ax=ax, column='indicator_value', cmap=cmap,
                                          legend=True, edgecolor='black', linewidth=0.5,
                                          vmin=vmin, vmax=vmax)

                    ax.axis('off')
                    ax.set_title(self.indicator_reverse_mapping[self.current_indicator], fontsize=12)

                    # 컬러바 조정
                    if len(selected_gdf) > 0:
                        cbar = ax.get_figure().get_axes()[-1]
                        if self.current_indicator == "평균노령화지수":
                            cbar.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}'))
                        elif self.current_indicator == "복지시설률":
                            cbar.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
                        else:
                            cbar.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}'))
                else:
                    # 선택된 지역이 없는 경우
                    fig, ax = plt.subplots(figsize=(5, 4))
                    gdf_copy.plot(ax=ax, color='#f0f0f0', edgecolor='black', linewidth=0.5)
                    ax.axis('off')

                print("matplotlib 지도 생성 완료")

                # 임시 파일로 저장
                map_filename = f"temp_choropleth_map_{self.current_indicator.replace(' ', '_')}.png"
                print(f"지도를 {map_filename}에 저장 중...")
                plt.savefig(map_filename, bbox_inches="tight", dpi=100, facecolor='white')
                plt.close()
                print("지도 파일 저장 완료")

                # 이미지 로드 및 UI 업데이트
                print("이미지 로드 시작")
                img = Image.open(map_filename)
                img = img.resize((300, 250), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                print("이미지 로드 완료")

                def update_ui():
                    print("UI 업데이트 시작")
                    self.map_loading_label.pack_forget()
                    self.map_label.config(image=tk_img)
                    self.map_label.image = tk_img  # 참조 유지
                    self.map_label.pack(expand=True)
                    print("UI 업데이트 완료")

                self.parent.after(0, update_ui)

                # 임시 파일 삭제
                try:
                    os.remove(map_filename)
                    print("임시 파일 삭제 완료")
                except:
                    print("임시 파일 삭제 실패")
                    pass

            except Exception as e:
                print(f"지도 생성 오류: {e}")
                print(f"오류 상세: {traceback.format_exc()}")

                def show_error():
                    self.map_loading_label.config(text=f"지도 생성 실패: {str(e)}")

                self.parent.after(0, show_error)

        # 백그라운드 스레드에서 지도 생성
        threading.Thread(target=generate_map, daemon=True).start()

    def update_visualizations(self):
        """비교하기 버튼 클릭 시 차트와 지도를 모두 업데이트"""
        self.update_chart()
        self.update_map()

    def on_indicator_change(self, event):
        """지표 변경 시 비교하기 버튼을 눌러야 업데이트되도록 메시지 표시"""
        display_name = self.indicator_var.get()
        self.current_indicator = self.indicator_display_names[display_name]  # 실제 키로 변환
        tk.messagebox.showinfo("지표 변경", "지표가 변경되었습니다. '비교하기' 버튼을 눌러 시각화를 업데이트하세요.")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True)
    app = RegionalComparisonPage(frame)
    root.mainloop()
