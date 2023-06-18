import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px

import yaml
import pandas as pd
from warnings import warn
import datetime as dt
import seaborn as sns


def color_generator(name, items):
    colors = pd.Series(sns.color_palette(name, len(items)).as_hex())
    colors.index = items
    return colors


def hover_datetime_format(resampling):
    """
    Returns a formating string for plotly as a function of resampling.
    """
    if (resampling is None) | (resampling == "1h"):
        return "%d.%m.%Y %H:%M"
    elif (resampling == "1D") | (resampling == "1W"):
        return "%d.%m.%Y"
    elif (resampling == "1M") | (resampling == "MS"):
        return "%m.%Y"
    elif resampling == "1Q":
        return "Q%q.%Y"
    elif (resampling == "1Y") | (resampling == "AS"):
        return "%Y"
    else:
        raise UserWarning("Resampling factor " + resampling + " not supported!")


class Plot(object):
    """
    Object enabling the plotting.
    """

    def __init__(self, style: str = "plotly", settings: str = "settings/plotting.yml", default_saving=False):
        # Load yaml settings
        with open(settings, mode="r", encoding='utf8') as file:
            self.settings = yaml.load(file, Loader=yaml.FullLoader)

        # Plotting setting
        self.path = self.settings["path"]
        self.dpi = self.settings["dpi"]
        self.style = style
        self.fossil_only = False
        self.figsize = self.settings["figsize"]
        self.save_fig = default_saving

        if style == "seaborn":
            import seaborn as sns
            sns.set_style("darkgrid")
            sns.set_palette("deep")
            self.suptitle_kwargs = {"horizontalalignment": "left", "fontsize": "xx-large", "fontweight": "bold"}
            self.title_kwargs = {"loc": "left"}

        elif style == "plotly":
            # plotly settings
            pio.templates["ew_style"] = go.layout.Template(
                # layout=go.Layout(font=dict(family="IBM Plex Sans", size=12)),
                # layout=go.Layout(font=dict(family="Roboto", size=12)),
                layout=go.Layout(
                    font=dict(
                        family="Roboto",    # Arial, Helvetica, Roboto, IBM Plex Sans
                        size=12,
                    ),
                    paper_bgcolor='white',
                    plot_bgcolor='white',
                    yaxis={'side': 'right'},
                ),

                # layout_paper_bgcolor = 'rgba(0,0,0,1)',
                # layout_plot_bgcolor = 'rgba(0,0,0,1)',
            )
            # pio.templates.default = "seaborn+ew_style"
            pio.templates.default = "simple_white+ew_style"
            # pio.templates.default = "ew_style"

            self._plotly_settings = {
                "margin": dict(l=10, r=10, t=80, b=20),
                # "legend_right": dict(yanchor="top", y=0.99, xanchor="left", x=1.01),
                # "legend_bottom": dict(orientation="h",
                #                       yanchor="top", y=-0.2,
                #                       xanchor="left", x=0.02),
                "legend_pos": dict(orientation="h",
                                   yanchor="top", y=-0.2,
                                   xanchor="left", x=0.02),
                # "legend_pos": dict(orientation="v",
                #                    yanchor="top", y=1-0,
                #                    xanchor="left", x=1.2),
                "title": dict(x=0,
                              xanchor="left",
                              xref="paper",  #  container or paper
                              yanchor="bottom"),
                "fixed_range": dict(
                    # yaxis={"fixedrange": True},
                    # xaxis={"fixedrange": True}
                )
            }
        else:
            raise ValueError("Style not supported".format(style))

    def get_plot(self):
        fig = plt.figure(figsize=self.figsize)
        ax = fig.add_subplot(111)
        return fig, ax

    def pretty_and_save(self, fig, title, unit, xaxis_title=None, yaxis_title=None):
        """Include pretty titles and save the figure. """
        # Setting titles
        if fig is None:
            return None
        if self.style == "seaborn":
            if title is not None:
                plt.suptitle(title, **self.suptitle_kwargs, x=fig.subplotpars.left)

            if unit is not None:
                plt.title(unit, **self.title_kwargs)
            plt.tight_layout()
            if title is not None:
                plt.suptitle(title, **self.suptitle_kwargs, x=fig.subplotpars.left)
                # saving only when title is not empty
                if self.save_fig:
                    plt.savefig(self.path + title + ".png")

        elif self.style == "plotly":
            fig.update_layout(
                title={
                    "text": "<b>{}</b><br>{}".format(title, unit),
                    **self._plotly_settings["title"]},
                xaxis_title=xaxis_title,
                yaxis_title=yaxis_title,
                yaxis={
                    'side': 'right',
                    'zerolinewidth': 2},
                xaxis={
                    'zerolinewidth': 2},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=self._plotly_settings["legend_pos"],
                margin=self._plotly_settings["margin"],
                **self._plotly_settings["fixed_range"]
            )
            if self.save_fig:
                fig.write_image(self.path + title + ".png", scale=self.dpi/200)

        return fig

    def plotter(self, data, kind: str = "line", **kwargs):
        """
        Plot the dataframe df as matplotlib or plotly plot.
        Args:
            data: dataframe, series or dict to be plotted
            kind: supporting the style where we support "line", "bar", "area"
            **kwargs:
                title: title of the plot
                xaxis_title: title of the x axis
                yaxis_title: title of the y axis
                unit: unit will be shown as subtitle
                resampling: will be used for plotly hover information
                total: shows the total sum in the plot

        Returns:

        """

        # extrakt keywords from kwargs
        try:
            title = kwargs["title"]
        except KeyError:
            title = None
        try:
            xaxis_title = kwargs["xaxis_title"]
        except KeyError:
            xaxis_title = None
        try:
            yaxis_title = kwargs["yaxis_title"]
        except KeyError:
            yaxis_title = None
        try:
            xaxis_range = kwargs["xaxis_range"]
        except KeyError:
            xaxis_range = [None, None]
        try:
            yaxis_range = kwargs["yaxis_range"]
        except KeyError:
            yaxis_range = [None, None]
        try:
            unit = kwargs["unit"]
        except KeyError:
            unit = ""
        try:
            resampling = kwargs["resampling"]
        except KeyError:
            resampling = "1Y"
        try:
            total = kwargs["total"]
        except KeyError:
            total = False
        try:
            colors = kwargs["colors"]
        except KeyError:
            colors = self.settings["colors"]

        # transform Series into DataFrame if necessary
        if isinstance(data, pd.Series):
            data = data.to_frame(name=data.name)

        fig = go.Figure()

        # Check maximum for an approbiate hover format
        if isinstance(data, pd.DataFrame):
            my_max = data.fillna(0).abs().to_numpy().max()
        elif isinstance(data, dict):
            max_pols = []
            for key, df in data.items():
                max_pols.append(df.abs().to_numpy().max())
            my_max = np.max(max_pols)
        else:
            my_max = np.NaN
            warn(f"Type of {type(data)} not supported")

        if my_max < 1:
            y_format = "y:,.3f"
        elif my_max < 100:
            y_format = "y:,.2f"
        elif my_max < 1000:
            y_format = "y:,.1f"
        else:
            y_format = "y:,.2f"

        # Check resolution and put the dots in the middle of the plot (only supported for dataframes)
        settings = {}
        try:
            if isinstance(data, pd.DataFrame):
                timedelta = data.index[1] - data.index[0]
            elif isinstance(data, dict):
                first_element = list(data.keys())[0]
                timedelta = data[first_element].index[1] - data[first_element].index[0]
            else:
                timedelta = None
            if timedelta is not None:
                try:
                    if timedelta > dt.timedelta(days=360):  # Year
                        settings["xperiodalignment"] = "start"
                        settings["xperiod"] = "M12"
                    elif timedelta > dt.timedelta(days=88):  # Quartal
                        settings["xperiodalignment"] = "middle"
                        settings["xperiod"] = "M3"
                    elif timedelta > dt.timedelta(days=26):  # Month
                        settings["xperiodalignment"] = "start"
                        settings["xperiod"] = "M1"
                except TypeError:
                    pass
        except TypeError: # no timeseries data
            pass

        hovertemplate = \
            "%{x|" + hover_datetime_format(resampling) + "}<br>" + \
            "%{" + y_format + "} " + unit + "<br>"

        if isinstance(data, pd.DataFrame):
            items = data.columns
        elif isinstance(data, dict):
            items = data.keys()
        else:
            raise TypeError(f"Type of {type(data)} not supported.")

        if (kind == "bar") | (kind == "bar-stacked"):
            for c in items:

                if c in colors.keys():
                    settings["marker"] = {"color": colors[c]}

                data_column = data[c]
                fig.add_trace(go.Bar(
                    x=data_column.index,
                    y=data_column,
                    name=c,
                    # text=c,
                    hovertemplate=hovertemplate,
                    **settings
                ))

            if kind == "bar-stacked":
                fig.update_layout(barmode='stack')

        elif (kind == "barh") | (kind == "barh-stacked"):
            for c in items:

                if c in colors.keys():
                    settings["marker"] = {"color": colors[c]}

                data_column = data[c]
                fig.add_trace(go.Bar(
                    x=data_column,
                    y=data_column.index,
                    name=c,
                    orientation='h',
                    width=1,
                    # text=c,
                    # hovertemplate=hovertemplate,
                    **settings
                ))

            if kind == "bar-stacked":
                fig.update_layout(barmode='stack')

        elif kind == "line":
            for c in items:

                if c in colors.keys():
                    settings["line"] = {"color": colors[c]}
                else:
                    settings["line"] = {}

                data_column = data[c]
                fig.add_trace(go.Scatter(
                    x=data_column.index,
                    y=data_column,
                    name=c,
                    text=c,
                    hovertemplate=hovertemplate,
                    **settings
                ))

        elif kind == "marker":
            for c in items:

                if c in colors.keys():
                    settings["marker"] = {"color": colors[c]}
                else:
                    settings["marker"] = {}

                data_column = data[c]
                fig.add_trace(go.Scatter(
                    x=data_column.index,
                    y=data_column,
                    name=c,
                    text=c,
                    hovertemplate=hovertemplate,
                    mode="markers",
                    **settings
                ))

        elif kind == "step":
            for c in items:

                if c in colors.keys():
                    settings["line"] = {"color": colors[c],
                                        "shape": "hv"}
                else:
                    settings["line"] = {"shape": "hv"}

                data_column = data[c]
                fig.add_trace(go.Scatter(
                    x=data_column.index,
                    y=data_column,
                    name=c,
                    text=c,
                    hovertemplate=hovertemplate,
                    mode='lines',
                    **settings
                ))

        elif kind == "heatmap":

            fig = go.Figure(data=go.Heatmap(
                z=data.values,
                y=data.index,
                x=data.columns,
                colorscale='RdBu_r',
                # coloraxis_colorbar_x=-0.15,
                **settings
            ))
            # fig.update_layout(coloraxis_colorbar_xpad="right")

        elif kind == "area":
            # sort by deviation (only suppored for dataframes)
            if isinstance(data, pd.DataFrame):
                df = data.loc[:, data.std().sort_values(ascending=False).index]

            for c in items:

                if c in colors.keys():
                    settings["line"] = {"color": colors[c], "width": 0.5}
                else:
                    settings["line"] = {"width": 0.5}

                data_column = data[c]
                fig.add_trace(go.Scatter(
                    x=data_column.index,
                    y=data_column,
                    name=c,
                    text=c,
                    hoverinfo='x+y',
                    mode='lines',
                    stackgroup='one',
                    hovertemplate=hovertemplate,
                    **settings
                ))
            fig.update_layout(barmode='stack')

        else:
            raise TypeError(f"Kind {kind} not supported.")

        fig.update_layout(
            xaxis_range=xaxis_range,
            yaxis_range=yaxis_range,
        )

        fig = self.pretty_and_save(fig, title, unit, xaxis_title, yaxis_title)

        return fig