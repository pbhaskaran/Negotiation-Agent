from utils.create_runner import create_runner

settings = {
    "agents": ["agents.random_agent.random_agent.RandomAgent", "agents.template_agent.template_agent.TemplateAgent"],
    "domain": "jobs",
    "deadline_rounds": 200,
}

runner = create_runner(settings)
runner.run()
