import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  hasPendingBlogImages,
  isRenderableImageSrc,
  stripBrokenBlogImages,
} from "./sanitize-blog-markdown";

describe("sanitize-blog-markdown", () => {
  it("detects blob and empty image markdown", () => {
    assert.equal(
      hasPendingBlogImages("![](blob:http://localhost:3001/abc)"),
      true,
    );
    assert.equal(hasPendingBlogImages("![]()"), true);
    assert.equal(hasPendingBlogImages("![](/uploads/a.webp)"), false);
  });

  it("strips broken images", () => {
    const md = "Intro\n\n![](blob:x)\n\n![]()\n\n![](/uploads/ok.webp)\n\nOutro";
    const cleaned = stripBrokenBlogImages(md);
    assert.match(cleaned, /\/uploads\/ok\.webp/);
    assert.doesNotMatch(cleaned, /blob:/);
    assert.doesNotMatch(cleaned, /!\[\]\(\)/);
  });

  it("rejects empty and blob src for render", () => {
    assert.equal(isRenderableImageSrc(""), false);
    assert.equal(isRenderableImageSrc("   "), false);
    assert.equal(isRenderableImageSrc("blob:http://x"), false);
    assert.equal(isRenderableImageSrc("/uploads/a.webp"), true);
  });
});
