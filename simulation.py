# 시뮬레이션

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import tkinter.messagebox
from utils import create_styled_frame, create_styled_button
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import os
import math
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


class SimulationPage:
    def __init__(self, parent):
        self.parent = parent
        self.setup_styles()

        # 데이터 로드 및 계수 계산
        if not self.setup_data():
            tk.messagebox.showerror("데이터 로드 실패",
                                    "CSV 파일을 찾을 수 없거나 읽을 수 없습니다.\n"
                                    "데이터셋/통합_시도별_데이터셋.csv 파일을 확인해주세요.")
            return

        self.create_interface()

    def setup_styles(self):
        self.title_font = tkFont.Font(family="맑은 고딕", size=16, weight="bold")
        self.subtitle_font = tkFont.Font(family="맑은 고딕", size=14, weight="bold")
        self.label_font = tkFont.Font(family="맑은 고딕", size=11)
        self.value_font = tkFont.Font(family="맑은 고딕", size=11, weight="bold")
        self.data_font = tkFont.Font(family="맑은 고딕", size=24, weight="bold")
        self.unit_font = tkFont.Font(family="맑은 고딕", size=10)
        self.change_font = tkFont.Font(family="맑은 고딕", size=10)

    def calculate_coefficients_from_data(self, df):
        """실제 데이터를 기반으로 회귀분석을 통해 계수 계산"""
        print("\n=== 데이터 기반 계수 계산 시작 ===")

        # 필요한 컬럼들 찾기
        suicide_col = None
        pension_col = None
        welfare_col = None
        alone_col = None
        aging_col = None

        for col in df.columns:
            if '65세이상' in col and '자살' in col:
                suicide_col = col
            elif '수급률' in col:
                pension_col = col
            elif '독거노인' in col and '가구' in col:
                alone_col = col
            elif '복지시설' in col:
                welfare_col = col
            elif '노령화' in col and '지수' in col:
                aging_col = col

        print(f"자살률 컬럼: {suicide_col}")
        print(f"기초연금 컬럼: {pension_col}")
        print(f"복지시설 컬럼: {welfare_col}")
        print(f"독거노인 컬럼: {alone_col}")
        print(f"노령화지수 컬럼: {aging_col}")

        # 필요한 컬럼이 모두 있는지 확인
        required_cols = [suicide_col, pension_col, welfare_col, alone_col, aging_col]
        if None in required_cols:
            print("ERROR: 필요한 컬럼을 찾을 수 없습니다!")
            return self.get_default_coefficients()

        # 데이터 정리 (결측값 제거)
        analysis_df = df[[suicide_col, pension_col, welfare_col, alone_col, aging_col]].copy()
        analysis_df = analysis_df.dropna()

        if len(analysis_df) < 5:
            print("ERROR: 분석에 충분한 데이터가 없습니다!")
            return self.get_default_coefficients()

        print(f"분석 데이터 크기: {len(analysis_df)} 행")

        # 독립변수(X)와 종속변수(y) 설정
        X = analysis_df[[pension_col, welfare_col, alone_col, aging_col]]
        y = analysis_df[suicide_col]

        print(f"독립변수 통계:")
        print(X.describe())
        print(f"\n종속변수(자살률) 통계:")
        print(y.describe())

        try:
            # 선형 회귀 분석 수행
            model = LinearRegression()
            model.fit(X, y)

            # 계수 추출
            coefficients = {
                "기초연금 수급률": model.coef_[0],
                "복지시설률": model.coef_[1],
                "독거노인가구비율": model.coef_[2],
                "노령화지수": model.coef_[3]
            }

            # 모델 성능 평가
            r2_score = model.score(X, y)
            print(f"\n=== 회귀분석 결과 ===")
            print(f"R² 점수: {r2_score:.4f}")
            print(f"절편: {model.intercept_:.4f}")

            print(f"\n원래 계수:")
            for factor, coef in coefficients.items():
                print(f"  {factor}: {coef:.6f}")

            if abs(coefficients["기초연금 수급률"]) > 10 or abs(coefficients["복지시설률"]) > 10:
                return self.get_default_coefficients()

            if coefficients["복지시설률"] > 0:
                coefficients["복지시설률"] = -abs(coefficients["복지시설률"])

            if coefficients["독거노인가구비율"] < 0:
                coefficients["독거노인가구비율"] = abs(coefficients["독거노인가구비율"])
            print(f"\n최종 조정된 계수:")
            for factor, coef in coefficients.items():
                print(f"  {factor}: {coef:.6f}")

            # 상관관계 분석
            correlation_matrix = analysis_df.corr()
            print(f"\n상관관계 분석:")
            suicide_corr = correlation_matrix[suicide_col]
            for col in [pension_col, welfare_col, alone_col, aging_col]:
                print(f"  {col} vs 자살률: {suicide_corr[col]:.4f}")

            return coefficients

        except Exception as e:
            print(f"ERROR: 회귀분석 실패 - {e}")
            return self.get_default_coefficients()

    def setup_data(self):
        """실제 데이터셋에서 데이터 로드 및 계수 계산"""
        print("=== 시뮬레이션 데이터 로드 시작 ===")

        # CSV 파일 경로 확인
        csv_path = "데이터셋/통합_시도별_데이터셋.csv"
        print(f"CSV 파일 경로: {csv_path}")
        print(f"파일 존재 여부: {os.path.exists(csv_path)}")

        if not os.path.exists(csv_path):
            print("ERROR: CSV 파일이 존재하지 않습니다!")
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

        # 데이터 기반 계수 계산
        self.coefficients = self.calculate_coefficients_from_data(df)

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
                region_short = region_full.replace('특별시', '').replace('광역시', '').replace('도', '').replace('특별자치시',
                                                                                                          '').replace(
                    '특별자치도', '').strip()
                print(f"  직접 매핑: {region_full} -> {region_short}")

            # 지역 데이터 초기화
            if region_short not in self.data:
                self.data[region_short] = {}

            # 각 지표별 데이터 추출
            for col in df.columns:
                if '65세이상' in col and '자살' in col:
                    try:
                        value = float(row[col])
                        self.data[region_short]["자살률"] = value
                        print(f"    자살률: {value}")
                    except Exception as e:
                        print(f"    자살률 변환 실패: {e}")

                elif '수급률' in col:
                    try:
                        value = float(row[col])
                        self.data[region_short]["기초연금 수급률"] = value
                        print(f"    기초연금 수급률: {value}")
                    except Exception as e:
                        print(f"    기초연금 수급률 변환 실패: {e}")

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

        # 데이터 검증
        if len(self.data) < 5:
            print(f"ERROR: 로드된 지역이 너무 적습니다 ({len(self.data)}개)")
            return False

        self.regions = sorted(list(self.data.keys()))
        self.current_region = self.regions[0]

        # 전국 평균 계산
        suicide_rates = [region_data["자살률"] for region_data in self.data.values() if "자살률" in region_data]
        if suicide_rates:
            self.national_avg = sum(suicide_rates) / len(suicide_rates)
        else:
            self.national_avg = 50.0

        # 시뮬레이션 변수
        self.original_values = {}
        self.simulated_values = {}
        self.reset_simulation()

        # 슬라이더 범위 설정
        self.slider_ranges = {
            "기초연금 수급률": (0, 100),
            "복지시설률": (0, 50),
            "독거노인가구비율": (0, 50),
            "노령화지수": (50, 2000)
        }

        print("=== 시뮬레이션 데이터 로드 완료 ===")
        print(f"총 {len(self.regions)}개 지역 로드됨: {self.regions}")
        print("최종 적용된 계수:")
        for factor, coef in self.coefficients.items():
            print(f"  {factor}: {coef:.6f}")
        return True

    def reset_simulation(self):
        if self.current_region in self.data:
            self.original_values = self.data[self.current_region].copy()
            self.simulated_values = self.original_values.copy()

    def create_interface(self):
        # 메인 컨테이너
        main_container = tk.Frame(self.parent, bg='#E3F2FD')
        main_container.pack(fill='both', expand=True)

        # 제목
        title_label = tk.Label(
            main_container,
            text="시뮬레이션",
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
        # 컨트롤 패널
        control_panel = tk.Frame(
            parent,
            bg='white',
            relief='solid',
            bd=1
        )
        control_panel.pack(fill='both', expand=True)

        # 내부 패딩
        inner_frame = tk.Frame(control_panel, bg='white', padx=20, pady=20)
        inner_frame.pack(fill='both', expand=True)

        # 지역 선택 드롭다운
        region_frame = tk.Frame(inner_frame, bg='white')
        region_frame.pack(fill='x', pady=(0, 20))

        # 지역 선택과 초기화 버튼을 나란히 배치하는 프레임
        top_controls_frame = tk.Frame(region_frame, bg='white')
        top_controls_frame.pack(fill='x')

        # 왼쪽: 지역 선택
        region_left_frame = tk.Frame(top_controls_frame, bg='white')
        region_left_frame.pack(side='left', fill='both', expand=True)

        region_label = tk.Label(
            region_left_frame,
            text="지역 선택",
            font=self.label_font,
            bg='white',
            fg='#333333'
        )
        region_label.pack(anchor='w', pady=(0, 5))

        self.region_var = tk.StringVar(value=self.current_region)
        region_combo = ttk.Combobox(
            region_left_frame,
            textvariable=self.region_var,
            values=self.regions,
            state="readonly",
            width=20,
            font=self.label_font
        )
        region_combo.pack(anchor='w')
        region_combo.bind('<<ComboboxSelected>>', self.on_region_change)

        # 오른쪽: 초기화 버튼
        reset_button = tk.Button(
            top_controls_frame,
            text="초기화",
            command=self.reset_and_update,
            font=self.label_font,
            bg='#f0f0f0',
            fg='#333333',
            relief='flat',
            cursor='hand2',
            width=8
        )
        reset_button.pack(side='right', padx=(10, 0), pady=(20, 0))

        # 슬라이더 생성 (자살률 제외)
        self.sliders = {}
        self.slider_values = {}
        self.slider_labels = {}
        self.range_labels = {}

        factors = ["기초연금 수급률", "복지시설률", "독거노인가구비율", "노령화지수"]

        for factor in factors:
            frame = tk.Frame(inner_frame, bg='white')
            frame.pack(fill='x', pady=(0, 15))

            # 요인 이름
            label = tk.Label(
                frame,
                text=factor,
                font=self.label_font,
                bg='white',
                fg='#333333',
                anchor='w'
            )
            label.pack(fill='x')

            # 슬라이더 값 표시
            value_frame = tk.Frame(frame, bg='white')
            value_frame.pack(fill='x', pady=(0, 5))

            # 슬라이더 범위 먼저 가져오기
            min_val, max_val = self.slider_ranges[factor]
            current_val = self.original_values.get(factor, min_val)

            slider = ttk.Scale(
                frame,
                from_=min_val,
                to=max_val,
                value=current_val,
                orient='horizontal'
            )
            slider.pack(fill='x')

            # 값 표시 라벨
            if factor == "노령화지수":
                display_text = f"{current_val:.0f}"
            else:
                display_text = f"{current_val:.1f}%"

            value_label = tk.Label(
                value_frame,
                text=display_text,
                font=self.value_font,
                bg='white',
                fg='#333333',
                anchor='e'
            )
            value_label.pack(side='right')

            # 변화율 표시
            change_label = tk.Label(
                value_frame,
                text="(0%)",
                font=self.change_font,
                bg='white',
                fg='black',
                anchor='e'
            )
            change_label.pack(side='right', padx=(0, 5))

            # 슬라이더 이벤트 연결
            slider.bind("<ButtonRelease-1>", lambda e, f=factor: self.on_slider_change(f))
            slider.bind("<B1-Motion>", lambda e, f=factor: self.on_slider_change(f))

            # 저장
            self.sliders[factor] = slider
            self.slider_values[factor] = value_label
            self.slider_labels[factor] = change_label

    def create_right_panel(self, parent):
        # 결과 패널
        result_panel = tk.Frame(
            parent,
            bg='white',
            relief='solid',
            bd=1
        )
        result_panel.pack(fill='both', expand=True)

        # 내부 패딩
        inner_frame = tk.Frame(result_panel, bg='white', padx=20, pady=20)
        inner_frame.pack(fill='both', expand=True)

        # 오른쪽 패널을 두 부분으로 나눔
        top_frame = tk.Frame(inner_frame, bg='white')
        top_frame.pack(fill='x', expand=False)

        bottom_frame = tk.Frame(inner_frame, bg='white')
        bottom_frame.pack(fill='x', expand=True, pady=(10, 0))

        # 예측 자살률 제목
        title_label = tk.Label(
            top_frame,
            text="예측 자살률(10만명당)",
            font=self.subtitle_font,
            bg='white',
            fg='#333333'
        )
        title_label.pack(pady=(0, 10))

        # 게이지 차트
        gauge_frame = tk.Frame(top_frame, bg='white')
        gauge_frame.pack(fill='x', pady=(0, 10))

        # matplotlib 설정
        plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 게이지 차트 크기
        self.gauge_fig, self.gauge_ax = plt.subplots(figsize=(4, 2.2))
        self.gauge_fig.patch.set_facecolor('white')
        self.gauge_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.gauge_canvas = FigureCanvasTkAgg(self.gauge_fig, gauge_frame)
        self.gauge_canvas.get_tk_widget().pack(fill='both', expand=True)

        # 데이터 표시 영역
        data_frame = tk.Frame(bottom_frame, bg='white', relief='solid', bd=1)
        data_frame.pack(fill='x', expand=True)

        # 전국 평균
        avg_frame = tk.Frame(data_frame, bg='white')
        avg_frame.pack(fill='x', pady=10, padx=10)

        avg_label = tk.Label(
            avg_frame,
            text="전국 평균",
            font=self.label_font,
            bg='white',
            fg='#666666',
            anchor='w'
        )
        avg_label.pack(side='left')

        self.avg_value = tk.Label(
            avg_frame,
            text=f"{self.national_avg:.1f}명",
            font=self.value_font,
            bg='white',
            fg='#333333',
            anchor='e'
        )
        self.avg_value.pack(side='right')

        # 구분선
        separator1 = ttk.Separator(data_frame, orient='horizontal')
        separator1.pack(fill='x', padx=10)

        # 시뮬레이션 전
        before_frame = tk.Frame(data_frame, bg='white')
        before_frame.pack(fill='x', pady=10, padx=10)

        before_label = tk.Label(
            before_frame,
            text="시뮬레이션 전",
            font=self.label_font,
            bg='white',
            fg='#666666',
            anchor='w'
        )
        before_label.pack(side='left')

        self.before_value = tk.Label(
            before_frame,
            text=f"{self.original_values.get('자살률', 0):.1f}명",
            font=self.value_font,
            bg='white',
            fg='#333333',
            anchor='e'
        )
        self.before_value.pack(side='right')

        # 구분선
        separator2 = ttk.Separator(data_frame, orient='horizontal')
        separator2.pack(fill='x', padx=10)

        # 시뮬레이션 후
        after_frame = tk.Frame(data_frame, bg='white')
        after_frame.pack(fill='x', pady=10, padx=10)

        after_label = tk.Label(
            after_frame,
            text="시뮬레이션 후",
            font=self.label_font,
            bg='white',
            fg='#666666',
            anchor='w'
        )
        after_label.pack(side='left')

        self.after_value = tk.Label(
            after_frame,
            text=f"{self.simulated_values.get('자살률', 0):.1f}명",
            font=self.value_font,
            bg='white',
            fg='#333333',
            anchor='e'
        )
        self.after_value.pack(side='right')

        # 변화량
        self.change_value = tk.Label(
            after_frame,
            text="",
            font=self.change_font,
            bg='white',
            fg='green',
            anchor='e'
        )
        self.change_value.pack(side='right', padx=(0, 5))

        # 초기 게이지 업데이트 및 시뮬레이션 적용
        self.calculate_suicide_rate()
        self.update_result_ui()

    def update_gauge(self):
        self.gauge_ax.clear()

        # 게이지 설정 (더 넓은 범위로 조정)
        min_val = 0
        max_val = 100  # 극단적 시나리오까지 표시 가능하도록 확장
        current_val = self.simulated_values.get('자살률', 0)

        # 위험 수준 구간 설정
        low_threshold = 30  # 낮은 위험 (녹색)
        medium_threshold = 60  # 중간 위험 (노란색)
        # 60 이상은 높은 위험 (빨간색)

        # 반원 각도 설정
        start_angle = 0
        end_angle = 180

        # 각 구간의 각도 계산
        low_angle = start_angle + (end_angle - start_angle) * (low_threshold / max_val)
        medium_angle = start_angle + (end_angle - start_angle) * (medium_threshold / max_val)

        # 게이지 배경 그리기
        angles = np.linspace(np.radians(start_angle), np.radians(end_angle), 100)

        # 초록색 구간 (0 ~ 30)
        green_angles = angles[angles <= np.radians(low_angle)]
        if len(green_angles) > 0:
            x_green = np.cos(green_angles)
            y_green = np.sin(green_angles)
            self.gauge_ax.plot(x_green, y_green, color='#4CAF50', linewidth=15, solid_capstyle='round')

        # 노란색 구간 (30 ~ 60)
        yellow_angles = angles[(angles > np.radians(low_angle)) & (angles <= np.radians(medium_angle))]
        if len(yellow_angles) > 0:
            x_yellow = np.cos(yellow_angles)
            y_yellow = np.sin(yellow_angles)
            self.gauge_ax.plot(x_yellow, y_yellow, color='#FFC107', linewidth=15, solid_capstyle='round')

        # 빨간색 구간 (60 ~ 100)
        red_angles = angles[angles > np.radians(medium_angle)]
        if len(red_angles) > 0:
            x_red = np.cos(red_angles)
            y_red = np.sin(red_angles)
            self.gauge_ax.plot(x_red, y_red, color='#F44336', linewidth=15, solid_capstyle='round')

        # 바늘 그리기
        needle_angle = start_angle + (end_angle - start_angle) * (min(current_val, max_val) / max_val)
        needle_rad = np.radians(needle_angle)

        # 바늘
        self.gauge_ax.plot([0, 0.8 * np.cos(needle_rad)], [0, 0.8 * np.sin(needle_rad)],
                           color='black', linewidth=3, solid_capstyle='round')

        # 중심점
        self.gauge_ax.plot(0, 0, 'ko', markersize=8)

        # 수치 표시 (게이지 아래)
        self.gauge_ax.text(0, -0.3, f"{current_val:.1f}",
                           ha='center', va='center', fontsize=16, fontweight='bold')

        # 축 설정
        self.gauge_ax.set_xlim(-1.2, 1.2)
        self.gauge_ax.set_ylim(-0.4, 1.2)
        self.gauge_ax.set_aspect('equal')
        self.gauge_ax.axis('off')

        # 그래프 업데이트
        self.gauge_canvas.draw()

    def on_region_change(self, event):
        self.current_region = self.region_var.get()
        self.reset_simulation()
        self.update_ui()

    def on_slider_change(self, factor):
        # 슬라이더 값 가져오기
        value = self.sliders[factor].get()

        # 값 표시 업데이트
        if factor == "노령화지수":
            display_value = f"{value:.0f}"
        else:
            display_value = f"{value:.1f}%"

        self.slider_values[factor].config(text=display_value)

        # 변화율 계산 및 표시
        original = self.original_values.get(factor, 0)
        if original > 0:
            change_pct = (value - original) / original * 100
            if change_pct > 0:
                self.slider_labels[factor].config(text=f"(↑{change_pct:.1f}%)", fg="green")
            elif change_pct < 0:
                self.slider_labels[factor].config(text=f"(↓{abs(change_pct):.1f}%)", fg="red")
            else:
                self.slider_labels[factor].config(text="(0%)", fg="black")

        # 시뮬레이션 값 업데이트
        self.simulated_values[factor] = value

        # 실시간 시뮬레이션 적용
        self.calculate_suicide_rate()
        self.update_result_ui()

    def calculate_suicide_rate(self):
        # 데이터 기반 회귀분석 계수를 사용한 자살률 계산
        base_suicide_rate = self.original_values.get("자살률", 50.0)
        new_suicide_rate = base_suicide_rate

        for factor, coef in self.coefficients.items():
            if factor in self.original_values and factor in self.simulated_values:
                original = self.original_values[factor]
                current = self.simulated_values[factor]
                change = current - original
                new_suicide_rate += change * coef

        # 음수 방지
        new_suicide_rate = max(0, new_suicide_rate)

        # 결과 업데이트
        self.simulated_values["자살률"] = new_suicide_rate

    def reset_and_update(self):
        self.reset_simulation()
        self.update_ui()

    def update_ui(self):
        # 슬라이더 값 업데이트
        for factor, slider in self.sliders.items():
            value = self.original_values.get(factor, 0)
            slider.set(value)

            # 값 표시 업데이트
            if factor == "노령화지수":
                display_value = f"{value:.0f}"
            else:
                display_value = f"{value:.1f}%"

            self.slider_values[factor].config(text=display_value)
            self.slider_labels[factor].config(text="(0%)", fg="black")

        # 결과 UI 업데이트
        self.update_result_ui()

    def update_result_ui(self):
        # 자살률 값 업데이트
        self.before_value.config(text=f"{self.original_values.get('자살률', 0):.1f}명")
        self.after_value.config(text=f"{self.simulated_values.get('자살률', 0):.1f}명")

        # 변화량 계산 및 표시
        original_rate = self.original_values.get('자살률', 0)
        simulated_rate = self.simulated_values.get('자살률', 0)
        change = simulated_rate - original_rate

        if change > 0:
            self.change_value.config(text=f"↑ ({change:.1f}명)", fg="red")
        elif change < 0:
            self.change_value.config(text=f"↓ ({abs(change):.1f}명)", fg="green")
        else:
            self.change_value.config(text="(0명)", fg="black")

        # 게이지 업데이트
        self.update_gauge()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True)
    app = SimulationPage(frame)
    root.mainloop()