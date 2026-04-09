import time
from starlette.responses import Response


class SessionCookies:
    """Gerencia os cookies da sessão"""
    
    MAX_AGE: int = 3600 * 12 # 12 horas
    PATH: str = "/"

    _SHARED_ATRRS: dict = dict(
        path=PATH,
        httponly=True,
        samesite='lax',
        max_age=MAX_AGE
    )

    @classmethod
    def set_user_id(cls, response: Response, user_id: int | str) -> None:
        response.set_cookie(
            key="user_id",
            value=str(user_id),
            **cls._SHARED_ATRRS
        )

    @classmethod
    def set_session_id(cls, response: Response, session_id: str) -> None:
        response.set_cookie(
            key="session_id",
            value=session_id,
            **cls._SHARED_ATRRS
        )

    @classmethod
    def set_last_activity(cls, response: Response) -> None:
        response.set_cookie(
            key="last_activity",
            value=str(int(time.time())),
            **cls._SHARED_ATRRS
        )

    @classmethod
    def set_session(cls, response: Response, user_id: int | str, session_id: str) -> None:
        cls.set_user_id(response, user_id)
        cls.set_session_id(response, session_id)
        cls.set_last_activity(response)

    @classmethod
    def clear_session(cls, response: Response) -> None:
        for key in ["user_id", "session_id", "last_activity"]:
            response.delete_cookie(
                key=key,
                path=cls.PATH,
                httponly=True,
            )
        