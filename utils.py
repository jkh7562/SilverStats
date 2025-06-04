import tkinter as tk
import tkinter.font as tkFont


def create_styled_frame(parent, bg='white', relief='flat', bd=1):
    """스타일이 적용된 프레임 생성"""
    frame = tk.Frame(parent, bg=bg, relief=relief, bd=bd)
    return frame


def create_styled_button(parent, text, command, bg='#2196F3', fg='white', width=None):
    """스타일이 적용된 버튼 생성"""
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        font=tkFont.Font(family="맑은 고딕", size=10, weight="bold"),
        relief='flat',
        bd=0,
        padx=20,
        pady=8,
        cursor='hand2'
    )

    if width:
        button.configure(width=width)

    # Hover effects
    def on_enter(event):
        button.configure(bg=lighten_color(bg, 0.1))

    def on_leave(event):
        button.configure(bg=bg)

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

    return button


def lighten_color(color, factor):
    """색상을 밝게 만드는 함수"""
    if color.startswith('#'):
        color = color[1:]

    # RGB 값 추출
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)

    # 밝기 조절
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))

    return f"#{r:02x}{g:02x}{b:02x}"


def create_styled_label(parent, text, font_size=10, font_weight="normal", bg='white', fg='black'):
    """스타일이 적용된 라벨 생성"""
    label = tk.Label(
        parent,
        text=text,
        font=tkFont.Font(family="맑은 고딕", size=font_size, weight=font_weight),
        bg=bg,
        fg=fg
    )
    return label


def show_info_dialog(title, message):
    """정보 다이얼로그 표시"""
    import tkinter.messagebox as msgbox
    msgbox.showinfo(title, message)


def show_error_dialog(title, message):
    """에러 다이얼로그 표시"""
    import tkinter.messagebox as msgbox
    msgbox.showerror(title, message)


def show_warning_dialog(title, message):
    """경고 다이얼로그 표시"""
    import tkinter.messagebox as msgbox
    msgbox.showwarning(title, message)