import decimal
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

from geniusweb.profileconnection import ProfileInterface
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)
from geniusweb.progress.ProgressRounds import ProgressRounds
from geniusweb.profile.utilityspace.LinearAdditive import LinearAdditive
from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.bidspace.Interval import Interval
from decimal import Decimal

from agents.template_agent.ExtendFrequencyOpponentModel import ExtendFrequencyOpponentModel


class Group37_NegotiationAssignment_Agent(DefaultParty):
    """
    Template agent that offers random bids until a bid with sufficient utility is offered.
    """

    def __init__(self):
        super().__init__()
        self.getReporter().log(logging.INFO, "party is initialized")
        self._profile: ProfileInterface = None
        self._last_offered_bid: Bid = None
        self._last_received_bid: Bid = None

        self._utilspace: LinearAdditive = None
        self._bidutils: BidsWithUtility = None
        self._expected_utilities = []

        self.opponent_util_space: LinearAdditive = None

        # We keep track of the received bids thus far, sorted by our utility
        self._received_bids = []
        self._progress: ProgressRounds = None
        self._e = None

        self._current_phase = 1
        # At which round of the negotiation should phase 2 and phase 3 begin:
        self._phase_two_start_round = 30
        self._phase_three_start_round = 196
        self._alpha = 0.9
        self._opponent_model: ExtendFrequencyOpponentModel = ExtendFrequencyOpponentModel.create()
        self._decrease_alpha = False

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
            self.set_optimal_expected_utility()

            self._opponent_model = self._opponent_model.With(newDomain=self._profile.getProfile().getDomain(),
                                                             newResBid=0)

        # ActionDone is an action send by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()
            # if it is an offer, set the last received bid and append it to the list of received bids
            if isinstance(action, Offer):
                # only learn the opponent for the first 25 rounds (phase 1)
                if self._current_phase == 1:
                    self._opponent_model = self._opponent_model.WithAction(action, self._last_received_bid,
                                                                           self._progress)
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

    # The utilspace attribute is casted from the Profile object to that of a LinearAdditive object
    # we need to do this casting so that we can use the BidsWithUtility object (in its constructor it takes a
    # LinearAdditive) object
    def _updateUtilSpace(self) -> LinearAdditive:
        newutilspace = self._profile.getProfile()
        if not newutilspace == self._utilspace:
            self._utilspace = cast(LinearAdditive, newutilspace)
            self._bidutils = BidsWithUtility.create(self._utilspace)
        return self._utilspace

    def set_optimal_expected_utility(self):
        expected_utilities = []
        # if agent has a reservation bid, store it in expected_utilities_list
        rv_bid = self._profile.getProfile().getReservationBid()
        if rv_bid is not None:
            rv = self._profile.getProfile().getUtility(rv_bid)
            expected_utilities.append(rv)
        else:
            expected_utilities.append(0)

            # using function new_utility = 0.25*(previous_utility)^2
        for i in range(1, 201):
            prev = expected_utilities[i - 1]
            util = 0.25 * (prev + 1.0) ** 2
            expected_utilities.append(util)
        self._expected_utilities = expected_utilities

    # execute a turn
    def _myTurn(self):
        # profile = self._profile.getProfile()
        if self._last_received_bid is not None:
            self._received_bids.append(self._last_received_bid)
        self._updateUtilSpace()
        self._updateCurrentPhase()
        # If we are making the first bid, we make the bid with the highest possible utility for ourselves (Agent Smith)
        if self._last_received_bid is None:
            next_bid = self._bidutils.getExtremeBid(True)
            self._last_offered_bid = next_bid
            action = Offer(self._me, next_bid)
            self.getConnection().send(action)
            return

        # We received a bid so we make initial check of Acceptance Criteria
        # We immediately accept if the proposed bid has utility > 0.9 for us
        if self._utilspace.getUtility(self._last_received_bid) > 0.9:
            action = Accept(self._me, self._last_received_bid)
            self.getConnection().send(action)
            return
        # Received bid did not meet initial acceptance criteria, so we make a counter-offer -> Negotiation Strategy
        # kicks in
        else:
            # Our negotiation strategy depends on which phase we are in (we have split up 200 rounds into three phases)
            if self._current_phase == 1:
                counter_offer_bid = self.phase_one_bid()
            elif self._current_phase == 2:
                counter_offer_bid = self.phase_two_bid()
            else:
                counter_offer_bid = self.phase_three_bid()
            # With our counter_offer bid, we check our Acceptance criteria. If we don't decide to accept, we proceed
            # to offer
            if self._isGood(self._last_received_bid, counter_offer_bid):
                action = Accept(self._me, self._last_received_bid)
                self.getConnection().send(action)
                return
            else:
                self._last_offered_bid = counter_offer_bid
                action = Offer(self._me, counter_offer_bid)
                self.getConnection().send(action)
                return

    # A bid we offer in phase one is quite selfish with high utility for ourselves (i.e Optimal Bids strategy),
    # this way the opponent can learn our profile. We also attempt to learn our opponent model during this phase
    def phase_one_bid(self) -> Bid:
        num_remaining_rounds = 200 - self._progress.getCurrentRound()
        cur_exp_optimal_utility = Decimal(self._expected_utilities[num_remaining_rounds])

        # Should we make lower bound change with time as in the time based agent?
        lower_bound = cur_exp_optimal_utility - Decimal(0.05)
        potential_bids = self._bidutils.getBids(Interval(lower_bound, cur_exp_optimal_utility))

        # Return a random bid from the potential bids
        if potential_bids.size() == 0:
            # I dont know what to do if we don't find bids, maybe just return maximum bid?
            return self._bidutils.getExtremeBid(True)
        else:
            return potential_bids.get(randint(0, potential_bids.size() - 1))

    # A bid we offer in phase two is time concession based: with a mix between the Optimal Bid strategy (ignoring
    # opponent model) and the opponents desires (i.e including the Opponent Frequency Model)
    def phase_two_bid(self) -> Bid:
        # In the first half, we attempt to first make fortunate moves, then nice moves, and if we cannot find
        # any bid in these categories, we concede. In other words, we completely ignore selfish or unfortunate moves.
        # We begin our concession halfway through phase 2
        if self._progress.getCurrentRound() < round((self._phase_three_start_round + self._phase_two_start_round) / 2):
            # First we randomly find some bids in our BidSpace. The upper bound is found applying Optimal Bid Strategy
            # lower bid is decreased with alpha over time.
            lower_bound = self._alpha - 0.04
            upper_bound = (self._alpha + 0.05 + self._expected_utilities[200 - self._progress.getCurrentRound()]) / 2
            potential_bids = self._bidutils.getBids(Interval(Decimal(lower_bound), Decimal(upper_bound)))
            if self._decrease_alpha:
                self._alpha -= 0.0025

            # Now we split our potential bids into four sets of fortunate, nice, concession bids, and silent bids
            fortunate_bids = []
            nice_bids = []
            concession_bids = []
            silent_bids = []
            for bid in potential_bids:
                delta_me = self._utilspace.getUtility(bid) - self._utilspace.getUtility(self._last_offered_bid)
                delta_op = self._opponent_model.getUtility(bid) - self._opponent_model.getUtility(
                    self._last_offered_bid)
                if delta_me > 0 and delta_op > 0:
                    fortunate_bids.append(bid)
                elif -0.007 <= delta_me <= 0.007 and delta_op > 0:
                    nice_bids.append(bid)
                elif delta_me < 0 and delta_op >= 0:
                    concession_bids.append(bid)
                elif -0.005 <= delta_me <= 0.005 and -0.005 <= delta_me <= 0.005:
                    silent_bids.append(bid)
                else:
                    continue
            # Order of selecting a bid: Fortunate, Nice, Concession, Silent, Selfish or Unfortunate
            if len(fortunate_bids) != 0:
                self._decrease_alpha = False
                return fortunate_bids[randint(0, len(fortunate_bids) - 1)]
            elif len(nice_bids) != 0:
                self._decrease_alpha = False
                return nice_bids[randint(0, len(nice_bids) - 1)]
            elif len(concession_bids) != 0:
                self._decrease_alpha = True
                return concession_bids[randint(0, len(concession_bids) - 1)]
            elif len(silent_bids) != 0:
                self._decrease_alpha = True
                return silent_bids[randint(0, len(silent_bids) - 1)]
            else:
                self._decrease_alpha = True
                # Extreme worse case scenario we resort to unfortunate or selfish moves
                return potential_bids.get(randint(0, potential_bids.size() - 1))
        else:
            # next half of the rounds we slowly start conceding to the opponent
            #     lower_bound = self._alpha - 0.05
            #     num_remaining_rounds = 200 - self._progress.getCurrentRound()
            #     upper_bound = Decimal(self._expected_utilities[num_remaining_rounds])
            # find bids within the range
            lower_bound = self._alpha - 0.04
            upper_bound = (self._alpha + 0.05 + self._expected_utilities[200 - self._progress.getCurrentRound()]) / 2
            potential_bids = self._bidutils.getBids(Interval(Decimal(lower_bound), Decimal(upper_bound)))

            self._alpha -= 0.002
            result = sorted(potential_bids, key=lambda bid: self._opponent_model.getUtility(bid),
                            reverse=True)
            if result == 0:
                return self.random_bid_finder()
            else:
                maximum = min(100, len(result))
                return result[(randint(0, maximum - 1))]

    # A bid we offer in phase three has higher concession rates, and we offer bids that the opponent previously offered
    # to us, in hopes of settling the deal
    def phase_three_bid(self) -> Bid:
        self._received_bids = sorted(self._received_bids, key=lambda bid: self._profile.getProfile().getUtility(bid),
                                     reverse=True)
        return self._received_bids[0]

    # method that checks if we would agree with an offer
    def _isGood(self, last_bid, next_bid) -> bool:
        if last_bid is None:
            return False
        profile = self._utilspace
        progress = self._progress.get(0)
        # At any point if the utility is better than 0.9 then we accept
        if profile.getUtility(last_bid) > 0.9:
            return True
        # Depending on how many rounds have already passed, adjust the constant value we ask for
        # Combination of time-dependent, constant utility and next bid
        if progress < 0.5:
            return profile.getUtility(last_bid) > 0.85 and profile.getUtility(last_bid) >= profile.getUtility(next_bid)
        elif progress < 0.7:
            return profile.getUtility(last_bid) > 0.75 and profile.getUtility(last_bid) >= profile.getUtility(next_bid)
        elif progress < 0.9:
            return profile.getUtility(last_bid) > 0.6 and profile.getUtility(last_bid) >= profile.getUtility(next_bid)
        else:
            return profile.getUtility(last_bid) > 0.5 and profile.getUtility(last_bid) >= profile.getUtility(next_bid)

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
                if profile.getUtility(bid) > 0.65:
                    break
            else:
                if profile.getUtility(bid) > 0.6:
                    break
        return bid
