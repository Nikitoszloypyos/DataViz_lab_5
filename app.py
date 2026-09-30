from dash import Dash, Input, Output, dash_table, dcc, html

from dashboard_data import (
    filter_data,
    load_data,
    spatial_heatmap_figure,
    summary_metrics,
    table_records,
    temperature_histogram_figure,
    type_counts_figure,
    wind_box_figure,
)


DATA = load_data()
TYPE_OPTIONS = DATA["Тип пожара"].value_counts().index.tolist()
TEMP_MIN = float(DATA["temperature_c"].min())
TEMP_MAX = float(DATA["temperature_c"].max())
PRECIP_MIN = float(DATA["precipitation_mm"].min())
PRECIP_MAX = float(DATA["precipitation_mm"].max())

CARD_STYLE = {
    "backgroundColor": "white",
    "border": "1px solid #E2E8F0",
    "borderRadius": "14px",
    "boxShadow": "0 6px 18px rgba(15, 23, 42, 0.06)",
    "padding": "18px",
    "minWidth": "190px",
    "flex": "1",
}

GRAPH_STYLE = {
    "backgroundColor": "white",
    "border": "1px solid #E2E8F0",
    "borderRadius": "14px",
    "boxShadow": "0 6px 18px rgba(15, 23, 42, 0.05)",
    "padding": "8px",
    "minWidth": "420px",
    "flex": "1",
}


def metric_card(label: str, component_id: str) -> html.Div:
    return html.Div(
        [
            html.Div(label, style={"color": "#64748B", "fontSize": "14px"}),
            html.Div(
                id=component_id,
                style={
                    "color": "#0F172A",
                    "fontSize": "30px",
                    "fontWeight": "700",
                    "marginTop": "8px",
                },
            ),
        ],
        style=CARD_STYLE,
    )


app = Dash(__name__, title="Пожары в России — Dash")
server = app.server

