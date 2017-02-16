import kivy

kivy.require('1.9.1')
from kivy.app import App
from MainContainer import MainContainer
from kivy.lang import Builder

Builder.load_file('main.kv')


class MainApp(App):

    root=None

    def build(self):
        self.root=MainContainer()
        return self.root


if __name__ == '__main__':
    MainApp().run()
