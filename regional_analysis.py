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

# 경고 메시지 숨기기
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


class RegionalAnalysisPage:
    def __init__(self, parent):
        self.parent = parent
        self.setup_styles()
        self.setup_data()
        self.load_geodata()
        self.create_interface()

    def setup_styles(self):
        self.title_font = tkFont.Font(family="맑은 고딕", size=16, weight="bold")
        self.subtitle_font = tkFont.Font(family="맑은 고딕", size=14, weight="bold")
        self.label_font = tkFont.Font(family="맑은 고딕", size=11)
        self.data_font = tkFont.Font(family="맑은 고딕", size=24, weight="bold")
        self.unit_font = tkFont.Font(family="맑은 고딕", size=10)

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
                    print("지역명들:", self.gdf[self.지역컬럼].tolist()[:5])  # 처음 5개만 출력

                # 지역명이 제대로 읽혔는지 확인
                if self.지역컬럼 and len(self.gdf[self.지역컬럼].iloc[0]) > 0:
                    first_region = self.gdf[self.지역컬럼].iloc[0]
                    # 한글이 제대로 읽혔는지 확인 (깨진 문자가 아닌지)
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
                # 인코딩 없이 시도
                self.gdf = gpd.read_file("데이터셋/경계데이터/bnd_sido_00_2024_2Q.shp")
                self.지역컬럼 = 'SIDO_CD'  # 코드 컬럼 사용
                self.use_code_mapping = True
            except Exception as e:
                print(f"최종 로드 실패: {e}")
                self.gdf = None
                self.지역컬럼 = None
                return
        else:
            self.use_code_mapping = False

        # 지역명 매핑 설정
        if self.use_code_mapping:
            # SIDO_CD 기반 매핑
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
            # 지역명 기반 매핑
            self.region_mapping = {
                "서울특별시": "서울",
                "부산광역시": "부산",
                "대구광역시": "대구",
                "인천광역시": "인천",
                "광주광역시": "광주",
                "대전광역시": "대전",
                "울산광역시": "울산",
                "세종특별자치시": "세종",
                "경기도": "경기",
                "강원특별자치도": "강원",
                "강원도": "강원",
                "충청북도": "충북",
                "충청남도": "충남",
                "전북특별자치도": "전북",
                "전라북도": "전북",
                "전라남도": "전남",
                "경상북도": "경북",
                "경상남도": "경남",
                "제주특별자치도": "제주"
            }

        # 역매핑 생성
        self.reverse_mapping = {v: k for k, v in self.region_mapping.items()}
        print("지도 데이터 로드 완료")

    def setup_data(self):
        # 지역별 데이터
        self.data = {
            "서울": {
                "자살률": 20.5,
                "기초연금 수급률": 15.2,
                "1인 가구 수": 1250000,
                "복지시설 수": 850,
                "노령화 지수": 12.8
            },
            "부산": {
                "자살률": 25.3,
                "기초연금 수급률": 22.1,
                "1인 가구 수": 680000,
                "복지시설 수": 420,
                "노령화 지수": 18.5
            },
            "대구": {
                "자살률": 24.8,
                "기초연금 수급률": 20.5,
                "1인 가구 수": 520000,
                "복지시설 수": 310,
                "노령화 지수": 16.2
            },
            "인천": {
                "자살률": 21.9,
                "기초연금 수급률": 17.8,
                "1인 가구 수": 620000,
                "복지시설 수": 380,
                "노령화 지수": 14.1
            },
            "광주": {
                "자살률": 23.6,
                "기초연금 수급률": 19.3,
                "1인 가구 수": 320000,
                "복지시설 수": 180,
                "노령화 지수": 15.7
            },
            "대전": {
                "자살률": 22.4,
                "기초연금 수급률": 18.1,
                "1인 가구 수": 380000,
                "복지시설 수": 220,
                "노령화 지수": 13.9
            },
            "울산": {
                "자살률": 26.1,
                "기초연금 수급률": 16.5,
                "1인 가구 수": 280000,
                "복지시설 수": 150,
                "노령화 지수": 11.2
            },
            "세종": {
                "자살률": 18.5,
                "기초연금 수급률": 12.8,
                "1인 가구 수": 95000,
                "복지시설 수": 45,
                "노령화 지수": 8.9
            },
            "경기": {
                "자살률": 19.8,
                "기초연금 수급률": 14.5,
                "1인 가구 수": 2100000,
                "복지시설 수": 1200,
                "노령화 지수": 13.2
            },
            "강원": {
                "자살률": 28.7,
                "기초연금 수급률": 25.8,
                "1인 가구 수": 320000,
                "복지시설 수": 180,
                "노령화 지수": 22.1
            },
            "충북": {
                "자살률": 26.4,
                "기초연금 수급률": 23.2,
                "1인 가구 수": 280000,
                "복지시설 수": 160,
                "노령화 지수": 19.8
            },
            "충남": {
                "자살률": 25.1,
                "기초연금 수급률": 21.9,
                "1인 가구 수": 420000,
                "복지시설 수": 240,
                "노령화 지수": 18.5
            },
            "전북": {
                "자살률": 29.2,
                "기초연금 수급률": 26.7,
                "1인 가구 수": 380000,
                "복지시설 수": 200,
                "노령화 지수": 23.4
            },
            "전남": {
                "자살률": 31.2,
                "기초연금 수급률": 28.9,
                "1인 가구 수": 320000,
                "복지시설 수": 180,
                "노령화 지수": 25.6
            },
            "경북": {
                "자살률": 27.8,
                "기초연금 수급률": 24.5,
                "1인 가구 수": 520000,
                "복지시설 수": 280,
                "노령화 지수": 21.3
            },
            "경남": {
                "자살률": 26.9,
                "기초연금 수급률": 23.1,
                "1인 가구 수": 680000,
                "복지시설 수": 350,
                "노령화 지수": 19.7
            },
            "제주": {
                "자살률": 19.8,
                "기초연금 수급률": 16.2,
                "1인 가구 수": 140000,
                "복지시설 수": 80,
                "노령화 지수": 14.8
            }
        }

        self.regions = list(self.data.keys())
        self.current_region = "서울"

        # 지표 이름과 단위
        self.indicators = {
            "자살률": "명",
            "기초연금 수급률": "%",
            "1인 가구 수": "가구",
            "복지시설 수": "개",
            "노령화 지수": "???"
        }

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

        # 로딩 라벨
        self.loading_label = tk.Label(
            map_container,
            text="지도 로딩 중...",
            font=self.label_font,
            bg='white',
            fg='#666666'
        )
        self.loading_label.pack(expand=True)

        # 지도 이미지 라벨 (초기에는 숨김)
        self.map_label = tk.Label(map_container, bg='white')

        # 초기 지도 생성
        self.update_map()

    def update_map(self):
        """지도 업데이트 (백그라운드에서 실행)"""
        if self.gdf is None or self.지역컬럼 is None:
            self.loading_label.config(text="지도 데이터를 찾을 수 없습니다")
            return

        self.loading_label.config(text="지도 생성 중...")
        print(f"지도 업데이트 시작 - 현재 지역: {self.current_region}")

        def generate_map():
            try:
                print("지도 생성 함수 시작")

                # 지도 데이터 복사
                gdf_copy = self.gdf.copy()
                print(f"GeoDataFrame 복사 완료, 행 수: {len(gdf_copy)}")

                # 선택된 지역에 해당하는 키 찾기
                selected_key = self.reverse_mapping.get(self.current_region, self.current_region)
                print(f"선택된 지역 키: {selected_key}")

                # 색상 컬럼 생성
                if self.use_code_mapping:
                    print("코드 기반 매핑 사용")
                    # 코드 기반 매핑
                    gdf_copy["color"] = gdf_copy[self.지역컬럼].apply(
                        lambda x: "red" if str(x) == str(selected_key) else "lightblue"
                    )
                else:
                    print("지역명 기반 매핑 사용")
                    # 지역명 기반 매핑
                    gdf_copy["color"] = "lightblue"  # 기본 색상
                    for idx, row in gdf_copy.iterrows():
                        region_name = str(row[self.지역컬럼])
                        for full_name, short_name in self.region_mapping.items():
                            if full_name in region_name or short_name in region_name:
                                if short_name == self.current_region:
                                    gdf_copy.at[idx, "color"] = "red"
                                    print(f"지역 {region_name}을 빨간색으로 설정")
                                    break

                print("색상 설정 완료")

                # 지도 생성
                print("matplotlib 지도 생성 시작")
                fig, ax = plt.subplots(figsize=(4, 5))
                gdf_copy.plot(ax=ax, color=gdf_copy["color"], edgecolor="black", linewidth=0.5)
                ax.set_title(f"선택 지역: {self.current_region}", fontsize=12, pad=10)
                ax.axis('off')
                print("matplotlib 지도 생성 완료")

                # 임시 파일로 저장
                map_filename = f"temp_map_{self.current_region}.png"
                print(f"지도를 {map_filename}에 저장 중...")
                plt.savefig(map_filename, bbox_inches="tight", dpi=100, facecolor='white')
                plt.close()
                print("지도 파일 저장 완료")

                # 이미지 로드 및 UI 업데이트
                print("이미지 로드 시작")
                img = Image.open(map_filename)
                img = img.resize((300, 280), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                print("이미지 로드 완료")

                def update_ui():
                    print("UI 업데이트 시작")
                    self.loading_label.pack_forget()
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
                    self.loading_label.config(text=f"지도 생성 실패: {str(e)}")

                self.parent.after(0, show_error)

        # 백그라운드 스레드에서 지도 생성
        threading.Thread(target=generate_map, daemon=True).start()

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
            if indicator == "자살률":
                normalized = value / 35.0  # 최대 35로 가정
            elif indicator == "기초연금 수급률":
                normalized = value / 30.0  # 최대 30%로 가정
            elif indicator == "1인 가구 수":
                normalized = value / 2500000  # 최대 250만으로 가정
            elif indicator == "복지시설 수":
                normalized = value / 1500  # 최대 1500개로 가정
            elif indicator == "노령화 지수":
                normalized = value / 30.0  # 최대 30으로 가정

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

        # 5개 지표를 한 줄에 표시
        row_frame = tk.Frame(self.data_container, bg='white')
        row_frame.pack(expand=True, fill='x')

        for i, indicator in enumerate(indicators):
            col_frame = tk.Frame(row_frame, bg='white')
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

            if indicator == "1인 가구 수":
                if value >= 1000000:
                    value_text = f"{value // 10000}만{unit}"
                else:
                    value_text = f"{value // 1000}천{unit}"
            elif indicator == "복지시설 수":
                value_text = f"{int(value)}{unit}"
            elif unit == "%":
                value_text = f"{value:.1f}{unit}"
            else:
                value_text = f"{value:.1f}{unit}"

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