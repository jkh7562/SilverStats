import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from utils import create_styled_frame, create_styled_button
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import math


class SimulationPage:
    def __init__(self, parent):
        self.parent = parent
        self.setup_styles()
        self.setup_data()
        self.create_interface()

    def setup_styles(self):
        self.title_font = tkFont.Font(family="맑은 고딕", size=16, weight="bold")
        self.subtitle_font = tkFont.Font(family="맑은 고딕", size=14, weight="bold")
        self.label_font = tkFont.Font(family="맑은 고딕", size=11)
        self.value_font = tkFont.Font(family="맑은 고딕", size=11, weight="bold")
        self.data_font = tkFont.Font(family="맑은 고딕", size=24, weight="bold")
        self.unit_font = tkFont.Font(family="맑은 고딕", size=10)
        self.change_font = tkFont.Font(family="맑은 고딕", size=10)

    def setup_data(self):
        # 지역별 데이터
        self.data = {
            "서울": {
                "자살률": 20.5,
                "기초연금 수급률": 15.2,
                "복지시설 수": 850,
                "1인 가구 수": 1250000,
                "노령화 지수": 12.8
            },
            "부산": {
                "자살률": 25.3,
                "기초연금 수급률": 22.1,
                "복지시설 수": 420,
                "1인 가구 수": 680000,
                "노령화 지수": 18.5
            },
            "대구": {
                "자살률": 24.8,
                "기초연금 수급률": 20.5,
                "복지시설 수": 310,
                "1인 가구 수": 520000,
                "노령화 지수": 16.2
            },
            "인천": {
                "자살률": 21.9,
                "기초연금 수급률": 17.8,
                "복지시설 수": 380,
                "1인 가구 수": 620000,
                "노령화 지수": 14.1
            },
            "광주": {
                "자살률": 23.6,
                "기초연금 수급률": 19.3,
                "복지시설 수": 180,
                "1인 가구 수": 320000,
                "노령화 지수": 15.7
            },
            "대전": {
                "자살률": 22.4,
                "기초연금 수급률": 18.1,
                "복지시설 수": 220,
                "1인 가구 수": 380000,
                "노령화 지수": 13.9
            },
            "울산": {
                "자살률": 26.1,
                "기초연금 수급률": 16.5,
                "복지시설 수": 150,
                "1인 가구 수": 280000,
                "노령화 지수": 11.2
            },
            "세종": {
                "자살률": 18.5,
                "기초연금 수급률": 12.8,
                "복지시설 수": 45,
                "1인 가구 수": 95000,
                "노령화 지수": 8.9
            },
            "경기": {
                "자살률": 19.8,
                "기초연금 수급률": 14.5,
                "복지시설 수": 1200,
                "1인 가구 수": 2100000,
                "노령화 지수": 13.2
            },
            "강원": {
                "자살률": 28.7,
                "기초연금 수급률": 25.8,
                "복지시설 수": 180,
                "1인 가구 수": 320000,
                "노령화 지수": 22.1
            },
            "충북": {
                "자살률": 26.4,
                "기초연금 수급률": 23.2,
                "복지시설 수": 160,
                "1인 가구 수": 280000,
                "노령화 지수": 19.8
            },
            "충남": {
                "자살률": 25.1,
                "기초연금 수급률": 21.9,
                "복지시설 수": 240,
                "1인 가구 수": 420000,
                "노령화 지수": 18.5
            },
            "전북": {
                "자살률": 29.2,
                "기초연금 수급률": 26.7,
                "복지시설 수": 200,
                "1인 가구 수": 380000,
                "노령화 지수": 23.4
            },
            "전남": {
                "자살률": 31.2,
                "기초연금 수급률": 28.9,
                "복지시설 수": 180,
                "1인 가구 수": 320000,
                "노령화 지수": 25.6
            },
            "경북": {
                "자살률": 27.8,
                "기초연금 수급률": 24.5,
                "복지시설 수": 280,
                "1인 가구 수": 520000,
                "노령화 지수": 21.3
            },
            "경남": {
                "자살률": 26.9,
                "기초연금 수급률": 23.1,
                "복지시설 수": 350,
                "1인 가구 수": 680000,
                "노령화 지수": 19.7
            },
            "제주": {
                "자살률": 19.8,
                "기초연금 수급률": 16.2,
                "복지시설 수": 80,
                "1인 가구 수": 140000,
                "노령화 지수": 14.8
            }
        }

        self.regions = list(self.data.keys())
        self.current_region = "부산"

        # 전국 평균 계산
        self.national_avg = sum(region_data["자살률"] for region_data in self.data.values()) / len(self.data)

        # 시뮬레이션 변수
        self.original_values = {}
        self.simulated_values = {}
        self.reset_simulation()

        # 시뮬레이션 계수 (가상의 계수)
        self.coefficients = {
            "기초연금 수급률": -0.3,  # 기초연금 수급률 1% 증가 시 자살률 0.3 감소
            "복지시설 수": -0.01,  # 복지시설 10개 증가 시 자살률 0.1 감소
            "1인 가구 수": 0.2,  # 1인 가구 10만 증가 시 자살률 0.2 증가
            "노령화 지수": 0.15  # 노령화 지수 1 증가 시 자살률 0.15 증가
        }

        # 슬라이더 범위
        self.slider_ranges = {
            "기초연금 수급률": (0, 50),
            "복지시설 수": (0, 2000),
            "1인 가구 수": (0, 3000000),
            "노령화 지수": (0, 40)
        }

    def reset_simulation(self):
        # 현재 지역의 원래 값 저장
        self.original_values = self.data[self.current_region].copy()
        # 시뮬레이션 값 초기화
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

        self.region_var = tk.StringVar(value=self.current_region)
        region_combo = ttk.Combobox(
            region_frame,
            textvariable=self.region_var,
            values=self.regions,
            state="readonly",
            width=20,
            font=self.label_font
        )
        region_combo.pack(fill='x')
        region_combo.bind('<<ComboboxSelected>>', self.on_region_change)

        # 슬라이더 생성
        self.sliders = {}
        self.slider_values = {}
        self.slider_labels = {}

        factors = ["기초연금 수급률", "복지시설 수", "1인 가구 수", "노령화 지수"]

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

            # 슬라이더
            min_val, max_val = self.slider_ranges[factor]
            current_val = self.original_values[factor]

            slider = ttk.Scale(
                frame,
                from_=min_val,
                to=max_val,
                value=current_val,
                orient='horizontal'
            )
            slider.pack(fill='x')

            # 값 표시 라벨
            value_label = tk.Label(
                value_frame,
                text=f"{current_val:.1f}",
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

        # 버튼 영역
        button_frame = tk.Frame(inner_frame, bg='white')
        button_frame.pack(fill='x', pady=(10, 0))

        # 초기화 버튼만 남기고 적용 버튼 제거
        reset_button = tk.Button(
            button_frame,
            text="시뮬레이션 초기화",
            command=self.reset_and_update,
            font=self.label_font,
            bg='#f0f0f0',
            fg='#333333',
            relief='flat',
            cursor='hand2'
        )
        reset_button.pack(fill='x', ipady=8)

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
            text="예측 자살률",
            font=self.subtitle_font,
            bg='white',
            fg='#333333'
        )
        title_label.pack(pady=(0, 10))

        # 게이지 차트 (크기 축소)
        gauge_frame = tk.Frame(top_frame, bg='white')
        gauge_frame.pack(fill='x', pady=(0, 10))

        # matplotlib 설정
        plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 게이지 차트 크기 축소
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
            text=f"{self.national_avg:.1f}%",
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
            text=f"{self.original_values['자살률']:.1f}%",
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
            text=f"{self.simulated_values['자살률']:.1f}%",
            font=self.value_font,
            bg='white',
            fg='#333333',
            anchor='e'
        )
        self.after_value.pack(side='right')

        # 변화량 (시뮬레이션 후 값 옆에 표시)
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

        # 게이지 설정
        min_val = 0
        max_val = 40
        current_val = self.simulated_values['자살률']

        # 위험 수준 구간 설정
        low_threshold = 15
        medium_threshold = 25

        # 반원 각도 설정 (아래쪽이 열린 반원)
        start_angle = 0  # 오른쪽부터 시작
        end_angle = 180  # 왼쪽까지

        # 각 구간의 각도 계산
        low_angle = start_angle + (end_angle - start_angle) * (low_threshold / max_val)
        medium_angle = start_angle + (end_angle - start_angle) * (medium_threshold / max_val)

        # 게이지 배경 그리기
        angles = np.linspace(np.radians(start_angle), np.radians(end_angle), 100)

        # 초록색 구간 (0 ~ 15)
        green_angles = angles[angles <= np.radians(low_angle)]
        if len(green_angles) > 0:
            x_green = np.cos(green_angles)
            y_green = np.sin(green_angles)
            self.gauge_ax.plot(x_green, y_green, color='#4CAF50', linewidth=15, solid_capstyle='round')

        # 노란색 구간 (15 ~ 25)
        yellow_angles = angles[(angles > np.radians(low_angle)) & (angles <= np.radians(medium_angle))]
        if len(yellow_angles) > 0:
            x_yellow = np.cos(yellow_angles)
            y_yellow = np.sin(yellow_angles)
            self.gauge_ax.plot(x_yellow, y_yellow, color='#FFC107', linewidth=15, solid_capstyle='round')

        # 빨간색 구간 (25 ~ 40)
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

        # 축 설정
        self.gauge_ax.set_xlim(-1.2, 1.2)
        self.gauge_ax.set_ylim(-0.2, 1.2)
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
        if factor == "1인 가구 수":
            if value >= 1000000:
                display_value = f"{value / 10000:.0f}만"
            else:
                display_value = f"{value / 1000:.0f}천"
        else:
            display_value = f"{value:.1f}"

        self.slider_values[factor].config(text=display_value)

        # 변화율 계산 및 표시
        original = self.original_values[factor]
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
        # 자살률 계산
        base_suicide_rate = self.original_values["자살률"]
        new_suicide_rate = base_suicide_rate

        for factor, coef in self.coefficients.items():
            original = self.original_values[factor]
            current = self.simulated_values[factor]

            # 1인 가구 수는 10만 단위로 계산
            if factor == "1인 가구 수":
                change = (current - original) / 100000
            else:
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
            value = self.original_values[factor]
            slider.set(value)

            # 값 표시 업데이트
            if factor == "1인 가구 수":
                if value >= 1000000:
                    display_value = f"{value / 10000:.0f}만"
                else:
                    display_value = f"{value / 1000:.0f}천"
            else:
                display_value = f"{value:.1f}"

            self.slider_values[factor].config(text=display_value)
            self.slider_labels[factor].config(text="(0%)", fg="black")

        # 결과 UI 업데이트
        self.update_result_ui()

    def update_result_ui(self):
        # 자살률 값 업데이트 (% 단위로 변경)
        self.before_value.config(text=f"{self.original_values['자살률']:.1f}%")
        self.after_value.config(text=f"{self.simulated_values['자살률']:.1f}%")

        # 변화량 계산 및 표시 (% 단위로 변경)
        change = self.simulated_values['자살률'] - self.original_values['자살률']
        if change > 0:
            self.change_value.config(text=f"↑ ({change:.1f}%p)", fg="red")
        elif change < 0:
            self.change_value.config(text=f"↓ ({abs(change):.1f}%p)", fg="green")
        else:
            self.change_value.config(text="(0%p)", fg="black")

        # 게이지 업데이트
        self.update_gauge()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True)
    app = SimulationPage(frame)
    root.mainloop()