from distutils.command.upload import upload

import pygame
import time
import numpy as np
import soundfile as sf
import tkinter as tk
from tkinter import filedialog
from scipy.signal import butter, sosfilt
from blackboard import parse_midi, generate_audio
import os


pygame.init()
pygame.mixer.init()


file_browser_active = False
current_dir = os.path.dirname(os.path.abspath(__file__))

file_browser_scroll = 0

# Color settings
DARK_BG = (30, 30, 30)
LIGHT_GRID = (70, 70, 70)
HIGHLIGHT_RGBA = (100, 180, 255, 100)
ACTIVE_CELL = (255, 140, 0)
BUTTON_TEXT = (240, 240, 240)
BUTTON_PLAY = (76, 175, 80)
BUTTON_STOP = (244, 67, 54)
BUTTON_CLEAR = (255, 87, 34)
BUTTON_UPLOAD = (0, 188, 212)
BUTTON_DOWNLOAD = (255, 235, 59)
BUTTON_STYLE = (120, 120, 120)
BUTTON_SELECTED = (220, 220, 100)

# Window and grid settings
WIDTH, HEIGHT = 1500, 1000
GRID_ROWS = 16
INITIAL_GRID_COLS = 16
CELL_SIZE = 40
FIXED_COL_X_RATIO = 0.1

background_image = pygame.image.load("background.png")
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("PixelTone - 8-bit Music Sequencer")
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
title_font = pygame.font.Font(None, 48)

is_playing = False
bps = 2
playbar_x = None
playbar_interval = 1 / bps
last_update_time = time.time()
is_generated_audio_playing = False


SLIDER_MIN_COLUMNS = 4
SLIDER_MAX_COLUMNS = 32
slider_columns = INITIAL_GRID_COLS

SLIDER_MIN_BPS = 1
SLIDER_MAX_BPS = 10
slider_bps = bps

grid = [[0 for _ in range(INITIAL_GRID_COLS)] for _ in range(GRID_ROWS)]

FREQUENCIES = [523, 494, 466, 440, 392, 349, 330, 294, 262, 247, 220, 196, 175, 165, 147, 131]

SOUND_STYLES = ["Default", "GameBoy", "NES"]
current_sound_style = "NES"
style_buttons = [pygame.Rect(15, 320 + i * 50, 120, 40) for i in range(len(SOUND_STYLES))]


def safe_file_dialog(func, *args, **kwargs):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    result = func(*args, **kwargs)
    root.destroy()
    return result


