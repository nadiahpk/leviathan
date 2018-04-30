# make it so a punisher in a group with no one to punish instead contributes (or not, depending on rule)
# want to see what difference it makes to punish non-voters

# c: contribute to public good
# v: award vote to someone
# v_rules: award rules
# p: punisher
# p_rules: punishment rules

import random
from pyeda.boolalg.expr import exprvar, And, Or, Not
from pyeda.inter import expr2truthtable, expr
from pyeda.boolalg.boolfunc import point2term, point2upoint
import itertools as it
from bisect import bisect
import matplotlib.pyplot as plt


# parameters
# ---

#random.seed(2)

# default start values 
mon_0 = 1 # money at start of each round
pow_0 = 1 # power at start of each round
pgg_multiplier = 7 # return for every unit put in the pool NOTE how to choose?
pow_multiplier = 2 # number of votes received is multiplied by this to determine punishing power
mutn_rate = 0.01 # probability with which a random possiblity chosen instead
gen_max = 200 # max no. of generations

grp_size = 10
no_grps = 20

# create the variables and a handy dictionary for them
# ---

c, v, p = map(exprvar, 'cvp') # creates boolean variables c, v, and p representing contribute, vote, and punish
evars = [c,v,p]

uniqid2evar = { vv.uniqid: vv for vv in evars }


# scenarios
# ---

scen = 0

if scen == 0:

    # no punishers, no voters

    f = And( Not(p), Not(v), Or(c, ~c, simplify=False), simplify=False ) 
    suffix = '0_nopun_novot'

elif scen == 1:

    # voters and punishers
    # punishers don't cooperate
    f = And( Not(And(p,c)), Not(And(~c,v)), Or(c, ~c, simplify=False), Not(And(p, v)), simplify=False )

    # punish non-cooperation only
    poss_prules = [
            [ And(~p, ~c) ] ]
    suffix = '1_punnocs'

elif scen == 2:

    # punishers don't cooperate
    f = And( Not(And(p,c)), Not(And(~c,v)), Or(c, ~c, simplify=False), Not(And(p, v)), simplify=False )

    # punish non-cooperators and non-voters
    poss_prules = [
            [ And(~p, ~c) ] ,
            [ And(~p, ~v) ] ]
    suffix = '2_punnocsnovs'

elif scen == 3:

    # punishers don't cooperate and nefarious voters
    f = And( Not(And(p,c)), Or(c, ~c, simplify=False), Not(And(p, v)), simplify=False )

    # punish non-cooperators and non-voters
    poss_prules = [
            [ And(~p, ~c) ] ,
            [ And(~p, ~v) ] ]
    suffix = '3_nefariousvots'


# find all possible species of individuals
# ---

tt = expr2truthtable(f) # truth table, each truth is one possible individual

poss_behs = list() # create a list of possible behaviours
for row in tt.iter_relation(): # for each row in the truth table

    if row[1].is_one(): # if this row is a true in the table

        # point2upoint creates something like (frozenset({1, 3, 5}), frozenset())
        # where the first set is false variables and the second set is true variables
        upoint = point2upoint(row[0]) 
        vv = [ ~uniqid2evar[u] for u in upoint[0] ] + [ uniqid2evar[u] for u in upoint[1] ]
        poss_behs.append( And(*vv) )




# awarder rules
# ---
# beh_vrules: rules to do with the basic behaviour of the punisher
# pun_vrules: rules to do with the punishment behaviour of the punisher -- if any these behaviours are in the punisher rules then will not vote for punsiher

# only vote for punishers
poss_beh_vrules = [ 
        [ p ], 
        ]

# NOTE for now the only pun_vrule is punishing self


# create all possible personalities
# ----


poss_pers = list()
pers_id = 0 # just to be handy
for beh in poss_behs:

    # if a punisher ...
    if And(beh, ~p) == expr(False): # if the product beh contains p, then And(beh, ~p) = False

        for prules in poss_prules:

            # ... and a voter
            if And(beh, ~v) == expr(False): # if the product beh contains p, then And(beh, ~p) = False

                for beh_vrules in poss_beh_vrules:

                    poss_pers.append( {'beh': beh, 'prules': prules, 'beh_vrules': beh_vrules, 'pun_vrules': [beh], 'pers_id': pers_id} )
                    pers_id += 1
                    # TODO make simple form?

            else: # ... and not a voter

                poss_pers.append( {'beh': beh, 'prules': prules, 'beh_vrules': list(), 'pun_vrules': list(), 'pers_id': pers_id } )
                pers_id += 1

    else: # if not a punisher

        # ... and a voter
        if And(beh, ~v) == expr(False): # if the product beh contains p, then And(beh, ~p) = False

            for beh_vrules in poss_beh_vrules:

                poss_pers.append( {'beh': beh, 'prules': list(), 'beh_vrules': beh_vrules, 'pun_vrules': [beh], 'pers_id': pers_id } )
                pers_id += 1

        else: # ... and not a voter

            poss_pers.append( {'beh': beh, 'prules': list(), 'beh_vrules': list(), 'pun_vrules': list(), 'pers_id': pers_id } )
            pers_id += 1




