/**
 * Upload an image file to the server.
 * Returns the public URL path of the uploaded image.
 */
export async function uploadImage(file: File): Promise<string> {
  const formData = new FormData();
  formData.set("file", file);

  const res = await fetch("/api/upload/image", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Upload failed (${res.status})`);
  }

  const data = await res.json();
  return data.src as string;
}
