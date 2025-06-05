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

        # 지역명 매핑 설정
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
        # 확장된 지역별 데이터 (17개 시도)
        self.data = {
            "복지시설 수": {
                "서울": 850, "부산": 420, "대구": 310, "인천": 380, "광주": 180,
                "대전": 220, "울산": 150, "세종": 45, "경기": 1200, "강원": 180,
                "충북": 160, "충남": 240, "전북": 200, "전남": 180, "경북": 280,
                "경남": 350, "제주": 80
            },
            "자살률": {
                "서울": 20.5, "부산": 25.3, "대구": 24.8, "인천": 21.9, "광주": 23.6,
                "대전": 22.4, "울산": 26.1, "세종": 18.5, "경기": 19.8, "강원": 28.7,
                "충북": 26.4, "충남": 25.1, "전북": 29.2, "전남": 31.2, "경북": 27.8,
                "경남": 26.9, "제주": 19.8
            },
            "인구수": {
                "서울": 9720000, "부산": 3390000, "대구": 2410000, "인천": 2950000, "광주": 1440000,
                "대전": 1450000, "울산": 1130000, "세종": 370000, "경기": 13530000, "강원": 1530000,
                "충북": 1590000, "충남": 2120000, "전북": 1780000, "전남": 1860000, "경북": 2660000,
                "경남": 3350000, "제주": 670000
            },
            "기초연금 수급률": {
                "서울": 15.2, "부산": 22.1, "대구": 20.5, "인천": 17.8, "광주": 19.3,
                "대전": 18.1, "울산": 16.5, "세종": 12.8, "경기": 14.5, "강원": 25.8,
                "충북": 23.2, "충남": 21.9, "전북": 26.7, "전남": 28.9, "경북": 24.5,
                "경남": 23.1, "제주": 16.2
            },
            "노령화 지수": {
                "서울": 12.8, "부산": 18.5, "대구": 16.2, "인천": 14.1, "광주": 15.7,
                "대전": 13.9, "울산": 11.2, "세종": 8.9, "경기": 13.2, "강원": 22.1,
                "충북": 19.8, "충남": 18.5, "전북": 23.4, "전남": 25.6, "경북": 21.3,
                "경남": 19.7, "제주": 14.8
            }
        }

        # 지역 체크박스 변수들
        self.region_vars = {}
        self.regions = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
                        "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]

        for region in self.regions:
            self.region_vars[region] = tk.BooleanVar()

        # 전체 선택 변수
        self.select_all_var = tk.BooleanVar()

        # 기본 선택 지역
        self.region_vars["서울"].set(True)
        self.region_vars["경기"].set(True)
        self.region_vars["강원"].set(True)

        # 현재 선택된 지표
        self.current_indicator = "복지시설 수"

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
                bg='white'
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

        self.indicator_var = tk.StringVar(value=self.current_indicator)
        indicator_combo = ttk.Combobox(
            indicator_frame,
            textvariable=self.indicator_var,
            values=list(self.data.keys()),
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
            self.ax.set_ylabel(self.current_indicator, fontsize=10)
            self.ax.tick_params(axis='x', rotation=45, labelsize=9)
            self.ax.tick_params(axis='y', labelsize=9)

            # Y축 포맷팅
            if self.current_indicator in ["복지시설 수", "인구수"]:
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
            else:
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}'))

            # 막대 위에 값 표시
            for bar, value in zip(bars, values):
                height = bar.get_height()
                if self.current_indicator in ["복지시설 수", "인구수"]:
                    label = f'{int(value):,}'
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

                for idx, row in gdf_copy.iterrows():
                    if self.use_code_mapping:
                        region_code = str(row[self.지역컬럼])
                        region_name = self.region_mapping.get(region_code)
                    else:
                        region_full_name = str(row[self.지역컬럼])
                        region_name = None
                        for full_name, short_name in self.region_mapping.items():
                            if full_name in region_full_name or short_name in region_full_name:
                                region_name = short_name
                                break

                    # 선택된 지역인지 확인
                    if region_name and region_name in selected_regions:
                        gdf_copy.at[idx, 'is_selected'] = True
                        if region_name in indicator_data:
                            gdf_copy.at[idx, 'indicator_value'] = indicator_data[region_name]

                print("지표 값 매핑 완료")

                # 선택된 지역의 값들만 가져오기
                selected_values = gdf_copy[gdf_copy['is_selected'] == True]['indicator_value'].dropna()

                if len(selected_values) > 0:
                    vmin, vmax = selected_values.min(), selected_values.max()

                    # 지도 생성
                    fig, ax = plt.subplots(figsize=(5, 4))

                    # 색상 맵 설정
                    if self.current_indicator == "자살률":
                        cmap = plt.cm.Reds
                    elif self.current_indicator == "복지시설 수":
                        cmap = plt.cm.Blues
                    elif self.current_indicator == "인구수":
                        cmap = plt.cm.Greens
                    elif self.current_indicator == "기초연금 수급률":
                        cmap = plt.cm.Oranges
                    else:  # 노령화 지수
                        cmap = plt.cm.Purples

                    # 먼저 모든 지역을 흰색으로 그리기
                    gdf_copy.plot(ax=ax, color='white', edgecolor='black', linewidth=0.5)

                    # 선택된 지역만 색상으로 그리기
                    selected_gdf = gdf_copy[gdf_copy['is_selected'] == True]
                    if len(selected_gdf) > 0:
                        selected_gdf.plot(ax=ax, column='indicator_value', cmap=cmap,
                                          legend=True, edgecolor='black', linewidth=0.5,
                                          vmin=vmin, vmax=vmax)

                    # 제목 제거 (이 부분을 제거하거나 주석 처리)
                    # ax.set_title(f'{self.current_indicator} 분포 (선택된 지역)', fontsize=12, pad=10)

                    ax.axis('off')

                    # 컬러바 조정
                    if len(selected_gdf) > 0:
                        cbar = ax.get_figure().get_axes()[-1]
                        if self.current_indicator in ["복지시설 수", "인구수"]:
                            cbar.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
                        else:
                            cbar.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}'))
                else:
                    # 선택된 지역이 없는 경우
                    fig, ax = plt.subplots(figsize=(5, 4))
                    gdf_copy.plot(ax=ax, color='white', edgecolor='black', linewidth=0.5)
                    # 제목 제거 (이 부분도 제거)
                    # ax.set_title('지역을 선택해주세요', fontsize=12, pad=10)
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
        self.current_indicator = self.indicator_var.get()
        tk.messagebox.showinfo("지표 변경", "지표가 변경되었습니다. '비교하기' 버튼을 눌러 시각화를 업데이트하세요.")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True)
    app = RegionalComparisonPage(frame)
    root.mainloop()