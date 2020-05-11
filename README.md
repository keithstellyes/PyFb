# About

This "PyFb" repo is the home of many so-called "Facebook bots", this also includes
a shared library with Facebook bots specifically in mind, this is a simple layer on the official
Facebook Python Graph library, given its hyper-focus on bots, there is no desire for any added APIs that
do not service this end.

# On Practices

I generally have tried to maintain best coding practices, such as separation of FB and bot core logic. However
a decent amount of this code is very fire-and-forget, some lines of code were written incredibly hastily. For example,
a decent amount of Tetris code was written when I was out having dinner with friends, phone blown up by "hey bot's ignoring
votes!! Botmin please don't do this", and getting back late, doing just enough code so it's working again, then going to sleep.

In addition, comments and documentation is sparse, you'll probably have to read the code and logic itself. Thankfully,
as far as software goes, this is on the simpler side :). Always feel free to reach out or comment for any questions. In addition,
there's some temporary, sandbox-y files that still need cleaning up, too.

# Usage

For the most part these bots are generally coded in such a way that it's easy to run "off-line", in a "dry-run" way,
in other words, run through their code and logic (mainly for debugging purposes). However this is not an absolute truth
for all cases (For example, `wheres-angus` doesn't have an offline way of checking `doanswer` logic)

These bots are designed to be ran from a so-called `cron job` (Or your platform's equivalent), that means to get them
running regularly, you will have to set up a `cron job` to actually call the program. For configuring `cron`, I
highly recommend https://crontab.guru/ , this is what I use.

Bot logic assumes it can read from a `tokens.json`, `add-token.py` is a command-line utility that holds your hand
in adding new tokens. For what the key is, you'll have to dig in

You are free to stand up an instance of these bots if you so desire; however I ask 3 things:

* Reference Keith Stellyes as original author in bot's description
* Link to this repo in bot's description
* If you're going to stand-up an instance, please have one of the following be true:
-- Have it be _derivitative_
-- Have the original bot be inactive for at least 1 week
-- Not be on Facebook (e.g. Instagram or Reddit are OK)

The original bots are as follows (please link to original if standing up an instance):

* `jeopardy`: [Jeopardybot Jeff69](https://www.facebook.com/jeopardybot69/)
* `tetris`: [Tetris Bot 1984](https://www.facebook.com/tetrisbot1984)
* `wheres-angus`: [Where's Angus Bot 1215](https://www.facebook.com/wheresangus1215)

# TODOs

* Clean-up of lazy coding (isn't this a TODO for every project? :-)
* Ensure Python requirements.txt is correct
* More documentation is always a good thing (Right now much documentation requires actual reading of source code)