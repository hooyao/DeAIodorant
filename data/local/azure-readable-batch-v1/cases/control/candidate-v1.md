# Nuxt Test Utils v4：集成 Vitest v4，重构 Mock 机制与环境初始化

Nuxt Test Utils 4.0.0 版本已于 2026 年 2 月 7 日发布，这是 Nuxt 官方测试库合并包生命周期中的首个主版本。该版本以 Vitest v4 为唯一依赖，取代了此前的 Vitest v3，带来了多项重要更新，包括测试环境初始化方式的调整、mock 机制的重构，以及依赖项的版本要求提升。

## 主要更新内容

### 测试环境初始化迁移至 beforeAll

4.0.0 版本最显著的变化，是将 Nuxt 测试环境的初始化逻辑从 `setupFiles` 迁移到了 `beforeAll` 钩子。旧版本中，`vi.mock` 和 `mockNuxtImport` 往往无法及时拦截中间件或插件内的组合式函数，因为这些函数可能在 mock 生效前就已被执行，导致模块级 mock 失效。此次调整后，初始化逻辑会在所有 mock 注册完成后才启动 Nuxt，确保 mock 行为在整个测试套件中一致且可预测，修复了长期存在的模块级 mock 被静默忽略的问题。

需要注意的是，这一变更带来了迁移成本。如果在 `describe` 代码块的顶层直接调用 Nuxt 组合式函数（如 `useRouter()`、`useNuxtApp()`），会因测试环境尚未初始化而抛出 `[nuxt] instance unavailable` 错误。推荐的做法是将相关调用移入 `beforeAll`：

```text
describe('router test', () => {
  let router: ReturnType<typeof useRouter>
  beforeAll(() => {
    router = useRouter()
  })
})
```

### mockNuxtImport 优化

`mockNuxtImport` 现已支持将原始实现传入工厂函数。这样，测试时无需从零构建完整 mock 对象，可以直接包装或扩展真实实现，仅针对需要的部分进行定制，简化了部分 mock 的编写。

### registerEndpoint 状态管理修复

`registerEndpoint` 工具也进行了两项修复：  
- 解决了测试间模块重置时，配置文件中注册的端点丢失的问题。  
- 支持 URL 模式包含查询参数的端点正常匹配，修复了参数化 API 路径测试中的一类故障。

### Mock 导出规则更严格

随着 Vitest v4 的升级，mock 导出的规则变得更为严格。以往访问 mock 模块中工厂函数未显式返回的导出项时，会静默返回 `undefined`，而在 Vitest v4 下会直接抛出错误。推荐的修复方式是在工厂返回值中展开 `importOriginal`，默认保留所有原始导出，仅覆盖测试需要的部分。

### 依赖项版本要求提升

对等依赖的版本要求也有所提高：
- `happy-dom` 需为 20.0.11 及以上版本
- `jsdom` 需为 27.4.0 及以上版本
- `@jest/globals` 停止支持 30.0.0 以下版本
- `@cucumber/cucumber` 需为 11 及以上版本

团队如有锁定旧版本依赖，需在升级 Vitest v4 的同时同步更新这些依赖。

## Nuxt Test Utils 的定位

Nuxt Test Utils 在 Vue 测试生态中具有独特作用。  
- `@vue/test-utils` 主要用于独立组件的单元测试  
- Playwright、Cypress 等工具覆盖浏览器端到端场景  
- Nuxt Test Utils 则衔接二者，能够在测试环境中启动完整的 Nuxt 应用，支持服务端渲染校验，并在完整的 Nuxt 插件与组合式函数上下文中挂载组件

## 迁移与文档

从 v3 迁移的团队可参考 Nuxt 官方测试文档及 4.0.0 版本说明。此前使用已废弃的 `nuxt-vitest` 包的用户，可在 GitHub 迁移问题中查阅具体迁移步骤。

## 维护与社区

Nuxt Test Utils 由 Nuxt 核心团队维护，Daniel Roe 主导开发，基于 MIT 协议开源。该库每周在 npm 上的下载量超过 47 万次，广泛应用于 Nuxt 模块生态，为应用代码和模块开发者提供标准化的测试支持。

---

如需了解英文原文，可参见：Nuxt Test Utils v4: Vitest v4 Requirement, Mocking Overhaul and Stricter Environment Setup