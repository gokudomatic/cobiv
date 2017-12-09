from kivy.vector import Vector

from cobiv.modules.core.entity import Entity


class GestureManager(Entity):
    __touches = []

    strategies = {}
    current_strategy = None
    strategy_candidates = []
    stroke_list = {}
    last_tick = None
    first_tick = None

    stroke_error_margin = 20
    stroke_tick_time = 0.1
    stroke_identify_timeout = 0.3

    last_touches = {}

    def __init__(self):
        super(GestureManager, self).__init__()

    def build_yaml_config(self, config):
        return super(GestureManager, self).build_yaml_config(config)

    def ready(self):
        for gesture_strategy in self.lookups('Gesture'):
            touch_count = gesture_strategy.required_touch_count()

            if not self.strategies.has_key(touch_count):
                self.strategies[touch_count] = []
            self.strategies[touch_count].append(gesture_strategy)

    def on_touch_down(self, touch):
        self.__touches.append(touch)

        nb_touch = len(self.__touches)
        if nb_touch >= 2: # and nb_touch in self.strategies:
            self.strategy_candidates = []
            if nb_touch in self.strategies:
                for strategy in self.strategies[nb_touch]:
                    strategy.initialize(self.__touches)
                    self.strategy_candidates.append(strategy)
            self.current_strategy = None
            self.last_tick = touch.time_update
            self.first_tick = touch.time_update
            self.stroke_list = {}
            self.last_touches = {}
            for t in self.__touches:
                # print("init touch",t.uid)
                self.last_touches[t.uid] = t.pos
                self.stroke_list[t.uid] = [Vector(0, 0)]
        else:
            self.last_touches = {}


    def on_touch_up(self, touch):
        nb_touch = len(self.__touches)
        if nb_touch >= 2 and nb_touch in self.strategies:
            self.update_last_touch(touch)
            self.stroke_list[touch.uid][-1] = self.round_vector(self.stroke_list[touch.uid][-1].normalize())

        if nb_touch >= 2 and nb_touch in self.strategies:
            if self.current_strategy is not None:
                self.current_strategy.finalize(self.__touches, self.stroke_list)
                self.current_strategy = None

        self.__touches.remove(touch)

    def on_touch_move(self, touch):
        if not touch.uid in self.last_touches:
            return

        # print(self.stroke_list)

        self.update_last_touch(touch)

        if touch.time_update - self.last_tick > self.stroke_tick_time:
            self.add_stroke(touch)

        self.process_or_validate_strategies(touch)

    def add_stroke(self,touch):
        do_new_stroke = False
        for t in self.__touches:
            self.last_touches[t.uid] = t.pos

            # check if current stroke is not null nor identical to previous
            v = self.stroke_list[touch.uid][-1]
            if v.length() > 0:
                if len(self.stroke_list[touch.uid]) > 1:
                    do_new_stroke = do_new_stroke or (v - self.stroke_list[touch.uid][-2]).length() > 0
                else:
                    do_new_stroke = True

        if do_new_stroke:
            for t in self.__touches:
                self.stroke_list[t.uid].append(Vector(0, 0))

        self.last_tick = touch.time_update

    def process_or_validate_strategies(self,touch):
        if self.current_strategy is not None:
            self.current_strategy.process(self.__touches, self.stroke_list)
        else:
            if touch.time_update - self.first_tick > self.stroke_identify_timeout:


                self.strategy_candidates = [c for c in self.strategy_candidates if c.validate(self.__touches,self.stroke_list)]
                if len(self.strategy_candidates) == 1:
                    self.current_strategy = self.strategy_candidates[0]
                    self.current_strategy.process(self.__touches, self.stroke_list)
                elif len(self.strategy_candidates) == 0:
                    # print("no strategy found")
                    # print(self.stroke_list)
                    pass  # TODO set path strategy

    def get_touch_count(self):
        return len(self.__touches)

    def round_vector(self, v):

        def sign(x):
            return (x > 0) - (x < 0)

        if abs(v.y) <= 0.38:
            return Vector(sign(v.x), 0)
        elif abs(v.x) <= 0.38:
            return Vector(0, sign(v.y))
        else:
            return Vector(sign(v.x), sign(v.y))

    def update_last_touch(self, touch):
        tx, ty = self.last_touches[touch.uid]
        v = Vector(touch.x - tx, touch.y - ty)
        v1 = v
        if 0 < v.length() < self.stroke_error_margin:
            v = Vector(0, 0)

        if v.length() > 0:
            self.stroke_list[touch.uid][-1] = self.round_vector(v.normalize())

            # print(touch.uid,v1,"->",v)
