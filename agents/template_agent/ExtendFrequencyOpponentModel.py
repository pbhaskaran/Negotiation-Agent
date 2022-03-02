from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel
from geniusweb.issuevalue.Bid import Bid
from geniusweb.utils import val, HASH, toStr
from geniusweb.issuevalue.Domain import Domain
from decimal import Decimal
from geniusweb.actions.Action import Action
from geniusweb.progress.Progress import Progress
from geniusweb.actions.Offer import Offer
from geniusweb.issuevalue.Value import Value
from typing import Dict, Optional

class ExtendFrequencyOpponentModel(FrequencyOpponentModel):

    def __init__(self, domain: Optional[Domain],
                 freqs: Dict[str, Dict[Value, int]],
                 weights: Dict[str, int],
                 total: int,
                 resBid: Optional[Bid]):
        '''
        internal constructor. DO NOT USE, see create. Assumes the freqs keyset is
        equal to the available issues.

        @param domain the domain. Should not be None
        @param freqs  the observed frequencies for all issue values. This map is
                      assumed to be a fresh private-access only copy.
        @param weights the issue weights
        @param total  the total number of bids contained in the freqs map. This
                      must be equal to the sum of the Integer values in the
                      {@link #bidFrequencies} for each issue (this is not
                      checked).
        @param resBid the reservation bid. Can be null
        '''
        self._domain = domain
        self._bidFrequencies = freqs
        self._issueWeights = weights
        self._totalBids = total
        self._resBid = resBid
        self.epsilon = 0.25

    @staticmethod
    def create() -> "ExtendFrequencyOpponentModel":
        return ExtendFrequencyOpponentModel(None, {}, {}, 0, None)

    @staticmethod
    def cloneMap1(weights: Dict[str, int]) -> Dict[str, int]:
        '''
        @param weights
        @return deep copy of weights map.
        '''
        map: Dict[str, int] = {}
        for issue in weights:
            map[issue] = weights[issue]
        return map

    # Override
    def With(self, newDomain: Domain, newResBid: Optional[Bid]) -> "ExtendFrequencyOpponentModel":
        if newDomain == None:
            raise ValueError("domain is not initialized")
        # FIXME merge already available frequencies?
        return ExtendFrequencyOpponentModel(newDomain,
                                      {iss: {} for iss in newDomain.getIssues()},
                                      {iss: {10} for iss in newDomain.getIssues()},
                                      0, newResBid)

    # Override
    def WithAction(self, action: Action, lastBid: Bid, progress: Progress) -> "ExtendFrequencyOpponentModel":
        if self._domain == None:
            raise ValueError("domain is not initialized")

        if not isinstance(action, Offer):
            return self

        bid: Bid = action.getBid()
        print(bid)
        print("---------------------------")
        print(lastBid)
        newFreqs: Dict[str, Dict[Value, int]] = self.cloneMap(self._bidFrequencies)
        newWeights: Dict[str, int] = self.cloneMap1(self._issueWeights)
        for issue in self._domain.getIssues():  # type:ignore
            freqs: Dict[Value, int] = newFreqs[issue]
            value = bid.getValue(issue)
            if value != None:
                oldfreq = 0
                if value in freqs:
                    oldfreq = freqs[value]
                freqs[value] = oldfreq + 1  # type:ignore

        return ExtendFrequencyOpponentModel(self._domain, newFreqs, newWeights,
                                      self._totalBids + 1, self._resBid)

    # Override
    def getUtility(self, bid: Bid) -> Decimal:
        if self._domain == None:
            raise ValueError("domain is not initialized")
        if self._totalBids == 0:
            return Decimal(1)
        sum = Decimal(0)
        # Assume all issues have equal weight.
        for issue in val(self._domain).getIssues():
            if issue in bid.getIssues():
                sum = sum + self._getFraction(issue, val(bid.getValue(issue)))
        return round(sum / len(self._bidFrequencies), ExtendFrequencyOpponentModel._DECIMALS)

