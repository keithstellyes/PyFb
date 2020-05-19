#Description

XKCD bot is pretty simple in coding all things considered. 
It'll try to load from its cache as much as possible, in an attempt to minimize strain
on the XKCD servers. It picks a comic by picking a number in the range `1 <= N <= LATEST_COMIC_IN_CACHE`.
It loads from cache because this bot is expected to be ran every hour, and it seems very unlikely XKCD
will ever be posting more than a few comics a day. (Generally, no more than once a day...)

#Usage

`poster.py` does all the magic of reading the token, picking a number, downloading chosen comic if not already
in cache, generating post, and uploading it. `xkcd.py` contains core logic of grabbing comics AND when ran by itself,
it will grab the latest comic, and put it into the cache if not already present. **NOTE:** `poster.py` will fail if
`xkcd.py` has never been ran yet.

I recommend setting up a cronjob of `cd ~/PyFb/xkcd && python3 poster.py` every hour, and every 12 hours,
running `xkcd.py`, cronjob being `0 */12 * * * cd ~/PyFb/xkcd && python3 xkcd.py`