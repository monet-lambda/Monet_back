"""Draw ROOT canvas"""

###############################################################################
# (c) Copyright 2000-2020 CERN for the benefit of the LHCb Collaboration      #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
import glob

from bokeh.models import Label

from renderer.histo_draw.helpers import convert_color


def find_pattern_path(img_path, run_number):
    temp = img_path
    if temp.endswith(".root"):
        temp = temp.removesuffix(".root")

    # Check first by run range
    patfiles_perrange = glob.glob(
        temp + "_[0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9].root"
    )
    if patfiles_perrange:
        # run ranges
        run_ranges = {}
        for f in patfiles_perrange:
            run_ranges[f] = (
                int(f.split("_")[-2]),
                int(f.split("_")[-1].replace(".root", "")),
            )
        for key, value in run_ranges.items():
            if run_number >= value[0] and run_number <= value[1]:
                return key
    return temp + ".root"


def _draw_boxes(primitives, plot):
    """Draw TBox objects"""

    def is_box(p):
        return p.ClassName() == "TBox"

    boxes = list(filter(is_box, primitives))

    plot.multi_line(
        [[b.GetX1(), b.GetX2(), b.GetX2(), b.GetX1(), b.GetX1()] for b in boxes],
        [[b.GetY1(), b.GetY1(), b.GetY2(), b.GetY2(), b.GetY1()] for b in boxes],
        color=[convert_color(b.GetFillColor()) for b in boxes],
        line_color=[convert_color(b.GetLineColor()) for b in boxes],
        line_width=[b.GetLineWidth() for b in boxes],
    )

    filled_boxes = [b for b in boxes if b.GetFillStyle() != 0]
    plot.quad(
        top=[b.GetY1() for b in filled_boxes],
        bottom=[b.GetY2() for b in filled_boxes],
        left=[b.GetX1() for b in filled_boxes],
        right=[b.GetX2() for b in filled_boxes],
        fill_color=[
            "#%02x%02x%02x" % convert_color(b.GetFillColor()) for b in filled_boxes
        ],
        alpha=0.5,
        line_width=1,
    )


def _get_aligns(align_type):
    halign = int(align_type / 10)
    valign = align_type % 10

    if halign == 2:
        text_align = "center"
    elif halign == 3:
        text_align = "right"
    else:
        text_align = "left"

    if valign == 2:
        text_baseline = "middle"
    elif valign == 3:
        text_baseline = "top"
    else:
        text_baseline = "bottom"

    return text_align, text_baseline


def _draw_texts(primitives, plot):
    """Draw TText objects"""

    def is_text(p):
        return p.ClassName() == "TText"

    texts = list(filter(is_text, primitives))
    for text in texts:
        x_val = text.GetX()
        y_val = text.GetY()
        text_align, text_baseline = _get_aligns(text.GetTextAlign())
        if plot.y_range.start:
            if y_val + y_val / 20 < plot.y_range.start:
                plot.y_range.start = y_val + y_val / 20
        if plot.y_range.end:
            if y_val + y_val / 20 > plot.y_range.end:
                plot.y_range.end = y_val + y_val / 20
        if plot.x_range.start:
            if x_val + x_val / 20 < plot.x_range.start:
                plot.x_range.start = x_val + x_val / 20
        if plot.x_range.end:
            if x_val + x_val / 20 > plot.x_range.end:
                plot.x_range.end = x_val + x_val / 20
        label = Label(
            x=x_val,
            y=y_val,
            text=text.GetTitle(),
            text_font_size=f"{text.GetTextSize() * 200}pt",
            text_color=convert_color(text.GetTextColor()),
            text_align=text_align,
            text_baseline=text_baseline,
        )
        plot.add_layout(label)


def _draw_pavetexts(primitives, plot):
    """Draw TText objects"""

    def is_text(p):
        return p.ClassName() == "TPaveText"

    texts = list(filter(is_text, primitives))
    for text in texts:
        text_align, text_baseline = _get_aligns(text.GetLine(0).GetTextAlign())
        if text_align == "right":
            x_val = text.GetX2() + text.GetMargin() * (text.GetX1() - text.GetX2())
        elif text_align == "left":
            x_val = text.GetX1() + text.GetMargin() * (text.GetX2() - text.GetX1())
        else:
            x_val = 0.5 * (text.GetX1() + text.GetX2())
        if text_baseline == "top":
            y_val = text.GetY2() + text.GetMargin() * (text.GetY1() - text.GetY2())
        elif text_baseline == "bottom":
            y_val = text.GetY1() + text.GetMargin() * (text.GetY2() - text.GetY1())
        else:
            y_val = 0.5 * (text.GetY1() + text.GetY2())

        y_val = text.GetY1()
        the_text = text.GetLine(0).GetTitle()
        plot.text(
            x_val,
            y_val,
            text=[the_text],
            text_align=text_align,
            color=convert_color(text.GetLine(0).GetTextColor()),
        )


ROOT_STYLE_TO_BOKEH_STYLE = {
    1: "solid",
    2: (2, 2),
    3: (1, 1),
    5: (3, 2, 1, 2),
    6: (3, 2, 1, 2, 1, 2, 1, 2),
    7: (3, 2),
    8: (3, 2, 1, 2, 1, 2),
    9: (10, 2),
    10: (10, 3, 1, 3),
}

