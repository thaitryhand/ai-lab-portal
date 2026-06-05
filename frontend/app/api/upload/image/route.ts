import { NextRequest, NextResponse } from "next/server";
import sharp from "sharp";
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { randomUUID } from "crypto";

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/avif"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_DIMENSION = 1920; // max width or height

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // Validate file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return NextResponse.json(
        { error: `Unsupported file type: ${file.type}. Allowed: ${ALLOWED_TYPES.join(", ")}` },
        { status: 400 },
      );
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: `File too large: ${(file.size / 1024 / 1024).toFixed(1)}MB. Max: ${MAX_FILE_SIZE / 1024 / 1024}MB` },
        { status: 400 },
      );
    }

    const buffer = Buffer.from(await file.arrayBuffer());

    // Process image: resize if needed, convert to WebP
    const metadata = await sharp(buffer).metadata();
    let processedBuffer: Buffer;
    let extension: string;

    // For GIFs, skip processing (keep original)
    if (file.type === "image/gif") {
      processedBuffer = buffer;
      extension = "gif";
    } else {
      // Resize if larger than max dimension
      const resizeOpts: sharp.ResizeOptions = {};
      if (metadata.width && metadata.width > MAX_DIMENSION) {
        resizeOpts.width = MAX_DIMENSION;
      }
      if (metadata.height && metadata.height > MAX_DIMENSION) {
        resizeOpts.height = MAX_DIMENSION;
      }
      resizeOpts.fit = "inside";
      resizeOpts.withoutEnlargement = true;

      processedBuffer = await sharp(buffer)
        .resize(resizeOpts)
        .webp({ quality: 82, effort: 4 })
        .toBuffer();
      extension = "webp";
    }

    // Ensure uploads directory exists
    const uploadsDir = join(process.cwd(), "public", "uploads");
    await mkdir(uploadsDir, { recursive: true });

    // Generate unique filename
    const filename = `${randomUUID()}.${extension}`;
    const filepath = join(uploadsDir, filename);
    await writeFile(filepath, processedBuffer);

    const url = `/uploads/${filename}`;

    return NextResponse.json({ src: url, filename });
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json({ error: "Upload failed" }, { status: 500 });
  }
}

/** Increase body size limit for image uploads */
export const config = {
  api: {
    bodyParser: false,
  },
};
