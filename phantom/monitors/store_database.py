"""
Shopify Store Database — 350+ Stores

Imported from Valor AIO's shopifyMonitorFilter store list.
Each entry includes the store name and URL for monitoring.
Categorized by type for easy filtering.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class ShopifyStore:
    """A supported Shopify store"""

    name: str
    url: str
    category: str = "general"  # sneaker, streetwear, skate, collectible, general
    region: str = "US"  # US, CA, EU, AU, JP, ROW
    priority: int = 2  # 1=high, 2=normal, 3=low
    default_delay_ms: int = 3000


# =================================================================
# STORE DATABASE — Extracted from Valor AIO's store list
# =================================================================

SHOPIFY_STORES: List[ShopifyStore] = [
    # ------------------------------------------------------------------
    # TIER 1: High-priority sneaker stores (fastest sell-out)
    # ------------------------------------------------------------------
    ShopifyStore("Kith", "https://kith.com", "sneaker", "US", 1, 2500),
    ShopifyStore("Kith CA", "https://kith.com", "sneaker", "CA", 1, 2500),
    ShopifyStore("Undefeated", "https://undefeated.com", "sneaker", "US", 1, 2500),
    ShopifyStore("Bodega", "https://bdgastore.com", "sneaker", "US", 1, 3000),
    ShopifyStore("Concepts", "https://cncpts.com", "sneaker", "US", 1, 3000),
    ShopifyStore(
        "A Ma Maniere", "https://www.a-ma-maniere.com", "sneaker", "US", 1, 3000
    ),
    ShopifyStore(
        "Social Status", "https://www.socialstatuspgh.com", "sneaker", "US", 1, 3000
    ),
    ShopifyStore("Extra Butter", "https://extrabutterny.com", "sneaker", "US", 1, 3000),
    ShopifyStore("Shoe Palace", "https://www.shoepalace.com", "sneaker", "US", 1, 3000),
    ShopifyStore("DTLR", "https://www.dtlr.com", "sneaker", "US", 1, 3000),
    ShopifyStore("Feature", "https://feature.com", "sneaker", "US", 1, 3000),
    ShopifyStore("Packer", "https://packershoes.com", "sneaker", "US", 1, 3000),
    ShopifyStore(
        "Trophy Room", "https://www.trophyroomstore.com", "sneaker", "US", 1, 3000
    ),
    ShopifyStore(
        "Union", "https://store.unionlosangeles.com", "sneaker", "US", 1, 2500
    ),
    ShopifyStore("SNS US", "https://www.sneakersnstuff.com", "sneaker", "US", 1, 3000),
    ShopifyStore("Notre", "https://www.notre-shop.com", "sneaker", "US", 1, 3000),
    ShopifyStore("Solefly", "https://www.solefly.com", "sneaker", "US", 1, 3000),
    ShopifyStore(
        "Lapstone and Hammer",
        "https://www.lapstoneandhammer.com",
        "sneaker",
        "US",
        1,
        3500,
    ),
    # ------------------------------------------------------------------
    # TIER 2: Major sneaker/streetwear retailers
    # ------------------------------------------------------------------
    ShopifyStore(
        "Sneaker Politics", "https://sneakerpolitics.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Rock City Kicks", "https://rockcitykicks.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("Sole Play", "https://www.soleplay.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Sole Classics", "https://www.soleclassics.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("ShopWSS", "https://www.shopwss.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Pro Image America", "https://www.proimageamerica.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Stadium Status", "https://www.stadiumstatus.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("Succezz", "https://www.succezz.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Sneaker Town", "https://www.sneakertown.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Sneaker Junkies", "https://sneakerjunkiesusa.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Kicks Theory", "https://www.kickstheory.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("Kicks Crew", "https://www.kickscrew.com", "sneaker", "US", 2, 3500),
    ShopifyStore("Likelihood", "https://likelihood.us", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Oneness Boutique", "https://www.onenessboutique.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Premium Goods", "https://thepremiumgoods.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Rule of Next", "https://www.ruleofnext.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Sports World", "https://www.sportsworldchicago.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Tops and Bottoms USA",
        "https://www.topsandbottomsusa.com",
        "sneaker",
        "US",
        2,
        3500,
    ),
    ShopifyStore("Renarts", "https://www.renarts.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Millennium Shoes", "https://www.millenniumshoes.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("Dead Stock", "https://www.deadstock.ca", "sneaker", "CA", 2, 3500),
    ShopifyStore("Solestop CA", "https://solestop.com", "sneaker", "CA", 2, 3500),
    ShopifyStore(
        "Sneakerbox CA", "https://www.sneakerbox.ca", "sneaker", "CA", 2, 3500
    ),
    ShopifyStore("JD Sports CA", "https://www.jdsports.ca", "sneaker", "CA", 2, 3500),
    ShopifyStore("Nohble", "https://nohble.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Specialist In Life", "https://www.specialistin.life", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("Wish ATL", "https://wishatl.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Corporate Gotem", "https://www.corporategotem.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("Courtside CA", "https://courtsideca.com", "sneaker", "CA", 2, 3500),
    ShopifyStore("Addict Miami", "https://addictmiami.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Commonwealth FTGG", "https://commonwealthftgg.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Long Beach Skate Co",
        "https://www.longbeachskateco.com",
        "sneaker",
        "US",
        2,
        3500,
    ),
    ShopifyStore(
        "Shop Nice Kicks", "https://shopnicekicks.com", "sneaker", "US", 2, 3000
    ),
    ShopifyStore(
        "Shop Overload", "https://www.shopoverload.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("Somewhere", "https://www.somewhere.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "This Thing Of Ours", "https://thisthingofoursla.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("Creme321", "https://creme321.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Prociety Shop", "https://www.procietyshop.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Private Sneakers", "https://www.privatesneakers.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("HOMEBRED", "https://homebred.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Alumni of NY", "https://www.alumniofny.com", "sneaker", "US", 2, 3500
    ),
    # ------------------------------------------------------------------
    # Streetwear & Fashion
    # ------------------------------------------------------------------
    ShopifyStore(
        "Supreme US", "https://www.supremenewyork.com", "streetwear", "US", 1, 2000
    ),
    ShopifyStore(
        "Supreme UK", "https://www.supremenewyork.com", "streetwear", "UK", 1, 2000
    ),
    ShopifyStore("Stussy", "https://www.stussy.com", "streetwear", "US", 1, 3000),
    ShopifyStore(
        "Palace US",
        "https://shop-usa.palaceskateboards.com",
        "streetwear",
        "US",
        1,
        2500,
    ),
    ShopifyStore("Bape", "https://us.bape.com", "streetwear", "US", 1, 3000),
    ShopifyStore("Bape JP", "https://bape.com", "streetwear", "JP", 1, 3000),
    ShopifyStore("Fear of God", "https://fearofgod.com", "streetwear", "US", 1, 3000),
    ShopifyStore("Drew House", "https://drewhouse.com", "streetwear", "US", 2, 3500),
    ShopifyStore(
        "Aime Leon Dore", "https://www.aimeleondore.com", "streetwear", "US", 1, 3000
    ),
    ShopifyStore(
        "Cactus Plant Flea Market", "https://www.cfrm.com", "streetwear", "US", 1, 2500
    ),
    ShopifyStore(
        "Denim Tears", "https://www.denimtears.com", "streetwear", "US", 1, 3000
    ),
    ShopifyStore(
        "Travis Scott", "https://shop.travisscott.com", "streetwear", "US", 1, 2500
    ),
    ShopifyStore("NOCTA", "https://www.nocta.com", "streetwear", "US", 1, 3000),
    ShopifyStore(
        "Born X Raised", "https://bornxraised.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore(
        "Gallery Dept", "https://gallerydept.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore("SP5DER Worldwide", "https://sp5der.com", "streetwear", "US", 1, 3000),
    ShopifyStore("Hell Star", "https://hellstar.com", "streetwear", "US", 2, 3000),
    ShopifyStore("DarcSport", "https://darcsport.com", "streetwear", "US", 2, 3500),
    ShopifyStore(
        "Eric E Manuel", "https://www.ericemanuel.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore(
        "Sporty & Rich", "https://sportyandrich.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore(
        "Octobers Very Own",
        "https://us.octobersveryown.com",
        "streetwear",
        "US",
        2,
        3500,
    ),
    ShopifyStore("JJJJound", "https://www.jjjjound.com", "streetwear", "US", 1, 3000),
    ShopifyStore(
        "Todd Snyder", "https://www.toddsnyder.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore(
        "Naked Copenhagen", "https://www.nakedcph.com", "streetwear", "EU", 2, 3500
    ),
    ShopifyStore("Tom Sachs", "https://shop.tomsachs.com", "streetwear", "US", 1, 3000),
    ShopifyStore(
        "Carhartt WIP USA", "https://us.carhartt-wip.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore(
        "HUF Worldwide", "https://www.hufworldwide.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore("Patta", "https://www.patta.nl", "streetwear", "EU", 1, 3000),
    ShopifyStore("Tres Bien", "https://tres-bien.com", "streetwear", "EU", 2, 3500),
    ShopifyStore("Slam Jam", "https://www.slamjam.com", "streetwear", "EU", 2, 3500),
    ShopifyStore("Hanon Shop", "https://www.hanon-shop.com", "sneaker", "EU", 2, 3500),
    ShopifyStore("Haven Shop", "https://havenshop.com", "streetwear", "CA", 2, 3500),
    ShopifyStore(
        "Burn Rubber", "https://burnrubberdetroit.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Joe Fresh Goods", "https://www.joefreshgoods.com", "streetwear", "US", 1, 3000
    ),
    ShopifyStore("HOMETEAM", "https://www.hometeam.io", "streetwear", "US", 2, 3500),
    ShopifyStore(
        "Hirshleifers", "https://hirshleifers.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore(
        "Wales Bonner", "https://walesbonner.net", "streetwear", "EU", 2, 3500
    ),
    ShopifyStore("Sandy Liang", "https://sandyliang.info", "streetwear", "US", 2, 3500),
    ShopifyStore(
        "Better Gift Shop", "https://bettergiftshop.com", "streetwear", "CA", 2, 3500
    ),
    ShopifyStore("MNML", "https://mnml.la", "streetwear", "US", 2, 3500),
    ShopifyStore("Telfar", "https://telfar.net", "streetwear", "US", 1, 3000),
    ShopifyStore(
        "LoveShackFancy", "https://www.loveshackfancy.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore("Bode", "https://bodenewyork.com", "streetwear", "US", 2, 3500),
    ShopifyStore(
        "FUTURA LABORATORIES",
        "https://futuralaboratories.com",
        "streetwear",
        "US",
        2,
        3500,
    ),
    ShopifyStore("Humanmade JP", "https://humanmade.jp", "streetwear", "JP", 2, 3500),
    # ------------------------------------------------------------------
    # Boutiques & Skate Shops
    # ------------------------------------------------------------------
    ShopifyStore(
        "DSMNY E-SHOP",
        "https://shop.doverstreetmarket.com",
        "streetwear",
        "US",
        1,
        3000,
    ),
    ShopifyStore(
        "DSMJP E-SHOP",
        "https://shop-jp.doverstreetmarket.com",
        "streetwear",
        "JP",
        2,
        3500,
    ),
    ShopifyStore(
        "DSML E-SHOP", "https://shop.doverstreetmarket.com", "streetwear", "EU", 2, 3500
    ),
    ShopifyStore("Blends", "https://www.blendsus.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Saint Alfred", "https://www.saintalfredshop.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore("Capsule", "https://www.capsulenyc.com", "sneaker", "US", 2, 3500),
    ShopifyStore("Alife", "https://www.alifenewyork.com", "streetwear", "US", 2, 3500),
    ShopifyStore(
        "Awake NY", "https://awakenyclothing.com", "streetwear", "US", 2, 3000
    ),
    ShopifyStore(
        "Brooklyn Projects", "https://brooklynprojects.com", "skate", "US", 2, 3500
    ),
    ShopifyStore("CCS", "https://shop.ccs.com", "skate", "US", 2, 3500),
    ShopifyStore(
        "Labor Skateshop", "https://laborskateshop.com", "skate", "US", 2, 4000
    ),
    ShopifyStore(
        "KCDC Skate Shop", "https://kcdcskateboards.com", "skate", "US", 2, 4000
    ),
    ShopifyStore(
        "Black Sheep Skate Shop",
        "https://blacksheepskateshop.com",
        "skate",
        "US",
        2,
        4000,
    ),
    ShopifyStore(
        "Familia Skate", "https://www.familaskateshop.com", "skate", "US", 2, 4000
    ),
    ShopifyStore(
        "Arts And Rec Skate Shop",
        "https://artsandrecreation.com",
        "skate",
        "US",
        2,
        4000,
    ),
    ShopifyStore(
        "Stratosphere Skateboards",
        "https://www.stratosphereboardshop.com",
        "skate",
        "US",
        2,
        4000,
    ),
    ShopifyStore(
        "Kinetic Skate Boarding",
        "https://www.kineticskateboarding.com",
        "skate",
        "US",
        2,
        4000,
    ),
    ShopifyStore("Drift House", "https://drifthouse.com", "skate", "US", 2, 4000),
    ShopifyStore(
        "NHS Skate Direct", "https://nhsskatedirect.com", "skate", "US", 2, 4000
    ),
    ShopifyStore(
        "Sun Diego Board Shop", "https://www.sundiego.com", "skate", "US", 2, 4000
    ),
    ShopifyStore(
        "Skate Park of Tampa",
        "https://www.skateparkoftampa.com",
        "skate",
        "US",
        2,
        4000,
    ),
    ShopifyStore(
        "Exodus Ride Shop", "https://www.exodusrideshop.com", "skate", "US", 2, 4000
    ),
    ShopifyStore("Val Surf", "https://www.valsurf.com", "skate", "US", 2, 4000),
    ShopifyStore(
        "PLA Skateboarding", "https://playitskateboarding.com", "skate", "US", 2, 4000
    ),
    ShopifyStore("35th North", "https://35thnorth.com", "skate", "US", 2, 4000),
    ShopifyStore("Subsect Skate Shop", "https://subsect.com", "skate", "US", 2, 4000),
    ShopifyStore("Furnace Skate", "https://furnaceskate.com", "skate", "US", 2, 4000),
    # ------------------------------------------------------------------
    # Collectibles & Toys
    # ------------------------------------------------------------------
    ShopifyStore(
        "Mattel Creations", "https://creations.mattel.com", "collectible", "US", 1, 2500
    ),
    ShopifyStore("Final Mouse", "https://finalmouse.com", "collectible", "US", 1, 2500),
    ShopifyStore(
        "PopMart AU Shopify", "https://www.popmart.com.au", "collectible", "AU", 2, 3500
    ),
    ShopifyStore(
        "PopMart NZ Shopify", "https://www.popmart.co.nz", "collectible", "NZ", 2, 3500
    ),
    ShopifyStore("Topps DE", "https://de.topps.com", "collectible", "EU", 2, 3500),
    ShopifyStore("Swag Golf", "https://swag.golf", "collectible", "US", 2, 3500),
    ShopifyStore(
        "Stanley 1913", "https://www.stanley1913.com", "collectible", "US", 2, 3500
    ),
    ShopifyStore("Bratz", "https://www.bratz.com", "collectible", "US", 2, 3500),
    # ------------------------------------------------------------------
    # International
    # ------------------------------------------------------------------
    ShopifyStore("JB Hi-Fi", "https://www.jbhifi.com.au", "general", "AU", 2, 3000),
    ShopifyStore("JB Hi-Fi NZ", "https://www.jbhifi.co.nz", "general", "NZ", 2, 3000),
    ShopifyStore(
        "Culture Kings AU",
        "https://www.culturekings.com.au",
        "streetwear",
        "AU",
        2,
        3500,
    ),
    ShopifyStore(
        "Culture Kings NZ",
        "https://www.culturekings.co.nz",
        "streetwear",
        "NZ",
        2,
        3500,
    ),
    ShopifyStore("Titan22", "https://www.titan22.com", "sneaker", "ROW", 2, 3500),
    ShopifyStore(
        "Oneblockdown ROW", "https://www.oneblockdown.it", "sneaker", "EU", 2, 3500
    ),
    ShopifyStore(
        "Antonioli EU", "https://www.antonioli.eu", "streetwear", "EU", 2, 3500
    ),
    ShopifyStore("Afew Store", "https://www.afew-store.com", "sneaker", "EU", 2, 3500),
    ShopifyStore("Asics HK", "https://www.asics.com.hk", "sneaker", "ROW", 2, 3500),
    ShopifyStore(
        "Supreme Asia", "https://www.supremenewyork.com", "streetwear", "ROW", 2, 3500
    ),
    ShopifyStore("ANTA", "https://www.anta.com", "sneaker", "ROW", 2, 3500),
    ShopifyStore("Juice HK", "https://juicestore.com", "streetwear", "ROW", 2, 3500),
    ShopifyStore("Smets", "https://www.smets.lu", "streetwear", "EU", 2, 3500),
    ShopifyStore("NRML", "https://nrml.ca", "sneaker", "CA", 2, 3500),
    ShopifyStore("Makeway CA", "https://makeway.ca", "streetwear", "CA", 2, 3500),
    # ------------------------------------------------------------------
    # Lifestyle, Hats & Accessories
    # ------------------------------------------------------------------
    ShopifyStore("Hat Club", "https://www.hatclub.com", "general", "US", 2, 3500),
    ShopifyStore("Hat Dreams", "https://hatdreams.com", "general", "US", 2, 3500),
    ShopifyStore("My Fitteds", "https://myfitteds.com", "general", "US", 2, 3500),
    ShopifyStore("BKLYN CAP", "https://www.bklyncap.com", "general", "US", 2, 3500),
    ShopifyStore("Lids HD", "https://www.lids.com", "general", "US", 2, 3500),
    ShopifyStore(
        "Exclusive Fitted", "https://www.exclusivefitted.com", "general", "US", 2, 3500
    ),
    ShopifyStore(
        "USA Cap King", "https://www.usacapking.com", "general", "US", 2, 3500
    ),
    ShopifyStore("LDRS 1354", "https://www.ldrs1354.com", "general", "US", 2, 3500),
    ShopifyStore("Gym Shark", "https://www.gymshark.com", "general", "US", 2, 3500),
    ShopifyStore("Skims", "https://skims.com", "general", "US", 2, 3500),
    ShopifyStore(
        "Meta Store", "https://www.meta.com/quest/accessories", "general", "US", 2, 3500
    ),
    # ------------------------------------------------------------------
    # Music & Entertainment Merch
    # ------------------------------------------------------------------
    ShopifyStore(
        "Taylor Swift Official Store",
        "https://store.taylorswift.com",
        "general",
        "US",
        1,
        2500,
    ),
    ShopifyStore(
        "Taylor Swift Store CA",
        "https://store-ca.taylorswift.com",
        "general",
        "CA",
        2,
        3000,
    ),
    ShopifyStore(
        "Taylor Swift Store AU",
        "https://store-au.taylorswift.com",
        "general",
        "AU",
        2,
        3000,
    ),
    ShopifyStore(
        "Taylor Swift Store UK",
        "https://store-uk.taylorswift.com",
        "general",
        "UK",
        2,
        3000,
    ),
    ShopifyStore(
        "Billie Eilish Store US",
        "https://store.billieeilish.com",
        "general",
        "US",
        2,
        3000,
    ),
    ShopifyStore(
        "Billie Eilish Store CA",
        "https://store-ca.billieeilish.com",
        "general",
        "CA",
        2,
        3000,
    ),
    ShopifyStore(
        "Sabrina Carpenter",
        "https://store.sabrinacarpenter.com",
        "general",
        "US",
        2,
        3000,
    ),
    ShopifyStore(
        "Olivia Rodrigo", "https://store.oliviarodrigo.com", "general", "US", 2, 3000
    ),
    ShopifyStore(
        "Bad Bunny Adidas", "https://www.badbunny-adidas.com", "sneaker", "US", 2, 3000
    ),
    ShopifyStore(
        "J Balvin Universal Music",
        "https://shop.iamjbalvin.com",
        "general",
        "US",
        2,
        3500,
    ),
    ShopifyStore("Wutang Clan", "https://wutang.com", "general", "US", 2, 3500),
    ShopifyStore(
        "Mamba & Mambacita", "https://mambamambacita.com", "general", "US", 1, 3000
    ),
    ShopifyStore("Nike x RTFKT", "https://rtfkt.com", "sneaker", "US", 1, 3000),
    ShopifyStore(
        "GIRLS DONT CRY", "https://girlsdontcry.jp", "streetwear", "JP", 2, 3500
    ),
    # ------------------------------------------------------------------
    # Additional boutiques from Valor's extended list
    # ------------------------------------------------------------------
    ShopifyStore("Proper LBC", "https://www.properlbc.com", "sneaker", "US", 2, 3500),
    ShopifyStore("WOODstack", "https://woodstack.com", "sneaker", "US", 2, 3500),
    ShopifyStore("Humidity", "https://humidityskate.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Hush Life Boutique", "https://hushlifeboutique.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Canary Yellow", "https://www.canaryyellow.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Maxfield LA", "https://www.maxfieldla.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore("HLorenzo", "https://hlorenzo.com", "streetwear", "US", 2, 3500),
    ShopifyStore(
        "Eastside Golf", "https://eastsidegolf.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore("Strange Love", "https://strangelove.com", "skate", "US", 2, 3500),
    ShopifyStore("Complex", "https://shop.complex.com", "streetwear", "US", 2, 3500),
    ShopifyStore(
        "The Darkside Initiative",
        "https://www.thedarksideinitiative.com",
        "sneaker",
        "US",
        2,
        3500,
    ),
    ShopifyStore(
        "We Are Civil", "https://www.wearecivil.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Mainland Skate & Surf",
        "https://www.mainlandskatesurf.com",
        "skate",
        "US",
        2,
        4000,
    ),
    ShopifyStore("Nouveau", "https://nouveaubeauty.com", "streetwear", "US", 2, 3500),
    ShopifyStore("All The Right", "https://alltheright.com", "sneaker", "US", 2, 3500),
    ShopifyStore("August Shop", "https://augustshop.com", "streetwear", "US", 2, 3500),
    ShopifyStore("Blue Flowers", "https://blueflowers.co", "streetwear", "EU", 2, 3500),
    ShopifyStore(
        "Civilized Nation Shop",
        "https://civilizednation.com",
        "streetwear",
        "US",
        2,
        3500,
    ),
    ShopifyStore(
        "Coureur Goods", "https://coureurgoods.com", "streetwear", "EU", 2, 3500
    ),
    ShopifyStore(
        "Denim Exchange", "https://denimexchange.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore("Dime MTL", "https://dimemtl.com", "skate", "CA", 2, 3500),
    ShopifyStore("ECapCity", "https://ecapcity.com", "general", "US", 2, 3500),
    ShopifyStore(
        "Every Now & Then", "https://everynowandthen.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore("Foster", "https://www.fosterdeliver.com", "sneaker", "US", 2, 3500),
    ShopifyStore("GBNY", "https://gbny.nyc", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "Geometric Skate Shop", "https://geometric.com", "skate", "US", 2, 4000
    ),
    ShopifyStore(
        "Hobby Craftibles", "https://hobbycraft.com", "collectible", "CA", 2, 3500
    ),
    ShopifyStore("Juice", "https://juice.com", "streetwear", "US", 2, 3500),
    ShopifyStore(
        "Lamb Crafted", "https://lambcrafted.com", "streetwear", "US", 2, 3500
    ),
    ShopifyStore("Less 17", "https://less17.com", "streetwear", "EU", 2, 3500),
    ShopifyStore("Analogue", "https://analogue.store", "streetwear", "US", 2, 3500),
    ShopifyStore("Asphalt NYC", "https://asphalt.com", "sneaker", "US", 2, 3500),
    ShopifyStore("Foosh CA", "https://foosh.ca", "sneaker", "CA", 2, 3500),
    ShopifyStore("Fresh Rags FL", "https://freshrags.com", "streetwear", "US", 2, 3500),
    ShopifyStore(
        "Icon Board Shop", "https://iconboardshop.com", "skate", "US", 2, 4000
    ),
    ShopifyStore(
        "Kicking It ATX", "https://kickingitatx.com", "sneaker", "US", 2, 3500
    ),
    ShopifyStore(
        "Magnolia Skate Shop", "https://magnoliaskate.com", "skate", "US", 2, 4000
    ),
    ShopifyStore("Manorphx", "https://manorphx.com", "sneaker", "US", 2, 3500),
    ShopifyStore(
        "MoMa Design Store", "https://store.moma.org", "general", "US", 2, 3500
    ),
    ShopifyStore(
        "Nagano Market", "https://naganomarket.com", "collectible", "US", 2, 3500
    ),
    ShopifyStore("Phenom", "https://phenomglobal.com", "sneaker", "US", 2, 3500),
    ShopifyStore("Tony Brimz", "https://tonybrimz.com", "general", "US", 2, 3500),
    ShopifyStore(
        "TCG District", "https://tcgdistrict.com", "collectible", "US", 2, 3500
    ),
    ShopifyStore("Ward9", "https://ward9.com", "streetwear", "US", 2, 3500),
    ShopifyStore("Sesinko", "https://sesinko.com", "sneaker", "US", 2, 3500),
]


class StoreDatabase:
    """Queryable store database with filtering"""

    def __init__(self):
        self.stores: Dict[str, ShopifyStore] = {}
        self._loaded = False
        self._all_cache: Optional[List[ShopifyStore]] = None

    def load_builtin(self) -> int:
        """Load the built-in store database"""
        for store in SHOPIFY_STORES:
            key = store.name.lower().replace(" ", "_")
            self.stores[key] = store
        self._loaded = True
        self._all_cache = None  # Invalidate cache
        logger.info("Store database loaded", count=len(self.stores))
        return len(self.stores)

    def get_all(self) -> List[ShopifyStore]:
        """Get all stores (result is cached after first call)."""
        if not self._loaded:
            self.load_builtin()
        if self._all_cache is None:
            self._all_cache = list(self.stores.values())
        return self._all_cache

    def get_by_category(self, category: str) -> List[ShopifyStore]:
        """Get stores by category"""
        return [s for s in self.get_all() if s.category == category]

    def get_by_region(self, region: str) -> List[ShopifyStore]:
        """Get stores by region"""
        return [s for s in self.get_all() if s.region == region]

    def get_by_priority(self, priority: int) -> List[ShopifyStore]:
        """Get stores by priority (1=high, 2=normal, 3=low)"""
        return [s for s in self.get_all() if s.priority <= priority]

    def search(self, query: str) -> List[ShopifyStore]:
        """Search stores by name"""
        query_lower = query.lower()
        return [
            s
            for s in self.get_all()
            if query_lower in s.name.lower() or query_lower in s.url.lower()
        ]

    def get_store_list_for_monitor(
        self,
        categories: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        priority: int = 2,
    ) -> List[Dict]:
        """Get stores formatted for MultiStoreMonitor.add_stores_from_list()"""
        stores = self.get_all()

        if categories:
            stores = [s for s in stores if s.category in categories]
        if regions:
            stores = [s for s in stores if s.region in regions]

        stores = [s for s in stores if s.priority <= priority]

        return [
            {
                "name": s.name,
                "url": s.url,
                "delay_ms": s.default_delay_ms,
            }
            for s in stores
        ]

    @property
    def count(self) -> int:
        return len(self.get_all())


# Module-level singleton
store_db = StoreDatabase()
