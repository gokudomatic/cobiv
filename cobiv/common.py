cmd_actions = {}
cmd_hotkeys = {}


def set_action(name, fn, profile="default"):
    if name in cmd_actions:
        cmd_actions[name][profile] = fn
    else:
        cmd_actions[name] = {profile: fn}


def set_hotkey(key, command, modifier=0, profile="default"):
    if key in cmd_hotkeys:
        hotkey = cmd_hotkeys[key]
        if profile in hotkey:
            hotkey[profile][modifier] = command
        else:
            hotkey[profile] = {modifier: command}
    else:
        cmd_hotkeys[key] = {profile: {modifier: command}}


def get_hotkey_command(key, modifier=0, profile="default"):
    hotkeys_profiles = cmd_hotkeys[key]
    if profile in hotkeys_profiles:
        hotkeys = hotkeys_profiles[profile]
        if modifier in hotkeys:
            return hotkeys[modifier]

    return False
