#!/usr/bin/env python3
"""
Billing Test Setup Helper
--------------------------
Creates test data for billing smoke tests:
- Free user (no subscription)
- Pro user (active subscription)
- Team on paid plan
- Expired subscription
- Grace period (PAST_DUE)
- Feature denial scenarios
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

# Add parent directory to path to import swx_core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Get user emails from environment variables (set by bash script)
FREE_EMAIL = os.getenv("FREE_EMAIL", "free_user_billing@example.com")
PRO_EMAIL = os.getenv("PRO_EMAIL", "pro_user_billing@example.com")
EXPIRED_EMAIL = os.getenv("EXPIRED_EMAIL", "expired_user_billing@example.com")
GRACE_EMAIL = os.getenv("GRACE_EMAIL", "grace_user_billing@example.com")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from swx_core.models.billing import (
    BillingAccount, BillingAccountType, Subscription, SubscriptionStatus,
    Plan, PlanEntitlement, Feature, FeatureType
)
from swx_core.models.user import User
from swx_core.models.team import Team
from swx_core.services.billing.subscription_service import SubscriptionService
from swx_core.database.db import AsyncSessionLocal

async def setup_billing_tests():
    """Set up all billing test scenarios."""
    async with AsyncSessionLocal() as session:
        print("Setting up billing test scenarios...")
        
        # 1. Ensure Free plan exists
        free_plan_stmt = select(Plan).where(Plan.key == "free")
        result = await session.execute(free_plan_stmt)
        free_plan = result.scalar_one_or_none()
        if not free_plan:
            free_plan = Plan(
                key="free",
                name="Free Plan",
                description="Free tier with basic features",
                is_active=True,
                is_public=True
            )
            session.add(free_plan)
            await session.commit()
            await session.refresh(free_plan)
            print(f"Created Free plan: {free_plan.id}")
        
        # 2. Ensure Pro plan exists
        pro_plan_stmt = select(Plan).where(Plan.key == "pro")
        result = await session.execute(pro_plan_stmt)
        pro_plan = result.scalar_one_or_none()
        if not pro_plan:
            pro_plan = Plan(
                key="pro",
                name="Pro Plan",
                description="Pro tier with advanced features",
                is_active=True,
                is_public=True
            )
            session.add(pro_plan)
            await session.commit()
            await session.refresh(pro_plan)
            print(f"Created Pro plan: {pro_plan.id}")
        
        # 3. Ensure Team plan exists
        team_plan_stmt = select(Plan).where(Plan.key == "team")
        result = await session.execute(team_plan_stmt)
        team_plan = result.scalar_one_or_none()
        if not team_plan:
            team_plan = Plan(
                key="team",
                name="Team Plan",
                description="Team tier with collaboration features",
                is_active=True,
                is_public=True
            )
            session.add(team_plan)
            await session.commit()
            await session.refresh(team_plan)
            print(f"Created Team plan: {team_plan.id}")
        
        # 4. Ensure features exist
        features = {
            "api.calls": FeatureType.QUOTA,
            "llm.tokens": FeatureType.QUOTA,
            "advanced.analytics": FeatureType.BOOLEAN,
            "team.members": FeatureType.QUOTA,
        }
        
        feature_objs = {}
        for key, feature_type in features.items():
            feature_stmt = select(Feature).where(Feature.key == key)
            result = await session.execute(feature_stmt)
            feature = result.scalar_one_or_none()
            if not feature:
                feature = Feature(
                    key=key,
                    name=key.replace(".", " ").title(),
                    description=f"Feature: {key}",
                    feature_type=feature_type,
                    unit="requests" if "calls" in key else ("tokens" if "tokens" in key else ("members" if "members" in key else None))
                )
                session.add(feature)
                await session.commit()
                await session.refresh(feature)
                print(f"Created feature: {key}")
            feature_objs[key] = feature
        
        # 5. Set up plan entitlements
        # Free plan: 100 API calls, 1000 tokens, no advanced analytics
        free_entitlements = {
            "api.calls": "100",
            "llm.tokens": "1000",
            "advanced.analytics": "false",
        }
        
        for key, value in free_entitlements.items():
            feature = feature_objs[key]
            stmt = select(PlanEntitlement).where(
                PlanEntitlement.plan_id == free_plan.id,
                PlanEntitlement.feature_id == feature.id
            )
            result = await session.execute(stmt)
            entitlement = result.scalar_one_or_none()
            if not entitlement:
                entitlement = PlanEntitlement(
                    plan_id=free_plan.id,
                    feature_id=feature.id,
                    value=value
                )
                session.add(entitlement)
                await session.commit()
                print(f"Assigned {key}={value} to Free plan")
        
        # Pro plan: 10000 API calls, 100000 tokens, advanced analytics
        pro_entitlements = {
            "api.calls": "10000",
            "llm.tokens": "100000",
            "advanced.analytics": "true",
        }
        
        for key, value in pro_entitlements.items():
            feature = feature_objs[key]
            stmt = select(PlanEntitlement).where(
                PlanEntitlement.plan_id == pro_plan.id,
                PlanEntitlement.feature_id == feature.id
            )
            result = await session.execute(stmt)
            entitlement = result.scalar_one_or_none()
            if not entitlement:
                entitlement = PlanEntitlement(
                    plan_id=pro_plan.id,
                    feature_id=feature.id,
                    value=value
                )
                session.add(entitlement)
                await session.commit()
                print(f"Assigned {key}={value} to Pro plan")
        
        # Team plan: 50000 API calls, 500000 tokens, advanced analytics, 50 team members
        team_entitlements = {
            "api.calls": "50000",
            "llm.tokens": "500000",
            "advanced.analytics": "true",
            "team.members": "50",
        }
        
        for key, value in team_entitlements.items():
            feature = feature_objs[key]
            stmt = select(PlanEntitlement).where(
                PlanEntitlement.plan_id == team_plan.id,
                PlanEntitlement.feature_id == feature.id
            )
            result = await session.execute(stmt)
            entitlement = result.scalar_one_or_none()
            if not entitlement:
                entitlement = PlanEntitlement(
                    plan_id=team_plan.id,
                    feature_id=feature.id,
                    value=value
                )
                session.add(entitlement)
                await session.commit()
                print(f"Assigned {key}={value} to Team plan")
        
        # 6. Find or create test users
        subscription_service = SubscriptionService(session)
        
        # Free user (no subscription) - use email from environment
        free_user_stmt = select(User).where(User.email == FREE_EMAIL)
        result = await session.execute(free_user_stmt)
        free_user = result.scalar_one_or_none()
        result = await session.execute(free_user_stmt)
        free_user = result.scalar_one_or_none()
        if not free_user:
            print("WARNING: Free user not found. They should be created via API first.")
            print("  Email: free_user_billing@example.com")
            print("Continuing with setup for other users...")
            free_user = None
        else:
            print(f"Found Free user: {free_user.id} ({free_user.email})")
        
        # Pro user (active subscription)
        pro_user_stmt = select(User).where(User.email == PRO_EMAIL)
        result = await session.execute(pro_user_stmt)
        pro_user = result.scalar_one_or_none()
        if not pro_user:
            print("WARNING: Pro user not found. They should be created via API first.")
            print("Continuing with setup for other users...")
            pro_user = None
        else:
            print(f"Found Pro user: {pro_user.id}")
        
        # Expired user
        expired_user_stmt = select(User).where(User.email == EXPIRED_EMAIL)
        result = await session.execute(expired_user_stmt)
        expired_user = result.scalar_one_or_none()
        if not expired_user:
            print("WARNING: Expired user not found. They should be created via API first.")
            print("  Email: expired_user_billing@example.com")
            print("Continuing with setup for other users...")
            expired_user = None
        else:
            print(f"Found Expired user: {expired_user.id} ({expired_user.email})")
        
        # Grace period user (PAST_DUE)
        grace_user_stmt = select(User).where(User.email == GRACE_EMAIL)
        result = await session.execute(grace_user_stmt)
        grace_user = result.scalar_one_or_none()
        if not grace_user:
            print("WARNING: Grace user not found. They should be created via API first.")
            print("  Email: grace_user_billing@example.com")
            print("Continuing with setup for other users...")
            grace_user = None
        else:
            print(f"Found Grace user: {grace_user.id} ({grace_user.email})")
        
        # Team - get the first one if multiple exist
        team_stmt = select(Team).where(Team.name == "BillingTestTeam")
        result = await session.execute(team_stmt)
        teams = result.scalars().all()
        if not teams:
            print("WARNING: Team not found. They should be created via API first.")
            print("Continuing with setup for other users...")
            team = None
        else:
            team = teams[0]  # Use first team if multiple exist
            print(f"Found Team: {team.id} (using first of {len(teams)} teams with this name)")
        
        # 7. Create billing accounts and subscriptions
        
        # Free user: No subscription (just account)
        if free_user:
            free_account = await subscription_service.get_or_create_account(
                free_user.id, BillingAccountType.USER, free_user.email
            )
            print(f"Free user account: {free_account.id} (no subscription)")
        
        # Pro user: Active subscription
        if pro_user:
            pro_account = await subscription_service.get_or_create_account(
                pro_user.id, BillingAccountType.USER, pro_user.email
            )
            # Cancel any existing subscriptions
            existing_stmt = select(Subscription).where(
                Subscription.account_id == pro_account.id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
            result = await session.execute(existing_stmt)
            for sub in result.scalars().all():
                sub.status = SubscriptionStatus.CANCELED
                sub.ended_at = datetime.utcnow()
            await session.commit()
            
            # Create active Pro subscription
            pro_sub = Subscription(
                account_id=pro_account.id,
                plan_id=pro_plan.id,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30)
            )
            session.add(pro_sub)
            await session.commit()
            await session.refresh(pro_sub)
            print(f"Pro user subscription: {pro_sub.id} (ACTIVE)")
        
        # Expired user: Expired subscription
        if expired_user:
            expired_account = await subscription_service.get_or_create_account(
                expired_user.id, BillingAccountType.USER, expired_user.email
            )
            # Cancel any existing subscriptions
            existing_stmt = select(Subscription).where(
                Subscription.account_id == expired_account.id
            )
            result = await session.execute(existing_stmt)
            for sub in result.scalars().all():
                sub.status = SubscriptionStatus.CANCELED
                sub.ended_at = datetime.utcnow()
            await session.commit()
            
            # Create expired subscription
            expired_sub = Subscription(
                account_id=expired_account.id,
                plan_id=pro_plan.id,
                status=SubscriptionStatus.EXPIRED,
                current_period_start=datetime.utcnow() - timedelta(days=60),
                current_period_end=datetime.utcnow() - timedelta(days=30),
                ended_at=datetime.utcnow() - timedelta(days=30)
            )
            session.add(expired_sub)
            await session.commit()
            await session.refresh(expired_sub)
            print(f"Expired user subscription: {expired_sub.id} (EXPIRED)")
        
        # Grace period user: PAST_DUE subscription
        if grace_user:
            grace_account = await subscription_service.get_or_create_account(
                grace_user.id, BillingAccountType.USER, grace_user.email
            )
            # Cancel any existing subscriptions
            existing_stmt = select(Subscription).where(
                Subscription.account_id == grace_account.id
            )
            result = await session.execute(existing_stmt)
            for sub in result.scalars().all():
                sub.status = SubscriptionStatus.CANCELED
                sub.ended_at = datetime.utcnow()
            await session.commit()
            
            # Create PAST_DUE subscription (grace period)
            grace_sub = Subscription(
                account_id=grace_account.id,
                plan_id=pro_plan.id,
                status=SubscriptionStatus.PAST_DUE,
                current_period_start=datetime.utcnow() - timedelta(days=5),
                current_period_end=datetime.utcnow() + timedelta(days=25)
            )
            session.add(grace_sub)
            await session.commit()
            await session.refresh(grace_sub)
            print(f"Grace user subscription: {grace_sub.id} (PAST_DUE)")
        
        # Team: Active subscription
        if team:
            team_account = await subscription_service.get_or_create_account(
                team.id, BillingAccountType.TEAM, None
            )
            # Cancel any existing subscriptions
            existing_stmt = select(Subscription).where(
                Subscription.account_id == team_account.id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
            result = await session.execute(existing_stmt)
            for sub in result.scalars().all():
                sub.status = SubscriptionStatus.CANCELED
                sub.ended_at = datetime.utcnow()
            await session.commit()
            
            # Create active Team subscription
            team_sub = Subscription(
                account_id=team_account.id,
                plan_id=team_plan.id,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30)
            )
            session.add(team_sub)
            await session.commit()
            await session.refresh(team_sub)
            print(f"Team subscription: {team_sub.id} (ACTIVE)")
        
        print("\n✅ Billing test setup complete!")
        print("\nTest users (if created via API):")
        if free_user:
            print(f"  ✅ Free user: free_user_billing@example.com (no subscription)")
        if pro_user:
            print(f"  ✅ Pro user: pro_user_billing@example.com (ACTIVE Pro subscription)")
        if expired_user:
            print(f"  ✅ Expired user: expired_user_billing@example.com (EXPIRED subscription)")
        if grace_user:
            print(f"  ✅ Grace user: grace_user_billing@example.com (PAST_DUE subscription)")
        if team:
            print(f"  ✅ Team: BillingTestTeam (ACTIVE Team subscription)")
        
        if not (free_user and pro_user and expired_user and grace_user and team):
            print("\n⚠️  Some test users/teams were not found.")
            print("   Make sure to create them via API before running this script.")

if __name__ == "__main__":
    asyncio.run(setup_billing_tests())
