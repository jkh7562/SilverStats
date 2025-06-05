# 메인 대시보드

import tkinter as tk
import tkinter.font as tkFont
from regional_comparison import RegionalComparisonPage
from regional_analysis import RegionalAnalysisPage
from simulation import SimulationPage


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("노인 자살률 분석 시스템")
        self.root.geometry("1000x700")
        self.root.configure(bg='#E3F2FD')
        self.root.resizable(False, False)

        # 현재 페이지 추적
        self.current_page = None

        # Configure styles
        self.setup_styles()

        # Create navigation and content areas
        self.create_layout()

        # Show main page initially
        self.show_main_page()

    def setup_styles(self):
        self.title_font = tkFont.Font(family="맑은 고딕", size=18, weight="bold")
        self.card_font = tkFont.Font(family="맑은 고딕", size=12, weight="bold")
        self.nav_font = tkFont.Font(family="맑은 고딕", size=11, weight="bold")

    def create_layout(self):
        # 상단 네비게이션 바
        self.nav_frame = tk.Frame(self.root, bg='#1976D2', height=60)
        self.nav_frame.pack(fill='x')
        self.nav_frame.pack_propagate(False)

        # 네비게이션 버튼들
        nav_container = tk.Frame(self.nav_frame, bg='#1976D2')
        nav_container.pack(expand=True, fill='both')

        # 홈 버튼
        self.home_btn = tk.Button(
            nav_container,
            text="🏠 홈",
            font=self.nav_font,
            bg='#1976D2',
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=15,
            cursor='hand2',
            command=self.show_main_page
        )
        self.home_btn.pack(side='left', padx=10)

        # 뒤로가기 버튼
        self.back_btn = tk.Button(
            nav_container,
            text="← 뒤로가기",
            font=self.nav_font,
            bg='#1976D2',
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=15,
            cursor='hand2',
            command=self.show_main_page
        )
        self.back_btn.pack(side='left', padx=10)

        # 페이지 제목
        self.page_title = tk.Label(
            nav_container,
            text="노인 자살률 분석 시스템",
            font=self.title_font,
            bg='#1976D2',
            fg='white'
        )
        self.page_title.pack(side='left', padx=20)

        # 메인 컨텐츠 영역
        self.content_frame = tk.Frame(self.root, bg='#E3F2FD')
        self.content_frame.pack(fill='both', expand=True)

        # 네비게이션 버튼 호버 효과
        self.setup_nav_hover_effects()

    def setup_nav_hover_effects(self):
        for btn in [self.home_btn, self.back_btn]:
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg='#1565C0'))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg='#1976D2'))

    def clear_content(self):
        """현재 컨텐츠 프레임 내용 제거"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_main_page(self):
        """메인 페이지 표시"""
        self.clear_content()
        self.page_title.configure(text="노인 자살률 분석 시스템")
        self.current_page = "main"

        # 메인 페이지 컨텐츠
        main_container = tk.Frame(self.content_frame, bg='#E3F2FD')
        main_container.pack(expand=True, fill='both')

        # Cards frame
        cards_frame = tk.Frame(main_container, bg='#E3F2FD')
        cards_frame.pack(expand=True)

        # Create three cards
        self.create_card(cards_frame, "지표별 지역 비교", "📊", 0, self.show_regional_comparison)
        self.create_card(cards_frame, "지역 심층 분석", "🔍", 1, self.show_regional_analysis)
        self.create_card(cards_frame, "시뮬레이션", "📄", 2, self.show_simulation)

    def create_card(self, parent, title, icon, column, callback):
        # Card container
        card_container = tk.Frame(parent, bg='#E3F2FD')
        card_container.grid(row=0, column=column, padx=40, pady=20)

        # 카드 외부 프레임 (그림자 효과)
        shadow_frame = tk.Frame(
            card_container,
            bg='#D0D0D0',
            width=202,
            height=182
        )
        shadow_frame.pack()
        shadow_frame.pack_propagate(False)

        # 카드 메인 프레임
        card_frame = tk.Frame(
            card_container,
            bg='white',
            relief='flat',
            bd=0,
            width=200,
            height=180
        )
        card_frame.place(in_=shadow_frame, x=-2, y=-2)
        card_frame.pack_propagate(False)

        # Content container
        content_frame = tk.Frame(card_frame, bg='white')
        content_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Icon
        icon_label = tk.Label(
            content_frame,
            text=icon,
            font=tkFont.Font(size=40),
            bg='white',
            fg='#2196F3'
        )
        icon_label.pack(pady=(0, 15))

        # Title
        title_label = tk.Label(
            content_frame,
            text=title,
            font=self.card_font,
            bg='white',
            fg='#333333'
        )
        title_label.pack()

        # Make clickable
        for widget in [card_frame, content_frame, icon_label, title_label]:
            self.make_clickable(widget, callback, card_frame, content_frame, icon_label, title_label)

    def make_clickable(self, widget, callback, card_frame, content_frame, icon_label, title_label):
        def on_enter(event):
            widget.configure(cursor="hand2")
            card_frame.configure(bg='#F5F5F5')
            content_frame.configure(bg='#F5F5F5')
            icon_label.configure(bg='#F5F5F5')
            title_label.configure(bg='#F5F5F5')

        def on_leave(event):
            widget.configure(cursor="")
            card_frame.configure(bg='white')
            content_frame.configure(bg='white')
            icon_label.configure(bg='white')
            title_label.configure(bg='white')

        def on_click(event):
            callback()

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<Button-1>", on_click)

    def show_regional_comparison(self):
        """지표별 지역 비교 페이지 표시"""
        self.clear_content()
        self.page_title.configure(text="지표별 지역 비교")
        self.current_page = "comparison"

        # 페이지 인스턴스 생성 (부모를 content_frame으로)
        RegionalComparisonPage(self.content_frame)

    def show_regional_analysis(self):
        """지역 심층 분석 페이지 표시"""
        self.clear_content()
        self.page_title.configure(text="지역 심층 분석")
        self.current_page = "analysis"

        RegionalAnalysisPage(self.content_frame)

    def show_simulation(self):
        """시뮬레이션 페이지 표시"""
        self.clear_content()
        self.page_title.configure(text="정책 시뮬레이션")
        self.current_page = "simulation"

        SimulationPage(self.content_frame)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()