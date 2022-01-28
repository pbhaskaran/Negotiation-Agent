from geniusweb.protocol.NegoSettings import NegoSettings
from geniusweb.simplerunner.ClassPathConnectionFactory import \
    ClassPathConnectionFactory
from geniusweb.simplerunner.NegoRunner import NegoRunner
from pyson.ObjectMapper import ObjectMapper

from utils.std_out_reporter import StdOutReporter


def create_runner(settings) -> NegoRunner:
    agents = settings["agents"]
    domain = settings["domain"]
    profiles = [
        f"domains/{domain}/{domain}profileA.json",
        f"domains/{domain}/{domain}profileB.json",
    ]
    rounds = settings["deadline_rounds"]

    # quick and dirty checks
    assert isinstance(domain, str)
    assert isinstance(agents, list) and len(agents) == 2
    assert isinstance(rounds, int) and rounds > 0

    settings_full = {
        "SAOPSettings": {
            "participants": [
                {
                    "TeamInfo": {
                        "parties": [
                            {
                                "party": {
                                    "partyref": f"pythonpath:{agents[0]}",
                                    "parameters": {},
                                },
                                "profile": f"file:{profiles[0]}",
                            }
                        ]
                    }
                },
                {
                    "TeamInfo": {
                        "parties": [
                            {
                                "party": {
                                    "partyref": f"pythonpath:{agents[1]}",
                                    "parameters": {},
                                },
                                "profile": f"file:{profiles[1]}",
                            }
                        ]
                    }
                },
            ],
            "deadline": {"DeadlineRounds": {"rounds": rounds, "durationms": 999}},
        }
    }

    settings_obj = ObjectMapper().parse(settings_full, NegoSettings)
    return NegoRunner(settings_obj, ClassPathConnectionFactory(), StdOutReporter(), 0)
