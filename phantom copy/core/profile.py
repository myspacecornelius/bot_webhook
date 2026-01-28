"""
Profile Management for Phantom Bot
Handles checkout profiles with encrypted payment data
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import structlog

from ..utils.crypto import crypto
from ..utils.config import get_config

logger = structlog.get_logger()


class CardType(Enum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    UNKNOWN = "unknown"


@dataclass
class Address:
    """Shipping/Billing address"""
    first_name: str = ""
    last_name: str = ""
    address1: str = ""
    address2: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "United States"
    country_code: str = "US"
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def full_address(self) -> str:
        parts = [self.address1]
        if self.address2:
            parts.append(self.address2)
        parts.append(f"{self.city}, {self.state} {self.zip_code}")
        return ", ".join(parts)
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "address1": self.address1,
            "address2": self.address2,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "country_code": self.country_code,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Address':
        return cls(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            address1=data.get("address1", ""),
            address2=data.get("address2", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            zip_code=data.get("zip_code", ""),
            country=data.get("country", "United States"),
            country_code=data.get("country_code", "US"),
        )


@dataclass
class PaymentCard:
    """Payment card with encryption"""
    holder: str = ""
    _number: str = ""  # Encrypted
    expiry: str = ""  # MM/YY
    _cvv: str = ""  # Encrypted
    card_type: CardType = CardType.UNKNOWN
    
    def __post_init__(self):
        # Detect card type from number if not set
        if self.card_type == CardType.UNKNOWN and self._number:
            self.card_type = self._detect_card_type()
    
    def _detect_card_type(self) -> CardType:
        """Detect card type from number"""
        try:
            number = self.number.replace(" ", "").replace("-", "")
            if number.startswith("4"):
                return CardType.VISA
            elif number.startswith(("51", "52", "53", "54", "55")):
                return CardType.MASTERCARD
            elif number.startswith(("34", "37")):
                return CardType.AMEX
            elif number.startswith("6011"):
                return CardType.DISCOVER
        except:
            pass
        return CardType.UNKNOWN
    
    @property
    def number(self) -> str:
        """Get decrypted card number"""
        if self._number.startswith("gAAAAA"):  # Fernet encrypted
            return crypto.decrypt(self._number)
        return self._number
    
    @number.setter
    def number(self, value: str):
        """Set and encrypt card number"""
        clean = value.replace(" ", "").replace("-", "")
        self._number = crypto.encrypt(clean)
        self.card_type = self._detect_card_type()
    
    @property
    def cvv(self) -> str:
        """Get decrypted CVV"""
        if self._cvv.startswith("gAAAAA"):
            return crypto.decrypt(self._cvv)
        return self._cvv
    
    @cvv.setter
    def cvv(self, value: str):
        """Set and encrypt CVV"""
        self._cvv = crypto.encrypt(value)
    
    @property
    def number_masked(self) -> str:
        """Get masked card number for display"""
        return crypto.mask_card(self.number)
    
    @property
    def expiry_month(self) -> str:
        """Get expiry month"""
        if "/" in self.expiry:
            return self.expiry.split("/")[0]
        return self.expiry[:2] if len(self.expiry) >= 2 else ""
    
    @property
    def expiry_year(self) -> str:
        """Get expiry year (2-digit)"""
        if "/" in self.expiry:
            return self.expiry.split("/")[1]
        return self.expiry[2:] if len(self.expiry) >= 4 else ""
    
    @property
    def expiry_year_full(self) -> str:
        """Get expiry year (4-digit)"""
        year = self.expiry_year
        if len(year) == 2:
            return f"20{year}"
        return year
    
    def to_dict(self, decrypt: bool = False) -> Dict[str, str]:
        """Convert to dictionary"""
        return {
            "holder": self.holder,
            "number": self.number if decrypt else self._number,
            "expiry": self.expiry,
            "cvv": self.cvv if decrypt else self._cvv,
            "type": self.card_type.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'PaymentCard':
        card = cls(
            holder=data.get("holder", ""),
            expiry=data.get("expiry", ""),
        )
        # Set encrypted values directly if already encrypted
        number = data.get("number", "")
        cvv = data.get("cvv", "")
        
        if number.startswith("gAAAAA"):
            card._number = number
        else:
            card.number = number
            
        if cvv.startswith("gAAAAA"):
            card._cvv = cvv
        else:
            card.cvv = cvv
        
        if "type" in data:
            card.card_type = CardType(data["type"])
        
        return card


@dataclass
class Profile:
    """Complete checkout profile"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    group_id: Optional[str] = None
    
    # Contact
    email: str = ""
    phone: str = ""
    
    # Addresses
    shipping: Address = field(default_factory=Address)
    billing: Address = field(default_factory=Address)
    billing_same_as_shipping: bool = True
    
    # Payment
    card: PaymentCard = field(default_factory=PaymentCard)
    
    # Stats
    total_checkouts: int = 0
    total_spent: float = 0.0
    
    @property
    def billing_address(self) -> Address:
        """Get billing address (uses shipping if same)"""
        if self.billing_same_as_shipping:
            return self.shipping
        return self.billing
    
    @property
    def display_name(self) -> str:
        """Display name for UI"""
        if self.name:
            return self.name
        return self.shipping.full_name or self.email or self.id[:8]
    
    def to_dict(self, decrypt_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "group_id": self.group_id,
            "email": self.email,
            "phone": self.phone,
            "shipping": self.shipping.to_dict(),
            "billing": self.billing.to_dict(),
            "billing_same_as_shipping": self.billing_same_as_shipping,
            "card": self.card.to_dict(decrypt=decrypt_sensitive),
            "total_checkouts": self.total_checkouts,
            "total_spent": self.total_spent,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            group_id=data.get("group_id"),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            shipping=Address.from_dict(data.get("shipping", {})),
            billing=Address.from_dict(data.get("billing", {})),
            billing_same_as_shipping=data.get("billing_same_as_shipping", True),
            card=PaymentCard.from_dict(data.get("card", {})),
            total_checkouts=data.get("total_checkouts", 0),
            total_spent=data.get("total_spent", 0.0),
        )
    
    @classmethod
    def from_valor_format(cls, data: Dict[str, Any], profile_id: str = None) -> 'Profile':
        """Create from Valor bot format for import compatibility"""
        profile = cls(
            id=profile_id or str(uuid.uuid4()),
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phoneNumber", ""),
            billing_same_as_shipping=data.get("billingSameAsShipping", True),
        )
        
        # Shipping
        shipping_data = data.get("shipping", {})
        profile.shipping = Address(
            first_name=shipping_data.get("firstName", ""),
            last_name=shipping_data.get("lastName", ""),
            address1=shipping_data.get("addressLine1", ""),
            address2=shipping_data.get("addressLine2", ""),
            city=shipping_data.get("city", ""),
            state=shipping_data.get("state", ""),
            zip_code=shipping_data.get("zipCode", ""),
            country=shipping_data.get("countryName", "United States"),
            country_code=shipping_data.get("countryCode", "US"),
        )
        
        # Billing
        billing_data = data.get("billing", {})
        profile.billing = Address(
            first_name=billing_data.get("firstName", ""),
            last_name=billing_data.get("lastName", ""),
            address1=billing_data.get("addressLine1", ""),
            address2=billing_data.get("addressLine2", ""),
            city=billing_data.get("city", ""),
            state=billing_data.get("state", ""),
            zip_code=billing_data.get("zipCode", ""),
            country=billing_data.get("countryName", "United States"),
            country_code=billing_data.get("countryCode", "US"),
        )
        
        # Card
        card_data = data.get("card", {})
        profile.card = PaymentCard(
            holder=card_data.get("holder", ""),
            expiry=card_data.get("expiration", ""),
        )
        profile.card.number = card_data.get("number", "").replace(" ", "")
        profile.card.cvv = card_data.get("cvv", "")
        
        if "type" in card_data:
            try:
                profile.card.card_type = CardType(card_data["type"])
            except ValueError:
                pass
        
        return profile