# storage of how many of each type
# ---

stor = { pers_id: list() for pers_id in range(len(poss_pers)) }


# create initial system
# ---

if True:

    reg = list()
    for cnt_no_grps in range(no_grps):

        grp = list()
        for cnt_no_inds in range(grp_size):

            ind = { k: v for k, v in random.choice(poss_pers).items() } 

            grp.append( ind )

        reg.append(grp)


else: # NOTE for debugging

    grp = [ { k: v for k, v in pers.items() } for pers in poss_pers ] 

    grp_size = len(grp)

    gen_max = 1
    no_grps = 1
    reg = [grp]

# NOTE /debugging

# store info about system
# ---

for pers_id in stor.keys():

    stor[pers_id].append(0) # ready a step

for grp in reg:

    for ind in grp:

        pers_id = ind['pers_id'] # get personality index
        stor[pers_id][-1] += 1


for gen in range(gen_max): # one step of the game


    # initialise power and money of each individual
    # ---

    for grp_idx in range(no_grps):

        grp = reg[grp_idx]

        for foc_idx in range(grp_size):

            foc_ind = grp[foc_idx]
            foc_ind['money'] = mon_0
            foc_ind['power'] = pow_0


    # process each group
    # ---

    for grp_idx in range(no_grps):

        grp = reg[grp_idx]
        pool = 0


        # voting
        # --- 

        for foc_idx in range(grp_size):

            foc_ind = grp[foc_idx]

            # if a voter
            if And(foc_ind['beh'], ~v) == expr(False):

                # update 'vote_for' for who we're voting for

                foc_ind['vote_for'] = list()

                for oth_idx in range(len(grp)):

                    oth_ind = grp[oth_idx]

                    #print( str(foc_idx) + '->' + str(oth_idx) )

                    voteFor = False

                    # if other meets focal individual's voting behavioural rules
                    for beh_vrule in foc_ind['beh_vrules']:

                        if And(oth_ind['beh'], ~beh_vrule).to_dnf() == expr(False):

                            voteFor = True
                            break

                    # if other does not violate any focal individual's punishment rules
                    for pun_vrule in foc_ind['pun_vrules']:

                        for prule in oth_ind['prules']:

                            if And(foc_ind['beh'], Not(prule)).to_dnf() == expr(False): 

                                voteFor = False
                                break

                    # add to voting list if will vote for
                    if voteFor:

                        foc_ind['vote_for'].append(oth_idx) # NOTE issue here, modifying in place and should not


                # allocate votes
                no_votes = len(foc_ind['vote_for'])

                if no_votes > 0:

                    power = foc_ind['power']
                    per_vote = power / no_votes
                    foc_ind['power'] = 0

                    for oth_idx in foc_ind['vote_for']:

                        grp[oth_idx]['power'] += per_vote



        # calculate punishments due 
        # --- 
        # doing this first so if a punisher has no one to punish they can contribute

        for foc_idx in range(grp_size):

            foc_ind = grp[foc_idx]

            # if a punisher
            if And(foc_ind['beh'], ~p) == expr(False):

                # create a hit list with each individual's punishment due

                foc_ind['hit_list'] = dict()

                for oth_idx in range(len(grp)):

                    oth_ind = grp[oth_idx]

                    # if other is a non-punisher TODO remove this, as we might like different later
                    if And(oth_ind['beh'], p) == expr(False): 

                        pun_pts = 0

                        # behaviour punishment
                        for prule in foc_ind['prules']:

                            if And(oth_ind['beh'], Not(prule)).to_dnf() == expr(False):

                                pun_pts += 1

                        # # punishment for not voting for me TODO
                        # if foc_idx not in oth_ind['vote_for']:
                        # pun_pts += 1

                        # make a note of in hit_list
                        if pun_pts > 0:

                            foc_ind['hit_list'][oth_idx] = pun_pts


        # contribute to pgg
        # ---

        for foc_idx in range(grp_size):

            foc_ind = grp[foc_idx]

            # if a contributor
            if And(foc_ind['beh'], ~c) == expr(False):

                # if not a punisher or is a punisher but hit-list is empty

                if ( And(foc_ind['beh'], p) == expr(False) ) or ( And(foc_ind['beh'], ~p) == expr(False) and len(foc_ind['hit_list']) == 0 ):

                    pool += foc_ind['money']
                    foc_ind['money'] = 0


        # mete out punishments
        # ---


        for foc_idx in range(grp_size):

            foc_ind = grp[foc_idx]

            # if a punisher
            if And(foc_ind['beh'], ~p) == expr(False):

                money = foc_ind['money']
                power = foc_ind['power'] * pow_multiplier
                foc_ind['money'] = 0 # assumes we spend it all

                # mete out punishments according to the hitlist
                no_hits = sum( foc_ind['hit_list'].values() )
                if no_hits > 0:

                    per_hit = money*power / no_hits

                    for oth_idx, pun_pts in foc_ind['hit_list'].items():

                        grp[oth_idx]['money'] -= per_hit * pun_pts


        # the public goods game
        # ---

        pool = pool * pgg_multiplier
        len_grp = len(grp)
        per_pgg = pool / len_grp

        for foc_idx in range(grp_size):

            foc_ind = grp[foc_idx]
            foc_ind['money'] += per_pgg
        

    # reproduction and mutation
    # ---

    # flatten the list of individuals
    all_inds = [ ind for grp in reg for ind in grp ]

    # how much money each has - if negative set to 1
    all_moneys = [ ind['money'] for ind in all_inds ]
    min_money = min(all_moneys)
    max_money = max(all_moneys)
    diff = max_money - min_money
    if diff == 0:
        weights = [ 1 for m in all_moneys ]
    else:
        weights = [ (m-min_money)/diff for m in all_moneys ]


    # create new region by selecting individuals according to weights
    # with probability, choose a random

    cumulWeights = list( it.accumulate(weights) )

    reg = list()
    for cnt_no_grps in range(no_grps):

        grp = list()
        for cnt_no_inds in range(grp_size):

            if random.random() < mutn_rate:

                ind = { k: v for k, v in random.choice(poss_pers).items() } 

            else:

                idx = bisect( cumulWeights, random.random()*cumulWeights[-1] )
                ind = { k: v for k, v in all_inds[idx].items() }

            grp.append( ind )

        reg.append(grp)


    # update storage
    # ---

    for pers_id in stor.keys():

        stor[pers_id].append(0) # ready a step

    for grp in reg:

        for ind in grp:

            pers_id = ind['pers_id'] # get personality index
            stor[pers_id][-1] += 1

