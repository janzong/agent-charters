# dev.to 个人资料待填（**只有你自己能改**，API 不支持）

**为什么必须手填**：dev.to 的 v1 API 只有 `GET /api/users/me`，**没有任何写资料的路由**
（2026-09-14 实测：文章可写、评论只读、用户资料只读）。

**页面**：<https://dev.to/settings/profile>

| 字段 | 填什么 |
|---|---|
| Name | 保持 `Janz`（或个人偏好） |
| Bio | 见下面代码块（140 字符，上限 200） |
| Website URL | `https://github.com/janzong/agent-charters` |
| GitHub | `janzong`（若没有这个字段，就只填 Website；两个等价） |
| Location / Twitter | 可不填 |

Bio（直接粘）：

```
Rule-based labeling for AGENTS.md files. 558 files labeled against a 9-category taxonomy; numbers reported honestly, including the bad ones.
```

**为什么值得填**：文章页不显示这些，但读者点进 `dev.to/janzong` 会看到仓库入口 ——
我们缺的正是"让外部读者变成外部使用者"这一步，这是最便宜的一个入口。

**已经做完的（2026-09-14，我做的）**：文章已挂进合集
`AGENTS.md in the wild` → <https://dev.to/janzong/series/44219>（`collection_id 44219`）。
之后每篇同主题文章在 front matter 里带 `series: AGENTS.md in the wild` 就会自动进同一合集。
