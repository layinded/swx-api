# Agents Violations Analysis

This document analyzes the root causes of systemic violations found during the compliance audit.

## 1. Systemic Conflict: Dependency Management (UV vs. Poetry/Rye)

- **Nature**: Technical & Architectural
- **Root Cause**: The `.agents` rules were likely written at different times or copied from different templates (one favoring Poetry, another Rye). Meanwhile, the actual project implementation chose `uv`, which is a more modern and faster alternative but wasn't updated in the rules.
- **Analysis**: This is a maintenance failure. The rules have diverged from the project's actual toolchain. Keeping both Poetry and Rye requirements in the rules is confusing and unenforceable.

## 2. Architectural Divergence: Custom Auth vs. `fastapi-users`

- **Nature**: Architectural & Technical Debt
- **Root Cause**: The project required a highly customized RBAC system with multi-domain separation (Admin vs. User vs. System) and team-scoped permissions. `fastapi-users` is excellent for standard use cases but can be difficult to bend to such complex multi-tenant requirements without significant overrides.
- **Analysis**: The custom implementation provides better flexibility for the specific needs of SwX-API, but it violates the "standard library" rule. The rule itself might be too restrictive for enterprise-grade frameworks that require deep control over the auth lifecycle.

## 3. Structural Divergence: Directory Layout

- **Nature**: Cultural & Architectural
- **Root Cause**: The rules specify a standard `backend/src/` layout, likely based on a generic boilerplate. The actual project uses a "Core vs. App" separation (`swx_core` vs `swx_app`) which is a more advanced pattern for framework development.
- **Analysis**: The current structure is superior for a framework that is intended to be used as a base for other apps. The rules fail to recognize this "Framework vs. Application" distinction.

## 4. Coding Pattern Violation: `swx_app` Logic Leakage

- **Nature**: Technical Debt / Speed of Development
- **Root Cause**: High-risk violations in `swx_app/routes/qa_article_route.py` (direct SQL/LLM calls) are likely due to rapid prototyping or lack of strict enforcement during the creation of new features. 
- **Analysis**: While `swx_core` is very clean and follows the "Route -> Controller -> Service -> Repository" pattern, `swx_app` has started to accumulate debt by skipping these layers. This is a common pattern when "getting things to work" takes priority over "architectural purity."

## 5. Coding Style: Classes vs. Functions

- **Nature**: Cultural / Technical Debt
- **Root Cause**: The rule "avoid classes unless absolutely necessary" conflicts with common object-oriented patterns used in many Python boilerplates. Some developers find classes with static methods (like `QaArticleController`) a convenient way to group related logic, even if pure functions are cleaner.
- **Analysis**: This is a minor but systemic violation. It doesn't impact performance but does impact the "concise, functional" goal of the governance rules.