# plot
# ---

# plot colours

baddy_cmap = plt.get_cmap('autumn')
goody_cmap = plt.get_cmap('winter')
punis_cmap = plt.get_cmap('gist_rainbow')

goodys = list()
baddys = list()
puniss = list()
for pers in poss_pers:

    pers_id = pers['pers_id']
    beh = pers['beh']

    if ( And(beh, ~p) == expr(False) ):
        puniss.append(pers_id)
    elif ( And(beh, ~c) == expr(False) ):
        goodys.append(pers_id)
    else:
        baddys.append(pers_id)

tot_goodys = len(goodys)
tot_baddys = len(baddys)
tot_puniss = len(puniss)

pers_id2colour = dict()
for i, pers_id in enumerate(goodys):
    pers_id2colour[pers_id] = goody_cmap( i/(tot_goodys) ) 
for i, pers_id in enumerate(baddys):
    pers_id2colour[pers_id] = baddy_cmap( i/(tot_baddys) ) 
for i, pers_id in enumerate(puniss):
    pers_id2colour[pers_id] = punis_cmap( i/(tot_puniss) ) 

pers_id2ls = dict()
for pers in poss_pers:

    pers_id = pers['pers_id']
    beh = pers['beh']

    if ( And(beh, ~p) == expr(False) ):
        ls = 'solid'
    else:
        if ( And(beh, ~v) == expr(False) ):
            ls = 'dashed'
        else:
            ls = 'dotted'

    pers_id2ls[pers_id] = ls



for pers_id, l in stor.items():

    # create label string

    # basic behaviour
    pers = poss_pers[pers_id]
    beh = pers['beh']
    ss = str(beh) + ' '

    # if a punisher, add their prules
    if And(beh, ~p) == expr(False): 

        ss += 'punish'

        for prule in pers['prules']:

            ss += ' ' + str(prule)

    # if a voter, add their behavioural vrules
    if And(beh, ~v) == expr(False): 

        ss += 'vote for'

        for vrule in pers['beh_vrules']:

            ss += ' ' + str(vrule)

    # plot data
    plt.plot(l, label=ss, alpha=0.7, ls=pers_id2ls[pers_id], color=pers_id2colour[pers_id])

#plt.legend(loc='best', bbox_to_anchor=(0.5, -0.1))
plt.xlabel('time')
plt.ylabel('no. individuals')
lgd = plt.legend(bbox_to_anchor=(1.05, 0), loc='lower left', borderaxespad=0.)
#plt.show()
plt.savefig('firstegs_' + suffix + '.pdf', bbox_extra_artists=(lgd,), bbox_inches='tight')
#plt.savefig('test.pdf', bbox_extra_artists=(lgd,), bbox_inches='tight')
plt.close()
