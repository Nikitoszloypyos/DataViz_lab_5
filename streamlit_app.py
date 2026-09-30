import streamlit as st

from dashboard_data import (
    filter_data,
    load_data,
    spatial_heatmap_figure,
    summary_metrics,
    temperature_histogram_figure,
    type_counts_figure,
    wind_box_figure,
)


st.set_page_config(
    page_title="Пожары в России — Streamlit",
    page_icon="🔥",
    layout="wide",
)

data = load_data()
type_options = data["Тип пожара"].value_counts().index.tolist()

st.title("Пожары в России")
st.caption("Интерактивный дашборд по данным FiresRu")

with st.sidebar:
    st.header("Фильтры")
    selected_types = st.multiselect(
        "Тип пожара",
        options=type_options,
        default=type_options,
    )
    temperature_range = st.slider(
        "Температура, °C",
        min_value=float(data["temperature_c"].min()),
        max_value=float(data["temperature_c"].max()),
        value=(
            float(data["temperature_c"].min()),
            float(data["temperature_c"].max()),
        ),
        step=1.0,
    )
    precipitation_range = st.slider(
        "Осадки, мм",
        min_value=float(data["precipitation_mm"].min()),
        max_value=float(data["precipitation_mm"].max()),
        value=(
            float(data["precipitation_mm"].min()),
            float(data["precipitation_mm"].max()),
        ),
        step=0.1,
    )

filtered = filter_data(data, selected_types, temperature_range, precipitation_range)
metrics = summary_metrics(filtered)

metric_columns = st.columns(4)
metric_columns[0].metric("Наблюдений", f"{metrics['observations']:,}".replace(",", " "))
metric_columns[1].metric("Лесные пожары", f"{metrics['forest_share']:.1f}%")
metric_columns[2].metric("Медианная температура", f"{metrics['median_temperature']:.1f} °C")
metric_columns[3].metric("Осадки ≤ 0,1 мм", f"{metrics['dry_share']:.1f}%")

left, right = st.columns(2)
with left:
    st.plotly_chart(type_counts_figure(filtered), width="stretch")
with right:
    st.plotly_chart(temperature_histogram_figure(filtered), width="stretch")

left, right = st.columns(2)
with left:
    st.plotly_chart(wind_box_figure(filtered), width="stretch")
with right:
    st.plotly_chart(spatial_heatmap_figure(filtered), width="stretch")

st.subheader("Отфильтрованные данные")
st.caption(f"Показано до 500 строк из {len(filtered):,}".replace(",", " "))
table_columns = [
    "Тип пожара",
    "lon",
    "lat",
    "temperature_c",
    "precipitation_mm",
    "relative_humidity",
    "wind_speed_ms",
    "solar_radiation",
]
st.dataframe(filtered.loc[:, table_columns].head(500), width="stretch", hide_index=True)

st.caption(
    "Источник: каталог ИНИД, датасет «Метеорологические условия пожаров "
    "на территории России (2021–2022)»."
)
