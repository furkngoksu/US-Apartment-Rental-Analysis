import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import folium
from folium.plugins import MarkerCluster

# Load cleaned dataset
df = pd.read_csv("data/rents_cleaned.csv")
df["time"] = pd.to_datetime(df["time"])

# ----------------------------------------------------------------
# 1) HELPER FUNCTIONS FOR PLOTLY GRAPHS
# ----------------------------------------------------------------


def choropleth_map(df: pd.DataFrame, selected_city) -> go.Figure:
    """
    Creates a Choropleth map of average rental data by state.
    """
    filtered_data = (
        df.groupby("state")
        .agg({"price": "mean", "bedrooms": "mean", "square_feet": "mean"})
        .reset_index()
    )

    filtered_data["price"] = filtered_data["price"].round(1).astype(str)
    filtered_data["bedrooms"] = filtered_data["bedrooms"].round(1).astype(str)
    filtered_data["square_feet"] = filtered_data["square_feet"].round(1).astype(str)

    filtered_data["text"] = (
        "State: "
        + filtered_data["state"]
        + "<br>Price: "
        + filtered_data["price"]
        + " USD"
        + "<br>Bedrooms: "
        + filtered_data["bedrooms"]
        + "<br>Square Feet: "
        + filtered_data["square_feet"]
    )

    fig = go.Figure(
        data=go.Choropleth(
            locations=filtered_data["state"],
            z=filtered_data["price"].astype(float),
            locationmode="USA-states",
            colorscale="Viridis",
            autocolorscale=False,
            text=filtered_data["text"],
            marker_line_color="white",
        )
    )

    fig.update_layout(
        title_text="Average Apartment Prices by State",
        geo=dict(
            scope="usa",
            projection=go.layout.geo.Projection(type="albers usa"),
            showlakes=True,
            lakecolor="rgb(255, 255, 255)",
            bgcolor="#2a3e74",
        ),
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        paper_bgcolor="#2a3e74",
        font=dict(color="white"),
    )
    return fig


def bar_chart(filtered_df: pd.DataFrame) -> go.Figure:
    """
    Creates a bar chart of average price over time
    (with 3-month rolling average) using the *filtered* dataframe.
    """
    if filtered_df.empty:
        return go.Figure(layout={"title": "No data available"})

    avg_price = filtered_df.groupby(filtered_df["time"].dt.to_period("M"))[
        "price"
    ].mean()
    avg_price.index = avg_price.index.to_timestamp()

    rolling_avg = avg_price.rolling(window=3).mean()

    all_dates = avg_price.index

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=avg_price.index,
            y=avg_price,
            name="Average Price",
            marker=dict(color="#29b6f6"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=rolling_avg.index,
            y=rolling_avg,
            mode="lines",
            name="Rolling Avg (3 months)",
            line=dict(color="#ffbb00"),
        )
    )

    fig.update_layout(
        title="Average Price Over Time",
        xaxis_title="Date",
        yaxis_title="Average Price (USD)",
        xaxis=dict(
            tickmode="array",
            tickvals=all_dates,
            tickformat="%b %Y",
            tickangle=45,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.2)",  # Same faint color for y-axis
            gridwidth=0.2,
        ),
        paper_bgcolor="#2a3e74",
        plot_bgcolor="#2a3e74",
        font=dict(color="white"),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=1.1, bgcolor="#2a3e74"),
        bargap=0.2,
    )
    return fig


def heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Creates a heatmap of the correlation matrix with correlation values.
    """
    correlation_matrix = df[["price", "bedrooms", "bathrooms", "square_feet"]].corr()

    fig = go.Figure(
        data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.columns,
            zmin=-1,
            zmax=1,
            colorscale="Viridis",
            text=correlation_matrix.round(2).values,
            hoverinfo="text",
        )
    )

    # Add annotations for each cell in the heatmap
    annotations = []
    for i, row in enumerate(correlation_matrix.values):
        for j, val in enumerate(row):
            annotations.append(
                dict(
                    x=correlation_matrix.columns[j],
                    y=correlation_matrix.columns[i],
                    text=str(round(val, 2)),
                    font=dict(color="rgb(40,40,40)"),
                    showarrow=False,
                )
            )

    fig.update_layout(
        title="Correlation Matrix",
        annotations=annotations,
        plot_bgcolor="#2a3e74",
        paper_bgcolor="#2a3e74",
        font=dict(color="white"),
        legend=dict(bgcolor="#2a3e74"),
    )

    return fig


def scatter_plot(df: pd.DataFrame) -> go.Figure:
    """
    Creates a scatter plot of Price vs. Square Feet from the filtered data.
    """
    if df.empty:
        return go.Figure(layout={"title": "No data available"})

    fig = px.scatter(
        df,
        x="square_feet",
        y="price",
        title="Price vs Square Feet",
        labels={"square_feet": "Square Feet", "price": "Price (USD)"},
    )

    fig.update_traces(marker=dict(color="#ffbb00"))

    fig.update_layout(
        plot_bgcolor="#2a3e74",
        paper_bgcolor="#2a3e74",
        font=dict(color="white"),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.2)",  # Same faint color for y-axis
            gridwidth=0.2,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.2)",  # Same faint color for y-axis
            gridwidth=0.2,
        ),
    )
    return fig


# ----------------------------------------------------------------
# 2) NEW HELPER FUNCTION FOR FOLIUM MAP
# ----------------------------------------------------------------


def create_folium_map(filtered_df: pd.DataFrame) -> str:
    """
    Creates and returns an HTML representation of a Folium map
    showing city-level average prices as circles on a cluster layer.
    """
    if filtered_df.empty:
        return "<h4>No data available on the map</h4>"

    # 1. Compute average price by city
    city_avg = filtered_df.groupby("cityname")["price"].mean().reset_index()
    city_avg.rename(columns={"price": "avg_price"}, inplace=True)

    # 2. Compute average latitude/longitude by city
    location_data = (
        filtered_df.groupby("cityname")[["latitude", "longitude"]].mean().reset_index()
    )

    # 3. Merge them
    merged_df = pd.merge(city_avg, location_data, on="cityname", how="left")

    # 4. Create the Folium map
    center_lat = merged_df["latitude"].mean()
    center_lon = merged_df["longitude"].mean()
    bubble_map = folium.Map(location=[center_lat, center_lon], zoom_start=5)

    marker_cluster = MarkerCluster().add_to(bubble_map)

    # 5. Add circle markers
    for idx, row in merged_df.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=row["avg_price"] / 500,  # scale factor for bubble size
            popup=f"{row['cityname']} - Avg. Price: ${row['avg_price']:.2f}",
            color="blue",
            fill=True,
            fill_color="cyan",
        ).add_to(marker_cluster)

    return bubble_map._repr_html_()


# ----------------------------------------------------------------
# 2B) NEW HELPER FUNCTION FOR THE "TOP 10" BAR CHART
# ----------------------------------------------------------------


def top_locations_bar(df: pd.DataFrame, group_col: str = "cityname") -> go.Figure:
    """
    Groups by either 'cityname' or 'state', then plots Top 10
    by mean rental price in descending order.
    """
    grouped = (
        df.groupby(group_col)["price"]
        .agg(["mean", "median", "count"])
        .reset_index()
        .sort_values(by="mean", ascending=False)
        .head(10)
    )

    fig = go.Figure(
        go.Bar(
            x=grouped["mean"],
            y=grouped[group_col],
            orientation="h",
            text=[f"${v:,.0f}" for v in grouped["mean"]],
            textposition="auto",
            marker=dict(color="#29b6f6"),
        )
    )

    fig.update_layout(
        title=f"Top 10 {group_col.capitalize()} by Avg. Rental Price",
        xaxis_title="Avg. Rental Price (USD)",
        yaxis_title=group_col.capitalize(),
        paper_bgcolor="#2a3e74",
        plot_bgcolor="#2a3e74",
        font=dict(color="white"),
        margin=dict(l=100, r=20, t=60, b=40),
    )
    # Reverse the y-axis so the highest bar is at the top
    fig.update_yaxes(autorange="reversed")
    return fig


# ----------------------------------------------------------------
# 3) SETUP & APP LAYOUT
# ----------------------------------------------------------------

min_price, max_price = int(df["price"].min()), int(df["price"].max())
min_square_feet, max_square_feet = int(df["square_feet"].min()), int(
    df["square_feet"].max()
)

app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,400;0,500;0,700;1,400;1,700&display=swap"
    ],
)

PAGE_STYLE = {
    "backgroundColor": "#1f2c56",
    "color": "black",
    "fontFamily": "Roboto, Arial, sans-serif",
    "padding": "5px 110px",
    "margin": "0",
}

GRAPH_BOX_STYLE = {
    "borderRadius": "20px",
    "backgroundColor": "#2a3e74",
    "padding": "20px",
    "marginBottom": "40px",
    "height": "500px",
    "width": "46%",
}

GRAPH_STYLE = {
    "height": "100%",
    "width": "100%",
}

app.layout = html.Div(
    style=PAGE_STYLE,
    children=[
        # Header
        html.Div(
            style={"textAlign": "center", "padding": "10px"},
            children=[
                html.H1(
                    "Rental Apartments Data Dashboard",
                    style={"margin": "0", "padding": "10px", "color": "white"},
                ),
            ],
        ),
        # Filters row (with Count)
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "marginBottom": "40px",
                "height": "60px",
                "backgroundColor": "#2a3e74",
                "padding": "20px",
                "borderRadius": "20px",
            },
            children=[
                # State filter
                html.Div(
                    children=[
                        html.Label(
                            "State",
                            style={
                                "color": "white",
                                "fontSize": "14px",
                                "paddingBottom": "5px",
                                "display": "block",
                            },
                        ),
                        dcc.Dropdown(
                            id="state-filter",
                            options=[
                                {"label": state, "value": state}
                                for state in df["state"].unique()
                            ],
                            placeholder="Select a state",
                            style={
                                "width": "100%",
                                "fontSize": "14px",
                                "borderRadius": "15px",
                            },
                        ),
                    ],
                    style={
                        "flex": "1",
                        "padding": "5px",
                        "marginRight": "10px",
                    },
                ),
                # City filter
                html.Div(
                    children=[
                        html.Label(
                            "City",
                            style={
                                "color": "white",
                                "fontSize": "14px",
                                "paddingBottom": "5px",
                                "display": "block",
                            },
                        ),
                        dcc.Dropdown(
                            id="city-filter",
                            options=[
                                {"label": city, "value": city}
                                for city in df["cityname"].unique()
                            ],
                            placeholder="Select a city",
                            style={
                                "width": "100%",
                                "fontSize": "14px",
                                "borderRadius": "15px",
                            },
                        ),
                    ],
                    style={
                        "flex": "1",
                        "padding": "5px",
                        "marginRight": "10px",
                    },
                ),
                # Bedroom filter
                html.Div(
                    children=[
                        html.Label(
                            "Bedrooms",
                            style={
                                "color": "white",
                                "fontSize": "14px",
                                "paddingBottom": "5px",
                                "display": "block",
                            },
                        ),
                        dcc.Dropdown(
                            id="bedroom-filter",
                            options=[
                                {"label": f"{bedroom} Bedrooms", "value": bedroom}
                                for bedroom in sorted(df["bedrooms"].unique())
                            ],
                            placeholder="Select number of bedrooms",
                            style={
                                "width": "100%",
                                "fontSize": "14px",
                                "borderRadius": "15px",
                            },
                        ),
                    ],
                    style={
                        "flex": "1",
                        "padding": "5px",
                        "marginRight": "20px",
                    },
                ),
                # Price range filter
                html.Div(
                    children=[
                        html.Label(
                            "Price Range",
                            style={
                                "color": "white",
                                "fontSize": "14px",
                                "marginBottom": "10px",
                                "display": "block",
                            },
                        ),
                        dcc.RangeSlider(
                            id="price-filter",
                            min=min_price,
                            max=max_price,
                            step=100,
                            marks={
                                i: {"label": f"${i}", "style": {"color": "#d1a324"}}
                                for i in range(
                                    min_price,
                                    max_price + 1,
                                    max((max_price - min_price) // 5, 1),
                                )
                            },
                            value=[min_price, max_price],
                            tooltip={"always_visible": False},
                        ),
                    ],
                    style={
                        "flex": "2",
                        "padding": "5px",
                        "marginRight": "20px",
                    },
                ),
                # Square Feet Range
                html.Div(
                    children=[
                        html.Label(
                            "Square Feet Range",
                            style={
                                "color": "white",
                                "fontSize": "14px",
                                "marginBottom": "10px",
                                "display": "block",
                            },
                        ),
                        dcc.RangeSlider(
                            id="square-feet-filter",
                            min=min_square_feet,
                            max=max_square_feet,
                            step=50,
                            marks={
                                i: {"label": str(i), "style": {"color": "#d1a324"}}
                                for i in range(
                                    min_square_feet,
                                    max_square_feet + 1,
                                    max((max_square_feet - min_square_feet) // 5, 1),
                                )
                            },
                            value=[min_square_feet, max_square_feet],
                            tooltip={"always_visible": False},
                        ),
                    ],
                    style={"flex": "2", "padding": "5px"},
                ),
                # Count of filtered listings
                html.Div(
                    style={
                        "flex": "1",
                        "padding": "5px",
                        "textAlign": "center",
                    },
                    children=[
                        html.Div(
                            "Number of Rentals",
                            style={
                                "fontSize": "16px",
                                "color": "white",
                                "marginBottom": "5px",
                            },
                        ),
                        html.Div(
                            id="renting-count",
                            style={
                                "fontSize": "24px",
                                "fontWeight": "bold",
                                "color": "#00bfff",
                            },
                        ),
                    ],
                ),
            ],
        ),
        # 1st row of graphs
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "width": "100%",
                "margin": "0 auto",
            },
            children=[
                html.Div(
                    style={**GRAPH_BOX_STYLE},
                    children=[
                        dcc.Graph(
                            id="choropleth-map",
                            style={**GRAPH_STYLE},
                            config={"displayModeBar": False},
                        )
                    ],
                ),
                html.Div(
                    style={**GRAPH_BOX_STYLE},
                    children=[
                        dcc.Graph(
                            id="bar-graph",
                            style={**GRAPH_STYLE},
                            config={"displayModeBar": False},
                        )
                    ],
                ),
            ],
        ),
        # 2nd row of graphs
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "width": "100%",
                "margin": "0 auto",
            },
            children=[
                html.Div(
                    style={**GRAPH_BOX_STYLE},
                    children=[
                        dcc.Graph(
                            id="heatmap",
                            style={**GRAPH_STYLE},
                            config={"displayModeBar": False},
                        )
                    ],
                ),
                html.Div(
                    style={**GRAPH_BOX_STYLE},
                    children=[
                        dcc.Graph(
                            id="scatter-plot",
                            style={**GRAPH_STYLE},
                            config={"displayModeBar": False},
                        )
                    ],
                ),
            ],
        ),
        # 3rd row: 75% Folium Map, 25% New Bar Chart
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "width": "100%",
                "margin": "0 auto",
            },
            children=[
                # Folium map (75%)
                html.Div(
                    style={**GRAPH_BOX_STYLE, "width": "70%"},
                    children=[
                        html.Iframe(
                            id="usa-map",
                            style={
                                "width": "100%",
                                "height": "100%",
                                "border": "none",
                                "borderRadius": "20px",
                            },
                        )
                    ],
                ),
                # New bar chart (25%)
                html.Div(
                    style={**GRAPH_BOX_STYLE, "width": "23%"},
                    children=[
                        # Radio to pick between city or state
                        dcc.RadioItems(
                            id="location-radio",
                            options=[
                                {"label": "Cities", "value": "cityname"},
                                {"label": "States", "value": "state"},
                            ],
                            value="cityname",
                            labelStyle={"display": "inline", "color": "white"},
                            style={"textAlign": "center"},
                        ),
                        dcc.Graph(
                            id="top-locations-bar",
                            style={**GRAPH_STYLE},
                            config={"displayModeBar": False},
                        ),
                    ],
                ),
            ],
        ),
    ],
)

# ----------------------------------------------------------------
# 4) CALLBACKS
# ----------------------------------------------------------------


# Update city dropdown options based on chosen state
@app.callback(Output("city-filter", "options"), [Input("state-filter", "value")])
def update_city_options(selected_state):
    if selected_state:
        filtered_cities = df[df["state"] == selected_state]["cityname"].unique()
        return [{"label": c, "value": c} for c in sorted(filtered_cities)]
    else:
        all_cities = df["cityname"].unique()
        return [{"label": c, "value": c} for c in sorted(all_cities)]


# Auto-select the state if a city is chosen
@app.callback(
    Output("state-filter", "value"),
    Input("city-filter", "value"),
    prevent_initial_call=True,
)
def update_state_value(selected_city):
    if selected_city:
        state_of_city = df.loc[df["cityname"] == selected_city, "state"].iloc[0]
        return state_of_city
    return None


# Main callback for updating the first four graphs + Folium map
@app.callback(
    [
        Output("choropleth-map", "figure"),
        Output("bar-graph", "figure"),
        Output("heatmap", "figure"),
        Output("scatter-plot", "figure"),
        Output("usa-map", "srcDoc"),
    ],
    [
        Input("city-filter", "value"),
        Input("bedroom-filter", "value"),
        Input("price-filter", "value"),
        Input("square-feet-filter", "value"),
        Input("state-filter", "value"),
    ],
)
def update_graphs(
    selected_city, selected_bedroom, price_range, square_feet_range, selected_state
):
    # Make a filtered copy of the DataFrame
    filtered_df = df.copy()

    if selected_city:
        filtered_df = filtered_df[filtered_df["cityname"] == selected_city]
    if selected_bedroom:
        filtered_df = filtered_df[filtered_df["bedrooms"] == selected_bedroom]
    if price_range:
        filtered_df = filtered_df[
            (filtered_df["price"] >= price_range[0])
            & (filtered_df["price"] <= price_range[1])
        ]
    if square_feet_range:
        filtered_df = filtered_df[
            (filtered_df["square_feet"] >= square_feet_range[0])
            & (filtered_df["square_feet"] <= square_feet_range[1])
        ]
    if selected_state:
        filtered_df = filtered_df[filtered_df["state"] == selected_state]

    # Plotly figures
    choropleth_fig = choropleth_map(filtered_df, selected_city)
    bar_fig = bar_chart(filtered_df)
    heatmap_fig = heatmap(df)  # uses the entire dataset
    scatter_fig = scatter_plot(filtered_df)

    # Folium map (HTML string)
    folium_map_html = create_folium_map(filtered_df)

    return choropleth_fig, bar_fig, heatmap_fig, scatter_fig, folium_map_html


# Callback for the top-locations-bar
@app.callback(Output("top-locations-bar", "figure"), Input("location-radio", "value"))
def update_top_locations_bar(location_type):
    return top_locations_bar(df, group_col=location_type)


# Callback to display the Number of Rentals
@app.callback(
    Output("renting-count", "children"),
    [
        Input("state-filter", "value"),
        Input("city-filter", "value"),
        Input("bedroom-filter", "value"),
        Input("price-filter", "value"),
        Input("square-feet-filter", "value"),
    ],
)
def update_renting_count(
    selected_state, selected_city, selected_bedroom, price_range, square_feet_range
):
    filtered_df = df.copy()

    if selected_state:
        filtered_df = filtered_df[filtered_df["state"] == selected_state]
    if selected_city:
        filtered_df = filtered_df[filtered_df["cityname"] == selected_city]
    if selected_bedroom:
        filtered_df = filtered_df[filtered_df["bedrooms"] == selected_bedroom]
    if price_range:
        filtered_df = filtered_df[
            (filtered_df["price"] >= price_range[0])
            & (filtered_df["price"] <= price_range[1])
        ]
    if square_feet_range:
        filtered_df = filtered_df[
            (filtered_df["square_feet"] >= square_feet_range[0])
            & (filtered_df["square_feet"] <= square_feet_range[1])
        ]

    # Number of rentings
    count_value = len(filtered_df)
    # Format with commas (e.g. 10,000)
    count_formatted = f"{count_value:,}"

    # Return only the formatted number; the label is in the layout above
    return count_formatted


if __name__ == "__main__":
    app.run_server(debug=True, port=8070)
