from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["legacy-redirects"])

_redirects = {
    "/inbound": "/page/inbound",
    "/outbound": "/page/outbound",
    "/move": "/page/move",
    "/inventory": "/page/inventory",
    "/history": "/page/history",
    "/excel": "/page/excel",
    "/labels": "/page/labels",
    "/calendar": "/page/calendar",
    "/admin": "/login",
}

for src, dst in _redirects.items():
    @router.get(src, include_in_schema=False)
    def _r(dst=dst):
        return RedirectResponse(url=dst)
