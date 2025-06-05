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
        self.regions = []  # CSV에서 로드된 지역들로 설정됨
        self.region_vars = {}

        # 전체 선택 변수
        self.select_all_var = tk.BooleanVar()

        # 현재 선택된 지표
        self.current_indicator = "65세이상_평균자살률"

        # 데이터 로드 (더미 데이터 없음)
        if not self.setup_data():
            # CSV 로드 실패 시 에러 메시지 표시하고 종료
            tk.messagebox.showerror("데이터 로드 실패",
                                    "CSV 파일을 찾을 수 없거나 읽을 수 없습니다.\n"
                                    "데이터셋/통합_시도별_데이터셋.csv 파일을 확인해주세요.")
            return

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
        """실제 데이터셋에서 데이터 로드 - 더미 데이터 없음"""
        print("=== 데이터 로드 시작 ===")

        # CSV 파일 경로 확인
        csv_path = "데이터셋/통합_시도별_데이터셋.csv"
        print(f"CSV 파일 경로: {csv_path}")
        print(f"파일 존재 여부: {os.path.exists(csv_path)}")

        if not os.path.exists(csv_path):
            print("ERROR: CSV 파일이 존재하지 않습니다!")
            print("현재 디렉토리:", os.getcwd())
            if os.path.exists("데이터셋"):
                print("데이터셋 폴더 내용:", os.listdir("데이터셋"))
            else:
                print("데이터셋 폴더가 없습니다!")
            return False

        # CSV 파일 로드 시도
        df = None
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1']

        for encoding in encodings:
            try:
                print(f"{encoding} 인코딩으로 CSV 로드 시도...")
                df = pd.read_csv(csv_path, encoding=encoding)
                print(f"SUCCESS: {encoding} 인코딩으로 로드 성공!")
                print(f"데이터 크기: {len(df)} 행, {len(df.columns)} 열")
                break
            except Exception as e:
                print(f"FAILED: {encoding} 인코딩 실패 - {e}")
                continue

        if df is None:
            print("ERROR: 모든 인코딩으로 CSV 로드 실패!")
            return False

        # 컬럼명 출력
        print("\n=== CSV 컬럼명 ===")
        for i, col in enumerate(df.columns):
            print(f"{i + 1:2d}. {col}")

        # 첫 몇 행 출력
        print("\n=== 첫 3행 데이터 ===")
        print(df.head(3))

        # 시도명 컬럼 찾기
        region_col = None
        for col in df.columns:
            if '시도' in col or '지역' in col:
                region_col = col
                print(f"시도명 컬럼 찾음: {region_col}")
                break

        if region_col is None:
            region_col = df.columns[0]
            print(f"시도명 컬럼을 찾지 못해 첫 번째 컬럼 사용: {region_col}")

        # 시도명 목록 출력
        print(f"\n=== {region_col} 컬럼의 값들 ===")
        for i, region in enumerate(df[region_col]):
            print(f"{i + 1:2d}. {region}")

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

        print("\n=== 데이터 추출 시작 ===")

        # 데이터 채우기
        for _, row in df.iterrows():
            region_full = str(row[region_col]).strip()
            print(f"\n처리 중인 지역: {region_full}")

            # 시도명 정리 (특별시, 광역시, 도 등 제거)
            region_short = None
            for full, short in self.region_mapping.items():
                if region_full in full or full in region_full:
                    region_short = short
                    print(f"  매핑됨: {region_full} -> {region_short}")
                    break

            # 매핑된 지역명이 없으면 원래 이름 사용
            if region_short is None:
                # 시도명에서 '특별시', '광역시', '도' 등 제거
                region_short = region_full.replace('특별시', '').replace('광역시', '').replace('도', '').replace('특별자치시',
                                                                                                          '').replace(
                    '특별자치도', '').strip()
                print(f"  직접 매핑: {region_full} -> {region_short}")

            # 각 지표별로 데이터 추출
            for csv_col, indicator in column_mapping.items():
                for col in df.columns:
                    if csv_col.lower() in col.lower():
                        try:
                            value = float(row[col])
                            self.data[indicator][region_short] = value
                            print(f"    {indicator}: {value}")
                            break
                        except (ValueError, TypeError) as e:
                            print(f"    {indicator} 변환 실패: {e}")
                            continue

        print("\n=== 최종 데이터 확인 ===")
        for indicator, values in self.data.items():
            print(f"{indicator}: {len(values)} 지역")
            if len(values) > 0:
                print(f"  샘플: {list(values.items())[:3]}")

        # 데이터 검증 - 최소한의 지역과 지표가 있는지 확인
        total_regions = set()
        for indicator_data in self.data.values():
            total_regions.update(indicator_data.keys())

        if len(total_regions) < 5:
            print(f"ERROR: 로드된 지역이 너무 적습니다 ({len(total_regions)}개)")
            return False

        # 지역 목록 설정
        self.regions = sorted(list(total_regions))

        # 지역 체크박스 변수 설정
        for region in self.regions:
            self.region_vars[region] = tk.BooleanVar()

        # 기본 선택 지역 - 전국
        for region in self.regions:
            self.region_vars[region].set(True)
        # 전체 선택 체크박스도 선택
        self.select_all_var.set(True)

        print("=== 데이터 로드 완료 ===")
        print(f"총 {len(self.regions)}개 지역 로드됨: {self.regions}")
        return True

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
            values = []
            valid_regions = []

            for region in selected_regions:
                if region in self.data[self.current_indicator]:
                    values.append(self.data[self.current_indicator][region])
                    valid_regions.append(region)

            if not values:
                self.ax.clear()
                self.ax.text(0.5, 0.5, '선택된 지역의 데이터가 없습니다',
                             horizontalalignment='center', verticalalignment='center',
                             transform=self.ax.transAxes, fontsize=12)
                self.ax.set_xticks([])
                self.ax.set_yticks([])
            else:
                # 차트 그리기
                self.ax.clear()
                bars = self.ax.bar(valid_regions, values, color='#4285F4', alpha=0.8)

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