from decimal import Decimal
from typing import Optional, Dict

from geniusweb.actions.Offer import Offer
from geniusweb.issuevalue.Domain import Domain
from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel
from geniusweb.issuevalue.Value import Value
from geniusweb.issuevalue.Bid import Bid
from geniusweb.actions.Action import Action
from geniusweb.progress.Progress import Progress
from geniusweb.utils import val


class OurFrequencyOpponentModel(FrequencyOpponentModel):
    def __init__(self, domain: Optional[Domain], freqs: Dict[str, Dict[Value, int]], total: int, resBid: Optional[Bid]):
        super().__init__(domain, freqs, total, resBid)

    @staticmethod
    def create() -> "FrequencyOpponentModel":
        return OurFrequencyOpponentModel(None, {}, 0, None)

    # Override
    def With(self, newDomain: Domain, newResBid: Optional[Bid]) -> "FrequencyOpponentModel":
        if newDomain == None:
            raise ValueError("domain is not initialized")
        # FIXME merge already available frequencies?
        return OurFrequencyOpponentModel(newDomain,
                                      {iss: {} for iss in newDomain.getIssues()},
                                      0, newResBid)

    # Override
    def WithAction(self, action: Action, progress: Progress) -> "FrequencyOpponentModel":
        if self._domain == None:
            raise ValueError("domain is not initialized")

        if not isinstance(action, Offer):
            return self

        bid: Bid = action.getBid()
        newFreqs: Dict[str, Dict[Value, int]] = self.cloneMap(self._bidFrequencies)
        for issue in self._domain.getIssues():  # type:ignore
            freqs: Dict[Value, int] = newFreqs[issue]
            value = bid.getValue(issue)
            if value != None:
                oldfreq = 0
                if value in freqs:
                    oldfreq = freqs[value]
                freqs[value] = oldfreq + 1  # type:ignore

        return OurFrequencyOpponentModel(self._domain, newFreqs,
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
        return round(sum / len(self._bidFrequencies), FrequencyOpponentModel._DECIMALS)