import flet as ft
import flet_audio as fta
from tinytag import TinyTag
import os
import random

async def main(page: ft.Page):
    ## UI Config
    page.title = "Music Player"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    ## Variables
    playlist = []
    current_index = 0
    total_duration = 0
    is_playing = False

    ## UI Elements
    song_title_text = ft.Text("Elige una canción", size=20, weight=ft.FontWeight.BOLD)
    author_text = ft.Text("Artista Desconocido", size=16, color="gray")
    #song_cover = ft.Image(width=250, height=250, fit=ft.ImageFit.COVER, border_radius=15)
    
    current_time_text = ft.Text("0:00", size=12, color="gray")
    total_time_text = ft.Text("0:00", size=12, color="gray")


    def load_duration(duration):
        nonlocal total_duration
        total_duration = (duration.minutes * 60) + duration.seconds
        total_time_text.value = f"{duration.minutes}:{duration.seconds:02d}"

    current_song = fta.Audio(
        src="BYE.mp3", 
        volume=0.5, 
        autoplay=False,
        on_position_change=lambda e: update_timebar(e.position),
        on_duration_change=lambda e: load_duration(e.duration),
        on_state_change=lambda e: print("State changed:", e.state),
    )

    ## Auxiliar methods
    async def select_directory(e):
        nonlocal playlist, current_index
        if e.path:
            playlist = []

            try:
                for file_name in os.listdir(e.path):
                    if file_name.lower().endswith(('.mp3', '.wav', '.ogg')):
                        route = os.path.join(e.path, file_name)
                        song_data = extract_song_info(route)
                        if song_data:
                            playlist.append(song_data)
            except Exception as e:
                print(f"Error reading directory: {e}")

    def extract_song_info(file_path):
        try:
            tag = TinyTag.get(file_path)
            song_title_text.value = tag.title if tag.title else "Unknown Title"
            author_text.value = tag.artist if tag.artist else "Unknown Artist"
            #song_cover.src = tag.album_art if tag.album_art else "default_cover.jpg"
        except Exception as e:
            print(f"Error extracting song info: {e}")
        page.update()
    
    ## Methods for controlling the audio and UI
    async def button_play(e):
        nonlocal is_playing 
        
        if is_playing:
            await current_song.pause()
            is_playing = False
            e.control.icon = ft.Icons.PLAY_ARROW
        else:
            if timebar.value > 0:
                await current_song.resume()
            else:
                await current_song.play() 
                
            is_playing = True
            e.control.icon = ft.Icons.PAUSE
        page.update()

    async def button_next_song(e):
        print("Next song button clicked")

    async def button_previous_song(e):
        print("Previous song button clicked")

    def set_volume(value: float):
        current_song.volume = value

    def select_random_song():
        if playlist:
            change_song(random.choice(playlist))
        
    def change_song(index):
        nonlocal current_index, is_playing
        if 0 <= index < len(playlist):
            current_index = index
            song_data = playlist[current_index]
            current_song.src = song_data['route']
            song_title_text.value = song_data['title']
            author_text.value = song_data['artist']
            #song_cover.src = song_data['cover'] if 'cover' in song_data else "default_cover.jpg"
            timebar.value = 0
            current_time_text.value = "0:00"
            total_time_text.value = "0:00"
            page.update()
            
            if is_playing:
                current_song.play()

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
        new_position = e.control.value * total_duration
        await current_song.seek(int(new_position * 1000))

    page.services.append(current_song)
    page.update()

    timebar = ft.Slider(
        min=0.0, 
        max=1.0, 
        value=0.0, 
        active_color="blue", 
        thumb_color="transparent",
        overlay_color="transparent",
        secondary_track_value=0.0,
        interaction="None",
        on_change=update_slider
   )
    
    playlist_view = ft.ListView(
        spacing=10,
        padding=20,
        expand=True,
        controls=[
            ft.Text(f"Cancion {i}", color=ft.Colors.ON_SECONDARY) for i in range(0, 60)
        ])
    #ft.ListView(expand=True, spacing=10)

    add_songs_btn = ft.Button(
        "Agregar Canciones",
        icon=ft.Icons.ADD_LINK,
        # on_click= ... (apuntará a tu lógica de seleccionar archivos)
    )

    random_song_btn = ft.IconButton(
        icon=ft.Icons.SHUFFLE,
        hover_color="transparent",
        on_click=lambda e: select_random_song()
    )

    page.expand = True
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
                                        # Actual time
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            controls=[current_time_text, ft.Text("/", size=16, color="gray"), total_time_text]
                                        ),
                                        # Progress bar
                                        timebar,
                                        # Buttons
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            controls=[
                                                ft.IconButton(ft.Icons.SKIP_PREVIOUS, hover_color="transparent"),
                                                ft.IconButton(ft.Icons.PLAY_ARROW, on_click=button_play, hover_color="transparent"),
                                                ft.IconButton(ft.Icons.SKIP_NEXT, hover_color="transparent"),
                                                random_song_btn, # Tu nuevo botón shuffle
                                            ],
                                        ),
                                        # Volume Slider
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            spacing=5,
                                            controls=[
                                                ft.Icon(ft.Icons.VOLUME_DOWN, color="gray"),
                                                ft.Slider(min=0.0, max=1.0, value=0.5, active_color="blue", overlay_color="transparent", label="{value}%", on_change=lambda e: set_volume(e.control.value)),
                                            ]
                                        )
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
                                        add_songs_btn,
                                    ]
                                ),
                                ft.Divider(),
                                playlist_view,
                            ]
                        )
                    )
                ]
            )
        )
    )

ft.run(main)

