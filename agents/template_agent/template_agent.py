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
from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)
from geniusweb.progress.ProgressRounds import ProgressRounds
from agents.template_agent.ExtendFrequencyOpponentModel import ExtendFrequencyOpponentModel


class TemplateAgent(DefaultParty):
    """
    Template agent that offers random bids until a bid with sufficient utility is offered.
    """

    def __init__(self):
        super().__init__()
        self.getReporter().log(logging.INFO, "party is initialized")
        self._profile = None
        self._last_offered_bid: Bid = None
        self._last_received_bid: Bid = None

        # We keep track of the received bids thus far, sorted by our utility
        self._received_bids = []
        self._progress: ProgressRounds = None
        self._e = None

        self._current_phase = 1
        # At which round of the negotiation should phase 2 and phase 3 begin:
        self._phase_two_start_round = 30
        self._phase_three_start_round = 175
        self._alpha = 0.7
        self._opponent_model: ExtendFrequencyOpponentModel = ExtendFrequencyOpponentModel.create()
        self._our_utilities = {}

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

            for key, value in self._profile.getProfile().getUtilities().items():
                self._our_utilities[key] = value.getUtilities()
            print(self._our_utilities)


        # ActionDone is an action send by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()
            # if it is an offer, set the last received bid and it isn't from us
            if isinstance(action, Offer) and not str(action.getActor()).__contains__("template"):
                self._opponent_model = self._opponent_model.WithAction(action, self._last_received_bid, self._progress)
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

    # This method updates the current_phase attribute of the agent
    def _updateCurrentPhase(self):
        current_round = self._progress.getCurrentRound()
        if current_round >= self._phase_two_start_round:
            self._current_phase = 2
        if current_round >= self._phase_three_start_round:
            self._current_phase = 3

    # execute a turn
    def _myTurn(self):
        profile = self._profile.getProfile()

        # If we are making the first bid, we make the bid with the highest possible utility for ourselves (Agent Smith)
        if self._last_received_bid is None:
            next_bid = self.random_bid_finder()
            self._last_offered_bid = next_bid

            action = Offer(self._me, next_bid)
            self.getConnection().send(action)
            return

        # We received a bid so we check Acceptance Criteria
        if self._isGood(profile):
            action = Accept(self._me, self._last_received_bid)
            self.getConnection().send(action)
            return
        # Received bid did not meet acceptance criteria, so we make a counter-offer -> Negotiation Strategy kicks in
        else:
            # Our negotiation strategy depends on which phase we are in (we have split up 200 rounds into three phases)
            counter_offer_bid = None
            self._updateCurrentPhase()
            if self._current_phase == 1:
                counter_offer_bid = self.phase_one_bid()
            elif self._current_phase == 2:
                counter_offer_bid = self.phase_two_bid()
            else:
                counter_offer_bid = self.phase_three_bid()

            self._last_offered_bid = counter_offer_bid
            action = Offer(self._me, counter_offer_bid)
            self.getConnection().send(action)

    # A bid we offer in phase one is quite selfish with high utility for ourselves (i.e Optimal Bids strategy),
    # this way the opponent can learn our profile. We also attempt to learn our opponent model during this phase
    def phase_one_bid(self) -> Bid:
        # print(self._current_phase)
        # print(self._progress.getCurrentRound())
        return self.random_bid_finder()

    # A bid we offer in phase two is time concession based: with a mix between the Optimal Bid strategy (ignoring
    # opponent model) and the opponents desires (i.e including the Opponent Frequency Model)
    def phase_two_bid(self) -> Bid:
        #basic idea:select a subset of bids having the same utility as the round before (0.7).
        #send back the bid that has the highest utility for the opponent. If opponent rejects
        # start conceding by small amounts from there
        domain = self._profile.getProfile().getDomain()
        all_bids = AllBidsList(domain)
        profile = self._profile.getProfile()
        bidList = []
        for i in range(0, 500):
            currentBid = all_bids.get(randint(0, all_bids.size() - 1))
            if profile.getUtility(currentBid) > self._alpha and profile.getUtility(currentBid) < self._alpha + 0.2:
                bidList.append(currentBid)
        self._alpha -= 0.005
        print(self._alpha)
        result = self.sort(bidList)
        return result[0]

    # A bid we offer in phase three has higher concession rates, and we offer bids that the opponent previously offered
    # to us, in hopes of settling the deal
    def phase_three_bid(self) -> Bid:
        print("hello")
        return self.random_bid_finder()

    # method that checks if we would agree with an offer
    def _isGood(self, profile) -> bool:
        # We immediately accept if the proposed bid has utility > 0.9 for us
        if profile.getUtility(self._last_received_bid) > 0.9:
            return True
        # If the opponent offers utility value exceeds that of our agent’s last offered bid -> we accept
        elif self._last_offered_bid is not None and profile.getUtility(self._last_received_bid) > profile.getUtility(self._last_offered_bid):
            return True
        else:
            return False

    def random_bid_finder(self) -> Bid:
        # compose a list of all possible bids
        domain = self._profile.getProfile().getDomain()
        all_bids = AllBidsList(domain)
        progress = self._progress.get(0)
        profile = self._profile.getProfile()
        # take 50 attempts at finding a random bid that has utility better than 0.6
        for _ in range(50):
            bid = all_bids.get(randint(0, all_bids.size() - 1))
            if progress < 0.5:
                if profile.getUtility(bid) > 0.6:
                    break
            else:
                if profile.getUtility(bid) > 0.6:
                    break
        #bid = all_bids.get(0)
        return bid

    # def optimalBids(self, bidList):

    def sort(self, bidList):
        for i in range(0, len(bidList)):
            key = i
            for j in range(i, len(bidList)):
               if self._opponent_model.getUtility(bidList[j]) > self._opponent_model.getUtility(bidList[key]):
                    key = j
            temp = bidList[i]
            bidList[i] = bidList[key]
            bidList[key] = temp
        return bidList



    # method that checks if we would agree with an offer
    # def _isGood(self, last_bid: Bid, next_bid: Bid) -> bool:
    #     if last_bid is None:
    #         return False
    #     profile = self._profile.getProfile()
    #
    #     # If we get a bid with utility better than 0.9 at any time, accept it
    #     if profile.getUtility(last_bid) > 0.9:
    #         return True
    #
    #     progress = self._progress.get(0)
    #
    #     # Depending on how many rounds have already passed, adjust the constant value we ask for
    #     # Combination of time-dependent, constant utility and next bid
    #     if progress < 0.5:
    #         return profile.getUtility(last_bid) > 0.75 and profile.getUtility(last_bid) > profile.getUtility(next_bid)
    #     elif progress < 0.7:
    #         return profile.getUtility(last_bid) > 0.65 and profile.getUtility(last_bid) > profile.getUtility(next_bid)
    #     elif progress < 0.9:
    #         return profile.getUtility(last_bid) > 0.55 and profile.getUtility(last_bid) > profile.getUtility(next_bid)
    #     else:
    #         return profile.getUtility(last_bid) > 0.45 and profile.getUtility(last_bid) > profile.getUtility(next_bid)
    #
