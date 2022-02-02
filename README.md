# Collaborative AI @ TU Delft
This is a template repository for the Negotiation Practical Assignment of the course on Collaborative AI at the TU Delft. This template is aimed at students that want to implement their agent in Python.

## Overview
- directories
    - `agents`: Contains directories with the agents. The `template_agent` directory contains the template for this assignment.
    - `domains`: Contains the domains which are problems over which the agents are supposed to negotiate.
    - `utils`: Arbitrary utilities (don't use).
- files
    - `run.py`: Main interface to test agents.
    - `requirements.txt`: Python dependencies for your agent.
    - `requirements_allowed.txt`: Additional dependencies that you are allowed to use (ask TA's if you need unlisted packages).

## Installation
The agents will be run on Python 3.9, so we advise that you develop on Python 3.9 as well. The dependencies are listed in the `requirements.txt` file and can be installed through `pip install -r requirements`.

As already mentioned, should you need any additional dependencies, you can ask the TA's of this course. A few of the most common dependencies are already listed in the `requirements_allowed.txt` file, based on a [prepackaged version of Anaconda](https://docs.anaconda.com/anaconda/packages/py3.9_linux-64/). If you require another package that is on this webpage, then that is likely to be no problem, **but ask first**.

For VSCode devcontainer users: We included a devcontainer specification in the `.devcontainer` directory.

## Quickstart
- Copy and rename the template agent's directory, files and classname.
- Read through the code to familiarise yourself with its workings. The agent already works but is not very good.
- Develop your agent in the copied directory. Make sure that all the files that you use are in the directory.
- Test your agent through `run.py`, results will be returned as dictionaries and saved as json-file.

## More information
[More documentation can be found here](https://tracinsy.ewi.tudelft.nl/pubtrac/GeniusWebPython/wiki/WikiStart). Part of this documentation was written for the Java version of GeniusWeb, but classes en functionality is left identical as much as possible.