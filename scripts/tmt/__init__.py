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
    boundingbox: bool = None,
    shading: bool = None,
    texturing: bool = None,
    playback: bool = None,
    visible: bool = None,
    color: int | tuple[float, float, float] | None = None,
    opacity: float = None,
):
    cmds.setAttr(f"{nodename}.overrideEnabled", enable)

    displaytype_args = [normal, template, reference]
    if sum(displaytype_args) not in [0, 1]:
        raise ValueError("Mutually exclusive parameters: normal, template, reference")
    if sum(displaytype_args) == 1:
        displaytype = displaytype_args.index(True)
        cmds.setAttr(f"{nodename}.overrideDisplayType", displaytype)

    if boundingbox is not None:
        levelofdetail = {False: 0, True: 1}[boundingbox]
        cmds.setAttr(f"{nodename}.overrideLevelOfDetail", levelofdetail)

    if shading is not None:
        cmds.setAttr(f"{nodename}.overrideShading", shading)

    if texturing is not None:
        cmds.setAttr(f"{nodename}.overrideTexturing", texturing)

    if playback is not None:
        cmds.setAttr(f"{nodename}.overridePlayback", playback)

    if visible is not None:
        cmds.setAttr(f"{nodename}.overrideVisibility", visible)

    if isinstance(color, (int, tuple)):
        color_is_rgb = isinstance(color, tuple)
        cmds.setAttr(f"{nodename}.overrideRGBColors", color_is_rgb)

        if color_is_rgb:
            cmds.setAttr(f"{nodename}.overrideColorRGB", *color)
            if opacity is not None:
                cmds.setAttr(f"{nodename}.overrideColorA", opacity)
        else:
            cmds.setAttr(f"{nodename}.overrideColor", color)
