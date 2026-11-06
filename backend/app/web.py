from pathlib import Path
from starlette.exceptions import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or path.startswith('api/') or '.' in Path(path).name:
                raise
            return FileResponse(Path(self.directory) / 'index.html')
