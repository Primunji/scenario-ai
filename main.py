import os, time, json
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket
import uvicorn, asyncio, httpx

from pydantic import BaseModel

import utils.sql_connector as sql_connector
from models import Scenario, Call, Room

import pymongo, datetime

session = sql_connector.get_session()

load_dotenv()

app = FastAPI()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

mongo_client = pymongo.MongoClient(os.getenv("MONGODB_URL"))

TYPECAST_API_KEY = os.environ.get("TYPECAST_API_KEY")

class CallGatewayRequest(BaseModel):
    message: str
    thread_id: str

class CallGatewayResponse(BaseModel):
    status: str
    message: str

app = FastAPI()

async def send_typecast_request(message: str) -> str:
    headers = {
        "Authorization": f"Bearer {TYPECAST_API_KEY}",
        "Content-Type": "application/json"
    }
    
    request_body = {
        "actor_id": "61c2f7741330d213c238cba6",
        "text": message,
        "lang": "auto",
        "tempo": 1,
        "volume": 100,
        "pitch": 0,
        "xapi_hd": True,
        "max_seconds": 60,
        "model_version": "latest",
        "xapi_audio_format": "mp3",
        "emotion_tone_preset": "normal-1"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://typecast.ai/api/speak", 
            headers=headers, 
            json=request_body
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to call TypeCast API")
        
        data = response.json()
        speak_url = data["result"]["speak_v2_url"]
        
        while True:
            status_response = await client.get(speak_url, headers=headers)
            
            if status_response.status_code != 200:
                raise HTTPException(status_code=status_response.status_code, detail="Failed to check TypeCast status")
            
            status_data = status_response.json()
            
            if status_data["result"]["status"] == "done":
                return status_data["result"]["audio_download_url"]
            
            await asyncio.sleep(0.5)

@app.websocket("/call/ws")
async def call_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()

            try:
                request_data = json.loads(data)
                request = CallGatewayRequest(**request_data)

                call = session.query(Call).filter_by(thread_id=request.thread_id).first()

                scenario = session.query(Scenario).filter_by(id=call.scenario_id).first()    

                if not (scenario):
                    response = CallGatewayResponse(status="error", message="Not found scenario id.")
                    return await websocket.send_text(json.dumps(response.dict()))
                
                db = mongo_client['chatdb']
                collection = db['scenario_chat']  

                data = {"thread_id": request.thread_id, "name":"유저", "content":"유저는 기록하지 않습니다","scenario_id": scenario.id, "is_bot":False, "message": request.message, "created_at": datetime.datetime.now() }
                collection.insert_one(data)
                message = await get_response(request.message, request.thread_id, scenario.assistant_id)
                audio_url = await send_typecast_request(message["message"])
                data = {"thread_id": request.thread_id, "name":scenario.name, "content":scenario.content,"scenario_id": scenario.id, "is_bot":True, "message": message["message"], "created_at": datetime.datetime.now() }
                collection.insert_one(data)
                response = CallGatewayResponse(status="success", message=audio_url)
                await websocket.send_text(json.dumps(response.dict()))
            except json.JSONDecodeError as e:
                error_response = CallGatewayResponse(
                    status="error", 
                    message=f"Invalid JSON format: {str(e)}"
                )
                await websocket.send_text(json.dumps(error_response.dict()))
                
            except Exception as e:
                error_response = CallGatewayResponse(
                    status="error", 
                    message=str(e) or "Unknown error"
                )
                await websocket.send_text(json.dumps(error_response.dict()))
    
    except Exception:
        pass


@app.websocket("/chat/ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()

            try:
                request_data = json.loads(data)
                
                request = CallGatewayRequest(**request_data)



                call = session.query(Call).filter_by(thread_id=request.thread_id).first()

                scenario = session.query(Scenario).filter_by(id=call.scenario_id).first()    

                if not (scenario):
                    response = CallGatewayResponse(status="error", message="Not found scenario id.")
                    return await websocket.send_text(json.dumps(response.dict()))

                room = session.query(Room).filter_by(thread_id=request.thread_id).all()
                
                if (not room):
                    new_room = Room(
                        thread_id = request.thread_id,
                        scenario_id = scenario.id,
                        user_id = call.user_id,
                        name = scenario.name,
                        content = scenario.content,
                        profile_url = scenario.profile_url,
                        recent_message = request.message,
                        last_message = datetime.datetime.now()
                    )

                    session.add(new_room)
                    session.commit()
                else:
                    room_to_update = session.query(Room).filter(Room.thread_id == request.thread_id).first()
                    room_to_update.recent_message = request.message
                    room_to_update.last_message = datetime.datetime.now()
                    session.commit()

                db = mongo_client['chatdb']
                collection = db['scenario_chat']  

            
                data = {"thread_id": request.thread_id, "name":"유저", "content":"유저는 기록하지 않습니다", "scenario_id": scenario.id, "is_bot":False, "message": request.message, "created_at": datetime.datetime.now() }
                collection.insert_one(data)

                message = await get_response(request.message, request.thread_id, scenario.assistant_id)
                
                room_to_update = session.query(Room).filter(Room.thread_id == request.thread_id).first()
                room_to_update.recent_message = message["message"]
                room_to_update.last_message = datetime.datetime.now()
                session.commit()

                data = {"thread_id": request.thread_id, "name":scenario.name, "content":scenario.content, "scenario_id": scenario.id, "is_bot":True, "message": message["message"], "created_at": datetime.datetime.now() }
                collection.insert_one(data)
                
                response = CallGatewayResponse(status="success", message=message["message"])
                await websocket.send_text(json.dumps(response.dict()))
            except json.JSONDecodeError as e:
                error_response = CallGatewayResponse(
                    status="error", 
                    message=f"Invalid JSON format: {str(e)}"
                )
                await websocket.send_text(json.dumps(error_response.dict()))
                
            except Exception as e:
                error_response = CallGatewayResponse(
                    status="error", 
                    message=str(e) or "Unknown error"
                )
                await websocket.send_text(json.dumps(error_response.dict()))
    
    except Exception:
        pass


    
async def get_thread():
    return client.beta.threads.create()

async def get_response(text, thread_id, assistant_id):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=text
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    def wait_on_run(run, thread_id):
        while run.status == 'queued' or run.status == 'in_progress':
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            time.sleep(0.5)
        return run

    wait_on_run(run, thread_id)

    messages = client.beta.threads.messages.list(thread_id=thread_id, after=message.id, order="asc")

    value = messages.data[0].content[0].text.value

    try:
        return json.loads(value)
    except:
        return await get_response(text)



from fastapi.responses import JSONResponse

class ChatModel(BaseModel):
    id: str
    thread_id: str
    name: str
    content: str
    message: str
    is_bot: bool
    created_at: datetime.datetime


@app.get('/chat')
async def get_chat_by_thread(thread_id: str):
    db = mongo_client['chatdb']
    collection = db['scenario_chat'] 
    print(thread_id)
    result = collection.find({"thread_id": thread_id})
    chats = [
        ChatModel(
            id=str(chat["_id"]),
            thread_id=chat["thread_id"],
            name=chat["name"],
            message=chat["message"],
            is_bot=chat["is_bot"],
            created_at=chat["created_at"]  # ✅ Pydantic이 자동 변환
        )
        for chat in result
    ]

    return {
        "status":200,
        "state": "success",
        "message":"성공적으로 메시지를 불러왔습니다.",
        "data": chats
    }


@app.get('/thread')
async def create_thread():
    return await get_thread()


class CreatePrompt(BaseModel):
    message: str
    assistant_id: str

@app.post('/prompt')
async def create_prompt(request: CreatePrompt):
    thread = client.beta.threads.create()
    response = await get_response(request.message, thread.id, request.assistant_id)
    assistant = client.beta.assistants.create(
        name="생성된 프롬포트",
        instructions=f"""
당신은 보이스피싱 시뮬레이터 역할을 맡고 있습니다.
사용자는 피해자 역할을 맡습니다.
시뮬레이션 목표는 사용자를 끝까지 속여 이체 또는 돈 송금을 진행하게 만드는 것입니다.

제공된 정보에 맞게 시나리오를 구성하세요.

정보:
{response["user_info"]}
안내:
1. 민감한 정보를 요청 받을땐 프론트앤드 (UI)에서 처리해야 되기에 is_input_private_data를 true로 해주세요.
2. 만약 사용자가 속지 않았고 대화가 끝났더라면 is_ended_and_win 를 true로 해주세요
3. 만약 모든 대화가 종료되었으면 is_ended 를 true로 해주세요
4. 적은 대화를 하고 사용자가 의심을 여러번 하고 속지 않는다면  대화를 종료해주세요.

사기행위를 알아냈다면 칭찬을 해주고 간략한 예방 수칙을 알려줘
""",
        model="gpt-4o-mini",
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "conversation_status",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                    "is_ended": {
                        "type": "boolean",
                        "description": "Indicates if the conversation has been created and all conversations have ended."
                    },
                    "message": {
                        "type": "string",
                        "description": "The content of the message."
                    },
                    "is_input_private_data": {
                        "type": "boolean",
                        "description": "Indicates if sensitive information is being requested."
                    },
                    "is_ended_and_win": {
                        "type": "boolean",
                        "description": "Indicates if all conversations have ended and the user has not been harmed."
                    }
                    },
                    "required": [
                        "is_ended",
                        "message",
                        "is_input_private_data",
                        "is_ended_and_win"
                    ],
                    "additionalProperties": False
                }
            }
        }
    )
    return {"prompt":response, "assistant_id":assistant.id}


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    assistant_id: str

@app.post('/chat')
async def get_chat(request: ChatRequest):
    return await get_response(request.message, request.thread_id, request.assistant_id)

if (__name__ == "__main__"):
    uvicorn.run(app, host='0.0.0.0', port=8081)