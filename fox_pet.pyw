# -*- coding: utf-8 -*-
"""橘子狐狐 - Windows transparent pixel desktop companion. Python 3.10+, stdlib only."""
import json
import math
import os
import random
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

try:
    import winsound
except ImportError:
    winsound = None

APP_NAME = '橘子狐狐'
CHROMA = '#ff00fe'
PIXEL = 4
SPRITE_W, SPRITE_H = 42, 35
WINDOW_W, WINDOW_H = 210, 205
SAVE_DIR = Path(os.getenv('APPDATA', str(Path.home()))) / 'OrangeFoxPet'
SAVE_FILE = SAVE_DIR / 'settings.json'
OUTFITS = ['無', '紅色圍巾', '藍色領結', '小花', '魔法帽']
DEFAULTS = {
    'affection': 15, 'outfit': '無', 'sound': True,
    'follow': False, 'always_on_top': True, 'study_minutes': 25,
    'break_minutes': 5, 'x': None, 'y': None
}


def clamp(v, low, high):
    return max(low, min(high, v))


def load_data():
    result = dict(DEFAULTS)
    try:
        data = json.loads(SAVE_FILE.read_text(encoding='utf-8'))
        if isinstance(data, dict):
            result.update({k: v for k, v in data.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    result['affection'] = clamp(int(result['affection']), 0, 100)
    if result['outfit'] not in OUTFITS:
        result['outfit'] = '無'
    return result


class PixelPainter:
    """Draw a low-resolution palette image to a Tk Canvas without third-party packages."""
    def __init__(self):
        self.pixels = {}

    def put(self, x, y, color):
        if 0 <= x < SPRITE_W and 0 <= y < SPRITE_H:
            self.pixels[(int(x), int(y))] = color

    def rect(self, x1, y1, x2, y2, color):
        for y in range(y1, y2):
            for x in range(x1, x2):
                self.put(x, y, color)

    def poly(self, vertices, color):
        min_x = max(0, math.floor(min(p[0] for p in vertices)))
        max_x = min(SPRITE_W, math.ceil(max(p[0] for p in vertices)))
        min_y = max(0, math.floor(min(p[1] for p in vertices)))
        max_y = min(SPRITE_H, math.ceil(max(p[1] for p in vertices)))
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                inside = False
                j = len(vertices) - 1
                for i in range(len(vertices)):
                    xi, yi = vertices[i]
                    xj, yj = vertices[j]
                    if ((yi > y + .5) != (yj > y + .5)) and (x + .5 < (xj - xi) * (y + .5 - yi) / (yj - yi) + xi):
                        inside = not inside
                    j = i
                if inside:
                    self.put(x, y, color)

    def render(self, canvas, frame_x, frame_y, mirror=False, scale=PIXEL):
        # Combine horizontal runs to reduce the number of Tk canvas objects.
        lines = {}
        for (x, y), color in self.pixels.items():
            xx = SPRITE_W - 1 - x if mirror else x
            lines.setdefault(y, []).append((xx, color))
        for y, entries in lines.items():
            entries.sort()
            start = old_x = entries[0][0]
            old_color = entries[0][1]
            for x, color in entries[1:] + [(SPRITE_W + 1, None)]:
                if x != old_x + 1 or color != old_color:
                    canvas.create_rectangle(frame_x + start * scale, frame_y + y * scale,
                                            frame_x + (old_x + 1) * scale, frame_y + (y + 1) * scale,
                                            fill=old_color, outline='', tags='art')
                    start, old_color = x, color
                old_x = x


def fox_sprite(action, frame, outfit, facing):
    p = PixelPainter()
    border, orange, bright, light, dark = '#713817', '#e98031', '#ffae51', '#fff0d5', '#4d2e2a'
    asleep = action == 'sleep'
    blink = frame % 25 == 0 or asleep
    hop = frame % 4 in (1, 2) if action in ('dance', 'happy') else False
    shift = -2 if hop else 0
    tail_swing = (frame // 3) % 3 - 1
    # Tail (body behind)
    p.poly([(16, 23 + shift), (9, 18 + tail_swing + shift),
            (3, 16 + tail_swing + shift), (1, 10 + tail_swing + shift),
            (8, 11 + shift), (14, 16 + shift), (19, 21 + shift)], border)
    p.poly([(15, 22 + shift), (9, 17 + tail_swing + shift),
            (4, 15 + tail_swing + shift), (3, 12 + tail_swing + shift),
            (9, 13 + shift), (16, 18 + shift)], orange)
    p.poly([(3, 12 + tail_swing + shift), (8, 12 + shift), (9, 17 + tail_swing + shift),
            (4, 15 + tail_swing + shift)], light)
    # Paws
    step = frame % 4 if action in ('walk', 'follow') else 0
    p.rect(15, 28 + shift + (1 if step == 1 else 0), 21, 33 + shift, border)
    p.rect(25, 28 + shift + (1 if step == 3 else 0), 31, 33 + shift, border)
    p.rect(16, 29 + shift, 20, 32 + shift, dark)
    p.rect(26, 29 + shift, 30, 32 + shift, dark)
    # Body
    p.poly([(13, 21 + shift), (19, 17 + shift), (28, 18 + shift),
            (33, 26 + shift), (31, 30 + shift), (14, 30 + shift), (11, 26 + shift)], border)
    p.poly([(14, 22 + shift), (19, 19 + shift), (28, 20 + shift),
            (31, 26 + shift), (29, 29 + shift), (15, 29 + shift), (13, 26 + shift)], orange)
    p.poly([(21, 23 + shift), (29, 23 + shift), (29, 29 + shift), (20, 29 + shift)], light)
    # Ears and face
    head_y = 4 + shift if not asleep else 9
    p.poly([(14, 12 + head_y), (14, 1 + head_y), (22, 7 + head_y)], border)
    p.poly([(27, 7 + head_y), (35, 1 + head_y), (35, 13 + head_y)], border)
    p.poly([(16, 10 + head_y), (16, 4 + head_y), (21, 9 + head_y)], '#ffb7a7')
    p.poly([(29, 9 + head_y), (33, 4 + head_y), (33, 10 + head_y)], '#ffb7a7')
    p.poly([(12, 14 + head_y), (17, 8 + head_y), (32, 8 + head_y),
            (37, 16 + head_y), (33, 24 + head_y), (17, 25 + head_y), (11, 20 + head_y)], border)
    p.poly([(14, 14 + head_y), (18, 10 + head_y), (31, 10 + head_y),
            (35, 16 + head_y), (32, 23 + head_y), (18, 23 + head_y), (13, 20 + head_y)], orange)
    p.rect(18, 11 + head_y, 30, 14 + head_y, bright)
    p.poly([(13, 18 + head_y), (19, 17 + head_y), (24, 20 + head_y),
            (30, 17 + head_y), (35, 18 + head_y), (32, 23 + head_y),
            (18, 23 + head_y)], light)
    if blink:
        p.rect(18, 16 + head_y, 22, 17 + head_y, dark)
        p.rect(28, 16 + head_y, 32, 17 + head_y, dark)
    else:
        p.rect(19, 15 + head_y, 21, 19 + head_y, dark)
        p.rect(29, 15 + head_y, 31, 19 + head_y, dark)
        p.put(19, 15 + head_y, '#ffffff')
        p.put(29, 15 + head_y, '#ffffff')
    p.rect(24, 20 + head_y, 27, 22 + head_y, dark)
    p.put(23, 23 + head_y, '#b85f61')
    p.put(28, 23 + head_y, '#b85f61')

    if outfit == '紅色圍巾':
        p.rect(18, 25 + shift, 30, 27 + shift, '#da4547')
        p.rect(27, 27 + shift, 30, 33 + shift, '#da4547')
        p.rect(28, 29 + shift, 29, 32 + shift, '#ffd2c5')
    elif outfit == '藍色領結':
        p.poly([(23, 26 + shift), (18, 23 + shift), (18, 28 + shift)], '#599cf1')
        p.poly([(25, 26 + shift), (30, 23 + shift), (30, 28 + shift)], '#599cf1')
        p.rect(23, 25 + shift, 26, 28 + shift, '#2965bc')
    elif outfit == '小花':
        for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
            p.rect(35 + dx, 10 + dy + shift, 37 + dx, 12 + dy + shift, '#f8b2d0')
        p.rect(35, 10 + shift, 37, 12 + shift, '#ffe079')
    elif outfit == '魔法帽':
        p.poly([(21, 12 + shift), (28, 0 + shift), (33, 12 + shift)], '#7661b4')
        p.rect(18, 12 + shift, 36, 14 + shift, '#50428a')
        p.rect(24, 9 + shift, 31, 11 + shift, '#f2ce66')
    return p


class FoxApp:
    def __init__(self):
        self.data = load_data()
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.configure(bg=CHROMA)
        self.root.overrideredirect(True)
        self.root.geometry(f'{WINDOW_W}x{WINDOW_H}+10+10')
        self.root.wm_attributes('-topmost', bool(self.data['always_on_top']))
        if sys.platform == 'win32':
            self.root.wm_attributes('-transparentcolor', CHROMA)
        else:
            # Program is designed for Windows. Alpha fallback for testing on other systems.
            self.root.wm_attributes('-alpha', .97)
        self.canvas = tk.Canvas(self.root, width=WINDOW_W, height=WINDOW_H,
                                bg=CHROMA, highlightthickness=0, bd=0, cursor='hand2')
        self.canvas.pack(fill='both', expand=True)
        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()
        pos_x = self.data.get('x')
        pos_y = self.data.get('y')
        self.x = clamp(int(pos_x) if isinstance(pos_x, (int, float)) else self.sw - WINDOW_W - 60,
                       0, max(0, self.sw - WINDOW_W))
        self.y = clamp(int(pos_y) if isinstance(pos_y, (int, float)) else self.sh - WINDOW_H - 60,
                       0, max(0, self.sh - WINDOW_H))
        self._place()
        self.mode = 'walk'
        self.direction = -1
        self.frame = 0
        self.mode_until = 0
        self.next_decision = time.monotonic() + 5
        self.last_interaction = time.monotonic()
        self.drag_data = None
        self.speech = ''
        self.speech_until = 0
        self.panel = None
        self.command_entry = None
        self.log_text = None
        self.study_running = False
        self.study_phase = '專注'
        self.study_remaining = int(self.data['study_minutes']) * 60
        self.timer_last = time.monotonic()
        self.running = True
        self.menu = tk.Menu(self.root, tearoff=0)
        self._bind_events()
        self._build_menu()
        self.say('嗨！我是橘子狐狐 ♡', 3)
        self.root.after(160, self._tick)
        self.root.after(1000, self._timer_tick)
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def _place(self):
        self.root.geometry(f'{WINDOW_W}x{WINDOW_H}+{self.x}+{self.y}')

    def _bind_events(self):
        self.canvas.bind('<ButtonPress-1>', self._down)
        self.canvas.bind('<B1-Motion>', self._drag)
        self.canvas.bind('<ButtonRelease-1>', self._up)
        self.canvas.bind('<Double-Button-1>', lambda e: self.open_panel())
        self.canvas.bind('<Button-3>', self._show_menu)
        self.root.bind('<Escape>', lambda e: self.close() if self.panel is None else None)

    def _build_menu(self):
        self.menu.delete(0, 'end')
        for label, callback in [
            ('🍎 餵食', self.feed), ('♡ 摸摸', self.pet), ('💤 睡覺', self.sleep),
            ('♪ 跳舞', self.dance), ('📚 讀書／指令面板', self.open_panel)]:
            self.menu.add_command(label=label, command=callback)
        outfit_menu = tk.Menu(self.menu, tearoff=0)
        for name in OUTFITS:
            outfit_menu.add_command(label=name, command=lambda n=name: self.set_outfit(n))
        self.menu.add_cascade(label='🎀 換裝', menu=outfit_menu)
        self.menu.add_separator()
        self.menu.add_command(label='🔈 音效：' + ('開' if self.data['sound'] else '關'),
                              command=self.toggle_sound)
        self.menu.add_command(label='🐾 跟隨滑鼠：' + ('開' if self.data['follow'] else '關'),
                              command=self.toggle_follow)
        self.menu.add_command(label='📌 視窗置頂：' + ('開' if self.data['always_on_top'] else '關'),
                              command=self.toggle_topmost)
        self.menu.add_separator()
        self.menu.add_command(label='✕ 正常結束', command=self.close)

    def _show_menu(self, event):
        self._build_menu()
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _down(self, event):
        self.drag_data = (event.x_root, event.y_root, self.x, self.y, False)

    def _drag(self, event):
        if not self.drag_data:
            return
        mx, my, ox, oy, _ = self.drag_data
        if abs(event.x_root - mx) + abs(event.y_root - my) > 8:
            self.drag_data = (mx, my, ox, oy, True)
            self.x = clamp(ox + event.x_root - mx, 0, max(0, self.sw - WINDOW_W))
            self.y = clamp(oy + event.y_root - my, 0, max(0, self.sh - WINDOW_H))
            self._place()
            self.mode = 'happy'
            self.mode_until = time.monotonic() + .5

    def _up(self, event):
        if self.drag_data and not self.drag_data[4]:
            self.pet()
        self.drag_data = None
        self.save()

    def say(self, words, seconds=3):
        self.speech = words
        self.speech_until = time.monotonic() + seconds

    def sound(self):
        if self.data['sound'] and winsound:
            try:
                winsound.PlaySound('SystemAsterisk', winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            except RuntimeError:
                pass

    def action(self, mode, duration=2):
        self.mode = mode
        self.mode_until = time.monotonic() + duration
        self.last_interaction = time.monotonic()

    def gain(self, amount):
        before = self.data['affection']
        self.data['affection'] = clamp(before + amount, 0, 100)
        self.save()
        self.refresh_panel()

    def pet(self):
        self.action('happy', 1.9)
        self.gain(2)
        self.say(random.choice(['好舒服～♡', '嘿嘿！', '最喜歡摸摸了！', '嗷嗚～']), 2)
        self.sound()

    def feed(self):
        self.action('eat', 3)
        self.gain(5)
        self.say('蘋果好好吃！🍎  +5 ♡', 3)
        self.sound()

    def sleep(self):
        self.action('sleep', 18)
        self.say('Zzz…晚安', 3)

    def dance(self):
        self.action('dance', 5)
        self.say('狐狸跳跳舞 ♪', 3)
        self.sound()

    def set_outfit(self, name):
        if name in OUTFITS:
            if self.data['outfit'] == name:
                return
            self.data['outfit'] = name
            self.action('happy', 2)
            self.say('換好衣服啦！', 2)
            self.save()
            self.refresh_panel()

    def toggle_sound(self):
        self.data['sound'] = not self.data['sound']
        self.save()
        self.refresh_panel()

    def toggle_follow(self):
        self.data['follow'] = not self.data['follow']
        self.say('我要跟著你！' if self.data['follow'] else '我自己去散步～')
        self.save()
        self.refresh_panel()

    def toggle_topmost(self):
        self.data['always_on_top'] = not self.data['always_on_top']
        self.root.wm_attributes('-topmost', self.data['always_on_top'])
        self.save()
        self.refresh_panel()

    def _tick(self):
        if not self.running:
            return
        now = time.monotonic()
        self.frame += 1
        if not self.drag_data and self.mode_until < now:
            if now - self.last_interaction > 55:
                self.mode = 'sleep'
                self.mode_until = now + random.randint(10, 20)
                self.last_interaction = now - 15
            elif self.data['follow']:
                mx, my = self.root.winfo_pointerxy()
                # Follow only horizontally. Do not cover the mouse pointer or change the user's screen position vertically.
                target_x = clamp(mx - WINDOW_W // 2, 0, max(0, self.sw - WINDOW_W))
                dist = target_x - self.x
                if abs(dist) > 90:
                    self.direction = 1 if dist > 0 else -1
                    self.x += self.direction * min(5, abs(dist))
                    self.mode = 'follow'
                else:
                    self.mode = 'idle'
            else:
                if now >= self.next_decision:
                    self.next_decision = now + random.uniform(3, 8)
                    self.mode = random.choices(['walk', 'idle', 'happy'], [6, 3, 1])[0]
                    self.direction = random.choice([-1, 1])
                if self.mode == 'walk':
                    self.x += self.direction * 3
                    if self.x <= 0 or self.x >= self.sw - WINDOW_W:
                        self.direction *= -1
                    self.x = clamp(self.x, 0, max(0, self.sw - WINDOW_W))
            self._place()
        self._draw()
        self.root.after(160, self._tick)

    def _draw(self):
        c = self.canvas
        c.delete('all')
        # The chroma-key canvas will be fully transparent on Windows.
        if time.monotonic() < self.speech_until:
            c.create_rectangle(7, 1, 202, 34, fill='#fff8ed', outline='#965d3e', width=2)
            c.create_text(104, 17, text=self.speech, fill='#794831', font=('Microsoft JhengHei UI', 10, 'bold'), width=185)
        sx, sy = 19, 44
        sprite = fox_sprite(self.mode, self.frame, self.data['outfit'], self.direction < 0)
        sprite.render(c, sx, sy)
        if self.mode == 'eat':
            c.create_oval(155, 140, 177, 162, fill='#e44e54', outline='#9b323d', width=2)
            c.create_rectangle(164, 133, 168, 140, fill='#7d6134', outline='')
            c.create_oval(167, 134, 176, 139, fill='#4c9a66', outline='')
        if self.mode == 'sleep':
            c.create_text(176, 79, text='Zzz', font=('Segoe UI', 15, 'bold'), fill='#7a69b7')
        elif self.mode in ('happy', 'dance'):
            c.create_text(184, 86, text='♥', font=('Segoe UI Symbol', 17), fill='#ea748a')
        c.create_text(105, 190, text=f'♡ {self.data["affection"]}/100',
                      font=('Segoe UI', 10, 'bold'), fill='#c96b7d')

    def _timer_tick(self):
        if not self.running:
            return
        now = time.monotonic()
        elapsed = max(0, int(now - self.timer_last))
        self.timer_last = now
        if self.study_running and elapsed:
            self.study_remaining = max(0, self.study_remaining - elapsed)
            if self.study_remaining == 0:
                if self.study_phase == '專注':
                    self.study_phase = '休息'
                    self.study_remaining = int(self.data['break_minutes']) * 60
                    self.say('讀書完成！起來休息吧 ♡', 7)
                    self.action('dance', 7)
                else:
                    self.study_phase = '專注'
                    self.study_remaining = int(self.data['study_minutes']) * 60
                    self.say('休息結束～繼續加油！', 7)
                    self.action('happy', 7)
                self.sound()
                self.refresh_panel()
        self.refresh_timer_label()
        self.root.after(1000, self._timer_tick)

    def start_study(self):
        self.study_running = True
        self.timer_last = time.monotonic()
        self.say('專心讀書！我陪你 📚', 3)
        self.refresh_timer_label()

    def pause_study(self):
        self.study_running = False
        self.say('暫停計時～', 2)
        self.refresh_timer_label()

    def reset_study(self):
        self.study_running = False
        self.study_phase = '專注'
        self.study_remaining = int(self.data['study_minutes']) * 60
        self.refresh_timer_label()

    def change_study_length(self):
        if self.panel is None:
            return
        try:
            study = int(self.study_var.get())
            rest = int(self.break_var.get())
            if not (1 <= study <= 180 and 1 <= rest <= 60):
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showwarning('時間設定', '專注請設 1～180 分鐘，休息請設 1～60 分鐘。', parent=self.panel)
            return
        self.data['study_minutes'] = study
        self.data['break_minutes'] = rest
        self.save()
        self.reset_study()
        self.say('新時間設定完成！', 3)

    def save(self):
        try:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            data = dict(self.data)
            data['x'], data['y'] = self.x, self.y
            tmp = SAVE_FILE.with_suffix('.tmp')
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            os.replace(tmp, SAVE_FILE)
        except OSError:
            pass

    def execute_command(self, command):
        cmd = command.strip().lower()
        if not cmd:
            return
        routes = {
            '/help': self.help_text, '/pet': self.pet, '/feed': self.feed,
            '/sleep': self.sleep, '/dance': self.dance,
            '/follow': self.toggle_follow, '/sound': self.toggle_sound,
            '/study': self.start_study, '/pause': self.pause_study,
            '/reset': self.reset_study, '/quit': self.close,
        }
        if cmd in routes:
            result = routes[cmd]()
            if result and self.log_text:
                self._log(result)
            else:
                self._log('已執行：' + cmd)
        elif cmd.startswith('/wear '):
            choice = command.strip()[6:].strip()
            if choice in OUTFITS:
                self.set_outfit(choice)
                self._log('已換裝：' + choice)
            else:
                self._log('找不到服裝，輸入 /help 查看名稱')
        elif cmd == '/status':
            self._log(f'好感度：{self.data["affection"]}/100｜服裝：{self.data["outfit"]}｜跟隨：{self.data["follow"]}')
        else:
            self._log('不知道這個指令～輸入 /help 查看指令。')
        if self.command_entry and self.command_entry.winfo_exists():
            self.command_entry.delete(0, 'end')

    def help_text(self):
        return ('/pet 摸摸  /feed 餵食  /sleep 睡覺  /dance 跳舞\n'
                '/follow 切換追滑鼠  /sound 切換音效\n'
                '/study 開始計時  /pause 暫停  /reset 重置\n'
                '/wear 紅色圍巾  （也可以選其他服裝）\n'
                '/status 查看狀態  /quit 離開  /help 指令說明')

    def _log(self, msg):
        if self.panel and self.log_text and self.log_text.winfo_exists():
            self.log_text.configure(state='normal')
            self.log_text.insert('end', msg + '\n')
            self.log_text.see('end')
            self.log_text.configure(state='disabled')

    def open_panel(self):
        if self.panel and self.panel.winfo_exists():
            self.panel.deiconify()
            self.panel.lift()
            return
        p = tk.Toplevel(self.root)
        self.panel = p
        p.title('🦊 橘子狐狐｜控制中心')
        p.geometry('425x610')
        p.minsize(400, 590)
        p.configure(bg='#fff8ed')
        p.attributes('-topmost', False)
        p.protocol('WM_DELETE_WINDOW', self.hide_panel)
        style = ttk.Style(p)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('Fox.TButton', font=('Microsoft JhengHei UI', 10), padding=7)
        style.configure('Fox.TLabel', background='#fff8ed', foreground='#704c3a', font=('Microsoft JhengHei UI', 10))
        wrapper = tk.Frame(p, bg='#fff8ed', padx=16, pady=12)
        wrapper.pack(fill='both', expand=True)
        tk.Label(wrapper, text='🦊  橘子狐狐', bg='#fff8ed', fg='#b65d29',
                 font=('Microsoft JhengHei UI', 18, 'bold')).pack(anchor='w')
        self.affection_label = tk.Label(wrapper, bg='#fff8ed', fg='#a45e79', font=('Microsoft JhengHei UI', 11, 'bold'))
        self.affection_label.pack(anchor='w', pady=(2, 8))
        buttons = tk.Frame(wrapper, bg='#fff8ed')
        buttons.pack(fill='x')
        for i, (label, fun) in enumerate([('♡ 摸摸', self.pet), ('🍎 餵食', self.feed),
                                           ('💤 睡覺', self.sleep), ('♪ 跳舞', self.dance)]):
            ttk.Button(buttons, text=label, command=fun, style='Fox.TButton').grid(row=0, column=i, padx=2, sticky='ew')
            buttons.grid_columnconfigure(i, weight=1)
        tk.Label(wrapper, text='🎀 服裝', bg='#fff8ed', fg='#704c3a', font=('Microsoft JhengHei UI', 10, 'bold')).pack(anchor='w', pady=(14, 2))
        self.outfit_var = tk.StringVar(value=self.data['outfit'])
        ttk.Combobox(wrapper, values=OUTFITS, textvariable=self.outfit_var, state='readonly').pack(fill='x')
        self.outfit_var.trace_add('write', lambda *_: self.set_outfit(self.outfit_var.get()))
        toggles = tk.Frame(wrapper, bg='#fff8ed')
        toggles.pack(fill='x', pady=8)
        self.sound_var = tk.BooleanVar(value=self.data['sound'])
        self.follow_var = tk.BooleanVar(value=self.data['follow'])
        ttk.Checkbutton(toggles, text='音效', variable=self.sound_var, command=self.toggle_sound).pack(side='left', padx=(0, 14))
        ttk.Checkbutton(toggles, text='跟隨滑鼠', variable=self.follow_var, command=self.toggle_follow).pack(side='left')
        sep = ttk.Separator(wrapper)
        sep.pack(fill='x', pady=(8, 12))
        tk.Label(wrapper, text='📚 讀書提醒（番茄鐘）', bg='#fff8ed', fg='#704c3a',
                 font=('Microsoft JhengHei UI', 11, 'bold')).pack(anchor='w')
        self.timer_label = tk.Label(wrapper, text='', bg='#fff8ed', fg='#ad632f', font=('Consolas', 24, 'bold'))
        self.timer_label.pack(pady=(1, 5))
        timebox = tk.Frame(wrapper, bg='#fff8ed')
        timebox.pack()
        self.study_var = tk.StringVar(value=str(self.data['study_minutes']))
        self.break_var = tk.StringVar(value=str(self.data['break_minutes']))
        tk.Label(timebox, text='專注 (分)', bg='#fff8ed').pack(side='left')
        ttk.Entry(timebox, width=5, textvariable=self.study_var).pack(side='left', padx=4)
        tk.Label(timebox, text='休息 (分)', bg='#fff8ed').pack(side='left', padx=(8, 0))
        ttk.Entry(timebox, width=5, textvariable=self.break_var).pack(side='left', padx=4)
        ttk.Button(timebox, text='套用', command=self.change_study_length).pack(side='left', padx=4)
        tbuttons = tk.Frame(wrapper, bg='#fff8ed')
        tbuttons.pack(pady=5)
        for label, fun in [('▶ 開始', self.start_study), ('Ⅱ 暫停', self.pause_study), ('↺ 重置', self.reset_study)]:
            ttk.Button(tbuttons, text=label, command=fun).pack(side='left', padx=4)
        ttk.Separator(wrapper).pack(fill='x', pady=(8, 9))
        tk.Label(wrapper, text='⌨ 指令輸入', bg='#fff8ed', fg='#704c3a',
                 font=('Microsoft JhengHei UI', 11, 'bold')).pack(anchor='w')
        entrybox = tk.Frame(wrapper, bg='#fff8ed')
        entrybox.pack(fill='x', pady=5)
        self.command_entry = ttk.Entry(entrybox)
        self.command_entry.pack(side='left', fill='x', expand=True, padx=(0, 7))
        self.command_entry.bind('<Return>', lambda e: self.execute_command(self.command_entry.get()))
        ttk.Button(entrybox, text='送出', command=lambda: self.execute_command(self.command_entry.get())).pack(side='right')
        self.log_text = tk.Text(wrapper, height=5, font=('Microsoft JhengHei UI', 9),
                                bg='#fffdf8', fg='#77533d', relief='solid', bd=1, wrap='word')
        self.log_text.pack(fill='both', expand=True, pady=3)
        self._log('歡迎來到狐狸小窩！輸入 /help 查看指令。')
        ttk.Button(wrapper, text='✕ 結束小狐狸程式', command=self.close).pack(fill='x', pady=(5, 0))
        self.refresh_panel()
        self.refresh_timer_label()

    def refresh_panel(self):
        if self.panel and self.panel.winfo_exists():
            self.affection_label.config(text=f'♡ 好感度：{self.data["affection"]}/100')
            self.sound_var.set(self.data['sound'])
            self.follow_var.set(self.data['follow'])
            if self.outfit_var.get() != self.data['outfit']:
                self.outfit_var.set(self.data['outfit'])

    def refresh_timer_label(self):
        if self.panel and self.panel.winfo_exists():
            m, s = divmod(self.study_remaining, 60)
            state = '進行中' if self.study_running else '暫停'
            self.timer_label.config(text=f'{self.study_phase}  {m:02}:{s:02}  {state}')

    def hide_panel(self):
        if self.panel and self.panel.winfo_exists():
            self.panel.destroy()
        self.panel = None
        self.command_entry = None
        self.log_text = None

    def close(self):
        if not self.running:
            return
        self.running = False
        self.save()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    FoxApp().run()
