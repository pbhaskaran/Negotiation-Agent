# Collaborative AI @ TU Delft
This is a template repository for the Negotiation Practical Assignment of the course on Collaborative AI at the TU Delft. This template is aimed at students that want to implement their agent in Python.

## Overview
- directories:
    - `agents`: Contains directories with the agents. The `template_agent` directory contains the template for this assignment.
    - `domains`: Contains the domains which are problems over which the agents are supposed to negotiate.
    - `utils`: Arbitrary utilities (don't use).
- files:
    - `run.py`: Main interface to test agents in single session runs.
    - `run_tournament.py: Main interface to test a set of agents in a tournament. Here, every agent will negotiate against every other agent in the set on every set of preferences profiles that is provided (see code).
    - `requirements.txt`: Python dependencies for your agent.
    - `requirements_allowed.txt`: Additional dependencies that you are allowed to use (ask TA's if you need unlisted packages).

## Installation
Download or clone this repository. *Note that if you fork this repository you cannot make it private*, which is default behaviour of GitHub. This will cause your code to be publicly visible if you push it to your forked repository.

We recommend using Python 3.9. The required dependencies are listed in the `requirements.txt` file and can be installed through `pip install -r requirements.txt`.

As already mentioned, should you need any additional dependencies, you can ask the TA's of this course. A few of the most common dependencies are already listed in `requirements_allowed.txt` file. If you require another package that is not listed, **ask first**.

For VSCode devcontainer users: We included a devcontainer specification in the `.devcontainer` directory.

## Quickstart
- Copy and rename the template agent's directory, files and classname.
- Read through the code to familiarise yourself with its workings. The agent already works but is not very good.
- Develop your agent in the copied directory. Make sure that all the files that you use are in the directory.
- Test your agent through `run.py`, results will be returned as dictionaries and saved as json-file. A plot of the negotiation trace will also be saved.
- You can also test your agent more extensively by running a tournament with a set of agents. Use the `run_tournament.py` script for this. Summaries of the results will be saved to the results directory.

## More information
[More documentation can be found here](https://tracinsy.ewi.tudelft.nl/pubtrac/GeniusWebPython/wiki/WikiStart). Part of this documentation was written for the Java version of GeniusWeb, but classes and functionality are left identical as much as possible.
