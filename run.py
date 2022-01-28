from utils.create_runner import create_runner

# Settings to run a negotiation session:
#   We need to specify the classpath of 2 agents to start a negotiation.
#   We need to specify one of the domains (name of one of the directories in the ./domains directory)
#   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement
settings = {
    "agents": [
        "agents.random_agent.random_agent.RandomAgent",
        "agents.template_agent.template_agent.TemplateAgent",
    ],
    "domain": "jobs",
    "deadline_rounds": 200,
}

# obtain the negotiation session runner
runner = create_runner(settings)

# run the session
runner.run()
