# Collaborative AI @ TU Delft
This is a template repository for the Negotiation Practical Assignment of the course on Collaborative AI at the TU Delft. This template is aimed at student that want to implement their agent in Python.

## Overview
- directories
    - `agents`: Contains directories with the agents. The `template_agent` directory contains the template for this assignment.
    - `domains`: Contains the domains which are problem over which the agents are supposed to negotiate.
    - `utils`: Arbitrary utilities (don't use).
- files
    - `run.py`: Main interface to test agents.
    - `requirements.txt`: Python dependencies for your agent.
    - `requirements_allowed.txt`: Additional dependencies that you are allowed to use (ask TA's if you need unlisted packages).

## Installation
The agents will be run on Python 3.9, so we advise that you develop on Python 3.9 as well. The dependencies are listed in the `requirements.txt` file and can be installed through `pip install -r requirements`.

For VSCode devcontainer users: We included a devcontainer specification in the `.devcontainer` directory.

## Quickstart
- Copy and rename the template agent's directory, files and classname.
- Read through the code to familiarise yourself with its workings. The agent already works, but is not very good.
- Develop your agent in the copied directory. Make sure that all the files that you use are in the directory.
- Test you agent through `run.py`

## More information
[More documentation can be found here](https://tracinsy.ewi.tudelft.nl/pubtrac/GeniusWebPython/wiki/WikiStart). Part of this documentation was written for the Java version of GeniusWeb, but classes en functionality is left identical as much as possible.