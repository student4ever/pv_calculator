import streamlit as st
from src.plot import Plot
import plotly.graph_objects as go
import pandas as pd
import scipy.stats as stats
import datetime as dt


p = Plot().plotter


def get_st_download_link(df, name="data"):
    @st.cache_data
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv(index=True, sep=";", decimal=",").encode('utf-8-sig')

    csv = convert_df(df)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name=name+'.csv',
        mime='text/csv',
    )
    # st.markdown(get_table_download_link_csv(df), unsafe_allow_html=True)


def fig_and_link(df, add_on=None, download_link=True, **kwargs):
    """
    Make a plot and
    Args:
        df:
        add_on:
        **kwargs:

    Returns:

    """
    df = df.copy()

    if isinstance(df, pd.Series):
        try:
            name = kwargs["name"]
        except KeyError:
            name = "data"
        df = df.to_frame(name=name)

    try:
        use_container_width = kwargs["use_container_width"]
    except KeyError:
        use_container_width = True

    fig = p(df, **kwargs)

    if add_on is not None:
        for i in add_on:
            d = add_on[i]
            df.loc[:, d["name"]] = d["data"]
            if "line" in i:
                fig.add_trace(go.Scatter(
                    x=d["data"].index,
                    y=d["data"],
                    name=d["name"],
                    # text=d["name"],
                    # hovertemplate=hovertemplate,
                    line_color=d["color"],
                    line_width=d["width"],
                ))
            if "step" in i:
                fig.add_trace(go.Scatter(
                    x=d["data"].index,
                    y=d["data"],
                    name=d["name"],
                    # text=d["name"],
                    # hovertemplate=hovertemplate,
                    line_color=d["color"],
                    line_width=d["width"],
                    line_shape='hvh',
                ))
            if "fill_between" in i:
                fig.add_trace(go.Scatter(
                    x=d["data"].index,
                    y=d["data"],
                    name=d["name"],
                    fill='tonexty',
                    # text=d["name"],
                    # hovertemplate=hovertemplate,
                    line_color=d["color"],
                    line_width=d["width"],
                ))
                # df[d["name"]] = d["data"]

    fig.update_layout(height=600, width=400)

    st.plotly_chart(fig, use_container_width=use_container_width)

    if download_link:
        from io import BytesIO
        # Create an in-memory buffer
        import io

        buffer = io.BytesIO()

        # Save the figure as a pdf to the buffer
        fig.write_image(file=buffer, format="svg", width=600, height=500) # width=600, height=350

        st.download_button(
            label="Download SVG",
            data=buffer,
            file_name="figure.svg",
            mime="application/svg",
        )

        try:
            name = kwargs["title"] + " in " + kwargs["unit"]
        except KeyError:
            name = "data"

        get_st_download_link(df, name)


def get_trend_of_ts(df):
    df = df.copy()
    idx = df.index

    # To perform the linear regression we need the dates to be numeric
    df.index = df.index.map(dt.date.toordinal)
    # Perform linear regression
    slope, y0, r, p, stderr = stats.linregress(df.index, df.iloc[:, 0])

    # x co-ordinates for the start and end of the line
    x_endpoints = pd.Series([df.index[0], df.index[-1]])

    # Compute predicted values from linear regression
    y_endpoints = y0 + slope * x_endpoints

    s1 = pd.Series(index=[idx[0], idx[-1]], data=y_endpoints.values)
    return s1