from pydantic import BaseModel
from typing import Any, Optional, Union

'''
전체 API Response 구조
'''
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[Union[str, Any]] = None