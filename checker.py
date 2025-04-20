import threading
import requests
import queue
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivy.uix.textinput import TextInput
from demo2 import KV
from kivy.core.window import Window
import os
from kivy.animation import Animation
Window.size = (360, 640)  # Set size for testing
#Window.fullscreen = 'auto'
q = queue.Queue()
valid_proxies = []
stop_event = threading.Event()

class HomeScreen(Screen):
    pass

class SecondScreen(Screen):
    pass

class ThirdScreen(Screen):
    def add_result(self, proxy):
        print(f"Adding result for proxy: {proxy}")
        text_input = TextInput(
            text=proxy, readonly=True, multiline=False, cursor_blink=True,
            background_color=(0, 0, 0, 0), foreground_color=(0,0,0,1),
            size_hint_y=None, height=40, use_bubble=True, use_handles=True
        )
        self.ids.result_box.add_widget(text_input)

        # Print current results for validation
        print("Current Results in UI:", [child.text for child in self.ids.result_box.children])


    def set_loading(self, loading):
        # Debug print to check if loading text updates are being made
        print(f"Setting loading: {loading}")
        self.ids.loading_label.text = "Loading..." if loading else ""

    def show_completed_message(self):
        # Debug print for completed message
        print("Showing completed message")
        self.ids.loading_label.text = "Completed Checking"

    def enable_check_again(self):
        print("Check again button enabled")
        self.ids.check_again_btn.opacity = 1
        self.ids.check_again_btn.disabled = False


