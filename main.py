import hashlib
import pathlib
import tempfile

import docker
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

client = docker.from_env()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

pathlib.Path("./stickers").mkdir(parents=True, exist_ok=True)


@app.post("/")
async def convert(file: UploadFile):
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    if pathlib.Path(f"./stickers/{file_hash}.gif").exists():
        if pathlib.Path(f"./stickers/{file_hash}.gif").exists():
            return FileResponse(f"./stickers/{file_hash}.gif", headers={"X-File-Hash": file_hash})

        raise HTTPException(status_code=404, detail="Item not found")

    with tempfile.TemporaryDirectory() as file_dir:
        file_name = f"{file_dir}/sticker.tgs"

        with open(file_name, "wb") as buffer:
            buffer.write(content)

            client.containers.run(
                "edasriyan/tgs-to-gif",
                volumes={file_dir: {"bind": "/source", "mode": "rw"}}
            )

        with open(f"{file_dir}/sticker.tgs.gif", "rb") as buffer:
            with open(f"./stickers/{file_hash}.gif", "wb") as output:
                output.write(buffer.read())

            if pathlib.Path(f"./stickers/{file_hash}.gif").exists():
                return FileResponse(f"./stickers/{file_hash}.gif", headers={"X-File-Hash": file_hash})

        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/{file_hash}")
async def get_sticker(file_hash: str):
    return FileResponse(f"./stickers/{file_hash}.gif")
