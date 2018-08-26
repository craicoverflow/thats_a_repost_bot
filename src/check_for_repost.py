#!/usr/bin/python
# -*- coding: utf-8 -*-
import praw
import os
import re
import pdb
import argparse
from configparser import ConfigParser
from collections import defaultdict
from io import StringIO

def load_config():
    default = defaultdict(str)
    default["subreddit"] = "louisebot"
    default["limit"] = "10"
    default["bot"] = "louisebot"

    config_path = os.path.expanduser("./config/check_for_repost.rc")
    section_name = "root"
    try:
        config = ConfigParser(default)
        with open(config_path, "r") as stream:
            stream = StringIO("[{section_name}]\n{stream_read}"
            .format(section_name=section_name, stream_read=stream.read()))

            if sys.version_info >= (3, 0):
                config.read_file(stream)
            else:
                config.readfp(stream)

            ret = {}

            def add_to_ret(fun, name):
                try:
                    ret[name] = fun(section_name, name)
                except ValueError as e:
                    err_string = "Error in config file. Variable '{}': {}. The default '{}' will be used."

                    # print sys.stderr >> err.str_format(name, str(e), default[name])
                    ret[name] = default[name]

            add_to_ret(config.get, "subreddit")
            add_to_ret(config.getint, "limit")
            add_to_ret(config.get, "bot")

            return ret
        
    except IOError as e:
        return default

config = load_config()

def parse_args():
    parser = argparse.ArgumentParser(description = "Your friendly neighbourhood Louisebot")
    parser.add_argument("-s", "--subreddit", type=str, default=config["subreddit"])
    parser.add_argument("-l", "--limit", type=int, default=config["limit"])
    parser.add_argument("-b", "--bot", type=str, default=config["bot"])

    args = parser.parse_args()
    return args

def filter_duplicates(duplicate_list, submission_created_utc, subreddit_name):
    for el in duplicate_list:
        if el.subreddit == subreddit_name and submission_created_utc > el.created_utc: yield el

def get_last_duplicate(submission, subreddit_name):
    duplicate_list = list(filter_duplicates(submission.duplicates(), submission.created_utc, subreddit_name))

    last_duplicate = None

    if len(duplicate_list):
        last_duplicate = duplicate_list[0]

    return last_duplicate

def get_posts_replied_to(f):
    posts_replied_to = f.read()
    posts_replied_to = posts_replied_to.split("\n")
    posts_replied_to = list(filter(None, posts_replied_to)) # filter the list of replied to posts so we don't go replying to the same ones again

    return posts_replied_to

if __name__ == '__main__':

    args = parse_args()

    subreddit_name = args.subreddit
    limit = args.limit
    bot_name = args.bot

    reddit = praw.Reddit(bot_name)
    subreddit = reddit.subreddit(subreddit_name) 
    
    if not os.path.isfile("posts_replied_to.txt"):
        posts_replied_to = [] # Create an empty list to store the IDs of posts that have been replied to
    else:
        with open("posts_replied_to.txt", "r") as f:

            posts_replied_to = get_posts_replied_to(f)

            for submission in subreddit.new(limit = limit):

                if submission.id not in posts_replied_to and submission.is_self is False:

                    latest_duplicate = get_last_duplicate(submission, subreddit_name)

                    if latest_duplicate:
                        print("I found a repost: {}".format(submission.permalink.encode('utf-8')))

                        # form the full URL of the duplicate so we can let the poster know
                        post_url = 'https://reddit.com' + latest_duplicate.permalink

                        # Reply to the current submission with a message showing them that this has already been posted.
                        submission.reply("This has been [submitted already](" + post_url + ") you lazy bastard.\n____________________________________________________________________________\n*This is an automated bot. Have feedback? Just send me a message or reply to this comment!*")
                                
                        # Add the submission ID to the list of IDs
                        posts_replied_to.append(submission.id)

# Update the text file with the new IDs of what has been replied to
with open("posts_replied_to.txt", "w") as f:
    for post_id in posts_replied_to:
        f.write(post_id + "\n")

