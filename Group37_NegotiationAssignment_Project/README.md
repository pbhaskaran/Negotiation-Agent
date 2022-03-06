__Opponent modelling:__ \
We decided to use the first 25 rounds to model the opponent and then use those value and issue weights for 
the remainder of the negotiation. The reasoning is that we assume our opponent 
starts off by doing very selfish bids before they start conceding. Our opponent model extends from the original Opponent_model class
since we also give weights to the issues(not just the values)


__Bidding strategy:__\
The bidding strategy is split into three phases. The first phase would send optimal bids for us so the opponent can learn our preferences. 
The second phase, we start very slowly conceding to the opponent while also trying to maximise our utility. The final phase we send back 
bid the opponent has already offered as a last ditch strategy to reach an agreement. 




__Acceptance strategy:__\
The acceptance strategy can be paired well with a time-based concession strategy. Namely, if at every round we concede our bids,
we should accept the counter bid from the opponent if that has a higher utility from our previous offer. 



Please refer to the report for further details on any of these topics.