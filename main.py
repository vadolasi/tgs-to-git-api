import hashlib
import pathlib
import tempfile

import docker
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prisma import Prisma, Base64

client = docker.from_env()

db = Prisma()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

pathlib.Path("./stickers").mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


@app.post("/")
async def convert(file: UploadFile, sticker_id: str = Form(), compress: bool = Form(False)):
    sticker = await db.sticker.find_unique(
        where={
            "id": sticker_id
        }
    )

    if sticker:
        return Response(Base64.decode(sticker.file), headers={"X-File-Hash": sticker.hash}, media_type="image/gif")

    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    with tempfile.TemporaryDirectory() as file_dir:
        file_name = f"{file_dir}/sticker.tgs"

        with open(file_name, "wb") as buffer:
            buffer.write(content)

            client.containers.run(
                "edasriyan/tgs-to-gif",
                volumes={file_dir: {"bind": "/source", "mode": "rw"}},
                environment={
                    "WIDTH": "256" if compress else "512",
                    "HEIGHT": "256" if compress else "512",
                    "FPS": "25" if compress else "50",
                    "QUALITY": "45" if compress else "90"
                }
            )

        with open(f"{file_dir}/sticker.tgs.gif", "rb") as buffer:
            gif = buffer.read()
            await db.sticker.create(
                data={
                    "id": sticker_id,
                    "file": Base64.encode(gif),
                    "hash": file_hash
                }
            )

            return Response(gif, headers={"X-File-Hash": file_hash}, media_type="image/gif")


@app.get("/{sticker_id}")
async def get_sticker(sticker_id: str):
    sticker = await db.sticker.find_unique(
        where={
            "id": sticker_id
        }
    )

    if sticker:
        return Response(Base64.decode(sticker.file), headers={"X-File-Hash": sticker.hash}, media_type="image/gif")

    raise HTTPException(status_code=404, detail="Item not found")
