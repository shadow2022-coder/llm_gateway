from pydantic import BaseModel


class ChatCompletionRequest(BaseModel):
    prompt: str
    model: str


class CreateAPIKeyRequest(BaseModel):
    owner: str


class CreateAPIKeyResponse(BaseModel):
    id: int
    owner: str
    raw_key: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    model: str
    choices: list[ChatChoice]
    usage: Usage
