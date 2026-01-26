# Billing Domain Design

## Overview
The SwX-API Billing System is an entitlement-driven platform designed to decouple monetization logic from business features. It supports multi-tenancy (Users and Teams), various plan tiers, and pluggable payment providers.

## Core Concepts

### 1. Plan
A container for a set of entitlements offered at a specific price point (e.g., Free, Pro, Enterprise).
- Plans are configurable and versioned.
- Plans define what a `BillingAccount` is entitled to.

### 2. Feature
A functional capability of the system that can be gated (e.g., `api.calls`, `llm.tokens`, `advanced.analytics`).
- Features are declared in a central `FeatureRegistry`.
- Feature Types:
    - **Boolean**: Yes/No access.
    - **Quota**: Fixed limit per period (e.g., 1000 calls/month).
    - **Metered**: Pay-as-you-go.

### 3. Entitlement
The bridge between a `Plan` and a `Feature`. It defines the specific access level or limit for a feature within a plan.
- Example: Plan "Pro" has Entitlement "api.calls" with a limit of 10,000.

### 4. BillingAccount
The entity that is billed and holds a subscription.
- Can be linked to a `User` (Individual billing).
- Can be linked to a `Team` (Shared billing).
- Can be linked to an `Organization` (Enterprise billing).

### 5. Subscription
The active link between a `BillingAccount` and a `Plan`.
- Time-bounded (start/end dates).
- States: `trialing`, `active`, `past_due`, `canceled`, `unpaid`, `expired`.
- Supports grace periods.

### 6. Usage Record
Tracks consumption of metered or quota-based features.
- Used by the `EntitlementResolver` to check limits.

## Entitlement Resolution Flow
1. Business code calls `entitlements.has(actor, feature, scope)`.
2. Resolver identifies the `BillingAccount` for the given scope (Team or User).
3. Resolver fetches the active `Subscription` for that account.
4. Resolver checks the `Plan` entitlements.
5. If the feature is quota-based, Resolver checks `UsageRecord`.
6. Resolver returns `True/False` or the remaining quota.

## Safety & Degradation
- If the billing system is unreachable, it should fail-closed for paid features but fail-open for core/free features (configurable).
- Subscriptions in `past_due` state may enter a grace period where features remain active but warnings are emitted.
