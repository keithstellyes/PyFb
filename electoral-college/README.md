#Description

Election bot generates a map and result bassed on a votes.json input. Map creation relies on the
`basemap` library, with logic heavily lifted from example code there.

#Usage

1. Generate vote results (`votes.json`) via `gen.py`
2. Create map image based on vote results `electoralcollege.py votes.json`
3. Use `poster.py` to post results.