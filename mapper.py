import sys

# source = open('soc-LiveJournal1Adj.txt', 'r')

for line in sys.stdin:  # for each line
    line = line.strip()  # get rid of spaces before and after the line
    line = line.split('\t')  # we're working with <tab> to separate keys and users.
    key = int(line[0])  # the first user is key

    if len(line) > 1:  # check to see if the user has any friends
        friends = line[1].split(',')  # make a list out of friends
        friends = sorted(map(int, friends))  # sort the friend list. This is important since we're considering each
        # line[0] as key. So we want all the information about a user go to the same reducer. in order to make sure
        # this happens without duplicates, we need to sort the list by order.

        for friend in friends:  # iterate over friends in the friend list
            place_holder1, place_holder2 = sorted([key, friend])  # since the key has been determined and we need the
            # information about each user go to the same reducer, we do a sort here as well
            pair = tuple((place_holder1, tuple((place_holder2, 'friend'))))
            print(f"""{place_holder1}\t{place_holder2}\tfriend""" + '\n')
            # file.write(f"""{place_holder1}\t{place_holder2}\tfriend""" + '\n')

        # now we need to iterate over friend combinations. since we're going to recommend people who are not friends,
        # we need to specify that these people exist in someone else's network so we flag them as not friends.
        for friend_index, friend in enumerate(friends):
            for other_friend in friends[friend_index:]:  # since we've ordered the list above and in order to prevent
                # generating duplicates,
                if friend != other_friend:
                    place_holder4, place_holder5 = friend, other_friend
                    print(f"""{place_holder4}\t{place_holder5}\tnot_friend""" + '\n')
                    # file.write(f"""{place_holder4}\t{place_holder5}\tnot_friend""" + '\n')
