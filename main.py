import uuid
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from pydantic.v1 import Field

import datahandler

app = FastAPI()

class User(BaseModel):
    id: Optional[uuid.UUID] = uuid.uuid4()
    name: str = Field(..., example="John Doe")


@app.get("/user/{user_id}")
def getUser(user_id: uuid.UUID):
    user = datahandler.getUser(user_id)
    return user


@app.post("/user")
def createUser(user: User):
    userRes = datahandler.createUser(user)
    return userRes