def generate_default_square_wave(freq, duration=0.3, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.5 * (1 + np.sign(np.sin(2 * np.pi * freq * t)))
    return pygame.mixer.Sound(buffer=(wave * 32767).astype(np.int16).tobytes())

def generate_gameboy_wave(freq, duration=0.3, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.5 * (1 + np.sign(np.sin(2 * np.pi * freq * t)))
    envelope = np.exp(-5 * t)
    wave *= envelope
    return pygame.mixer.Sound(buffer=(wave * 32767).astype(np.int16).tobytes())

def generate_nes_triangle_wave(freq, duration=0.3, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 2 * np.abs(2 * ((freq * t) % 1) - 1) - 1
    envelope = np.exp(-5 * t)
    wave *= envelope
    return pygame.mixer.Sound(buffer=(wave * 32767).astype(np.int16).tobytes())

def regenerate_sounds():
    global SOUNDS
    if current_sound_style == "Default":
        SOUNDS = [generate_default_square_wave(f) for f in FREQUENCIES]
    elif current_sound_style == "GameBoy":
        SOUNDS = [generate_gameboy_wave(f) for f in FREQUENCIES]
    elif current_sound_style == "NES":
        SOUNDS = [generate_nes_triangle_wave(f) for f in FREQUENCIES]

regenerate_sounds()

def handle_style_selection(pos):
    global current_sound_style
    for i, rect in enumerate(style_buttons):
        if rect.collidepoint(pos):
            current_sound_style = SOUND_STYLES[i]
            regenerate_sounds()
            update_status(f"Switched to {current_sound_style} style")
            return True
    return False


def update_grid_size(new_cols):
    global grid
    for r in range(GRID_ROWS):
        grid[r] = grid[r][:new_cols] + [0] * max(0, new_cols - len(grid[r]))

def get_fixed_col_x():
    return int(WIDTH * FIXED_COL_X_RATIO)

status_message = "Waiting for user action..."
status_last_update = 0
status_reset_delay = 0

def update_status(new_status, reset_after_seconds=None):
    global status_message, status_last_update, status_reset_delay
    status_message = new_status
    status_last_update = time.time()
    status_reset_delay = reset_after_seconds if reset_after_seconds else 0

def show_status_now(message):
    update_status(message)
    draw_controls()
    pygame.display.flip()
    pygame.time.wait(300)

play_button = pygame.Rect(50, HEIGHT - 80, 100, 50)
stop_button = pygame.Rect(170, HEIGHT - 80, 100, 50)
clear_button = pygame.Rect(290, HEIGHT - 80, 100, 50)

slider_columns_box = pygame.Rect(490, HEIGHT - 80, 300, 10)
slider_bps_box = pygame.Rect(480, HEIGHT - 40, 300, 10)


button_w = 100
button_h = 50
gap = 20
x_base = 1000
play_generated_button = pygame.Rect(x_base + 0 * (button_w + gap), HEIGHT - 80, button_w, button_h)
cancel_generated_button = pygame.Rect(x_base + 1 * (button_w + gap), HEIGHT - 80, button_w, button_h)
upload_button = pygame.Rect(x_base + 2 * (button_w + gap), HEIGHT - 80, button_w, button_h)
download_button = pygame.Rect(x_base + 3 * (button_w + gap), HEIGHT - 80, button_w, button_h)

slider_columns_box = pygame.Rect(470, HEIGHT - 80, 300, 10)
slider_bps_box = pygame.Rect(470, HEIGHT - 40, 300, 10)
upload_button = pygame.Rect(1150, HEIGHT - 80, 130, 50)
download_button = pygame.Rect(1300, HEIGHT - 80, 150, 50)
play_generated_button = pygame.Rect(1050, HEIGHT - 80, 80, 50)
uploaded_midi = None
generated_audio = None
dragging_slider = None

def draw_grid(play_col=None):
    fixed_col_x = get_fixed_col_x()
    top_offset = (HEIGHT - GRID_ROWS * CELL_SIZE - 160) // 2

    title_text = title_font.render("PixelTone - 8-bit Music Sequencer", True, (225, 225, 225))
    screen.blit(title_text, (fixed_col_x, top_offset - 60))

    grid_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    if play_col is not None and play_col >= 0:
        for row in range(GRID_ROWS):
            x = fixed_col_x + play_col * CELL_SIZE
            y = top_offset + row * CELL_SIZE
            pygame.draw.rect(grid_surface, HIGHLIGHT_RGBA, (x, y, CELL_SIZE, CELL_SIZE))

    for row in range(GRID_ROWS):
        for col in range(slider_columns):
            x = fixed_col_x + col * CELL_SIZE
            y = top_offset + row * CELL_SIZE
            cell_color = DARK_BG if not grid[row][col] else ACTIVE_CELL
            pygame.draw.rect(screen, cell_color, (x, y, CELL_SIZE, CELL_SIZE), border_radius=4)
            pygame.draw.rect(screen, LIGHT_GRID, (x, y, CELL_SIZE, CELL_SIZE), 1)

    screen.blit(grid_surface, (0, 0))

def draw_button(rect, text, bg_color, text_color=BUTTON_TEXT, enabled=True):
    if not enabled:
        bg_color = (100, 100, 100)
        text_color = (180, 180, 180)
    color = tuple(min(255, c + 30) for c in bg_color) if rect.collidepoint(pygame.mouse.get_pos()) and enabled else bg_color
    pygame.draw.rect(screen, color, rect, border_radius=10)
    label = font.render(text, True, text_color)
    screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

def draw_slider(x, y, width, value, min_val, max_val, label):
    pygame.draw.rect(screen, LIGHT_GRID, (x, y, width, 10), border_radius=5)
    knob_x = int(x + (value - min_val) / (max_val - min_val) * width)
    pygame.draw.circle(screen, HIGHLIGHT_RGBA[:3], (knob_x, y + 5), 8)
    label_surf = font.render(f"{label}: {value}", True, BUTTON_TEXT)
    screen.blit(label_surf, (x + width + 20, y - 10))

def draw_file_browser():
    global current_dir, file_browser_scroll
    pygame.draw.rect(screen, (30, 30, 30), (100, 100, WIDTH - 200, HEIGHT - 200))
    pygame.draw.rect(screen, (255, 255, 255), (100, 100, WIDTH - 200, HEIGHT - 200), 2)

    title = font.render("Select a MIDI File", True, (255, 255, 255))
    screen.blit(title, (120, 110))
    path_surf = small_font.render(current_dir, True, (200, 200, 200))
    screen.blit(path_surf, (120, 150))

    try:
        all_items = ["../"] + sorted(os.listdir(current_dir))
        items = []
        for item in all_items:
            full_path = os.path.abspath(os.path.join(current_dir, item))
            if os.access(full_path, os.R_OK):
                items.append(item)
    except PermissionError:
        items = ["../"]

    visible_items = items[file_browser_scroll:file_browser_scroll + 20]
    mouse_x, mouse_y = pygame.mouse.get_pos()

    for i, item in enumerate(visible_items):
        full_path = os.path.abspath(os.path.join(current_dir, item))
        y = 180 + i * 30
        if 120 <= mouse_x <= WIDTH - 100 and y <= mouse_y <= y + 30:
            pygame.draw.rect(screen, (80, 80, 80), (120, y, WIDTH - 240, 30))

        if item == "../":
            color = (255, 255, 150)
            label = "[../] (Up)"
        elif os.path.isdir(full_path):
            color = (255, 215, 0)
            label = f"[{item}]"
        elif item.endswith(".mid"):
            color = (150, 255, 150)
            label = item
        else:
            color = (120, 120, 120)
            label = item

        text = small_font.render(label, True, color)
        screen.blit(text, (130, y + 5))


def draw_controls():
    pygame.draw.rect(screen, (20, 20, 20), pygame.Rect(0, HEIGHT - 140, WIDTH, 160))
    draw_button(play_button, "Play", BUTTON_PLAY)
    draw_button(stop_button, "Stop", BUTTON_STOP)
    draw_button(clear_button, "Clear", BUTTON_CLEAR)
    if is_generated_audio_playing:
        draw_button(cancel_generated_button, "Cancel", BUTTON_STOP, enabled=True)
        draw_button(play_generated_button, "Play", BUTTON_PLAY, enabled=False)
        draw_button(upload_button, "Upload", BUTTON_UPLOAD, enabled=False)
        draw_button(download_button, "Save", BUTTON_DOWNLOAD, text_color=(200, 200, 200), enabled=False)
    else:
        draw_button(play_generated_button, "Play", BUTTON_PLAY)
        draw_button(upload_button, "Upload", BUTTON_UPLOAD)
        draw_button(download_button, "Save", BUTTON_DOWNLOAD, text_color=(20, 20, 20))
        draw_button(cancel_generated_button, "Cancel", BUTTON_STOP, enabled=False)

    draw_slider(490, HEIGHT - 80, 300, slider_columns, SLIDER_MIN_COLUMNS, SLIDER_MAX_COLUMNS, "Columns")
    draw_slider(490, HEIGHT - 40, 300, slider_bps, SLIDER_MIN_BPS, SLIDER_MAX_BPS, "BPS")

    status_text = small_font.render(status_message, True, BUTTON_TEXT)
    status_x = play_generated_button.x + 10
    status_y = play_generated_button.y - 25
    screen.blit(status_text, (status_x, status_y))

    for i, rect in enumerate(style_buttons):
        style = SOUND_STYLES[i]
        pygame.draw.rect(screen, BUTTON_SELECTED if style == current_sound_style else BUTTON_STYLE, rect, border_radius=6)
        label = small_font.render(style, True, BUTTON_TEXT)
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    
        

    draw_slider(490, HEIGHT - 80, 300, slider_columns, SLIDER_MIN_COLUMNS, SLIDER_MAX_COLUMNS, "Columns")
    draw_slider(490, HEIGHT - 40, 300, slider_bps, SLIDER_MIN_BPS, SLIDER_MAX_BPS, "BPS")

    draw_button(upload_button, "Upload", BUTTON_UPLOAD)
    draw_button(download_button, "Download", BUTTON_DOWNLOAD, text_color=(20, 20, 20))
    draw_button(play_generated_button, "play", BUTTON_PLAY)

    draw_slider(470, HEIGHT - 80, 300, slider_columns, SLIDER_MIN_COLUMNS, SLIDER_MAX_COLUMNS, "Columns")
    draw_slider(470, HEIGHT - 40, 300, slider_bps, SLIDER_MIN_BPS, SLIDER_MAX_BPS, "BPS")
    status_text = small_font.render(status_message, True, BUTTON_TEXT)
    status_x = play_generated_button.x + 10
    status_y = play_generated_button.y - 25
    screen.blit(status_text, (status_x, status_y))


    for i, rect in enumerate(style_buttons):
        style = SOUND_STYLES[i]
        pygame.draw.rect(screen, BUTTON_SELECTED if style == current_sound_style else BUTTON_STYLE, rect, border_radius=6)
        label = small_font.render(style, True, BUTTON_TEXT)
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

        
def upload_midi():
    global file_browser_active
    file_browser_active = True




def download_audio():
    global current_dir, uploaded_midi,generated_audio

    if generated_audio is not None and uploaded_midi is not None:

        filename = os.path.splitext(os.path.basename(uploaded_midi))[0]
        save_path = os.path.join(current_dir, f"{filename}_converted.wav")

        try:
            sf.write(save_path, generated_audio, samplerate=44100)
            update_status(f"Saved to {filename}_converted.wav", reset_after_seconds=6)
        except Exception as e:
            update_status(f"Save failed: {e}", reset_after_seconds=6)
    else:
        update_status("No audio to save.", reset_after_seconds=4)


def play_column(col):
    for row in range(GRID_ROWS):
        if col < len(grid[row]) and grid[row][col] == 1:
            SOUNDS[row].play()


def handle_mouse_click(pos):
    global is_playing, playbar_x, slider_columns, slider_bps, grid, bps, playbar_interval, dragging_slider, last_update_time, current_sound_style, generated_audio, uploaded_mid, is_generated_audio_playing 
    global is_playing, playbar_x, slider_columns, slider_bps, grid, bps, playbar_interval, dragging_slider, last_update_time, current_sound_style,generated_audio
    x, y = pos

    if pygame.mixer.get_busy() and (
        play_generated_button.collidepoint(x, y) or
        upload_button.collidepoint(x, y) or
        download_button.collidepoint(x, y)
    ):
        return

    if cancel_generated_button.collidepoint(x, y) and pygame.mixer.get_busy():
        pygame.mixer.stop()
        is_generated_audio_playing = False
        update_status("Playback stopped", reset_after_seconds=4)
        return

    if handle_style_selection(pos):
        return
            
    if play_generated_button.collidepoint(x, y):
        try:
            if generated_audio is not None:
                mono = (generated_audio * 32767).astype(np.int16)

                stereo = np.stack([mono, mono], axis=1)
                sound = pygame.sndarray.make_sound(stereo)
                sound.play()
                is_generated_audio_playing = True

                stereo = np.stack([mono, mono], axis=1)  # shape: (samples, 2)
                sound = pygame.sndarray.make_sound(stereo)
                sound.play()

                update_status("Playing generated audio", reset_after_seconds=5)
            else:
                update_status("No generated audio to play", reset_after_seconds=4)
        except Exception as e:
            update_status(f"Play error: {e}", reset_after_seconds=4)

    elif play_button.collidepoint(x, y):
        if playbar_x is None:
            playbar_x = get_fixed_col_x()
            last_update_time = time.time()
            play_column(0)
        is_playing = True

    elif stop_button.collidepoint(x, y):
        is_playing = False

    elif clear_button.collidepoint(x, y):
        is_playing = False
        for r in range(GRID_ROWS):
            for c in range(slider_columns):
                grid[r][c] = 0
        playbar_x = None

    elif slider_columns_box.collidepoint(x, y):
        dragging_slider = "columns"

    elif slider_bps_box.collidepoint(x, y):
        dragging_slider = "bps"

    elif upload_button.collidepoint(x, y):
        upload_midi()

    elif download_button.collidepoint(x, y):
        download_audio()

    else:
        fixed_col_x = get_fixed_col_x()
        top_offset = (HEIGHT - GRID_ROWS * CELL_SIZE - 160) // 2
        col = (x - fixed_col_x) // CELL_SIZE
        row = (y - top_offset) // CELL_SIZE
        if 0 <= row < GRID_ROWS and 0 <= col < slider_columns:
            grid[row][col] = 1 - grid[row][col]

def main():
    global playbar_x, last_update_time, is_playing, slider_columns, slider_bps, bps, playbar_interval, dragging_slider, status_reset_delay,\
            file_browser_active,file_browser_scroll, current_dir,generated_audio,uploaded_midi,is_generated_audio_playing 
            file_browser_active,file_browser_scroll, current_dir,generated_audio,uploaded_midi
    running = True
    while running:
        screen.blit(background_image, (0, 0))
        col = (playbar_x - get_fixed_col_x()) // CELL_SIZE if playbar_x is not None else None
        draw_grid(col)
        draw_controls()
        if file_browser_active:
            draw_file_browser()

        if status_reset_delay and time.time() - status_last_update > status_reset_delay:
            update_status("Waiting for user action...")
            status_reset_delay = 0

        if is_playing and playbar_x is not None:
            current_time = time.time()
            if current_time - last_update_time >= playbar_interval:
                last_update_time = current_time
                playbar_x += CELL_SIZE
                col = (playbar_x - get_fixed_col_x()) // CELL_SIZE
                if 0 <= col < slider_columns:
                    play_column(col)
                if col >= slider_columns:
                    playbar_x = get_fixed_col_x()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # elif event.type == pygame.MOUSEBUTTONDOWN:
            #     handle_mouse_click(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging_slider = None
            elif event.type == pygame.MOUSEMOTION and dragging_slider:
                x = event.pos[0]
                if dragging_slider == "columns":
                    slider_columns = max(SLIDER_MIN_COLUMNS, min(SLIDER_MAX_COLUMNS, SLIDER_MIN_COLUMNS + int((x - 470) / 300 * (SLIDER_MAX_COLUMNS - SLIDER_MIN_COLUMNS))))
                    update_grid_size(slider_columns)
                elif dragging_slider == "bps":
                    slider_bps = max(SLIDER_MIN_BPS, min(SLIDER_MAX_BPS, SLIDER_MIN_BPS + int((x - 470) / 300 * (SLIDER_MAX_BPS - SLIDER_MIN_BPS))))
                    bps = slider_bps
                    playbar_interval = 1 / bps
            elif event.type == pygame.MOUSEBUTTONDOWN and file_browser_active:
                x, y = event.pos
                if 120 <= x <= WIDTH - 100 and 180 <= y <= HEIGHT - 100:
                    index = (y - 180) // 30 + file_browser_scroll
                    try:
                        items = ["../"] + sorted(os.listdir(current_dir))
                        if 0 <= index < len(items):
                            selected = items[index]
                            selected_path = os.path.abspath(os.path.join(current_dir, selected))

                            if selected == "../":
                                parent_path = os.path.abspath(os.path.join(current_dir, ".."))
                                if os.access(parent_path, os.R_OK):
                                    current_dir = parent_path
                                    file_browser_scroll = 0
                                else:
                                    update_status("Access denied to parent directory", reset_after_seconds=4)

                            elif os.path.isdir(selected_path):
                                if os.access(selected_path, os.R_OK):
                                    current_dir = selected_path
                                    file_browser_scroll = 0
                                else:
                                    update_status(f"Access denied to: {selected}", reset_after_seconds=4)

                            elif selected.endswith(".mid"):
                                if os.access(selected_path, os.R_OK):
                                    notes = parse_midi(selected_path)
                                    generated_audio = generate_audio(notes)
                                    # sound = pygame.mixer.Sound(
                                    #     buffer=(generated_audio * 32767).astype(np.int16).tobytes())
                                    # sound.play()
                                    uploaded_midi = selected_path
                                    update_status(f"{selected} loaded.")
                                    file_browser_active = False
                                else:
                                    update_status(f"Cannot open file: {selected}", reset_after_seconds=4)
                    except Exception as e:
                        print(e)
                        update_status(f"Access error: {str(e)}", reset_after_seconds=4)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse_click(event.pos)

            elif event.type == pygame.MOUSEWHEEL and file_browser_active:
                try:
                    max_items = len(["../"] + sorted(os.listdir(current_dir)))
                    file_browser_scroll = max(0, min(file_browser_scroll - event.y, max(0, max_items - 20)))
                except:
                    pass

        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
