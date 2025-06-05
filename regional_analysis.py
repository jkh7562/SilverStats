# 지역 심층 분석

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import tkinter.messagebox
from utils import create_styled_frame, create_styled_button
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import geopandas as gpd
import pandas as pd
from PIL import Image, ImageTk
import threading
import os
import warnings
import traceback
from matplotlib.patches import Polygon
import matplotlib.patches as patches

# 경고 메시지 숨기기
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


class RegionalAnalysisPage:
    def __init__(self, parent):
        self.parent = parent
        self.setup_styles()

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
        self.data_font = tkFont.Font(family="맑은 고딕", size=24, weight="bold")
        self.unit_font = tkFont.Font(family="맑은 고딕", size=10)

    def load_geodata(self):
        """지도 데이터 로드 - 실패 시 더미 지도 생성"""
        self.gdf = None
        self.지역컬럼 = None
        self.use_code_mapping = False

        # 실제 지도 파일 로드 시도
        try:
            encodings_to_try = ['utf-8', 'euc-kr', 'cp949', 'latin1']

            for encoding in encodings_to_try:
                try:
                    print(f"인코딩 {encoding}으로 시도 중...")
                    self.gdf = gpd.read_file("데이터셋/경계데이터/bnd_sido_00_2024_2Q.shp", encoding=encoding)
                    print(f"지도 데이터 로드 성공 (인코딩: {encoding})")

                    # 지역명 컬럼 찾기
                    possible_columns = ['SIDO_NM', 'CTP_KOR_NM', 'NAME', 'SIDONM']
                    for col in possible_columns:
                        if col in self.gdf.columns:
                            self.지역컬럼 = col
                            break

                    if self.지역컬럼:
                        print(f"지역 컬럼 찾음: {self.지역컬럼}")
                        break

                except Exception as e:
                    print(f"인코딩 {encoding} 실패: {e}")
                    continue

        except Exception as e:
            print(f"지도 파일 로드 실패: {e}")

        # 지도 파일 로드 실패 시 더미 지도 데이터 생성
        if self.gdf is None:
            print("더미 지도 데이터 생성")
            self.create_dummy_map_data()

        # 지역명 매핑 설정
        self.region_mapping = {
            "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
            "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
            "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
            "강원특별자치도": "강원", "강원도": "강원", "충청북도": "충북",
            "충청남도": "충남", "전북특별자치도": "전북", "전라북도": "전북",
            "전라남도": "전남", "경상북도": "경북", "경상남도": "경남",
            "제주특별자치도": "제주"
        }

        # 역매핑 생성
        self.reverse_mapping = {v: k for k, v in self.region_mapping.items()}
        print("지도 데이터 준비 완료")

    def create_dummy_map_data(self):
        """더미 지도 데이터 생성 - 간단한 도형으로 각 지역 표현"""
        print("더미 지도 데이터 생성 중...")

        # 간단한 지역별 좌표 정의 (대략적인 위치)
        self.dummy_regions = {
            "서울": {"x": 0.5, "y": 0.7, "size": 0.08},
            "인천": {"x": 0.4, "y": 0.7, "size": 0.06},
            "경기": {"x": 0.5, "y": 0.6, "size": 0.12},
            "강원": {"x": 0.7, "y": 0.6, "size": 0.1},
            "충북": {"x": 0.5, "y": 0.5, "size": 0.08},
            "충남": {"x": 0.4, "y": 0.5, "size": 0.08},
            "대전": {"x": 0.45, "y": 0.45, "size": 0.05},
            "세종": {"x": 0.48, "y": 0.48, "size": 0.04},
            "전북": {"x": 0.35, "y": 0.4, "size": 0.08},
            "전남": {"x": 0.3, "y": 0.3, "size": 0.1},
            "광주": {"x": 0.32, "y": 0.35, "size": 0.05},
            "경북": {"x": 0.65, "y": 0.45, "size": 0.1},
            "대구": {"x": 0.6, "y": 0.4, "size": 0.06},
            "경남": {"x": 0.55, "y": 0.3, "size": 0.1},
            "부산": {"x": 0.65, "y": 0.25, "size": 0.06},
            "울산": {"x": 0.7, "y": 0.3, "size": 0.05},
            "제주": {"x": 0.3, "y": 0.1, "size": 0.06}
        }

        self.use_dummy_map = True
        print("더미 지도 데이터 생성 완료")

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

        # 데이터 추출
        self.data = {}

        # 지역명 매핑
        region_mapping = {
            "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
            "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
            "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
            "강원특별자치도": "강원", "강원도": "강원", "충청북도": "충북",
            "충청남도": "충남", "전북특별자치도": "전북", "전라북도": "전북",
            "전라남도": "전남", "경상북도": "경북", "경상남도": "경남",
            "제주특별자치도": "제주"
        }

        print("\n=== 데이터 추출 시작 ===")

        # 필수 지표들
        required_indicators = ["자살률(10만명당)", "기초연금 수급률", "독거노인가구비율", "복지시설률", "노령화지수"]

        for _, row in df.iterrows():
            region_full = str(row[region_col]).strip()
            print(f"\n처리 중인 지역: {region_full}")

            # 지역명 매핑
            region_short = None
            for full, short in region_mapping.items():
                if region_full in full or full in region_full:
                    region_short = short
                    print(f"  매핑됨: {region_full} -> {region_short}")
                    break

            if region_short is None:
                # 직접 매핑이 안되면 문자열 정리
                region_short = region_full.replace('특별시', '').replace('광역시', '').replace('도', '').replace('특별자치시',
                                                                                                          '').replace(
                    '특별자치도', '').strip()
                print(f"  직접 매핑: {region_full} -> {region_short}")

            # 지역 데이터 초기화
            if region_short not in self.data:
                self.data[region_short] = {}

            # 각 지표별 데이터 추출
            for col in df.columns:
                col_lower = col.lower()

                if '65세이상' in col and '자살' in col:
                    try:
                        value = float(row[col])
                        self.data[region_short]["자살률(10만명당)"] = value
                        print(f"    자살률: {value}")
                    except Exception as e:
                        print(f"    자살률 변환 실패: {e}")

                elif '수급률' in col:
                    try:
                        value = float(row[col])
                        self.data[region_short]["기초연금 수급률"] = value
                        print(f"    수급률: {value}")
                    except Exception as e:
                        print(f"    수급률 변환 실패: {e}")

                elif '독거노인' in col and '가구' in col:
                    try:
                        value = float(row[col])
                        self.data[region_short]["독거노인가구비율"] = value
                        print(f"    독거노인가구비율: {value}")
                    except Exception as e:
                        print(f"    독거노인가구비율 변환 실패: {e}")

                elif '복지시설' in col:
                    try:
                        value = float(row[col])
                        self.data[region_short]["복지시설률"] = value
                        print(f"    복지시설률: {value}")
                    except Exception as e:
                        print(f"    복지시설률 변환 실패: {e}")

                elif '노령화' in col and '지수' in col:
                    try:
                        value = float(row[col])
                        self.data[region_short]["노령화지수"] = value
                        print(f"    노령화지수: {value}")
                    except Exception as e:
                        print(f"    노령화지수 변환 실패: {e}")

        print("\n=== 최종 데이터 확인 ===")
        for region, data in self.data.items():
            print(f"{region}: {data}")

        # 데이터 검증 - 모든 지역이 모든 지표를 가지고 있는지 확인
        missing_data = []
        for region, data in self.data.items():
            for indicator in required_indicators:
                if indicator not in data:
                    missing_data.append(f"{region}의 {indicator}")

        if missing_data:
            print(f"\n경고: 누락된 데이터가 있습니다:")
            for missing in missing_data:
                print(f"  - {missing}")
            print("누락된 데이터가 있어 애플리케이션이 제대로 작동하지 않을 수 있습니다.")
            return False

        # 최소한의 지역이 있는지 확인
        if len(self.data) < 5:
            print(f"ERROR: 로드된 지역이 너무 적습니다 ({len(self.data)}개)")
            return False

        self.regions = sorted(list(self.data.keys()))
        self.current_region = self.regions[0]

        # 지표 이름과 단위
        self.indicators = {
            "자살률(10만명당)": "명",
            "기초연금 수급률": "%",
            "독거노인가구비율": "%",
            "복지시설률": "%",
            "노령화지수": ""
        }

        print("=== 데이터 로드 완료 ===")
        print(f"총 {len(self.regions)}개 지역 로드됨: {self.regions}")
        return True

    def create_interface(self):
        # 메인 컨테이너
        main_container = tk.Frame(self.parent, bg='#E3F2FD')
        main_container.pack(fill='both', expand=True)

        # 제목
        title_label = tk.Label(
            main_container,
            text="지역 심층 분석",
            font=self.title_font,
            bg='#E3F2FD',
            fg='#333333'
        )
        title_label.pack(pady=(20, 30))

        # 콘텐츠 영역
        content_frame = tk.Frame(main_container, bg='#E3F2FD')
        content_frame.pack(fill='both', expand=True, padx=40, pady=(0, 40))

        # 왼쪽 패널
        left_panel = tk.Frame(content_frame, bg='#E3F2FD')
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 20))

        # 오른쪽 패널
        right_panel = tk.Frame(content_frame, bg='#E3F2FD')
        right_panel.pack(side='right', fill='both', expand=True)

        # 왼쪽 패널 구성
        self.create_left_panel(left_panel)

        # 오른쪽 패널 구성
        self.create_right_panel(right_panel)

    def create_left_panel(self, parent):
        # 지역 선택 패널
        region_panel = tk.Frame(
            parent,
            bg='white',
            relief='solid',
            bd=1,
            width=400,
            height=150
        )
        region_panel.pack(fill='x', pady=(0, 20))
        region_panel.pack_propagate(False)

        # 지역 제목
        region_title = tk.Label(
            region_panel,
            text="지역",
            font=self.subtitle_font,
            bg='white',
            fg='#333333'
        )
        region_title.pack(pady=(20, 10))

        # 지역 선택 드롭다운
        self.region_var = tk.StringVar(value=self.current_region)
        region_combo = ttk.Combobox(
            region_panel,
            textvariable=self.region_var,
            values=self.regions,
            state="readonly",
            width=20,
            font=self.label_font
        )
        region_combo.pack(pady=(0, 20))
        region_combo.bind('<<ComboboxSelected>>', self.on_region_change)

        # 지도 패널
        map_panel = tk.Frame(
            parent,
            bg='white',
            relief='solid',
            bd=1,
            width=400,
            height=350
        )
        map_panel.pack(fill='both', expand=True)
        map_panel.pack_propagate(False)

        # 지도 생성
        self.create_map(map_panel)

    def create_right_panel(self, parent):
        # 레이더 차트 패널
        radar_panel = tk.Frame(
            parent,
            bg='white',
            relief='solid',
            bd=1,
            width=450,
            height=300
        )
        radar_panel.pack(fill='x', pady=(0, 20))
        radar_panel.pack_propagate(False)

        # 레이더 차트 생성
        self.create_radar_chart(radar_panel)

        # 데이터 표시 패널
        data_panel = tk.Frame(
            parent,
            bg='white',
            relief='solid',
            bd=1,
            width=450,
            height=200
        )
        data_panel.pack(fill='both', expand=True)
        data_panel.pack_propagate(False)

        # 데이터 표시 생성
        self.create_data_display(data_panel)

    def create_map(self, parent):
        # 지도 컨테이너
        map_container = tk.Frame(parent, bg='white')
        map_container.pack(expand=True, fill='both', padx=10, pady=10)

        # matplotlib 지도 생성 (즉시 생성)
        self.map_fig, self.map_ax = plt.subplots(figsize=(4, 5))
        self.map_fig.patch.set_facecolor('white')

        # tkinter에 지도 임베드
        self.map_canvas = FigureCanvasTkAgg(self.map_fig, map_container)
        self.map_canvas.get_tk_widget().pack(fill='both', expand=True)

        # 초기 지도 생성
        self.update_map()

    def update_map(self):
        """지도 업데이트 - 무조건 지도 표시"""
        print(f"지도 업데이트 시작 - 현재 지역: {self.current_region}")

        self.map_ax.clear()

        if hasattr(self, 'use_dummy_map') and self.use_dummy_map:
            # 더미 지도 생성
            print("더미 지도 생성")

            # 배경 설정
            self.map_ax.set_xlim(0, 1)
            self.map_ax.set_ylim(0, 1)
            self.map_ax.set_aspect('equal')

            # 각 지역을 원으로 표시
            for region, coords in self.dummy_regions.items():
                if region == self.current_region:
                    color = 'red'
                    alpha = 0.8
                else:
                    color = 'lightblue'
                    alpha = 0.6

                # 원 그리기
                circle = patches.Circle((coords["x"], coords["y"]), coords["size"],
                                        color=color, alpha=alpha, edgecolor='black', linewidth=1)
                self.map_ax.add_patch(circle)

                # 지역명 표시
                self.map_ax.text(coords["x"], coords["y"], region,
                                 ha='center', va='center', fontsize=8, fontweight='bold')

            self.map_ax.set_title(f"선택 지역: {self.current_region}", fontsize=12, pad=10)

        elif self.gdf is not None and self.지역컬럼 is not None:
            # 실제 지도 데이터 사용
            print("실제 지도 데이터 사용")

            try:
                # 지도 데이터 복사
                gdf_copy = self.gdf.copy()

                # 색상 설정
                gdf_copy["color"] = "lightblue"  # 기본 색상
                for idx, row in gdf_copy.iterrows():
                    region_name = str(row[self.지역컬럼])
                    for full_name, short_name in self.region_mapping.items():
                        if full_name in region_name or short_name in region_name:
                            if short_name == self.current_region:
                                gdf_copy.at[idx, "color"] = "red"
                                break

                # 지도 그리기
                gdf_copy.plot(ax=self.map_ax, color=gdf_copy["color"], edgecolor="black", linewidth=0.5)
                self.map_ax.set_title(f"선택 지역: {self.current_region}", fontsize=12, pad=10)

            except Exception as e:
                print(f"실제 지도 그리기 실패: {e}")
                # 실패 시 더미 지도로 대체
                self.use_dummy_map = True
                self.update_map()
                return
        else:
            # 최후의 수단: 텍스트 지도
            print("텍스트 지도 생성")
            self.map_ax.text(0.5, 0.5, f"선택된 지역:\n{self.current_region}",
                             ha='center', va='center', fontsize=16, fontweight='bold',
                             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
            self.map_ax.set_xlim(0, 1)
            self.map_ax.set_ylim(0, 1)

        self.map_ax.axis('off')

        # 지도 업데이트
        self.map_canvas.draw()
        print("지도 업데이트 완료")

    def create_radar_chart(self, parent):
        # matplotlib 레이더 차트
        self.radar_fig, self.radar_ax = plt.subplots(figsize=(4, 3), subplot_kw=dict(projection='polar'))
        self.radar_fig.patch.set_facecolor('white')

        # tkinter에 차트 임베드 (먼저 캔버스 생성)
        self.radar_canvas = FigureCanvasTkAgg(self.radar_fig, parent)
        self.radar_canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

        # 그 다음 차트 업데이트 (순서 중요!)
        self.update_radar_chart()

    def update_radar_chart(self):
        self.radar_ax.clear()

        # 현재 지역 데이터
        region_data = self.data[self.current_region]

        # 지표들과 값들
        indicators = list(self.indicators.keys())
        values = []

        # 값들을 0-1 범위로 정규화
        for indicator in indicators:
            value = region_data[indicator]
            if indicator == "자살률(10만명당)":
                normalized = value / 80.0  # 최대 80으로 가정
            elif indicator == "기초연금 수급률":
                normalized = value / 100.0  # 최대 100%
            elif indicator == "독거노인가구비율":
                normalized = value / 20.0  # 최대 20%로 가정
            elif indicator == "복지시설률":
                normalized = value / 15.0  # 최대 15%로 가정
            elif indicator == "노령화지수":
                normalized = value / 1000.0  # 최대 1000으로 가정

            values.append(min(normalized, 1.0))  # 1.0을 넘지 않도록

        # 각도 계산
        angles = np.linspace(0, 2 * np.pi, len(indicators), endpoint=False).tolist()
        values += values[:1]  # 닫힌 도형을 만들기 위해
        angles += angles[:1]

        # 레이더 차트 그리기
        self.radar_ax.plot(angles, values, 'o-', linewidth=2, color='purple', alpha=0.8)
        self.radar_ax.fill(angles, values, alpha=0.3, color='purple')

        # 축 레이블 설정
        self.radar_ax.set_xticks(angles[:-1])
        self.radar_ax.set_xticklabels(indicators, fontsize=8)
        self.radar_ax.set_ylim(0, 1)
        self.radar_ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        self.radar_ax.set_yticklabels([])
        self.radar_ax.grid(True)

        # 차트 업데이트
        self.radar_canvas.draw()

    def create_data_display(self, parent):
        # 데이터 표시 컨테이너
        self.data_container = tk.Frame(parent, bg='white')
        self.data_container.pack(expand=True, fill='both', padx=20, pady=20)

        # 초기 데이터 표시
        self.update_data_display()

    def update_data_display(self):
        # 기존 위젯들 제거
        for widget in self.data_container.winfo_children():
            widget.destroy()

        # 현재 지역 데이터
        region_data = self.data[self.current_region]

        # 데이터 표시
        indicators = list(self.indicators.keys())

        # 첫 번째 줄 (3개 지표)
        row1_frame = tk.Frame(self.data_container, bg='white')
        row1_frame.pack(expand=True, fill='x', pady=(0, 10))

        # 두 번째 줄 (2개 지표)
        row2_frame = tk.Frame(self.data_container, bg='white')
        row2_frame.pack(expand=True, fill='x')

        # 첫 번째 줄에 3개 지표 표시
        for i in range(min(3, len(indicators))):
            indicator = indicators[i]
            col_frame = tk.Frame(row1_frame, bg='white')
            col_frame.pack(side='left', expand=True, fill='both', padx=10)

            # 지표명
            indicator_label = tk.Label(
                col_frame,
                text=indicator,
                font=self.label_font,
                bg='white',
                fg='#666666'
            )
            indicator_label.pack(pady=(0, 5))

            # 값
            value = region_data[indicator]
            unit = self.indicators[indicator]

            if unit == "%":
                value_text = f"{value:.1f}{unit}"
            elif unit == "명":
                value_text = f"{value:.1f}{unit}"
            else:
                value_text = f"{value:.1f}"

            value_label = tk.Label(
                col_frame,
                text=value_text,
                font=self.data_font,
                bg='white',
                fg='#333333'
            )
            value_label.pack()

        # 두 번째 줄에 나머지 지표 표시
        for i in range(3, len(indicators)):
            indicator = indicators[i]
            col_frame = tk.Frame(row2_frame, bg='white')
            col_frame.pack(side='left', expand=True, fill='both', padx=10)

            # 지표명
            indicator_label = tk.Label(
                col_frame,
                text=indicator,
                font=self.label_font,
                bg='white',
                fg='#666666'
            )
            indicator_label.pack(pady=(0, 5))

            # 값
            value = region_data[indicator]
            unit = self.indicators[indicator]

            if unit == "%":
                value_text = f"{value:.1f}{unit}"
            elif unit == "명":
                value_text = f"{value:.1f}{unit}"
            else:
                value_text = f"{value:.1f}"

            value_label = tk.Label(
                col_frame,
                text=value_text,
                font=self.data_font,
                bg='white',
                fg='#333333'
            )
            value_label.pack()

    def on_region_change(self, event):
        self.current_region = self.region_var.get()
        print(f"지역 변경됨: {self.current_region}")
        self.update_radar_chart()
        self.update_data_display()
        self.update_map()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True)
    app = RegionalAnalysisPage(frame)
    root.mainloop()