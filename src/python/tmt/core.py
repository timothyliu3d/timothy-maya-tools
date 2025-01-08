import re as _re

import maya.api.OpenMaya as _om
import maya.cmds as _cmds
import maya.mel as _mel


def remove_unknown_plugins() -> list[str]:
    unknown_plugins = _cmds.unknownPlugin(query=True, list=True)
    unknown_plugins = unknown_plugins or []
    for unknown_plugin in unknown_plugins:
        _cmds.unknownPlugin(unknown_plugin, remove=True)
    return unknown_plugins


def prioritize_relative_filepaths(enable=True, strict=False):
    """
    :param enable: whether to prioritize relative filepath matching over absolute filepaths.
    :param strict: whether to completely disable absolute filepath matching.
    """
    prioritize_relative = "fileResolverResolveExactAfterRelative"
    only_allow_relative = "fileResolverStrictRelativePaths"

    _cmds.optionVar(intValue=(prioritize_relative, enable))

    if enable:
        _cmds.optionVar(intValue=(only_allow_relative, strict))
    else:
        _cmds.optionVar(intValue=(only_allow_relative, 0))


def list_assigned_faces(material: str) -> list[str]:
    sg = _cmds.listConnections(material, destination=True, type="shadingEngine")[0]
    assigned_faces = _cmds.sets(sg, query=True) or []
    return assigned_faces


def split_nodeattr(name: str) -> list[str]:
    """
    Split the input node attribute name and indices based on known Maya delimiter
    characters.

    Some examples:

    * Input of ``"nodename.vtx[2:4]"``
    * Returns ``["nodename", "vtx", "2", "4"]``

    * Input of ``"nodename.attrname[1][2]"``
    * Returns ``["nodename", "attrname", "1", "2"]``

    :param name: name to be split.
    :return: list of string sections split from the input value.
    """
    node, attr = name.split(".", maxsplit=1)
    return [node] + _re.findall(r"[^.\[:\]]+", attr)


def get_msl_of(*names: str) -> _om.MSelectionList:
    msl = _om.MSelectionList()
    for name in names:
        try:
            msl.add(name)
        except RuntimeError:
            dupes = _cmds.ls(name)
            dupes_msg = dupes[:5]
            if len(dupes_msg) != len(dupes):
                dupes_msg.append("...")
            dupes_msg = "\n".join(dupes_msg)
            raise ValueError(
                f"Non-unique or non-existent name: '{name}'"
                f"\n{len(dupes)} names found:"
                f"\n{dupes_msg}"
            )
    return msl


def as_mplug(nodeattr: str) -> _om.MPlug | None:
    if "." not in nodeattr:
        return None

    # Using MSelectionList.getPlug() raises TypeError on some attributes.
    # Have to use MFnDependencyNode.findPlug() instead.
    # Known versions: 2024.2, 2025.2
    nodename, attrname = nodeattr.split(".", maxsplit=1)
    if attrname in ["rotatePivot", "scalePivot"]:
        msl = get_msl_of(nodename)
        mobj = msl.getDependNode(0)
        fn = _om.MFnDependencyNode(mobj)
        mplug = fn.findPlug(attrname, False)

    else:
        msl = get_msl_of(nodeattr)
        try:
            mplug = msl.getPlug(0)
        except TypeError:
            return None

    return mplug


def as_mvector(
    xyz_or_name: tuple[float, float, float] | _om.MVector | str
) -> _om.MVector:
    if isinstance(xyz_or_name, (list, tuple, _om.MVector)):
        return _om.MVector(xyz_or_name)

    if isinstance(xyz_or_name, str):
        return _om.MVector(
            _cmds.xform(xyz_or_name, query=True, worldSpace=True, translation=True)
        )

    raise ValueError(
        f"Input argument must be a point position or dagNode name: '{xyz_or_name}'"
    )


def get_wireframe_color(nodename: str) -> int | tuple[float, float, float]:
    mode = _cmds.getAttr(f"{nodename}.useObjectColor")

    if is_default := mode == 0:
        return 0

    elif is_index := mode == 1:
        color = _cmds.getAttr(f"{nodename}.objectColor")

        # .objectColor value ranges from 0-7.
        # Add 1 to stay consistent with cmds.color(), which ranges from 1-8.
        color += 1

    elif is_rgb := mode == 2:
        color = _cmds.getAttr(f"{nodename}.wireColorRGB")[0]

    return color


def set_wireframe_color(nodename: str, color: int | tuple[float, float, float] = 0):
    if color is None:
        _cmds.color(nodename)  # restores default color
    elif isinstance(color, int):
        _cmds.color(nodename, userDefined=color)
    elif len(color) == 3:
        _cmds.color(nodename, rgbColor=color)


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
    color: int | tuple[float, float, float] = None,
    opacity: float = None,
):
    _cmds.setAttr(f"{nodename}.overrideEnabled", enable)

    displaytype_args = [normal, template, reference]
    if sum(displaytype_args) not in [0, 1]:
        raise ValueError("Mutually exclusive parameters: normal, template, reference")
    if sum(displaytype_args) == 1:
        displaytype = displaytype_args.index(True)
        _cmds.setAttr(f"{nodename}.overrideDisplayType", displaytype)

    if boundingbox is not None:
        levelofdetail = {False: 0, True: 1}[boundingbox]
        _cmds.setAttr(f"{nodename}.overrideLevelOfDetail", levelofdetail)

    if shading is not None:
        _cmds.setAttr(f"{nodename}.overrideShading", shading)

    if texturing is not None:
        _cmds.setAttr(f"{nodename}.overrideTexturing", texturing)

    if playback is not None:
        _cmds.setAttr(f"{nodename}.overridePlayback", playback)

    if visible is not None:
        _cmds.setAttr(f"{nodename}.overrideVisibility", visible)

    if isinstance(color, (int, tuple)):
        color_is_rgb = isinstance(color, tuple)
        _cmds.setAttr(f"{nodename}.overrideRGBColors", color_is_rgb)

        if color_is_rgb:
            _cmds.setAttr(f"{nodename}.overrideColorRGB", *color)
            if opacity is not None:
                _cmds.setAttr(f"{nodename}.overrideColorA", opacity)
        else:
            _cmds.setAttr(f"{nodename}.overrideColor", color)


def add_attr_enum(
    nodename: str,
    longname: str,
    enums: list[str],
    default=0,
    shortname="",
    nicename="",
):
    _cmds.addAttr(
        nodename,
        longName=longname,
        shortName=shortname or longname,
        niceName=nicename or longname,
        attributeType="enum",
        enumName=":".join(enums),
        defaultValue=default,
        keyable=True,
        hidden=False,
    )
    return f"{nodename}.{longname}"


def add_attr_bool_as_enum(nodename, longname, default=0, shortname="", nicename=""):
    return add_attr_enum(
        nodename,
        longname=longname,
        shortname=shortname,
        nicename=nicename,
        enums=["False", "True"],
        default=default,
    )


def get_next_free_multi_index(nodeattr, start_index=0):
    next_free_index = _mel.eval(f"getNextFreeMultiIndex {nodeattr} {start_index}")
    return f"{nodeattr}[{next_free_index}]"
