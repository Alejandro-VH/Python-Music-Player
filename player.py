import sys
import flet as ft
import flet_audio as fta
from tinytag import TinyTag
import os
import random
from config_manager import load_config, save_config

config = load_config()

async def main(page: ft.Page):
    ## UI Config
    page.title = "VibeTracks"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Stuff to set the app icon
    if getattr(sys, 'frozen', False):
        actual_route = sys._MEIPASS
    else:
        actual_route = os.path.dirname(os.path.abspath(__file__))
    
    icon_route = os.path.join(actual_route, "Assets", "icono.ico")
    page.window.icon = icon_route 

    # Windows settings
    page.window.min_width = 880
    page.window.min_height = 450
    page.window.width = 900
    page.window.height = 500
    page.window.update()
    await page.window.center()

    ## Variables
    playlist = config["songs_directory"]
    current_index = -1
    total_duration = 0
    is_playing = False
    MAX_AUDIO_GAIN = config.get("max_gain", 0.7)
    current_song = None

    # Methods
    def load_duration(duration):
        nonlocal total_duration
        total_duration = (duration.minutes * 60) + duration.seconds
        total_time_text.value = f"{duration.minutes}:{duration.seconds:02d}"

    async def get_song_directory():
        path = await ft.FilePicker().get_directory_path()
        if path:
            directory_path.value = path
            await load_songs(path)

    async def load_songs(songs_directory: str):
        nonlocal playlist
        if not songs_directory or songs_directory == "Sin carpeta seleccionada":
            return
        
        # Clears the playlist and ui
        playlist = []

        try:
            for file_name in os.listdir(songs_directory):
                if file_name.lower().endswith(('.mp3', '.wav', '.ogg')):
                    route = os.path.join(songs_directory, file_name)
                    song_data = extract_song_info(route)
                    if song_data:
                        playlist.append(song_data)

            config["songs_directory"] = songs_directory
            save_config(config)

            update_playlist_ui()
        except Exception as e:
            print(f"Error loading songs: {e}")
        page.update()

    def update_playlist_ui():
        playlist_view.controls.clear()

        selected_color = config.get("color", "blue")
        for index, song_data in enumerate(playlist):
            playlist_view.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.MUSIC_NOTE, color=selected_color),
                    title=ft.Text(song_data['title'], weight=ft.FontWeight.BOLD, size=14),
                    subtitle=ft.Text(song_data['artist'], size=12, color="gray"),
                    on_click=lambda e, idx=index: page.run_task(change_song, idx)
                )
            )
        playlist_view.update()

    def extract_song_info(file_path):
        try:
            tag = TinyTag.get(file_path)
            # If the metadata is correctly filled (the perfect case)
            if tag.title and tag.artist:
                return {
                    "title": tag.title.strip(),
                    "artist": tag.artist.strip(),
                    "route": file_path
                }
            
            # Aaaand if not, we need to try to set the correct title and artist from the file name 
            song_title = os.path.basename(file_path).replace(".mp3", "").replace(".wav", "").replace(".ogg", "")
            song_artist = tag.artist.strip() if tag.artist else "Artista Desconocido"

            # Hoping to match all the unnecessary terms for a cleaner view
            for trash in ["(Official Video)", "[Official Video]", "[Official Audio]", "(Official Audio)", "Lyrics", "[Video Oficial]", "(Video Oficial)", "4K", "HD", "[4K]", "[HD]", "(4K)", "(HD)", "Audio", "(Audio)", "[Audio]", "Official", "(Official)", "[Official]", "Video", "(Video)", "[Video]", "Lyric Video", "(Lyric Video)", "[Lyric Video]", "Lyric", "(Lyric)", "[Lyric]", "()" "( )", "[]", "[]"]:
                song_title = song_title.replace(trash, "").replace(trash.lower(), "")

            return {
                "title": song_title.strip(),
                "artist": song_artist.strip(),
                "route": file_path
            }
        except Exception as e:
            print(f"Error extracting song info: {e}")
            return None

    def state_change_handler(event):
        nonlocal is_playing
        if event.state == fta.AudioState.PLAYING:
            is_playing = True
            buttons_container.controls[1].icon = ft.Icons.PAUSE
        elif event.state == fta.AudioState.PAUSED:
            is_playing = False
            buttons_container.controls[1].icon = ft.Icons.PLAY_ARROW
        elif event.state == fta.AudioState.STOPPED:
            is_playing = False
            buttons_container.controls[1].icon = ft.Icons.PLAY_ARROW
        elif event.state == fta.AudioState.COMPLETED:
            page.run_task(button_next_song)
        page.update()

    async def change_song(index):
        nonlocal current_index, is_playing, current_song

        if 0 <= index < len(playlist):
            current_index = index
            song_data = playlist[current_index]
            
            if current_song is None:
                current_song = fta.Audio(
                    src=song_data['route'],
                    volume=config.get("volume", 0.35) * MAX_AUDIO_GAIN,
                    autoplay=True,
                    on_position_change=lambda e: update_timebar(e.position),
                    on_duration_change=lambda e: load_duration(e.duration),
                    on_state_change=lambda e: state_change_handler(e)
                )
                page.services.append(current_song)
            else:
                current_song.src = song_data['route']
            
            song_title_text.value = song_data['title']
            author_text.value = song_data['artist']

            timebar.value = 0
            current_time_text.value = "0:00"
            total_time_text.value = "0:00"

            is_playing = True
            page.update()

    ## Methods for controlling the audio and UI
    async def button_play(e):
        nonlocal is_playing 

        if current_song is None:
            if playlist:
                await change_song(0)
            return 
        
        if is_playing:
            await current_song.pause()
            is_playing = False
        else:
            if timebar.value > 0:
                await current_song.resume()
            else:
                await current_song.play() 
            is_playing = True
        page.update()

    async def button_next_song():
        nonlocal current_index
        if playlist:
            next_index = (current_index + 1) % len(playlist)
            await change_song(next_index)

    async def button_previous_song():
        nonlocal current_index
        if playlist:
            previous_index = (current_index - 1) % len(playlist)
            await change_song(previous_index)

    def set_volume(value: float):
        MAX_AUDIO_GAIN = config.get("max_gain", 0.7)
        if current_song is not None:
            current_song.volume = value * MAX_AUDIO_GAIN

        percentage = int(value * 100)
        volume_text.value = f"{percentage}%"
        
        # prob it would be better to save only when the app is closed, but for now its fine
        config["volume"] = value
        save_config(config)
        page.update()

    async def select_random_song():
        if playlist:
            await change_song(random.randint(0, len(playlist) - 1))
            
    def update_gain(value: float):
            config.update({"max_gain": value})
            gain_dialog_text.value = f"{int(value * 100)}%"
            page.update()

    def update_timebar(position):
        position_seconds = position / 1000
        if total_duration > 0:
            progress = min(position_seconds / total_duration, 1.0)
            timebar.value = progress

            current_mins = int(position_seconds // 60)
            current_secs = int(position_seconds % 60)
            current_time_text.value = f"{current_mins}:{current_secs:02d}"
        else:
            timebar.value = 0
        page.update()

    async def update_slider(e):
        if current_song is None or total_duration == 0:
            return

        new_position = e.control.value * total_duration
        await current_song.seek(int(new_position * 1000))

    def close_settings():
        save_config(config)
        # UI stuff
        new_color = config.get("color", "blue")
        timebar.active_color = new_color
        volume_slider.controls[1].active_color = new_color
        update_playlist_ui()

        # Update volume
        set_volume(volume_slider.controls[1].value)

        page.pop_dialog()
        page.update()

    page.services.append(current_song)

    ## UI Elements
    ### Left Side
    song_title_text = ft.Text("Elige una canción", size=20, weight=ft.FontWeight.BOLD)
    author_text = ft.Text("-", size=16, color="gray")
    
    current_time_text = ft.Text("0:00", size=12, color="gray")
    total_time_text = ft.Text("0:00", size=12, color="gray")

    current_time = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[current_time_text, ft.Text("/", size=16, color="gray"), total_time_text]
    )

    timebar = ft.Slider(
        min=0.0, 
        max=1.0, 
        value=0.0, 
        active_color=config.get("color", "blue"),
        thumb_color="transparent",
        overlay_color="transparent",
        secondary_track_value=0.0,
        interaction="None",
        on_change=update_slider
   )
    
    buttons_container = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.IconButton(ft.Icons.SKIP_PREVIOUS, on_click=button_previous_song, hover_color="transparent"),
            ft.IconButton(ft.Icons.PLAY_ARROW, on_click=button_play, hover_color="transparent"),
            ft.IconButton(ft.Icons.SKIP_NEXT, on_click=button_next_song, hover_color="transparent"),
            ft.IconButton(ft.Icons.SHUFFLE,hover_color="transparent",on_click= select_random_song)
        ],
    )

    volume_text = ft.Text(f"{int(config.get('volume', 0.35) * 100)}%", size=12, color="gray")
    volume_slider = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=5,
        controls=[
            ft.Icon(ft.Icons.VOLUME_DOWN, color="gray"),
            ft.Slider(min=0.0, max=1.0, value=config.get("volume", 0.35), active_color=config.get("color", "blue"), thumb_color="transparent", overlay_color="transparent", on_change=lambda e: set_volume(e.control.value)),
            volume_text
        ]
    )
    
    ### Right Side
    select_folder_btn = ft.IconButton(
        tooltip="Carpeta de música",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=get_song_directory,
    )

    config_btn = ft.IconButton(
        tooltip="Configuración",
        icon=ft.Icons.SETTINGS,
        hover_color="transparent",
        on_click=lambda e: page.show_dialog(config_dialog),
    )

    gain_dialog_text = ft.Text(f"{int(config.get('max_gain', 0.7) * 100)}%", size=12, weight=ft.FontWeight.BOLD, color=config.get("color", "blue"))
    config_dialog = ft.AlertDialog(
        title=ft.Text("Ajustes", size=16, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            tight=True,
            width=220,
            controls=[
                ft.Text("Ganancia de Audio:"),
                gain_dialog_text,
                ft.Slider(
                    min=0.1, 
                    max=1.0, 
                    active_color=config.get("color", "blue"),
                    value=config.get("max_gain", 0.5),
                    on_change=lambda e: update_gain(float(e.control.value)),
                ),
                
                ft.Text("Color del Interfaz:", size=12, color="gray"),
                ft.Dropdown(
                    height=45,
                    value=config.get("color", "blue"),
                    options=[
                        ft.dropdown.Option("blue", "Azul"),
                        ft.dropdown.Option("red", "Rojo"),
                        ft.dropdown.Option("green", "Verde"),
                        ft.dropdown.Option("orange", "Naranja"),
                        ft.dropdown.Option("purple", "Morado"),
                    ],
                    on_select=lambda e: config.update({"color": e.control.value}),
                ),
            ]
        ),        
        actions=[
            ft.TextButton("Guardar", on_click=close_settings, style=ft.ButtonStyle(color=config.get("color", "blue"))),
        ],
        open=True,
    )

    playlist_view = ft.ListView(
        spacing=10,
        padding=20,
        expand=True,
        build_controls_on_demand=True
    )

    page.add(
        ft.Container(
            padding=20,
            border_radius=15,
            expand=True,
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ### Left Side
                    ft.Container(
                        width=350,
                        expand=True, 
                        padding=ft.Padding(0, 20, 0, 20),
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                # Song data
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=5,
                                    controls=[
                                        song_title_text,
                                        author_text,
                                    ]
                                ),

                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=20,
                                    controls=[
                                        current_time,
                                        timebar,
                                        buttons_container,
                                        volume_slider

                                    ]
                                ) 
                            ]
                        ),
                    ),
                    ### Central Divider
                    ft.VerticalDivider(),
                
                    ### Right Side
                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Text("Lista de Reproducción", size=18, weight=ft.FontWeight.BOLD),
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.END,
                                            controls=[
                                                ft.Row(
                                                    controls=[
                                                        config_btn,
                                                        select_folder_btn
                                                    ]
                                                )
                                            ]
                                        )
                                    ]
                                ),
                                ft.Divider(),
                                directory_path := ft.Text(config.get("songs_directory", "Sin carpeta seleccionada"), size=12, color="gray", overflow=ft.TextOverflow.ELLIPSIS),
                                playlist_view
                            ]
                        )
                    )
                ]
            )
        )
    )

    if config.get("songs_directory"): 
        directory_path.value = config["songs_directory"]
        await load_songs(config["songs_directory"])
        
    page.update()

ft.run(main)