import json
import os

from utils.plot_trace import plot_trace
from utils.plot_trace import trace_special_points
from utils.runners import run_session
from utils.runners import get_special_points

# create results directory if it does not exist
if not os.path.exists("results"):
    os.mkdir("results")

# Current domain number
domain = "00"

# Settings to run a negotiation session:
#   We need to specify the classpath of 2 agents to start a negotiation.
#   We need to specify the preference profiles for both agents. The first profile will be assigned to the first agent.
#   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement
settings = {
    "agents": [
        #"agents.boulware_agent.boulware_agent.BoulwareAgent",
        # "agents.conceder_agent.conceder_agent.ConcederAgent",
         #"agents.hardliner_agent.hardliner_agent.HardlinerAgent",
        # "agents.linear_agent.linear_agent.LinearAgent",
        # "agents.random_agent.random_agent.RandomAgent",
        # "agents.stupid_agent.stupid_agent.StupidAgent",
        "agents.template_agent.template_agent.TemplateAgent",
        "agents.template_agent.template_agent.TemplateAgent"

    ],
    "profiles": ["domains/domain{}/profileA.json".format(domain), "domains/domain{}/profileB.json".format(domain)],
    "deadline_rounds": 200,
}

# run a session and obtain results in dictionaries
results_trace, results_summary = run_session(settings)
accept_point = []
agents_involved = settings["agents"]
# Iterate through and find an accepting bid if there is one
for index, action in enumerate(results_trace["actions"], 1):
    if "Accept" in action:
        offer = action["Accept"]
        for agent, util in offer["utilities"].items():
            accept_point.append(util)
            agents_involved.append(agent)

# Get the pareto optimal points + other special points
special_points_file = "domains/domain{}/specials.json".format(domain)
special_points = get_special_points(special_points_file)
trace_special_points(special_points, accept_point, agents_involved)

# plot trace to html file
plot_trace(results_trace, "results/trace_plot.html")

# write results to file
with open("results/results_trace.json", "w") as f:
    f.write(json.dumps(results_trace, indent=2))
with open("results/results_summary.json", "w") as f:
    f.write(json.dumps(results_summary, indent=2))