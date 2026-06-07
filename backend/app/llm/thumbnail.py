"""AI thumbnail generation for blog posts using OpenAI DALL-E."""

from __future__ import annotations

from openai import OpenAI


def generate_thumbnail(
    title: str,
    excerpt: str,
    api_key: str,
    model: str = "dall-e-3",
    size: str = "1792x1024",
) -> str | None:
    """Generate a blog thumbnail image using DALL-E.

    Args:
        title: Blog post title.
        excerpt: Blog post excerpt/summary.
        api_key: OpenAI API key.
        model: DALL-E model version.
        size: Image size (1792x1024 for landscape blog hero).

    Returns:
        The URL of the generated image, or None if generation failed.
    """
    try:
        client = OpenAI(api_key=api_key)

        prompt = (
            f"Professional blog header image for article titled '{title}'. "
            f"Summary: {excerpt}. "
            "Clean, modern design suitable for a technology blog. "
            "No text overlay. No person faces. "
            "Abstract or illustrative style with gradient colors."
        )

        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )

        return response.data[0].url if response.data else None

    except Exception:
        return None
