import json
from math import cos, sin, tau

import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageDraw

from set_math import BOARD, CARDS, quandle


SHAPES = ("oval", "diamond", "squiggle")
MARKER_SHAPES = ("circle", "diamond", "x")
SHAPE_GLYPHS = ("●", "◆", "×")
COLORS = ("purple", "red", "green")
CARD_COLORS = ("#752f91", "#c62828", "#237849")
EXPLORER_CARDS = tuple(card for card in CARDS if card[3] == 0)
SELECTED_BORDER = "#1976d2"
COMPLETION_BORDER = "#d97706"
GEOMETRY_BOUNDS = (-0.5, 2.5)


def card_label(card):
    number, shape, _, _ = card
    quantity = number + 1
    name = SHAPES[shape] if quantity == 1 else f"{SHAPES[shape]}s"
    return f"{quantity} {name}"


def explorer_label(card):
    quantity, name = card_label(card).split(" ", 1)
    return f"{quantity} {COLORS[card[2]]} {name}"


def node_label(card):
    number, shape, _, _ = card
    return " ".join([SHAPE_GLYPHS[shape]] * (number + 1))


def draw_card(card, border):
    number, shape, color, _ = card
    quantity = number + 1
    image = Image.new("RGB", (240, 112), "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1, 1, 238, 110), radius=12, outline=border, width=4)

    fill = CARD_COLORS[color]
    for index in range(quantity):
        x = 120 + (2 * index - quantity + 1) * 35
        y = 56
        if SHAPES[shape] == "oval":
            draw.ellipse((x - 26, y - 19, x + 26, y + 19), fill=fill)
        elif SHAPES[shape] == "diamond":
            draw.polygon([(x - 27, y), (x, y - 23), (x + 27, y), (x, y + 23)], fill=fill)
        else:
            # Bend an oval around a wave to form the squiggle's curved outline.
            outline = []
            for step in range(96):
                angle = tau * step / 96
                horizontal = cos(angle)
                wave = 14 * sin(tau * horizontal / 2)
                outline.append((x + 27 * horizontal, y + 12 * sin(angle) + wave))
            draw.polygon(outline, fill=fill)

    return image


def select_card(card):
    selected = st.session_state.selected_cards
    if len(selected) < 2 and card not in selected:
        st.session_state.selected_cards = (*selected, card)


def clear_selection():
    st.session_state.selected_cards = ()


def line_parameters(a, b):
    x1, y1 = a[:2]
    x2, y2 = b[:2]
    dx = (x2 - x1) % 3
    if dx == 0:
        return None, x1

    slope = ((y2 - y1) * pow(dx, -1, 3)) % 3
    intercept = (y1 - slope * x1) % 3
    return -1 if slope == 2 else slope, intercept


def line_segments(slope, intercept):
    low, high = GEOMETRY_BOUNDS
    if slope is None:
        return [(intercept, low, intercept, high)]
    if slope == 0:
        return [(low, intercept, high, intercept)]

    segments = []
    # Within these bounds only copies shifted by at most two periods can intersect.
    for period in range(-2, 3):
        offset = intercept + 3 * period
        # Find where each shifted line crosses the bottom and top of the plot.
        left, right = sorted(((low - offset) / slope, (high - offset) / slope))
        start, end = max(low, left), min(high, right)
        if start < end:
            segments.append((start, slope * start + offset, end, slope * end + offset))
    return segments


def show_geometry(selected, completion):
    st.subheader("Geometry")
    roles = {}
    layers = []
    if completion is not None:
        roles = dict.fromkeys(selected, "Selected")
        roles[completion] = "Completes the SET"
        slope, intercept = line_parameters(*selected)
        equation = f"x = {intercept}" if slope is None else f"y = {slope % 3}x + {intercept}"
        st.markdown(f"`{equation} (mod 3)`")
        layers.append({
            "data": {"values": [
                {"number": x1, "shape": y1, "end_number": x2, "end_shape": y2}
                for x1, y1, x2, y2 in line_segments(slope, intercept)
            ]},
            "mark": {"type": "rule", "color": "#7660a8", "strokeWidth": 2, "clip": True},
            "encoding": {"x2": {"field": "end_number"}, "y2": {"field": "end_shape"}},
        })

    axis = {
        "type": "quantitative",
        "scale": {"domain": list(GEOMETRY_BOUNDS), "nice": False},
    }
    ticks = {"values": [0, 1, 2], "labelAngle": 0, "labelOverlap": False}
    number_labels = ["0 (1 symbol)", "1 (2 symbols)", "2 (3 symbols)"]
    shape_labels = [f"{index} ({shape})" for index, shape in enumerate(SHAPES)]
    layers.append({
        "data": {"values": [
            {"number": card[0], "shape": card[1], "role": roles.get(card, "Board point")}
            for card in BOARD
        ]},
        "mark": {"type": "point", "filled": True, "size": 150},
        "encoding": {
            "color": {
                "field": "role",
                "type": "nominal",
                "scale": {
                    "domain": ["Board point", "Selected", "Completes the SET"],
                    "range": ["#8793a1", "#1976d2", "#d97706"],
                },
                "legend": {"title": None, "orient": "bottom"} if roles else None,
            },
        },
    })
    st.vega_lite_chart({
        "height": 260,
        "encoding": {
            "x": {
                **axis, "field": "number", "title": "Number (x)",
                "axis": {**ticks, "labelExpr": f"{json.dumps(number_labels)}[datum.value]"},
            },
            "y": {
                **axis, "field": "shape", "title": "Shape (y)",
                "axis": {**ticks, "labelExpr": f"{json.dumps(shape_labels)}[datum.value]"},
            },
        },
        "layer": layers,
    })


def show_board():
    selected = st.session_state.setdefault("selected_cards", ())
    completion = quandle(*selected) if len(selected) == 2 else None
    marks = {card: f"Selected {index}" for index, card in enumerate(selected, 1)}
    if completion is not None:
        marks[completion] = "Completes the SET"

    cards_by_position = {(card[0], card[1]): card for card in BOARD}
    for shape in reversed(range(len(SHAPES))):
        columns = st.columns(3)
        for number, column in enumerate(columns):
            card = cards_by_position[number, shape]
            label = card_label(card)
            if card in marks:
                label = f"{label} · {marks[card]}"
            border = "#ccd1d8"
            if card in selected:
                border = SELECTED_BORDER
            elif card == completion:
                border = COMPLETION_BORDER
            card_view = column.container(horizontal_alignment="center")
            card_view.image(draw_card(card, border), width=100)
            card_view.button(
                label,
                key=f"card-{number}-{shape}",
                type="primary" if card in marks else "secondary",
                on_click=select_card,
                args=(card,),
                disabled=completion is not None and card not in marks,
            )

    st.button("Clear selection", on_click=clear_selection, disabled=not selected)
    if marks:
        st.write("Coordinates in order: number, shape, color, shading")
        for card, mark in marks.items():
            st.write(f"{mark}: {card}")
    if completion is not None:
        a, b = selected
        intermediate = tuple(-left - right for left, right in zip(a, b))
        st.markdown(f"`(-a - b) mod 3 = {intermediate} mod 3 = {completion}`")

    show_geometry(selected, completion)


def show_explorer():
    first_column, second_column = st.columns(2)
    first = first_column.selectbox(
        "First card", EXPLORER_CARDS, index=None, format_func=explorer_label, key="explorer_first"
    )
    second = second_column.selectbox(
        "Second card",
        [card for card in EXPLORER_CARDS if card != first],
        index=None,
        format_func=explorer_label,
        key="explorer_second",
        disabled=first is None,
    )
    selected = tuple(card for card in (first, second) if card is not None)
    completion = quandle(*selected) if len(selected) == 2 else None
    highlights = dict(zip(selected, ("A", "B")))
    if completion is not None:
        highlights[completion] = "C"

    show_layers = st.checkbox("Show color layers", value=True, key="explorer_color_layers")
    figure = go.Figure()
    if show_layers:
        for z, color in enumerate(CARD_COLORS):
            figure.add_mesh3d(
                x=[-0.25, 2.25, 2.25, -0.25],
                y=[-0.25, -0.25, 2.25, 2.25],
                z=[z] * 4,
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=color,
                opacity=0.10,
                lighting=dict(ambient=1, diffuse=0, specular=0),
                hoverinfo="skip",
                showlegend=False,
            )
    hover = "%{customdata}<br>Coordinates (%{x}, %{y}, %{z}, 0)<extra></extra>"
    for shape, name in enumerate(SHAPES):
        cards = [card for card in EXPLORER_CARDS if card[1] == shape and card not in highlights]
        x, y, z, _ = zip(*cards)
        colors = [CARD_COLORS[color] for color in z]
        figure.add_scatter3d(
            x=x, y=y, z=z,
            mode="markers+text",
            name=name.capitalize(),
            legendgroup=name,
            text=[node_label(card) for card in cards],
            textposition="top center",
            textfont=dict(color=colors, size=12),
            customdata=[explorer_label(card) for card in cards],
            hovertemplate=hover,
            marker=dict(size=5, symbol=MARKER_SHAPES[shape], color=colors),
        )
    for card, letter in highlights.items():
        number, shape, color, _ = card
        figure.add_scatter3d(
            x=[number], y=[shape], z=[color],
            mode="markers+text",
            name=letter,
            legendgroup=SHAPES[shape],
            showlegend=False,
            text=[f"{letter} · {node_label(card)}"],
            textposition="top center",
            textfont=dict(color=CARD_COLORS[color], size=16),
            customdata=[explorer_label(card)],
            hovertemplate=hover,
            marker=dict(
                size=12, symbol=MARKER_SHAPES[shape], color=CARD_COLORS[color],
                line=dict(color="#182233", width=3),
            ),
        )
    axes = {
        axis: dict(title=title, tickvals=[0, 1, 2], range=[-0.25, 2.25])
        for axis, title in (("xaxis", "Number"), ("yaxis", "Shape"), ("zaxis", "Color"))
    }
    figure.update_layout(
        scene=dict(**axes, aspectmode="cube", dragmode="orbit"),
        uirevision="explorer-camera",
        margin=dict(l=0, r=0, t=76 if completion is not None else 0, b=0),
        legend=dict(orientation="h", itemsizing="constant", font=dict(size=11)),
    )
    if completion is not None:
        a, b = first[:3], second[:3]
        intermediate = tuple(-left - right for left, right in zip(a, b))
        figure.add_annotation(
            x=0.5, y=1, xref="paper", yref="paper",
            xanchor="center", yanchor="bottom", yshift=8,
            showarrow=False,
            text=(
                "<b>C = (-A - B) mod 3</b><br>"
                f"= (-{a} - {b}) mod 3<br>"
                f"= {intermediate} mod 3 = {completion[:3]}"
            ),
        )
    st.plotly_chart(figure, key="explorer_plot")

    if completion is not None:
        for column, card, label, border in zip(
            st.columns(3),
            highlights,
            ("A · First card", "B · Second card", "C · Completes the SET"),
            (SELECTED_BORDER, SELECTED_BORDER, COMPLETION_BORDER),
        ):
            column.image(draw_card(card, border), caption=f"{label} · {explorer_label(card)} · {card}")


def main():
    st.set_page_config(page_title="SET Explorer")
    st.title("SET Explorer")

    board_tab, explorer_tab = st.tabs(["9-Card Board", "3D Explorer"])
    with board_tab:
        show_board()
    with explorer_tab:
        show_explorer()


if __name__ == "__main__":
    main()
