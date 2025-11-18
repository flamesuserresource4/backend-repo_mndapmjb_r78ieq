import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Ambulance, Ride, Location

app = FastAPI(title="Mella - Ambulance On-Demand API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreatedResponse(BaseModel):
    id: str


@app.get("/")
def read_root():
    return {"name": "Mella API", "status": "ok"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            response["collections"] = db.list_collection_names()
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Users (lightweight for now)
@app.post("/users", response_model=CreatedResponse)
def create_user(user: User):
    user_id = create_document("user", user)
    return {"id": user_id}


# Ambulances
@app.post("/ambulances", response_model=CreatedResponse)
def register_ambulance(ambulance: Ambulance):
    amb_id = create_document("ambulance", ambulance)
    return {"id": amb_id}


@app.get("/ambulances")
def list_ambulances(
    available: Optional[bool] = Query(None),
    type: Optional[str] = Query(None, description="basic|advanced|icu"),
):
    filter_q = {}
    if available is not None:
        filter_q["available"] = available
    if type:
        filter_q["type"] = type
    ambs = get_documents("ambulance", filter_q)
    # Convert ObjectId and nested datetimes
    for a in ambs:
        a["id"] = str(a.pop("_id"))
    return ambs


# Rides
@app.post("/rides", response_model=CreatedResponse)
def request_ride(ride: Ride):
    # If ambulance_id provided, ensure it's a valid ObjectId
    if ride.ambulance_id:
        try:
            ObjectId(ride.ambulance_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ambulance_id")
    ride_id = create_document("ride", ride)
    return {"id": ride_id}


@app.get("/rides")
def list_rides(status: Optional[str] = Query(None)):
    filter_q = {"status": status} if status else {}
    rides = get_documents("ride", filter_q)
    for r in rides:
        r["id"] = str(r.pop("_id"))
    return rides


# Simple nearby search (very naive filtering by bounding box around point)
class NearbyQuery(BaseModel):
    center: Location
    radius_km: float = 5.0


@app.post("/ambulances/nearby")
def nearby_ambulances(payload: NearbyQuery):
    # Because we don't have geo indexes here, approximate with 0.01 deg ~ 1.11 km lat
    dlat = payload.radius_km / 111.0
    dlng = payload.radius_km / 111.0
    lat = payload.center.lat
    lng = payload.center.lng
    filter_q = {
        "location.lat": {"$gte": lat - dlat, "$lte": lat + dlat},
        "location.lng": {"$gte": lng - dlng, "$lte": lng + dlng},
        "available": True,
    }
    ambs = get_documents("ambulance", filter_q)
    for a in ambs:
        a["id"] = str(a.pop("_id"))
    return ambs


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
