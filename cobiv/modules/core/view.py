from cobiv.modules.core.component import Component


class View(Component):

    hud_available_profiles=[]
    hud_active_profiles=[]

    def on_switch(self):
        pass

    def on_switch_lose_focus(self):
        pass