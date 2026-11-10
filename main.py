from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from google import genai

app = FastAPI()

# MongoDB కనెక్షన్ (మీ డేటాబేస్ URL ఇక్కడ ఇవ్వండి)
MONGO_URL = "mongodb://localhost:27017" 
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client.fitness_db
users_collection = db.users
workouts_collection = db.workouts

# Google GenAI క్లైంట్ ఇనిషియలైజేషన్ (మీ జెమిని API కీ ఇక్కడ ఎంటర్ చేయండి)
ai_client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

class UserSignup(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class WorkoutCreate(BaseModel):
    email: str
    workout_details: str

class AIRequest(BaseModel):
    goal: str      # ఉదా: Muscle Gain / Weight Loss
    diet_type: str # ఉదా: Non-Veg with Roasted Flaxseed water

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI from Surya's Fitness Backend"}

@app.post("/signup")
async def signup(user: UserSignup):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="ఈ ఈమెయిల్ తో ఆల్రెడీ అకౌంట్ ఉంది!")
    await users_collection.insert_one(user.dict())
    return {"message": "అకౌంట్ సక్సెస్ ఫుల్ గా క్రియేట్ అయింది!"}

@app.post("/login")
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email, "password": user.password})
    if not db_user:
        raise HTTPException(status_code=400, detail="తప్పు ఈమెయిల్ లేదా పాస్‌వర్డ్!")
    return {"message": "లాగిన్ సక్సెస్!", "user": db_user["name"]}

@app.post("/add-workout")
async def add_workout(workout: WorkoutCreate):
    await workouts_collection.insert_one(workout.dict())
    return {"message": "వర్కౌట్ సేవ్ అయింది!"}

@app.get("/get-workouts/{email}")
async def get_workouts(email: str):
    cursor = workouts_collection.find({"email": email})
    workouts = []
    async for doc in cursor:
        workouts.append(doc["workout_details"])
    return {"workouts": workouts}

@app.post("/generate-ai-plan")
async def generate_ai_plan(data: AIRequest):
    try:
        prompt = f"Create a 1-day customized fitness workout and diet plan for a person whose goal is {data.goal} and diet preference is {data.diet_type}. Include roasted flaxseed water. Keep it structured, motivating, and professional."
        
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        return {"ai_plan": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
