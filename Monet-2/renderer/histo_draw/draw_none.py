
from bokeh.models import Label
from bokeh.plotting import figure


def render_none(
    histodb_hist,
    histo_data,
    draw_params,
    ref_data=None,
    highlight=None,
    motherplot=None,
    trend=False,
    is_mother=False,
    extratext="",
    comparison_data=None
):
    data = histo_data["data"]["key_data"]
    title = data.get("title", "")

    if not motherplot or isinstance(motherplot, Exception):
        plot = figure(
            sizing_mode="stretch_both",
            title=title + extratext,
            tools="pan,wheel_zoom,box_zoom,reset",
            active_drag="box_zoom",
            toolbar_location=None,
        )
        texte = Label(
            x=50,
            y=50,
            x_units="screen",
            y_units="screen",
            text="Not found",
            border_line_color="black",
            border_line_alpha=1.0,
            background_fill_color="white",
            background_fill_alpha=1.0,
        )

        plot.add_layout(texte)
        plot.scatter(0, 0, size=0)

    else:
        plot = motherplot
        plot.title.text = title

    plot.toolbar.logo = None

    return plot
