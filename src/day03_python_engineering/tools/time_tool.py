from datetime import datetime
from pydantic import BaseModel

class CurrentTimeInput(BaseModel):
    pass

def get_current_time() -> str:

   
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")