ROOT_MARKER_TO_BOKEH_MARKER = {
    1: "dot",
    2: "cross",  #                    +                    kPlus
    3: "asterisk",  #                    *                    kStar
    4: "circle",  #                    o                    kCircle
    5: "x",  #                 x                    kMultiply
    6: "dot",  #                    small dot            kFullDotSmall
    7: "dot",  #                    medium dot           kFullDotMedium
    8: "dot",  #                    large scalable dot   kFullDotLarge
    9: "dot",  #              large scalable dot
    10: "dot",
    11: "dot",
    12: "dot",
    13: "dot",
    14: "dot",
    15: "dot",
    16: "dot",
    17: "dot",
    18: "dot",
    19: "dot",
    20: "circle",  #                    full circle          kFullCircle
    21: "square",  #                    full square          kFullSquare
    22: "triangle",  #                    full triangle up     kFullTriangleUp
    23: "inverted_triangle",  #                    full triangle down   kFullTriangleDown
    24: "circle",  #                    open circle          kOpenCircle
    25: "square",  #                    open square          kOpenSquare
    26: "triangle",  #                    open triangle up     kOpenTriangleUp
    27: "diamond",  #                    open diamond         kOpenDiamond
    28: "plus",  #                    open cross           kOpenCross
    29: "star",  #                    full star            kFullStar
    30: "star",  #                    open star            kOpenStar
    31: "asterisk",  #                    *
    32: "inverted_triangle",  #                    open triangle down   kOpenTriangleDown
    33: "diamond",  #                    full diamond         kFullDiamond
    34: "plus",  #                    full cross           kFullCross
    35: "diamond_cross",  #                    open diamond cross   kOpenDiamondCross
    36: "square_x",  #                    open square diagonal kOpenSquareDiagonal
    37: "triangle_pin",  #                    open three triangle  kOpenThreeTriangles
    38: "dot",  #                    octagon with cross   kOctagonCross
    39: "dot",  #                    full three triangles kFullThreeTriangles
    40: "dot",  #                    open four triangleX  kOpenFourTrianglesX
    41: "dot",  #                    full four triangleX  kFullFourTrianglesX
    42: "dot",  #                    open double diamond  kOpenDoubleDiamond
    43: "dot",  #                   full double diamond  kFullDoubleDiamond
    44: "dot",  #                    open four triangle+  kOpenFourTrianglesPlus
    45: "dot",  #                    full four triangle+  kFullFourTrianglesPlus
    46: "dot",  #                   open cross X         kOpenCrossX
    47: "dot",  #                    full cross X         kFullCrossX
    48: "dot",  #                    four squares X       kFourSquaresX
    49: "dot",  #                    four squares+        kFourSquaresPlus
}


def _draw_polymarkers(primitives, plot):
    """Draw TPolyMarker"""

    def is_polymarker(p):
        return p.ClassName() == "TPolyMarker"

    markers = list(filter(is_polymarker, primitives))

    for m in markers:
        plot.scatter(
            [m.GetX()[i] for i in range(m.Size())],
            [m.GetY()[i] for i in range(m.Size())],
            size=m.GetMarkerSize() * 10,
            color=convert_color(m.GetMarkerColor()),
            marker=ROOT_MARKER_TO_BOKEH_MARKER[m.GetMarkerStyle()],
        )


def _get_line_style(root_style):
    """Get bokeh line style from ROOT style"""
    return ROOT_STYLE_TO_BOKEH_STYLE.get(root_style, "dotted")


def _draw_lines(primitives, plot):
    def is_line(p):
        return p.ClassName() == "TLine"

    lines = list(filter(is_line, primitives))

    lines_dict = {}  # helps split lines by style

    for line in lines:
        if _get_line_style(line.GetLineStyle()) not in lines_dict:
            lines_dict[_get_line_style(line.GetLineStyle())] = []
        lines_dict[_get_line_style(line.GetLineStyle())].append(line)

    for style, s in lines_dict.items():
        if s:
            plot.multi_line(
                [[line.GetX1(), line.GetX2()] for line in s],
                [[line.GetY1(), line.GetY2()] for line in s],
                color=[convert_color(line.GetLineColor()) for line in s],
                line_width=[line.GetLineWidth() for line in s],
                line_dash=[style] * len(s),
            )


def _draw_ellipses(primitives, plot):
    def is_ellipse(p):
        return p.ClassName() == "TEllipse"

    ellipses = list(filter(is_ellipse, primitives))
    ellipse_dict = {}  # helps split lines by style

    for ellipse in ellipses:
        if _get_line_style(ellipse.GetLineStyle()) not in ellipse_dict:
            ellipse_dict[_get_line_style(ellipse.GetLineStyle())] = []
        ellipse_dict[_get_line_style(ellipse.GetLineStyle())].append(ellipse)

    for style, s in ellipse_dict.items():
        if s:
            plot.ellipse(
                [e.GetX1() for e in ellipse_dict[style]],
                [e.GetY1() for e in ellipse_dict[style]],
                width=[2.0 * e.GetR1() for e in ellipse_dict[style]],
                height=[2.0 * e.GetR2() for e in ellipse_dict[style]],
                color=[convert_color(e.GetLineColor()) for e in s],
                fill_alpha=[0.0 if e.IsTransparent() else 1.0 for e in s],
                fill_color=[convert_color(e.GetFillColor()) for e in s],
                line_width=1.0,
                alpha=1.0,
                line_dash=style,
            )


def is_2dhisto(p):
    return p.ClassName() == "TH2D"


def draw_root_canvas_on_plot(canvas, plot):
    """draw ROOT canvas on plot"""
    primitives = list(canvas.GetListOfPrimitives())

    histos_2d = list(filter(is_2dhisto, primitives))
    if histos_2d:
        for i in histos_2d:
            the_list = i.GetListOfFunctions()
            if the_list:
                primitives.extend(the_list)

    _draw_boxes(primitives, plot)
    _draw_texts(primitives, plot)
    _draw_lines(primitives, plot)
    _draw_ellipses(primitives, plot)
    _draw_polymarkers(primitives, plot)
    _draw_pavetexts(primitives, plot)
