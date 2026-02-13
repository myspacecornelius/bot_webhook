"""
Profile service — CRUD operations for checkout profiles.
"""

import csv
import io
import json
from typing import Any, Dict

import structlog

from ..core.engine import engine
from ..core.profile import Address, PaymentCard, Profile
from ..domain.errors import NotFoundError, ValidationError
from ..domain.models import ProfileCreate

logger = structlog.get_logger()


class ProfileService:
    """Profile CRUD and batch import."""

    def list_profiles(self) -> Dict[str, Any]:
        return {
            "profiles": [p.to_dict() for p in engine.profile_manager.profiles.values()],
            "groups": [
                {"id": g.id, "name": g.name, "color": g.color}
                for g in engine.profile_manager.groups.values()
            ],
        }

    def get_profile(self, profile_id: str) -> Dict[str, Any]:
        profile = engine.profile_manager.get_profile(profile_id)
        if not profile:
            raise NotFoundError("Profile", profile_id)
        return profile.to_dict()

    def create_profile(self, data: ProfileCreate) -> Dict[str, str]:
        profile = Profile(
            name=data.name,
            email=data.email,
            phone=data.phone,
            billing_same_as_shipping=data.billing_same_as_shipping,
            shipping=Address(
                first_name=data.shipping_first_name,
                last_name=data.shipping_last_name,
                address1=data.shipping_address1,
                address2=data.shipping_address2,
                city=data.shipping_city,
                state=data.shipping_state,
                zip_code=data.shipping_zip,
                country=data.shipping_country,
            ),
            card=PaymentCard(holder=data.card_holder, expiry=data.card_expiry),
        )
        profile.card.number = data.card_number
        profile.card.cvv = data.card_cvv
        engine.profile_manager.add_profile(profile)
        return {"id": profile.id, "message": "Profile created"}

    def delete_profile(self, profile_id: str) -> Dict[str, str]:
        if engine.profile_manager.delete_profile(profile_id):
            return {"message": "Profile deleted"}
        raise NotFoundError("Profile", profile_id)

    def import_profiles(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Import profiles from JSON or CSV file content."""
        profiles_created = 0

        if filename.endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            profiles_list = data if isinstance(data, list) else data.get("profiles", [])

            for p in profiles_list:
                profile = Profile(
                    name=p.get("name", "Imported"),
                    email=p.get("email", ""),
                    phone=p.get("phone", ""),
                    shipping=Address(
                        first_name=p.get("shipping_first_name", ""),
                        last_name=p.get("shipping_last_name", ""),
                        address1=p.get("shipping_address1", ""),
                        address2=p.get("shipping_address2", ""),
                        city=p.get("shipping_city", ""),
                        state=p.get("shipping_state", ""),
                        zip_code=p.get("shipping_zip", ""),
                        country=p.get("shipping_country", "United States"),
                    ),
                    payment=PaymentCard(
                        holder_name=p.get("card_holder", ""),
                        number=p.get("card_number", ""),
                        expiry=p.get("card_expiry", ""),
                        cvv=p.get("card_cvv", ""),
                    ),
                )
                engine.profile_manager.add_profile(profile)
                profiles_created += 1

        elif filename.endswith(".csv"):
            reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
            for row in reader:
                profile = Profile(
                    name=row.get("name", "Imported"),
                    email=row.get("email", ""),
                    phone=row.get("phone", ""),
                    shipping=Address(
                        first_name=row.get("shipping_first_name", ""),
                        last_name=row.get("shipping_last_name", ""),
                        address1=row.get("shipping_address1", ""),
                        address2=row.get("shipping_address2", ""),
                        city=row.get("shipping_city", ""),
                        state=row.get("shipping_state", ""),
                        zip_code=row.get("shipping_zip", ""),
                        country=row.get("shipping_country", "United States"),
                    ),
                    payment=PaymentCard(
                        holder_name=row.get("card_holder", ""),
                        number=row.get("card_number", ""),
                        expiry=row.get("card_expiry", ""),
                        cvv=row.get("card_cvv", ""),
                    ),
                )
                engine.profile_manager.add_profile(profile)
                profiles_created += 1
        else:
            raise ValidationError("File must be .json or .csv", field="filename")

        return {
            "message": f"Imported {profiles_created} profiles",
            "count": profiles_created,
        }


profile_service = ProfileService()
