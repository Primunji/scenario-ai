import os, time, json
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from pydantic import BaseModel

load_dotenv()

app = FastAPI()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

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
        assistant_id="asst_pIL17UqXqng311CNA0Rep7s9",
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

@app.get('/thread')
async def create_thread():
    return await get_thread()


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    assistant_id: str

@app.get('/chat')
async def get_chat(request: ChatRequest):
    return await get_response(request.message, request.thread_id, request.assistant_id)

if (__name__ == "__main__"):
    uvicorn.run(app, host='0.0.0.0', port=8080)