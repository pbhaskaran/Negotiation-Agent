import logging
from random import randint
from typing import cast

from geniusweb.actions.Accept import Accept
from geniusweb.actions.Action import Action
from geniusweb.actions.EndNegotiation import EndNegotiation
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

import operator
import collections
import copy


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
        self._optimal_bid_list = []
        self._our_utilities = {}
        self._thresh_map = {0.5: 0.9, 0.4: 0.8, 0.3: 0.7, 0.2: 0.4, 0.1: 0.1, 0: 0}
        self._last_offered_bid = None
        self._no_preferable_deal = False


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
                # self._our_utilities[key] = value.getUtilities()
                res_dict = {}
                s = sorted(value.getUtilities().items(), key=lambda kv: kv[1], reverse=True)
                for item in s:
                    res_dict[item[0]] = item[1]
                self._our_utilities[key] = res_dict


            self._sorted_issue_weights = sorted(self._profile.getProfile().getWeights().items(), key=lambda kv: kv[1], reverse=True)

            self._potential_list = {}

            for issue, weight in self._sorted_issue_weights:
                self._potential_list[issue] = []
                utilities = self._our_utilities[issue]

            for w, thresh in self._thresh_map.items():
                if weight > w:
                    min_utility = thresh
                    break
            for value, utility in utilities.items():
                if utility > min_utility:
                    self._potential_list[issue].append(value)

            print("potential list: ", self._potential_list)


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
        self._refresh_thresh_map()
        # print(self._thresh_map)
        print("#############################################################", self._progress.get(0))
        # Get our next bid
        print(f"my turn, their last bid was: {self._profile.getProfile().getUtility(self._last_received_bid)} : {self._last_received_bid}")
        next_bid = self._findBid()
        print(f"I think of a bid: {self._profile.getProfile().getUtility(next_bid)} : {next_bid}")
        # check if the last received offer if the opponent is good enough
        if self._isGood(self._last_received_bid, next_bid):
            print("their bid is either better than mine or sufficient enough so I accept")
            # if so, accept the offer
            action = Accept(self._me, self._last_received_bid)
        elif self._no_preferable_deal:
            print("Ending negotiation because we did not find a preferable deal")
            action = EndNegotiation(self._me)
        else:
            print(f"I counteroffer at time {self._progress}")
            # if not, propose bid as counter offer
            self._last_offered_bid = next_bid
            action = Offer(self._me, next_bid)

        # send the action
        self.getConnection().send(action)

    # method that checks if we would agree with an offer
    def _isGood(self, last_bid: Bid, next_bid: Bid) -> bool:
        if last_bid is None:
            return False
        profile = self._profile.getProfile()

        progress = self._progress.get(0)
        print(f"last bid: {profile.getUtility(last_bid)}")
        print(f"next bid {profile.getUtility(next_bid)}")
        # Depending on how many rounds have already passed, adjust the constant value we ask for
        # Combination of time-dependent, constant utility and next bid
        if progress < 0.5:
            print("case 1")
            print(profile.getUtility(last_bid))
            return profile.getUtility(last_bid) > 0.8 and profile.getUtility(last_bid) >= profile.getUtility(next_bid)
        elif progress < 0.7:
            print("case 2")
            return profile.getUtility(last_bid) > 0.7 and profile.getUtility(last_bid) >= profile.getUtility(next_bid)
        elif progress < 0.9:
            print("case 3")
            return profile.getUtility(last_bid) > 0.6 and profile.getUtility(last_bid) >= profile.getUtility(next_bid)
        else:
            print("case 4")
            return profile.getUtility(last_bid) > 0.5 and profile.getUtility(last_bid) >= profile.getUtility(next_bid)

    def _findBid(self) -> Bid:
        # compose a list of all possible bids
        domain = self._profile.getProfile().getDomain()
        all_bids = AllBidsList(domain)
        profile = self._profile.getProfile()
        progress = self._progress.get(0)

        # In case we are the ones starting, offer a random bid that has a high utility for us
        if self._last_received_bid is None:
            # Store the best bid in case we don;t find a bid meeting our standards in the random sample
            return self._get_random_bid(0.9)



        if progress < 0.25:
            return self._findBidStage1()
        elif progress < 1:
            return self._findBidStage2()
        # Never hit for now because we may not need a stage3
        else:
            return self._get_random_bid(0,9)

    def _refresh_thresh_map(self):
        self._initial_thresh_map = {0.5: 0.9, 0.4: 0.8, 0.3: 0.7, 0.2: 0.4, 0.1: 0.1, 0: 0}
        self._final_thresh_map = {0.5: 0.7, 0.4: 0.6, 0.3: 0.5, 0.2: 0.2, 0.1: 0.1, 0: 0}

        for key, value in self._thresh_map.items():
            self._thresh_map[key] = self._initial_thresh_map[key] - (self._initial_thresh_map[key] - self._final_thresh_map[key])*self._progress.get(0)*2

    def _get_random_bid(self, thresh):
        domain = self._profile.getProfile().getDomain()
        all_bids = AllBidsList(domain)
        profile = self._profile.getProfile()
        best_bid = all_bids.get(randint(0, all_bids.size() - 1))
        for i, _ in enumerate(range(50)):
            bid = all_bids.get(randint(0, all_bids.size() - 1))
            if profile.getUtility(bid) > profile.getUtility(best_bid):
                best_bid = bid
            if profile.getUtility(bid) > thresh:
                best_bid = bid
                break
        return best_bid

    def _findBidStage1(self):
        # compose a list of all possible bids
        domain = self._profile.getProfile().getDomain()
        all_bids = AllBidsList(domain)
        profile = self._profile.getProfile()
        progress = self._progress.get(0)

        # We get the last received bid
        bid = self._last_received_bid
        # THe bid is not good enough to accept so we choose the one that has the lowest utility for us and make it the highest
        # Todo: more systematic: start changing issues which have more weight for us
        # todo: only needs to be done once

        change_counter = 0
        # print(self._our_utilities)
        new_bid = copy.deepcopy(bid.getIssueValues())
        for issue, weight in self._sorted_issue_weights:
            utilities = self._our_utilities[issue]
            highest_value = next(iter(utilities))
            new_bid[issue] = highest_value
            print(f"trying: {profile.getUtility(Bid(new_bid))} : {new_bid}")
            if self._isGood(Bid(new_bid), Bid(new_bid)):
                break

        new_bid = Bid(new_bid)
        print(f"Found bid {new_bid}")

        if new_bid == self._last_offered_bid:
            new_bid = self._get_random_bid(profile.getUtility(new_bid))
            print(f"To avoid bidding the same thing I am trying a random bid")

        return new_bid

        # print(bid.getIssueValues())
        # print(self._profile.getProfile().getUtility(bid))
        # for issue, value in bid.getIssueValues().items():
        #     print(issue, value)
        # Do this by sorting

        # Aim: to get a bid above a certain thresh (do we put it in a pool or just do it per round?)


    def _findBidStage2(self):
        # compose a list of all possible bids
        domain = self._profile.getProfile().getDomain()
        all_bids = AllBidsList(domain)
        profile = self._profile.getProfile()
        progress = self._progress.get(0)

        print(self._last_received_bid)
        print(self._potential_list)

        new_bid = copy.deepcopy(self._last_received_bid.getIssueValues())
        print(new_bid)

        for issue, value in self._last_received_bid.getIssueValues().items():
            if value not in self._potential_list[issue]:
                best_value = None
                value_counts = self._opponent_model.getCounts(issue)
                for potential_value in self._potential_list[issue]:
                    if best_value is None:
                        if potential_value in value_counts:
                            best_value = potential_value
                    else:
                        if potential_value in value_counts :
                            if value_counts[potential_value] > value_counts[best_value]:
                                best_value = potential_value
                if best_value is not None:
                    new_bid[issue] = best_value
                else:
                    self._no_preferable_deal = True

        new_bid = Bid(new_bid)

        return new_bid











