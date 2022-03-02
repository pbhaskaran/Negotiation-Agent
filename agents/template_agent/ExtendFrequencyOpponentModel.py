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
                 weights: Dict[str, float],
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

    @staticmethod
    def create() -> "ExtendFrequencyOpponentModel":
        return ExtendFrequencyOpponentModel(None, {}, {}, 0, None)

    @staticmethod
    def cloneMap1(weights: Dict[str, float]) -> Dict[str, float]:
        '''
        @param weights
        @return deep copy of weights map.
        '''
        map: Dict[str, float] = {}
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
                                      {iss: 10.0 for iss in newDomain.getIssues()},
                                      0, newResBid)

    # Override
    def WithAction(self, action: Action, lastBid: Bid, progress: Progress) -> "ExtendFrequencyOpponentModel":
        if self._domain == None:
            raise ValueError("domain is not initialized")

        if not isinstance(action, Offer):
            return self

        bid: Bid = action.getBid()
        # Clone the previous frequencies and weights
        newFreqs: Dict[str, Dict[Value, int]] = self.cloneMap(self._bidFrequencies)
        newWeights: Dict[str, float] = self.cloneMap1(self._issueWeights)
        # Iterate through all the issues
        for issue in self._domain.getIssues():  # type:ignore
            freqs: Dict[Value, int] = newFreqs[issue]
            weight: float = newWeights[issue]
            value = bid.getValue(issue)
            if lastBid != None:
                previous_value = lastBid.getValue(issue)
                # Get the ratio of the max frequency and sum of frequencies, capped at 0.25
                epsilon = min(max(freqs.values())/sum(freqs.values()), 0.4)
                # If the value of this issue changed then make it less important
                if previous_value != value:
                    newWeight = max(weight - min(1/epsilon, 0.4), 0.01)
                    newWeights[issue] = newWeight
                # If the value remained the same then make it more important
                else:
                    newWeight = weight + epsilon
                    newWeights[issue] = newWeight
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
        sumWeights = Decimal(0)

        # Use issue weights now that we have them
        for issue in val(self._domain).getIssues():
            if issue in bid.getIssues():
                sumWeights = sumWeights + Decimal(self._issueWeights[issue])
                sum = sum + Decimal(self._issueWeights[issue]) * self._getFraction(issue, val(bid.getValue(issue)))
        return round(sum / sumWeights, ExtendFrequencyOpponentModel._DECIMALS)

    def _getFraction(self, issue: str, value: Value) -> Decimal:
        '''
        @param issue the issue to check
        @param value the value to check
        @return the fraction of the total cases that bids contained given value
                for the issue.
        '''
        if self._totalBids == 0:
            return Decimal(1)
        if not (issue in self._bidFrequencies and value in self._bidFrequencies[issue]):
            return Decimal(0)
        freq: int = self._bidFrequencies[issue][value]
        # Add a lower bound of 0.2 for each value weight
        return round(max(Decimal(freq) / self._totalBids, Decimal(0.2)), FrequencyOpponentModel._DECIMALS)