@dataclass
class ProfileGroup:
    """Group of profiles"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    color: str = "#7289DA"
    profile_ids: List[str] = field(default_factory=list)


class ProfileManager:
    """
    Manages checkout profiles with encryption and grouping
    """
    
    def __init__(self):
        self.profiles: Dict[str, Profile] = {}
        self.groups: Dict[str, ProfileGroup] = {}
        self._profile_to_group: Dict[str, str] = {}
        
        logger.info("ProfileManager initialized")
    
    def add_profile(self, profile: Profile) -> str:
        """Add a profile"""
        self.profiles[profile.id] = profile
        
        if profile.group_id:
            self._profile_to_group[profile.id] = profile.group_id
            if profile.group_id in self.groups:
                self.groups[profile.group_id].profile_ids.append(profile.id)
        
        logger.debug("Profile added", profile=profile.display_name, id=profile.id)
        return profile.id
    
    def get_profile(self, profile_id: str) -> Optional[Profile]:
        """Get a profile by ID"""
        return self.profiles.get(profile_id)
    
    def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> Optional[Profile]:
        """Update a profile"""
        profile = self.profiles.get(profile_id)
        if not profile:
            return None
        
        for key, value in updates.items():
            if hasattr(profile, key):
                if key == "shipping" and isinstance(value, dict):
                    profile.shipping = Address.from_dict(value)
                elif key == "billing" and isinstance(value, dict):
                    profile.billing = Address.from_dict(value)
                elif key == "card" and isinstance(value, dict):
                    profile.card = PaymentCard.from_dict(value)
                else:
                    setattr(profile, key, value)
        
        logger.debug("Profile updated", profile=profile.display_name)
        return profile
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile"""
        if profile_id not in self.profiles:
            return False
        
        profile = self.profiles[profile_id]
        
        # Remove from group
        if profile.group_id and profile.group_id in self.groups:
            group = self.groups[profile.group_id]
            if profile_id in group.profile_ids:
                group.profile_ids.remove(profile_id)
        
        del self.profiles[profile_id]
        self._profile_to_group.pop(profile_id, None)
        
        logger.debug("Profile deleted", id=profile_id)
        return True
    
    def create_group(self, name: str, color: str = "#7289DA") -> ProfileGroup:
        """Create a profile group"""
        group = ProfileGroup(name=name, color=color)
        self.groups[group.id] = group
        logger.debug("Profile group created", name=name, id=group.id)
        return group
    
    def get_profiles_in_group(self, group_id: str) -> List[Profile]:
        """Get all profiles in a group"""
        if group_id not in self.groups:
            return []
        
        group = self.groups[group_id]
        return [self.profiles[pid] for pid in group.profile_ids if pid in self.profiles]
    
    def move_to_group(self, profile_id: str, group_id: str) -> bool:
        """Move a profile to a different group"""
        if profile_id not in self.profiles:
            return False
        
        profile = self.profiles[profile_id]
        
        # Remove from old group
        if profile.group_id and profile.group_id in self.groups:
            old_group = self.groups[profile.group_id]
            if profile_id in old_group.profile_ids:
                old_group.profile_ids.remove(profile_id)
        
        # Add to new group
        profile.group_id = group_id
        self._profile_to_group[profile_id] = group_id
        
        if group_id in self.groups:
            self.groups[group_id].profile_ids.append(profile_id)
        
        return True
    
    def duplicate_profile(self, profile_id: str, new_name: Optional[str] = None) -> Optional[Profile]:
        """Duplicate a profile"""
        original = self.profiles.get(profile_id)
        if not original:
            return None
        
        # Create copy with new ID
        data = original.to_dict(decrypt_sensitive=True)
        data["id"] = str(uuid.uuid4())
        data["name"] = new_name or f"{original.name} (Copy)"
        
        new_profile = Profile.from_dict(data)
        self.add_profile(new_profile)
        
        return new_profile
    
    def import_from_valor(self, valor_data: Dict[str, Any]) -> int:
        """Import profiles from Valor bot format"""
        count = 0
        
        profiles_data = valor_data.get("profiles", {})
        group_lists = profiles_data.get("groupLists", {})
        groups = profiles_data.get("groups", {})
        
        # Create groups
        for group_id, group_data in groups.items():
            group = ProfileGroup(
                id=group_id,
                name=group_data.get("name", "Imported"),
                color=group_data.get("stats", {}).get("activeColor", "#7289DA"),
            )
            self.groups[group_id] = group
        
        # Import profiles
        for group_id, profiles in group_lists.items():
            for profile_id, profile_data in profiles.items():
                try:
                    profile = Profile.from_valor_format(profile_data, profile_id)
                    profile.group_id = group_id
                    self.add_profile(profile)
                    count += 1
                except Exception as e:
                    logger.warning("Failed to import profile", error=str(e))
        
        logger.info("Profiles imported from Valor format", count=count)
        return count
    
    def export_to_dict(self, decrypt: bool = False) -> Dict[str, Any]:
        """Export all profiles and groups"""
        return {
            "profiles": {pid: p.to_dict(decrypt_sensitive=decrypt) for pid, p in self.profiles.items()},
            "groups": {gid: {"id": g.id, "name": g.name, "color": g.color, "profile_ids": g.profile_ids} 
                      for gid, g in self.groups.items()},
        }
    
    def get_random_profile(self, group_id: Optional[str] = None) -> Optional[Profile]:
        """Get a random profile, optionally from a specific group"""
        import random
        
        if group_id:
            profiles = self.get_profiles_in_group(group_id)
        else:
            profiles = list(self.profiles.values())
        
        if not profiles:
            return None
        
        return random.choice(profiles)
    
    def record_checkout(self, profile_id: str, amount: float):
        """Record a successful checkout for a profile"""
        profile = self.profiles.get(profile_id)
        if profile:
            profile.total_checkouts += 1
            profile.total_spent += amount
            logger.debug("Checkout recorded", profile=profile.display_name, amount=amount)
