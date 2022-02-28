import os
from collections import defaultdict

import plotly.graph_objects as go

def trace_pareto(pareto_points: list, accept_point: list, agents_involved: list):
    text = []
    x = []
    y = []
    # Keep track of all the pareto optimal points and their coordinates for hover over text
    for p in pareto_points:
        x.append(p[0])
        y.append(p[1])
        text.append(str(round(p[0], 3)) + ", " + str(round(p[1], 3)))
    # Create a figure
    fig = go.Figure()
    # Add the pareto optimal frontier
    fig.add_trace(
        go.Scatter(
            mode="lines+markers",
            x=x,
            y=y,
            marker={"color": "red", "size": 12},
            name = "Pareto Optimal Frontier",
            legendgroup= "Pareto Optimal Points",
            hovertext=text,
            hoverinfo="text",
        )
    )
    # If there is exactly one accepted bid (2 coordinates)
    if len(accept_point) == 2:
        text = []
        text.append(str(round(accept_point[0], 3)) + " , " + str(round(accept_point[1], 3)))
        fig.add_trace(
            go.Scatter(
                mode="markers",
                x=[accept_point[0]],
                y=[accept_point[1]],
                marker={"color": "green", "size": 12},
                name= "Agreed upon bid",
                hovertext=text,
                hoverinfo="text",
            )
        )
    fig.update_layout(
        # width=1000,
        height=800,
    )
    # Get the name of the agents
    xaxes_label = agents_involved[0].split(".")[3]
    yaxes_label = agents_involved[1].split(".")[3]
    # Update the axes and write to html file
    fig.update_xaxes(title_text="Utility of {}".format(xaxes_label), range=[0, 1], ticks="outside")
    fig.update_yaxes(title_text="Utility of {}".format(yaxes_label), range=[0, 1], ticks="outside")
    fig.write_html("results/pareto_plot.html")

def plot_trace(results_trace: dict, plot_file: str):
    utilities = defaultdict(lambda: defaultdict(lambda: {"x": [], "y": [], "bids": []}))
    accept = {"x": [], "y": [], "bids": []}
    for index, action in enumerate(results_trace["actions"], 1):
        if "Offer" in action:
            offer = action["Offer"]
            actor = offer["actor"]
            for agent, util in offer["utilities"].items():
                utilities[agent][actor]["x"].append(index)
                utilities[agent][actor]["y"].append(util)
                utilities[agent][actor]["bids"].append(offer["bid"]["issuevalues"])
        elif "Accept" in action:
            offer = action["Accept"]
            index -= 1
            for agent, util in offer["utilities"].items():
                accept["x"].append(index)
                accept["y"].append(util)
                accept["bids"].append(offer["bid"]["issuevalues"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            mode="markers",
            x=accept["x"],
            y=accept["y"],
            name="agreement",
            marker={"color": "green", "size": 15},
            hoverinfo="skip",
        )
    )

    color = {0: "red", 1: "blue"}
    for i, (agent, data) in enumerate(utilities.items()):
        for actor, utility in data.items():
            name = "_".join(agent.split("_")[-2:])
            text = []
            for bid, util in zip(utility["bids"], utility["y"]):
                text.append(
                    "<br>".join(
                        [f"<b>utility: {util:.3f}</b><br>"]
                        + [f"{i}: {v}" for i, v in bid.items()]
                    )
                )
            fig.add_trace(
                go.Scatter(
                    mode="lines+markers" if agent == actor else "markers",
                    x=utilities[agent][actor]["x"],
                    y=utilities[agent][actor]["y"],
                    name=f"{name} offered" if agent == actor else f"{name} received",
                    legendgroup=agent,
                    marker={"color": color[i]},
                    hovertext=text,
                    hoverinfo="text",
                )
            )

    fig.update_layout(
        # width=1000,
        height=800,
        legend={
            "yanchor": "bottom",
            "y": 1,
            "xanchor": "left",
            "x": 0,
        },
    )
    fig.update_xaxes(title_text="round", range=[0, index + 1], ticks="outside")
    fig.update_yaxes(title_text="utility", range=[0, 1], ticks="outside")
    fig.write_html(f"{os.path.splitext(plot_file)[0]}.html")