class Checker(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.selected_file_path = ""
        screen_manager = ScreenManager()
        self.screen = Builder.load_string(KV)
        self.icon="earth1-removebg-preview.png"

        self.file_manager = MDFileManager(exit_manager=self.exit_manager, select_path=self.select_path, ext=['.txt'])
        screen_manager.add_widget(HomeScreen(name='home'))
        screen_manager.add_widget(SecondScreen(name='second'))
        screen_manager.add_widget(ThirdScreen(name='third'))
        Clock.schedule_once(self.show_content, 6)
        return screen_manager

    def on_start(self):
        self.root.md_bg_color=(1,1,1,1)
        print("App has started.")

    def on_stop(self):
        print("App is stopping.")
    def show_content(self, *args):
        try:
            print("Loading GIF finished, showing content now")
            home_screen = self.root.get_screen('home')

            # Stop the GIF animation
            home_screen.ids.loading_gif.anim_delay = -1

            # Fade out the loading animation
            fade_out = Animation(opacity=0, duration=1)
            fade_out.start(home_screen.ids.loading_gif)

            # Callback to show app name and button after fade-out
            def show_app_content(dt):
                home_screen.ids.app_name.opacity = 1
                Animation(opacity=1, duration=1).start(home_screen.ids.app_name)
                Animation(opacity=1, duration=1).start(home_screen.ids.go_button)

            Clock.schedule_once(show_app_content, 1.2)  # Add a slight delay
        except Exception as e:
            print(f"Error in show_content: {e}")

    def go_to_second_screen(self):
        self.root.current = 'second'

    def go_to_third_screen(self):
        self.root.current = 'third'

    def file_manager_open(self):
        self.file_manager.show('/')  # Opens the file location at root path

    def select_path(self, path):
        if path.endswith('.txt'):
            self.selected_file_path = path
            self.root.get_screen('second').ids.file_path_label.text = f"Selected File: {os.path.basename(path)}"
            toast(f'Selected: {os.path.basename(path)}')
            self.exit_manager()
        else:
            toast('Please select a .txt file')

    def exit_manager(self, *args):
        self.file_manager.close()

    def run_proxy_check(self):
        global stop_event
        stop_event.clear()
        if not self.selected_file_path:
            toast("No file selected")
            return

        self.root.get_screen('third').ids.result_box.clear_widgets()
        self.root.get_screen('third').set_loading(True)
        self.root.get_screen('third').ids.check_again_btn.opacity = 0
        self.root.get_screen('third').ids.check_again_btn.disabled = True

        with open(self.selected_file_path, 'r') as file:
            proxies = file.read().splitlines()
            print(f"Loaded proxies: {proxies}")  # Debug output

        for proxy in proxies:
            q.put(proxy)

        for _ in range(10):
            thread = threading.Thread(target=self.check_proxy)
            thread.daemon = True
            thread.start()

        Clock.schedule_once(self.go_to_third_screen, 0.1)

    def check_proxy(self):
        global q, valid_proxies, stop_event
        valid_count = 0
        invalid_count = 0
        error_details = []

        while not q.empty() and not stop_event.is_set():
            proxy = q.get()
            try:
                print(f"Checking proxy: {proxy}")
                response = requests.get('https://ipinfo.io/json', proxies={'http': proxy, 'https': proxy}, timeout=5)
                if response.status_code == 200:
                    valid_proxies.append(proxy)
                    valid_count += 1
                    print(f"Valid Proxy: {proxy}")
                    Clock.schedule_once(lambda dt: self.root.get_screen('third').add_result(proxy), 0)
                else:
                    print(f"Invalid Proxy: {proxy} with status {response.status_code}")
                    invalid_count += 1
                    error_details.append(f"{proxy} returned status {response.status_code}")
            except requests.RequestException as e:
                print(f"Error with proxy {proxy}: {e}")
                invalid_count += 1
                error_details.append(f"{proxy} error: {str(e)}")
                continue

        # Once all proxies are checked
        Clock.schedule_once(lambda dt: self.root.get_screen('third').set_loading(False))
        Clock.schedule_once(lambda dt: self.root.get_screen('third').show_completed_message())
        Clock.schedule_once(lambda dt: self.root.get_screen('third').enable_check_again())

        print(f"Total Valid Proxies: {valid_count}")
        print(f"Total Invalid Proxies: {invalid_count}")
        for error in error_details:
            print(error)


    def go_to_third_screen(self, *args):
        self.root.current = 'third'

    def stop_check(self):
        global stop_event
        stop_event.set()

    def reset_and_check_again(self):
        global q, valid_proxies
        q.queue.clear()
        valid_proxies.clear()
        self.selected_file_path = ""  # Reset the selected file path
        second_screen = self.root.get_screen('second')
        second_screen.ids.file_path_label.text = "You Have Selected: None"  # Clear the file path label
        self.go_to_second_screen()


KV = """
ScreenManager:
    HomeScreen:
        name: 'home'
    SecondScreen:
        name: 'second'
    ThirdScreen:
        name: 'third'


<HomeScreen>:
    FloatLayout:
        md_bg_color:1,1,1,1

        Image:
            id: earth_icon
            source: "earth1.jpeg"   # Add your Earth icon file
            size_hint: 0.6, 0.6
            pos_hint: {'center_x': 0.52, 'center_y': 0.75}
            opacity: 1  # Show with loading

        Image:
            id: loading_gif
            source: "loading.gif"
            anim_delay: 0.08
            size_hint: 0.65, 0.4
            pos_hint: {'center_x': 0.5, 'center_y': 0.55}



        Label:
            id: app_name
            text: "VALID PROXY CHECKER"
            font_name: "ProtestGuerrilla-Regular.ttf"  # Set a custom font
            font_style: "H4"
            font_size: '25sp'
            bold: True
            italic: True
            halign: "center"
            pos_hint: {'center_x': 0.5, 'center_y': 0.55}
            opacity: 0
            color: 0.0, 0.7, 1, 1  # Hard Sky Blue color

        MDRaisedButton:
            id: go_button
            text: "Click Here"
            font_size: '18sp'
            halign: "center"
            pos_hint: {'center_x': 0.5, 'center_y': 0.25}
            size_hint: 0.4, 0.1
            opacity: 0  # Hidden initially
            on_release: app.root.current = 'second'


<SecondScreen>:
    MDLabel:
        text: "INSTRUCTION : Please Select The Downloaded .txt File of Proxies Here."   
        halign: "center"
        pos_hint: {'center_x': 0.5, 'center_y': 0.65}
        theme_text_color: "Primary"
        font_size: "20sp"

    MDLabel:
        id: file_path_label
        text: "You Have Selected: None"
        theme_text_color: "Secondary"
        halign: "center"
        pos_hint: {'center_x': 0.5, 'center_y': 0.40}
        font_size: '20sp'

    MDRaisedButton:
        text: "Select .txt File"
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        font_size: '24sp'
        size_hint: 0.2, 0.1
        on_release: app.file_manager_open()

    MDRectangleFlatButton:
        text: "Home"
        font_size: '24sp'
        pos_hint: {'center_x': 0.3, 'center_y': 0.28}
        size_hint: 0.2, 0.1
        on_release: app.root.current = 'home'

    MDRectangleFlatButton:
        text: "Check"
        font_size: '24sp'
        pos_hint: {'center_x': 0.7, 'center_y': 0.28}
        size_hint: 0.2, 0.1
        on_release: app.run_proxy_check()

<ThirdScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)

        ScrollView:
            size_hint_y: None
            height: self.parent.height * 0.6
            BoxLayout:
                id: result_box
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
                padding: dp(10)

        MDLabel:
            id: loading_label
            text: ""
            halign: "center"
            theme_text_color: "Primary"
            #text_color: 0, 1, 0, 1
            font_style: "H6"
            size_hint_y: None
            height: dp(40)






        MDRaisedButton:
            text: "Stop"
            pos_hint: {'center_x': 0.5}
            size_hint: 0.3, 0.1
            on_release: app.stop_check()

        MDRaisedButton:
            id: check_again_btn
            text: "Check Again"
            pos_hint: {'center_x': 0.5}
            size_hint: 0.3, 0.1
            opacity: 0
            disabled: True
            on_release: app.reset_and_check_again()


"""


if __name__ == "__main__":
    Checker().run()

