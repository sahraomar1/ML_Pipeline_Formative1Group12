# Task 2: MongoDB queries (run after load_mongo.py)
# run from the repo root:  python database/queries_mongo.py
from datetime import datetime
from pprint import pprint
from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB, MONGO_COLLECTION

col = MongoClient(MONGO_URI)[MONGO_DB][MONGO_COLLECTION]

print("Q1: latest record")
pprint(col.find_one({}, {"_id": 0}, sort=[("timestamp", -1)]))

print("\nQ2: records on 2017-06-01 (first 5 of the day)")
start = datetime(2017, 6, 1)
end = datetime(2017, 6, 2)
day = list(col.find({"timestamp": {"$gte": start, "$lt": end}}, {"_id": 0}).sort("timestamp", 1))
print("total records that day:", len(day))
for d in day[:5]:
    pprint(d)

print("\nQ3: average traffic for each hour of the day")
for row in col.aggregate([
    {"$group": {"_id": {"$hour": "$timestamp"}, "avg_traffic": {"$avg": "$traffic_volume"}}},
    {"$sort": {"_id": 1}},
]):
    print(row["_id"], round(row["avg_traffic"]))

print("\nQ4: average traffic for each weather type")
for row in col.aggregate([
    {"$group": {"_id": "$weather.main", "num_hours": {"$sum": 1},
                "avg_traffic": {"$avg": "$traffic_volume"}}},
    {"$sort": {"avg_traffic": -1}},
]):
    print(row["_id"], row["num_hours"], round(row["avg_traffic"]))

print("\nQ5: holidays (midnight rows only, they are the only ones flagged)")
for row in col.aggregate([
    {"$match": {"holiday": {"$ne": None}}},
    {"$group": {"_id": "$holiday", "num_hours": {"$sum": 1},
                "avg_traffic": {"$avg": "$traffic_volume"}}},
    {"$sort": {"avg_traffic": 1}},
]):
    print(row["_id"], row["num_hours"], round(row["avg_traffic"]))

print("\nQ6: hours recorded and average traffic per year")
for row in col.aggregate([
    {"$group": {"_id": {"$year": "$timestamp"}, "hours_recorded": {"$sum": 1},
                "avg_traffic": {"$avg": "$traffic_volume"}}},
    {"$sort": {"_id": 1}},
]):
    print(row["_id"], row["hours_recorded"], round(row["avg_traffic"]))