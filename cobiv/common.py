available_views = {}
cmd_actions = {}
cmd_hotkeys = {}


def set_action(name, fn, profile="default"):
    if cmd_actions.has_key(name):
        cmd_actions[name][profile] = fn
    else:
        cmd_actions[name] = {profile: fn}


def set_hotkey(key, command, modifier=0, profile="default"):
    if cmd_hotkeys.has_key(key):
        hotkey = cmd_hotkeys[key]
        if hotkey.has_key(profile):
            hotkey[profile][modifier] = command
        else:
            hotkey[profile] = {modifier: command}
    else:
        cmd_hotkeys[key] = {profile: {modifier: command}}


def get_hotkey_command(key, modifier=0, profile="default"):
    hotkeys_profiles = cmd_hotkeys[key]
    if hotkeys_profiles.has_key(profile):
        hotkeys = hotkeys_profiles[profile]
        if hotkeys.has_key(modifier):
            return hotkeys[modifier]

    return False
