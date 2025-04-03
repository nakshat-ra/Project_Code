import os
from livekit import api
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
from livekit.api import LiveKitAPI, ListRoomsRequest
import uuid
import redis
from livekit.api import DeleteRoomRequest

load_dotenv(dotenv_path=".env.local")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

async def generate_room_name():
    name = "room-" + str(uuid.uuid4())[:8]
    rooms = await get_rooms()
    while name in rooms:
        name = "room-" + str(uuid.uuid4())[:8]
    return name

async def get_rooms():
    api = LiveKitAPI()
    rooms = await api.room.list_rooms(ListRoomsRequest())
    await api.aclose()
    
    return [room.name for room in rooms.rooms]



redis_client = redis.StrictRedis(
    # host='your-redis-name.redis.cache.windows.net',
    host='RedisLivekit.redis.cache.windows.net',
    port=6380,
    password='zpir55fUl0BFP6cBXykbyWqfHN1ZBj22AAzCaF6YHSQ=',
    ssl=True,
    decode_responses=True,
    db=0
)

print(redis_client.ping())
print("Redis Connection Successful!")


@app.route('/sendData', methods=['POST'])
def receive_data():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data received"}), 400  # Ensure a valid response
    
    text = data.get("text", "")
    selected_llm = data.get("selectedLLM", "")
    selected_lang = data.get("selectedLang", "")
    selected_tts_provider = data.get("selectedProvider", "")
    selected_voice = data.get("selectedVoice", "")

    # Store in Redis (modify keys as needed)
    redis_client.set("context", text)
    redis_client.set("selected_llm", selected_llm)
    redis_client.set("selected_lang", selected_lang)
    redis_client.set("selected_tts_provider", selected_tts_provider)
    redis_client.set("selected_voice", selected_voice)
    print(selected_lang, selected_llm, selected_tts_provider, selected_voice)
    # redis_client.publish("context", value)    
    # Process data (Make sure this function doesn't exit without a return    statement)  
    # Debugging line
    return jsonify({"message": "Data received successfully"}), 200 
 

@app.route("/getToken")
async def get_token():
    
    # name = request.args.get("name", "my name")
    # room = request.args.get("room", None)
    name = "chirag"
    # room = None
    # if not room:
    
    room = await generate_room_name()
    
    token = api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET")) \
        .with_identity(name)\
        .with_name(name)\
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room
        ))
    print("token Generated Successfully")
    return {"room_name": room, "token": token.to_jwt()}

@app.route("/deleteRoom", methods=["POST"])
async def delete_room():
    try:
        print("delete Method Called")
        # Retrieve API key and secret from environment variables
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")

        # Get room name from the request body
        data = request.get_json()
        # room_name = data.get("room_name")
        roomName= redis_client.get("room_name")
        print(roomName)
        async with api.LiveKitAPI() as lkapi:
            await lkapi.room.delete_room(DeleteRoomRequest( room=roomName))
            print('Room Deleted {0}'.format(roomName))
      

        
        return jsonify({"message": f"Room '{roomName}' deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return "Server is running - 2", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)