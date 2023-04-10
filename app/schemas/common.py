from pydantic import BaseModel
from typing import Any, Optional, Union

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Union[str, Any]] = None