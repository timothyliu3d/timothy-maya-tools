import maya.cmds as cmds


def remove_unknown_plugins():
    unknown_plugins = cmds.unknownPlugin(query=True, list=True)
    unknown_plugins = unknown_plugins or []
    for unknown_plugin in unknown_plugins:
        cmds.unknownPlugin(unknown_plugin, remove=True)
    return unknown_plugins


def prioritize_relative_filepaths(enable=True, strict=False):
    prioritize_relative = "fileResolverResolveExactAfterRelative"
    only_allow_relative = "fileResolverStrictRelativePaths"

    cmds.optionVar(intValue=(prioritize_relative, enable))

    if enable:
        cmds.optionVar(intValue=(only_allow_relative, strict))
    else:
        cmds.optionVar(intValue=(only_allow_relative, 0))


def get_wireframe_color(nodename: str) -> int | tuple[float, float, float]:
    mode = cmds.getAttr(f"{nodename}.useObjectColor")

    if is_default := mode == 0:
        return 0

    elif is_index := mode == 1:
        color = cmds.getAttr(f"{nodename}.objectColor")

        # .objectColor value ranges from 0-7.
        # Add 1 to stay consistent with cmds.color(), which ranges from 1-8.
        color += 1

    elif is_rgb := mode == 2:
        color = cmds.getAttr(f"{nodename}.wireColorRGB")[0]

    return color


def set_wireframe_color(nodename: str, color: int | tuple[float, float, float] = 0):
    if color is None:
        cmds.color(nodename)  # restores default color
    elif isinstance(color, int):
        cmds.color(nodename, userDefined=color)
    elif len(color) == 3:
        cmds.color(nodename, rgbColor=color)


def set_drawing_overrides(
    nodename: str,
    enable=True,
    normal=False,
    template=False,
    reference=False,
    boundingbox=False,
    shading=True,
    texturing=True,
    playback=True,
    visible=True,
    color: int | tuple[float, float, float] = None,
    opacity=1.0,
):
    cmds.setAttr(f"{nodename}.overrideEnabled", enable)

    if not any([normal, template, reference]):
        normal = True

    if sum([normal, template, reference]) != 1:
        raise ValueError("Mutually exclusive: normal, template, reference")

    displaytype = [normal, template, reference].index(True)
    cmds.setAttr(f"{nodename}.overrideDisplayType", displaytype)

    levelofdetail = {False: 0, True: 1}[boundingbox]
    cmds.setAttr(f"{nodename}.overrideLevelOfDetail", levelofdetail)

    cmds.setAttr(f"{nodename}.overrideShading", shading)
    cmds.setAttr(f"{nodename}.overrideTexturing", texturing)
    cmds.setAttr(f"{nodename}.overridePlayback", playback)
    cmds.setAttr(f"{nodename}.overrideVisibility", visible)

    if color is not None:
        if isinstance(color, int):
            cmds.setAttr(f"{nodename}.overrideRGBColors", False)
            cmds.setAttr(f"{nodename}.overrideColor", color)

        elif isinstance(color, tuple):
            cmds.setAttr(f"{nodename}.overrideRGBColors", True)
            cmds.setAttr(f"{nodename}.overrideColorRGB", *color)
            cmds.setAttr(f"{nodename}.overrideColorA", opacity)