app.layout = html.Div(
    [
        html.Div(
            [
                html.H1(
                    "Пожары в России",
                    style={"margin": "0", "fontSize": "32px", "color": "#0F172A"},
                ),
                html.P(
                    "Интерактивный дашборд по данным FiresRu",
                    style={"margin": "8px 0 0", "color": "#64748B"},
                ),
            ]
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Тип пожара", style={"fontWeight": "600"}),
                        dcc.Dropdown(
                            id="type-filter",
                            options=[{"label": value, "value": value} for value in TYPE_OPTIONS],
                            value=TYPE_OPTIONS,
                            multi=True,
                            clearable=True,
                            placeholder="Выберите типы",
                        ),
                    ],
                    style={"flex": "2", "minWidth": "300px"},
                ),
                html.Div(
                    [
                        html.Label("Температура, °C", style={"fontWeight": "600"}),
                        dcc.RangeSlider(
                            id="temperature-filter",
                            min=TEMP_MIN,
                            max=TEMP_MAX,
                            step=1,
                            value=[TEMP_MIN, TEMP_MAX],
                            tooltip={"placement": "bottom", "always_visible": False},
                            marks={int(TEMP_MIN): f"{TEMP_MIN:.0f}", 0: "0", 15: "15", int(TEMP_MAX): f"{TEMP_MAX:.0f}"},
                        ),
                    ],
                    style={"flex": "2", "minWidth": "300px"},
                ),
                html.Div(
                    [
                        html.Label("Осадки, мм", style={"fontWeight": "600"}),
                        dcc.RangeSlider(
                            id="precipitation-filter",
                            min=PRECIP_MIN,
                            max=PRECIP_MAX,
                            step=0.1,
                            value=[PRECIP_MIN, PRECIP_MAX],
                            tooltip={"placement": "bottom", "always_visible": False},
                            marks={0: "0", 5: "5", 10: "10", 15: "15", 20: "20", 25: "25"},
                        ),
                    ],
                    style={"flex": "2", "minWidth": "300px"},
                ),
            ],
            style={
                "display": "flex",
                "gap": "26px",
                "flexWrap": "wrap",
                "backgroundColor": "white",
                "border": "1px solid #E2E8F0",
                "borderRadius": "14px",
                "padding": "20px",
                "marginTop": "22px",
            },
        ),
        html.Div(
            [
                metric_card("Наблюдений", "metric-observations"),
                metric_card("Лесные пожары", "metric-forest-share"),
                metric_card("Медианная температура", "metric-temperature"),
                metric_card("Осадки ≤ 0,1 мм", "metric-dry-share"),
            ],
            style={"display": "flex", "gap": "14px", "flexWrap": "wrap", "marginTop": "18px"},
        ),
        html.Div(
            [
                html.Div(dcc.Graph(id="type-chart", config={"displayModeBar": False}), style=GRAPH_STYLE),
                html.Div(dcc.Graph(id="temperature-chart", config={"displayModeBar": False}), style=GRAPH_STYLE),
            ],
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginTop": "18px"},
        ),
        html.Div(
            [
                html.Div(dcc.Graph(id="wind-chart", config={"displayModeBar": False}), style=GRAPH_STYLE),
                html.Div(dcc.Graph(id="spatial-chart", config={"displayModeBar": False}), style=GRAPH_STYLE),
            ],
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginTop": "16px"},
        ),
        html.Div(
            [
                html.H2("Фрагмент отфильтрованных данных", style={"fontSize": "20px"}),
                html.P(
                    "Показаны первые 200 строк; фильтры применяются ко всему датасету.",
                    style={"color": "#64748B"},
                ),
                dash_table.DataTable(
                    id="data-table",
                    page_size=12,
                    sort_action="native",
                    filter_action="native",
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "padding": "9px",
                        "textAlign": "left",
                        "fontFamily": "Arial, sans-serif",
                        "fontSize": "13px",
                        "minWidth": "110px",
                    },
                    style_header={
                        "backgroundColor": "#0F766E",
                        "color": "white",
                        "fontWeight": "700",
                    },
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#F8FAFC"}
                    ],
                ),
            ],
            style={
                "backgroundColor": "white",
                "border": "1px solid #E2E8F0",
                "borderRadius": "14px",
                "padding": "18px",
                "marginTop": "18px",
            },
        ),
        html.P(
            "Источник: каталог ИНИД, датасет «Метеорологические условия пожаров на территории России (2021–2022)».",
            style={"color": "#64748B", "fontSize": "13px", "marginTop": "18px"},
        ),
    ],
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#F1F5F9",
        "minHeight": "100vh",
        "padding": "28px",
        "maxWidth": "1500px",
        "margin": "0 auto",
    },
)


@app.callback(
    Output("metric-observations", "children"),
    Output("metric-forest-share", "children"),
    Output("metric-temperature", "children"),
    Output("metric-dry-share", "children"),
    Output("type-chart", "figure"),
    Output("temperature-chart", "figure"),
    Output("wind-chart", "figure"),
    Output("spatial-chart", "figure"),
    Output("data-table", "data"),
    Output("data-table", "columns"),
    Input("type-filter", "value"),
    Input("temperature-filter", "value"),
    Input("precipitation-filter", "value"),
)
def update_dashboard(selected_types, temperature_range, precipitation_range):
    filtered = filter_data(DATA, selected_types, temperature_range, precipitation_range)
    metrics = summary_metrics(filtered)
    records = table_records(filtered)
    columns = [{"name": key, "id": key} for key in records[0]] if records else []

    return (
        f"{metrics['observations']:,}".replace(",", " "),
        f"{metrics['forest_share']:.1f}%",
        f"{metrics['median_temperature']:.1f} °C",
        f"{metrics['dry_share']:.1f}%",
        type_counts_figure(filtered),
        temperature_histogram_figure(filtered),
        wind_box_figure(filtered),
        spatial_heatmap_figure(filtered),
        records,
        columns,
    )


if __name__ == "__main__":
    app.run(debug=False)
