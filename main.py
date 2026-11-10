from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ ఇక్కడ మీ MongoDB లింక్ పెట్టండి
MONGO_URL = "mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"

client = AsyncIOMotorClient(MONGO_URL)
db = client.fitness_app # డేటాబేస్ పేరు
users_collection = db.users # యూజర్స్ కలెక్షన్

# యూజర్ రిజిస్ట్రేషన్ కోసం ఫార్మాట్
class UserSignup(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/signup")
async def signup(user: UserSignup):
    # ఈమెయిల్ ఆల్రెడీ ఉందో లేదో చెక్ చేయడం
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="ఈ ఈమెయిల్ తో ఆల్రెడీ అకౌంట్ ఉంది")
    
    # డేటాబేస్ లో సేవ్ చేయడం
    await users_collection.insert_one(user.dict())
    return {"message": "అకౌంట్ సక్సెస్ ఫుల్ గా క్రియేట్ అయింది!", "name": user.name}

@app.post("/login")
async def login(user: LoginRequest):
    # డేటాబేస్ లో యూజర్ ని వెతకడం
    db_user = await users_collection.find_one({"email": user.email})
    
    if db_user and db_user["password"] == user.password:
        return {"message": "లాగిన్ సక్సెస్!", "user": db_user["name"]}
    else:
        raise HTTPException(status_code=401, detail="ఈమెయిల్ లేదా పాస్‌వర్డ్ తప్పు")
    # వర్కౌట్ డేటా రిసీవ్ చేసుకోవడానికి ఫార్మాట్
class WorkoutEntry(BaseModel):
    email: str
    workout_details: str

@app.post("/add-workout")
async def add_workout(workout: WorkoutEntry):
    # యూజర్ మెయిల్ ఆధారంగా వర్కౌట్ ని డేటాబేస్ లో సేవ్ చేయడం
    await users_collection.update_one(
        {"email": workout.email},
        {"$push": {"workouts": workout.workout_details}}
    )
    return {"message": "మీ వర్కౌట్ సక్సెస్ ఫుల్ గా సేవ్ అయింది! 💪"}
@app.get("/get-workouts/{email}")
async def get_workouts(email: str):
    # డేటాబేస్ లో యూజర్ కోసం వెతకడం
    user = await users_collection.find_one({"email": email})
    if user and "workouts" in user:
        # పాత వర్కౌట్స్ ఉంటే వాటిని పంపడం (రివర్స్ ఆర్డర్ లో, అంటే లేటెస్ట్ వి పైన వచ్చేలా)
        return {"workouts": user["workouts"][::-1]}
    return {"workouts": []}