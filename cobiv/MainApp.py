import kivy
kivy.require('1.8.0')
from kivy.app import App
from MainContainer import MainContainer

from kivy.lang import Builder

Builder.load_file('main.kv')

class MainApp(App):

    def build(self):
        return MainContainer()

if __name__ == '__main__':
    MainApp().run()