from typing import List, Optional

class UsageResponse:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    def __init__(self, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens

class MessageResponse:
    role: str
    content: str
    
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

class ChoiceResponse:
    index: int
    message: MessageResponse
    logprobs: Optional[str]
    finish_reason: str
    
    def __init__(self, index: int, message: MessageResponse, logprobs: Optional[str], finish_reason: str):
        self.index = index
        self.message = message
        self.logprobs = logprobs
        self.finish_reason = finish_reason

class ModelResponse:
    id: str
    object: str
    created: int
    model: str
    choices: List[ChoiceResponse]
    usage: UsageResponse
    system_fingerprint: str
    
    def __init__(self, id: str, object: str, created: int, model: str, choices: List[ChoiceResponse], usage: UsageResponse, system_fingerprint: str):
        self.id = id
        self.object = object
        self.created = created
        self.model = model
        self.choices = choices
        self.usage = usage
        self.system_fingerprint = system_fingerprint