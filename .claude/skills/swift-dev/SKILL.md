---
name: swift-dev
description: Swift language + SwiftUI/macOS specialization — Swift 5.9+, SwiftUI, SwiftPM, async/await, XCTest. Use for macOS app implementation. For API design patterns use /api-dev, for database work use /db-dev. Routed by PM or invoked directly for Swift tasks.
context: fork
agent: developer
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
---
# Swift/macOS Development Mode

You are now in **Swift specialization mode**. Before writing any code:

## 1. Load Project Conventions
```bash
Read /.claude/memory/standards/conventions.md
```

## 2. Query Context7 for Latest Docs
Based on the task, query relevant library documentation:
- **SwiftUI / AppKit interop**: `WindowGroup`, `NavigationSplitView`, menu bar, `NSWindow` bridging via `NSViewRepresentable`/`NSHostingView`
- **SwiftPM**: `Package.swift` manifest format, product/target/dependency config
- **swift-markdown** (Apple): Markdown AST parsing, formatting-preserving visitors
- **Yams**: YAML frontmatter parsing and round-trip serialization
- **GRDB / SQLite.swift**: if researcher selects SQLite FTS5 for search
- **swift-nio**: if MCP transport requires it
- **XCTest**: unit and UI test patterns, async test functions

## 3. Swift/SwiftUI Standards
- Swift 5.9+: use `@Observable`, typed throws, and macros; avoid legacy `ObservableObject` in new code
- SwiftUI-first; drop to AppKit only for capabilities SwiftUI lacks on macOS 14+ (document the specific gap inline)
- Concurrency: `async/await` + structured concurrency. `@MainActor` on view models. Actors for shared mutable state (e.g., `DataStore`). No `DispatchQueue.main.async` in new code
- Prefer value types (`struct`, `enum`); use `class` only when reference identity is required
- `Sendable` conformance on every type crossing actor boundaries
- Typed errors (`enum AppError: Error`); no silent `try?` in library code; no `fatalError` in `AppCore`
- Dependency injection via protocol + initializer (e.g., `FileSystem` protocol with in-memory test impl)
- Naming: PascalCase types, camelCase members, file name matches primary type
- Minimize `Foundation` in pure logic; isolate `AppKit`/`SwiftUI` to the UI layer
- DocC comments on all public API of `AppCore`

## 4. Security (Swift/macOS-Specific)
- No hardcoded secrets; persist identity under `~/Library/Application Support/YourApp/`
- Sanitize all path operations against traversal; reject paths not within the vault root
- MCP server binds `127.0.0.1` only in v1
- Use `FileManager` with explicit `URL` values, never string paths
- Prefer sandbox-compatible patterns; document required entitlements when used
- Never invoke `Process`/`NSTask` with user-controlled arguments
- Watch `Data`/`String` encoding boundaries on user-authored Markdown

## 5. Testing
- XCTest as default framework
- One test target per library module (`AppCoreTests`, etc.)
- Protocol-based DI enables tests against in-memory `FileSystem` impls
- Async paths: `func test_() async throws` or `XCTestExpectation`
- Golden-file tests where exact serialization matters (round-trip fidelity for file-format interop)
- Snapshot testing considered for SwiftUI views but not required for v1
- Coverage target: `AppCore` ≥80%, app target best-effort

## Task
$ARGUMENTS
