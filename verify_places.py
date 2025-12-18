
from places.places_engine import places_search

print("Running Google Places verification...")

results = places_search("pizza near New York", limit=3)

print("RESULTS:")
for r in results:
    print(r)
