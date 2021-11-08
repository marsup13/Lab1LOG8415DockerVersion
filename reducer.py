import sys


def add_friends(user_dict, k1, k2, connection):
    """
    add and count friend connection in reducer's dictionary
    :param user_dict: dictionary containing user's relation
    with it's mutuals. it's either directly friends with them or has mutual friends with them.
    :param k1: user_id 1
    :param k2: user_id 2
    :param connection: whether 'friend' or 'not_friend'
    """

    if k1 not in user_dict:  # if we haven't seen the user before
        user_dict[k1] = {}  # add user to user_dict
        user_dict[k1][k2] = [1, False]  # add counter that this user and k2 are mutuals and up the counter of how many
        # times this pair was seen

    else:  # if the user has been seen
        if k2 in user_dict[k1]:  # if k2 has been seen with current user, just up the counter
            user_dict[k1][k2][0] += 1
        else:  # if k2 hasn't been seen before, count and add to mutuals
            user_dict[k1][k2] = [1, False]

    if connection == 'friend':  # if they are flagged as 'friends'
        user_dict[k1][k2][0] -= 1  # lower counter by one because they've been counted once before above
        user_dict[k1][k2][1] = True  # set friend flag to true


user_dict = {}

for line in sys.stdin:
    line = line.strip("""\n""")
    line = line.split('\t')
    key, friend, connection = line
    # since mutuals are bidirectional, we need to do it both ways, once with one user as key and once as the other
    # user as key
    add_friends(user_dict, key, friend, connection)
    add_friends(user_dict, friend, key, connection)

for person in user_dict.keys():
    user_dict[person] = sorted(user_dict[person].items(), key=lambda x: x[1], reverse=True)
    user_dict[person] = [x for x in user_dict[person] if not x[1][1]]

