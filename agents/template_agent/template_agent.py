import logging
from random import randint
from typing import cast

from geniusweb.actions.Accept import Accept
from geniusweb.actions.Action import Action
from geniusweb.actions.Offer import Offer
from geniusweb.actions.PartyId import PartyId
from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.inform.ActionDone import ActionDone
from geniusweb.inform.Finished import Finished
from geniusweb.inform.Inform import Inform
from geniusweb.inform.Settings import Settings
from geniusweb.inform.YourTurn import YourTurn
from geniusweb.issuevalue.Bid import Bid
from geniusweb.issuevalue.Domain import Domain
from geniusweb.issuevalue.Value import Value
from geniusweb.issuevalue.ValueSet import ValueSet
from geniusweb.party.Capabilities import Capabilities
from geniusweb.party.DefaultParty import DefaultParty
from geniusweb.profile.utilityspace.UtilitySpace import UtilitySpace
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)
from geniusweb.progress.ProgressRounds import ProgressRounds
from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel


class TemplateAgent(DefaultParty):
    """
    Template agent that offers random bids until a bid with sufficient utility is offered.
    """

    def __init__(self):
        super().__init__()
        self.getReporter().log(logging.INFO, "party is initialized")
        self._profile = None
        self._last_received_bid: Bid = None
        self._opponent_model: FrequencyOpponentModel = FrequencyOpponentModel.create()

    def notifyChange(self, info: Inform):
        """This is the entry point of all interaction with your agent after is has been initialised.

        Args:
            info (Inform): Contains either a request for action or information.
        """

        # a Settings message is the first message that will be send to your
        # agent containing all the information about the negotiation session.
        if isinstance(info, Settings):
            self._settings: Settings = cast(Settings, info)
            self._me = self._settings.getID()

            # progress towards the deadline has to be tracked manually through the use of the Progress object
            self._progress: ProgressRounds = self._settings.getProgress()

            # the profile contains the preferences of the agent over the domain
            self._profile = ProfileConnectionFactory.create(
                info.getProfile().getURI(), self.getReporter()
            )

            self._opponent_model = self._opponent_model.With(newDomain=self._profile.getProfile().getDomain(),
                                                             newResBid=0)
        # ActionDone is an action send by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()

            # if it is an offer, set the last received bid
            if isinstance(action, Offer):
                self._opponent_model = self._opponent_model.WithAction(action, self._progress)
                self._last_received_bid = cast(Offer, action).getBid()
        # YourTurn notifies you that it is your turn to act
        elif isinstance(info, YourTurn):
            # execute a turn
            self._myTurn()

            # log that we advanced a turn
            self._progress = self._progress.advance()

        # Finished will be send if the negotiation has ended (through agreement or deadline)
        elif isinstance(info, Finished):
            # terminate the agent MUST BE CALLED
            self.terminate()
        else:
            self.getReporter().log(
                logging.WARNING, "Ignoring unknown info " + str(info)
            )

    # lets the geniusweb system know what settings this agent can handle
    # leave it as it is for this course
    def getCapabilities(self) -> Capabilities:
        return Capabilities(
            set(["SAOP"]),
            set(["geniusweb.profile.utilityspace.LinearAdditive"]),
        )

    # terminates the agent and its connections
    # leave it as it is for this course
    def terminate(self):
        self.getReporter().log(logging.INFO, "party is terminating:")
        super().terminate()
        if self._profile is not None:
            self._profile.close()
            self._profile = None

    #######################################################################################
    ########## THE METHODS BELOW THIS COMMENT ARE OF MAIN INTEREST TO THE COURSE ##########
    #######################################################################################

    # give a description of your agent
    def getDescription(self) -> str:
        return "Template agent for Collaborative AI course"

    # execute a turn
    def _myTurn(self):
        # Get our next bid
        next_bid = self._findBid()
        # check if the last received offer if the opponent is good enough
        if self._isGood(self._last_received_bid, next_bid):
            # if so, accept the offer
            action = Accept(self._me, self._last_received_bid)
        else:
            # if not, propose bid as counter offer
            action = Offer(self._me, next_bid)

        # send the action
        self.getConnection().send(action)

    # method that checks if we would agree with an offer
    def _isGood(self, last_bid: Bid, next_bid: Bid) -> bool:
        if last_bid is None:
            return False
        profile = self._profile.getProfile()

        progress = self._progress.get(0)

        # Depending on how many rounds have already passed, adjust the constant value we ask for
        # Combination of time-dependent, constant utility and next bid
        if progress < 0.5:
            return profile.getUtility(last_bid) > 0.8 and profile.getUtility(last_bid) > profile.getUtility(next_bid)
        elif progress < 0.7:
            return profile.getUtility(last_bid) > 0.7 and profile.getUtility(last_bid) > profile.getUtility(next_bid)
        elif progress < 0.9:
            return profile.getUtility(last_bid) > 0.6 and profile.getUtility(last_bid) > profile.getUtility(next_bid)
        else:
            return profile.getUtility(last_bid) > 0.5 and profile.getUtility(last_bid) > profile.getUtility(next_bid)

    def _findBid(self) -> Bid:
        # compose a list of all possible bids
        domain = self._profile.getProfile().getDomain()
        all_bids = AllBidsList(domain)

        profile = self._profile.getProfile()
        progress = self._progress.get(0)
        best_bid = all_bids.get(randint(0, all_bids.size() - 1))

        # In the first quarter of the game we offer random bids that have good utility for us while reading the opponent to estimate their utility
        if progress < 0.25:
            for _ in range(50):
                bid = all_bids.get(randint(0, all_bids.size() - 1))
                if profile.getUtility(bid) > profile.getUtility(best_bid):
                    best_bid = bid
                if self._isGood(bid, self._last_received_bid):
                    break
            return best_bid
        else:
            # Now we incorporate the utility of the opponent in our bid decisions
            for _ in range(50):
                bid = all_bids.get(randint(0, all_bids.size() - 1))
                if profile.getUtility(bid) > profile.getUtility(best_bid):
                    best_bid = bid
                if self._isGood(bid, self._last_received_bid) and self._opponent_model.getUtility(bid) > 0.6:
                    print(self._opponent_model.getUtility(bid))
                    break
            return best_bid
