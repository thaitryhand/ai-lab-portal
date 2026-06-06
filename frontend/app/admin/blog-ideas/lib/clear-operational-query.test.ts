import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { urlWithoutOperationalQuery } from "./clear-operational-query";

describe("urlWithoutOperationalQuery", () => {
  it("strips polling params but keeps publish params", () => {
    const url = urlWithoutOperationalQuery(
      "/admin/blog-ideas/abc",
      "opStage=outline&opStatus=queued&taskId=celery_1&message=queued&blogSlug=my-post",
    );
    assert.equal(url, "/admin/blog-ideas/abc?blogSlug=my-post");
  });

  it("returns pathname when only operational params present", () => {
    const url = urlWithoutOperationalQuery(
      "/admin/blog-ideas/abc",
      "opStage=outline&opStatus=queued&taskId=celery_1",
    );
    assert.equal(url, "/admin/blog-ideas/abc");
  });
});
