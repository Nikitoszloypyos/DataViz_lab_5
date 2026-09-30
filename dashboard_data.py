from functools import lru_cache
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


DATA_PATH = Path(__file__).resolve().parent / "FiresRu.csv"

TYPE_LABELS = {
    "Forest fire": "Лесной пожар",
    "Natural fire": "Природный пожар",
    "Uncontrolled burn": "Неконтролируемый пал",
    "Controlled burn": "Контролируемый пал",
    "Peat fire": "Торфяной пожар",
}

TYPE_COLORS = {
    "Лесной пожар": "#2A9D8F",
    "Природный пожар": "#F4A261",
    "Неконтролируемый пал": "#577590",
    "Контролируемый пал": "#C77DFF",
    "Торфяной пожар": "#90BE6D",
}

REQUIRED_COLUMNS = {
    "type_name",
    "type_id",
    "lon",
    "lat",
    "temperature_c",
    "precipitation_mm",
    "relative_humidity",
    "wind_speed_ms",
    "solar_radiation",
}


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    """Загружает и проверяет датасет FiresRu."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Не найден файл {DATA_PATH.name}. Поместите его рядом с dashboard_data.py."
        )

    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    missing_columns = REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        raise ValueError(
            "В FiresRu.csv отсутствуют столбцы: " + ", ".join(sorted(missing_columns))
        )

    numeric_columns = sorted(REQUIRED_COLUMNS.difference({"type_name"}))
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=list(REQUIRED_COLUMNS)).drop_duplicates().reset_index(drop=True)
    df["Тип пожара"] = df["type_name"].map(TYPE_LABELS).fillna(df["type_name"])
    return df


def filter_data(
    df: pd.DataFrame,
    selected_types: list[str] | None,
    temperature_range: tuple[float, float] | list[float] | None,
    precipitation_range: tuple[float, float] | list[float] | None,
) -> pd.DataFrame:
    """Возвращает строки, подходящие под выбранные пользователем фильтры."""
    mask = pd.Series(True, index=df.index)

    if selected_types:
        mask &= df["Тип пожара"].isin(selected_types)
    if temperature_range:
        mask &= df["temperature_c"].between(*temperature_range)
    if precipitation_range:
        mask &= df["precipitation_mm"].between(*precipitation_range)

    return df.loc[mask].copy()


def summary_metrics(df: pd.DataFrame) -> dict[str, float | int]:
    """Рассчитывает четыре показателя для карточек."""
    if df.empty:
        return {
            "observations": 0,
            "forest_share": 0.0,
            "median_temperature": 0.0,
            "dry_share": 0.0,
        }

    return {
        "observations": len(df),
        "forest_share": df["Тип пожара"].eq("Лесной пожар").mean() * 100,
        "median_temperature": df["temperature_c"].median(),
        "dry_share": df["precipitation_mm"].le(0.1).mean() * 100,
    }


def _empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text="Нет данных для выбранных фильтров",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 16, "color": "#64748B"},
    )
    fig.update_layout(title=title, template="plotly_white")
    return fig


def type_counts_figure(df: pd.DataFrame) -> go.Figure:
    title = "Количество наблюдений по типам пожаров"
    if df.empty:
        return _empty_figure(title)

    counts = (
        df["Тип пожара"]
        .value_counts()
        .rename_axis("Тип пожара")
        .reset_index(name="Количество")
        .sort_values("Количество")
    )
    fig = px.bar(
        counts,
        x="Количество",
        y="Тип пожара",
        orientation="h",
        color="Тип пожара",
        color_discrete_map=TYPE_COLORS,
        text="Количество",
        title=title,
    )
    fig.update_traces(textposition="outside", hovertemplate="%{y}: %{x}<extra></extra>")
    fig.update_xaxes(range=[0, counts["Количество"].max() * 1.16])
    fig.update_layout(showlegend=False, margin={"l": 20, "r": 30, "t": 55, "b": 20})
    return fig


def temperature_histogram_figure(df: pd.DataFrame) -> go.Figure:
    title = "Распределение температуры"
    if df.empty:
        return _empty_figure(title)

    fig = px.histogram(
        df,
        x="temperature_c",
        nbins=35,
        labels={"temperature_c": "Температура, °C", "count": "Наблюдений"},
        color_discrete_sequence=["#E76F51"],
        title=title,
    )
    fig.add_vline(
        x=15,
        line_dash="dash",
        line_color="#334155",
        annotation_text="+15 °C",
        annotation_position="top left",
    )
    fig.update_yaxes(title="Количество наблюдений")
    fig.update_layout(bargap=0.04, margin={"l": 20, "r": 20, "t": 55, "b": 20})
    return fig


def wind_box_figure(df: pd.DataFrame) -> go.Figure:
    title = "Скорость ветра по типам пожаров"
    if df.empty:
        return _empty_figure(title)

    order = df.groupby("Тип пожара")["wind_speed_ms"].median().sort_values().index
    fig = px.box(
        df,
        x="wind_speed_ms",
        y="Тип пожара",
        color="Тип пожара",
        category_orders={"Тип пожара": order.tolist()},
        color_discrete_map=TYPE_COLORS,
        points=False,
        labels={"wind_speed_ms": "Скорость ветра, м/с"},
        title=title,
    )
    fig.update_layout(showlegend=False, margin={"l": 20, "r": 20, "t": 55, "b": 20})
    return fig


def spatial_heatmap_figure(df: pd.DataFrame) -> go.Figure:
    title = "Географическая плотность наблюдений"
    if df.empty:
        return _empty_figure(title)

    spatial = df.assign(
        Долгота_ячейки=(df["lon"] // 5 * 5).astype(int),
        Широта_ячейки=(df["lat"] // 5 * 5).astype(int),
    )
    grid = (
        spatial.groupby(["Широта_ячейки", "Долгота_ячейки"])
        .size()
        .rename("Количество")
        .reset_index()
    )
    matrix = grid.pivot(
        index="Широта_ячейки",
        columns="Долгота_ячейки",
        values="Количество",
    ).fillna(0)

    fig = px.imshow(
        matrix,
        origin="lower",
        aspect="auto",
        color_continuous_scale="YlOrRd",
        labels={
            "x": "Долгота, начало интервала °",
            "y": "Широта, начало интервала °",
            "color": "Наблюдений",
        },
        title=title,
    )
    fig.update_layout(margin={"l": 20, "r": 20, "t": 55, "b": 20})
    return fig


def table_records(df: pd.DataFrame, limit: int = 200) -> list[dict]:
    columns = [
        "Тип пожара",
        "lon",
        "lat",
        "temperature_c",
        "precipitation_mm",
        "relative_humidity",
        "wind_speed_ms",
        "solar_radiation",
    ]
    return df.loc[:, columns].head(limit).round(2).to_dict("records")
