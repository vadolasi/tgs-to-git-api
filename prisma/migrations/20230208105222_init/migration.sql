-- CreateTable
CREATE TABLE "Sticker" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "hash" TEXT NOT NULL,
    "file" BLOB NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "Sticker_hash_key" ON "Sticker"("hash");
