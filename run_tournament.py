import json
import os

from utils.plot_trace import plot_trace
from utils.runners import run_tournament

# create results directory if it does not exist
if not os.path.exists("results"):
    os.mkdir("results")

# Settings to run a tournament:
#   We need to specify the classpath all agents that will participate in the tournament
#   We need to specify duos of preference profiles that will be played by the agents
#   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement
tournament_settings = {
    "agents": [
        "agents.random_agent.random_agent.RandomAgent",
        "agents.template_agent.template_agent.TemplateAgent",
        "agents.stupid_agent.stupid_agent.StupidAgent",
    ],
    "profile_sets": [
        ["domains/domain00/profileA.json", "domains/domain00/profileB.json"],
        ["domains/domain01/profileA.json", "domains/domain01/profileB.json"],
    ],
    "deadline_rounds": 200,
}

# run a session and obtain results in dictionaries
tournament, results_summaries = run_tournament(tournament_settings)

# save the tournament settings for reference
with open("results/tournament.json", "w") as f:
    f.write(json.dumps(tournament, indent=2))
# save the result summaries
with open("results/results_summaries.json", "w") as f:
    f.write(json.dumps(results_summaries, indent=2))
