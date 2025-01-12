from difflib import get_close_matches
from typing import Any, Literal

EntityType = Literal[
    "services",
    "commodities",
    "modules",
    "materials",
    "ships",
    "allegiances",
    "economies",
    "powers",
    "power_states",
    "station_types",
    "securities",
    "governments",
    "faction_states",
]


def autocorrect(type: EntityType, v: str, default: Any = None):
    l = known_entities.get(type, [])
    matches = get_close_matches(v, l, n=1)
    if matches:
        return matches[0]
    return default


def find_entities(query: str):
    entity_categories: dict[str, str] = {
        "services": "Services are provided by stations.",
        "commodities": "Commodities are traded at a stations market.",
        "modules": "Modules are sold at a stations outfitting.",
        "materials": 'Materials are used for engineering and can be traded at stations with a "Material Trader" service.',
        "ships": "Ships are sold at a stations shipyard.",
        "allegiances": "Allegiances describe the political allegiance of a system and their stations.",
        "economies": "Economies describe the economic activity of a system or a station.",
        "powers": "Powers are the political leaders controlling systems and their stations.",
        "power_states": "Power states describe the kind of control a power has over a system and their stations.",
        "station_types": "Station types describe the type of a station.",
        "securities": "Securities describe the security level of a system and their stations.",
        "governments": "Governments describe the form of government a system and their stations are under.",
        "faction_states": "Faction states describe the state the faction controlling a system and their stations is in.",
    }

    found_entities: list[dict] = []

    words = query.replace("?", "").split()
    # two word entities
    for i in range(len(words) - 1):
        word = query.split()[i] + " " + query.split()[i + 1]
        for category, entities in known_entities.items():
            matches = get_close_matches(word, entities)
            if matches:
                found_entities.append(
                    {
                        "category": category,
                        "description": entity_categories.get(category, None),
                        "examples": matches,
                    }
                )
                try:
                    words.pop(i)
                    words.pop(i)
                except:
                    pass
    # single word entities
    for word in words:
        for category, entities in known_entities.items():
            matches = get_close_matches(word, entities)
            if matches:
                found_entities.append(
                    {
                        "category": category,
                        "description": entity_categories.get(category, None),
                        "examples": matches,
                    }
                )
                try:
                    words.pop(words.index(word))
                except:
                    pass

    return found_entities


known_entities: dict[EntityType, list[str]] = {
    "station_types": [
        "Asteroid base",
        "Coriolis Starport",
        "Drake-Class Carrier",
        "Mega ship",
        "Ocellus Starport",
        "Orbis Starport",
        "Outpost",
        "Planetary Outpost",
        "Planetary Port",
        "Settlement",
    ],
    "modules": [
        "AX Missile Rack",
        "AX Multi-Cannon",
        "Abrasion Blaster",
        "Advanced Docking Computer",
        "Advanced Missile Rack",
        "Advanced Multi-Cannon",
        "Advanced Planetary Approach Suite",
        "Advanced Plasma Accelerator",
        "Auto Field-Maintenance Unit",
        "Beam Laser",
        "Bi-Weave Shield Generator",
        "Burst Laser",
        "Business Class Passenger Cabin",
        "Cannon",
        "Cargo Rack",
        "Cargo Scanner",
        "Caustic Sink Launcher",
        "Chaff Launcher",
        "Collector Limpet Controller",
        "Corrosion Resistant Cargo Rack",
        "Cytoscrambler Burst Laser",
        "Decontamination Limpet Controller",
        "Detailed Surface Scanner",
        "Economy Class Passenger Cabin",
        "Electronic Countermeasure",
        "Enforcer Cannon",
        "Enhanced AX Missile Rack",
        "Enhanced AX Multi-Cannon",
        "Enhanced Performance Thrusters",
        "Enhanced Xeno Scanner",
        "Enzyme Missile Rack",
        "Experimental Weapon Stabiliser",
        "Fighter Hangar",
        "First Class Passenger Cabin",
        "Fragment Cannon",
        "Frame Shift Drive",
        "Frame Shift Drive (SCO)",
        "Frame Shift Drive Interdictor",
        "Frame Shift Wake Scanner",
        "Fuel Scoop",
        "Fuel Tank",
        "Fuel Transfer Limpet Controller",
        "Guardian FSD Booster",
        "Guardian Gauss Cannon",
        "Guardian Hull Reinforcement",
        "Guardian Hybrid Power Distributor",
        "Guardian Hybrid Power Plant",
        "Guardian Module Reinforcement",
        "Guardian Nanite Torpedo Pylon",
        "Guardian Plasma Charger",
        "Guardian Shard Cannon",
        "Guardian Shield Reinforcement",
        "Hatch Breaker Limpet Controller",
        "Heat Sink Launcher",
        "Hull Reinforcement Package",
        "Imperial Hammer Rail Gun",
        "Kill Warrant Scanner",
        "Life Support",
        "Lightweight Alloy",
        "Luxury Class Passenger Cabin",
        "Meta Alloy Hull Reinforcement",
        "Military Grade Composite",
        "Mine Launcher",
        "Mining Lance",
        "Mining Laser",
        "Mining Multi Limpet Controller",
        "Mirrored Surface Composite",
        "Missile Rack",
        "Module Reinforcement Package",
        "Multi-Cannon",
        "Operations Multi Limpet Controller",
        "Pacifier Frag-Cannon",
        "Pack-Hound Missile Rack",
        "Planetary Approach Suite",
        "Planetary Vehicle Hangar",
        "Plasma Accelerator",
        "Point Defence",
        "Power Distributor",
        "Power Plant",
        "Prismatic Shield Generator",
        "Prospector Limpet Controller",
        "Pulse Disruptor Laser",
        "Pulse Laser",
        "Pulse Wave Analyser",
        "Pulse Wave Xeno Scanner",
        "Rail Gun",
        "Reactive Surface Composite",
        "Recon Limpet Controller",
        "Refinery",
        "Reinforced Alloy",
        "Remote Release Flak Launcher",
        "Remote Release Flechette Launcher",
        "Repair Limpet Controller",
        "Rescue Multi Limpet Controller",
        "Research Limpet Controller",
        "Retributor Beam Laser",
        "Rocket Propelled FSD Disruptor",
        "Seeker Missile Rack",
        "Seismic Charge Launcher",
        "Sensors",
        "Shield Booster",
        "Shield Cell Bank",
        "Shield Generator",
        "Shock Cannon",
        "Shock Mine Launcher",
        "Shutdown Field Neutraliser",
        "Standard Docking Computer",
        "Sub-Surface Displacement Missile",
        "Sub-Surface Extraction Missile",
        "Supercruise Assist",
        "Thargoid Pulse Neutraliser",
        "Thrusters",
        "Torpedo Pylon",
        "Universal Multi Limpet Controller",
        "Xeno Multi Limpet Controller",
        "Xeno Scanner",
    ],
    "materials": [
        "Aberrant Shield Pattern Analysis",
        "Abnormal Compact Emissions Data",
        "Adaptive Encryptors Capture",
        "Anomalous Bulk Scan Data",
        "Anomalous FSD Telemetry",
        "Antimony",
        "Arsenic",
        "Atypical Disrupted Wake Echoes",
        "Atypical Encryption Archives",
        "Basic Conductors",
        "Bio-Mechanical Conduits",
        "Biotech Conductors",
        "Boron",
        "Bronzite Chondrite",
        "Cadmium",
        "Carbon",
        "Cargo Rack (Wreckage)",
        "Caustic Crystal",
        "Caustic Shard",
        "Chemical Distillery",
        "Chemical Manipulators",
        "Chemical Processors",
        "Chemical Storage Units",
        "Chromium",
        "Classified Scan Databanks",
        "Classified Scan Fragment",
        "Category:Common materials",
        "Compact Composites",
        "Compound Shielding",
        "Conductive Ceramics",
        "Conductive Components",
        "Conductive Polymers",
        "Configurable Components",
        "Cordycep Growth",
        "Core Dynamics Composites",
        "Corrosive Mechanisms",
        "Cracked Industrial Firmware",
        "Crystal Shards",
        "Crystalline Cluster",
        "Crystalline Fragments",
        "Datamined Wake Exceptions",
        "Decoded Emission Data",
        "Distorted Shield Cycle Recordings",
        "Divergent Scan Data",
        "Eccentric Hyperspace Trajectories",
        "Electrochemical Arrays",
        "Encoded Materials",
        "Category:Encoded materials",
        "Exceptional Scrambled Emission Data",
        "Exquisite Focus Crystals",
        "Filament Composites",
        "Flawed Focus Crystals",
        "Focus Crystals",
        "Galvanising Alloys",
        "Germanium",
        "Grid Resistors",
        "Guardian Module Blueprint Fragment",
        "Guardian Power Cell",
        "Guardian Power Conduit",
        "Guardian Sentinel Weapon Parts",
        "Guardian Technology Component",
        "Guardian Vessel Blueprint Fragment",
        "Guardian Weapon Blueprint Fragment",
        "Guardian Wreckage Components",
        "Hardened Surface Fragments",
        "Heat Conduction Wiring",
        "Heat Dispersion Plate",
        "Heat Exchangers",
        "Heat Exposure Specimen",
        "Heat Resistant Ceramics",
        "Heat Vanes",
        "High Density Composites",
        "Hybrid Capacitors",
        "Imperial Shielding",
        "Improvised Components",
        "Inconsistent Shield Soak Analysis",
        "Iron",
        "Irregular Emission Data",
        "Lead",
        "Manganese",
        "Manufactured Materials",
        "Category:Manufactured materials",
        "Massive Energy Surge Analytics",
        "Category:Material sources",
        "Material Trader",
        "Materials",
        "Mechanical Components",
        "Mechanical Equipment",
        "Mechanical Scrap",
        "Mercury",
        "Mesosiderite",
        "Meta-Alloys",
        "Metallic Meteorite",
        "Military Grade Alloys",
        "Military Supercapacitors",
        "Modified Consumer Firmware",
        "Modified Embedded Firmware",
        "Molybdenum",
        "Mussidaen Seed Pod",
        "Needle Crystals",
        "Nickel",
        "Niobium",
        "Open Symmetric Keys",
        "Outcrop",
        "Pattern Alpha Obelisk Data",
        "Pattern Beta Obelisk Data",
        "Pattern Delta Obelisk Data",
        "Pattern Epsilon Obelisk Data",
        "Pattern Gamma Obelisk Data",
        "Peculiar Shield Frequency Data",
        "Pharmaceutical Isolators",
        "Phase Alloys",
        "Phasing Membrane Residue",
        "Phloem Excretion",
        "Phosphorus",
        "Piceous Cobble",
        "Polonium",
        "Polymer Capacitors",
        "Polyporous Growth",
        "Precipitated Alloys",
        "Private Data Beacons",
        "Proprietary Composites",
        "Propulsion Elements",
        "Proto Heat Radiators",
        "Proto Light Alloys",
        "Proto Radiolic Alloys",
        "Category:Rare materials",
        "Raw Materials",
        "Category:Raw materials",
        "Refined Focus Crystals",
        "Rhenium",
        "Ruthenium",
        "Salvaged Alloys",
        "Satellite",
        "Security Firmware Patch",
        "Selenium",
        "Sensor Fragment",
        "Shield Emitters",
        "Shielding Sensors",
        "Ship Flight Data",
        "Ship Systems Data",
        "Specialised Legacy Firmware",
        "Category:Standard materials",
        "Strange Wake Solutions",
        "Sulphur",
        "Synthesis",
        "Tactical Core Chip",
        "Tagged Encryption Codes",
        "Technetium",
        "Tellurium",
        "Tempered Alloys",
        "Thargoid Barnacle Barb",
        "Thargoid Carapace",
        "Thargoid Energy Cell",
        "Thargoid Interdiction Telemetry",
        "Thargoid Material Composition Data",
        "Thargoid Organic Circuitry",
        "Thargoid Residue Data",
        "Thargoid Ship Signature",
        "Thargoid Structural Data",
        "Thargoid Technological Components",
        "Thargoid Wake Data",
        "Thermic Alloys",
        "Tin",
        "Tungsten",
        "Unexpected Emission Data",
        "Unidentified Scan Archives",
        "Untypical Shield Scans",
        "Unusual Encrypted Files",
        "Weapon Parts",
        "Worn Shield Emitters",
        "Wreckage Components",
        "Yttrium",
        "Zinc",
        "Zirconium",
    ],
    "commodities": [
        "Advanced Catalysers",
        "Advanced Medicines",
        "Aepyornis Egg",
        "Aganippe Rush",
        "Agri-Medicines",
        "Agronomic Treatment",
        "AI Relics",
        "Alacarakmo Skin Art",
        "Albino Quechua Mammoth Meat",
        "Alexandrite",
        "Algae",
        "Altairian Skin",
        "Aluminium",
        "Alya Body Soap",
        "Ancient Artefact",
        "Ancient Key",
        "Anduliga Fire Works",
        "Animal Meat",
        "Animal Monitors",
        "Anomaly Particles",
        "Antimatter Containment Unit",
        "Antique Jewellery",
        "Antiquities",
        "Any Na Coffee",
        "Apa Vietii",
        "Aquaponic Systems",
        "Arouca Conventual Sweets",
        "Articulation Motors",
        "Assault Plans",
        "Atmospheric Processors",
        "Auto-Fabricators",
        "Az Cancri Formula 42",
        "Azure Milk",
        "Baked Greebles",
        "Baltah'sine Vacuum Krill",
        "Banki Amphibious Leather",
        "Basic Medicines",
        "Bast Snake Gin",
        "Battle Weapons",
        "Bauxite",
        "Beer",
        "Belalans Ray Leather",
        "Benitoite",
        "Bertrandite",
        "Beryllium",
        "Bioreducing Lichen",
        "Biowaste",
        "Bismuth",
        "Black Box",
        "Bone Fragments",
        "Bootleg Liquor",
        "Borasetani Pathogenetics",
        "Bromellite",
        "Buckyball Beer Mats",
        "Building Fabricators",
        "Burnham Bile Distillate",
        "Caustic Tissue Sample",
        "CD-75 Kitten Brand Coffee",
        "Centauri Mega Gin",
        "Ceramic Composites",
        "Ceremonial Heike Tea",
        "Ceti Rabbits",
        "Chameleon Cloth",
        "Chateau De Aegaeon",
        "Chemical Waste",
        "Cherbones Blood Crystals",
        "Chi Eridani Marine Paste",
        "Classified Experimental Equipment",
        "Clothing",
        "CMM Composite",
        "Cobalt",
        "Coffee",
        "Coltan",
        "Combat Stabilisers",
        "Commercial Samples",
        "Computer Components",
        "Conductive Fabrics",
        "Consumer Technology",
        "Copper",
        "Coquim Spongiform Victuals",
        "Coral Sap",
        "Crom Silver Fesh",
        "Crop Harvesters",
        "Cryolite",
        "Crystalline Spheres",
        "Cyst Specimen",
        "Damaged Escape Pod",
        "Damna Carapaces",
        "Data Core",
        "Delta Phoenicis Palms",
        "Deuringas Truffles",
        "Diplomatic Bag",
        "Diso Ma Corn",
        "Domestic Appliances",
        "Duradrives",
        "Earth Relics",
        "Eden Apples of Aerial",
        "Eleu Thermals",
        "Emergency Power Cells",
        "Encrypted Correspondence",
        "Encrypted Data Storage",
        "Energy Grid Assembly",
        "Eranin Pearl Whisky",
        "Eshu Umbrellas",
        "Esuseku Caviar",
        "Ethgreze Tea Buds",
        "Evacuation Shelter",
        "Exhaust Manifold",
        "Experimental Chemicals",
        "Explosives",
        "Fish",
        "Food Cartridges",
        "Fossil Remnants",
        "Fruit and Vegetables",
        "Fujin Tea",
        "Galactic Travel Guide",
        "Gallite",
        "Gallium",
        "Geawen Dance Dust",
        "Gene Bank",
        "Geological Equipment",
        "Geological Samples",
        "Gerasian Gueuze Beer",
        "Giant Irukama Snails",
        "Giant Verrix",
        "Gilya Signature Weapons",
        "Gold",
        "Goman Yaupon Coffee",
        "Goslarite",
        "Grain",
        "Grandidierite",
        "Guardian Casket",
        "Guardian Orb",
        "Guardian Relic",
        "Guardian Tablet",
        "Guardian Totem",
        "Guardian Urn",
        "Hafnium 178",
        "Haiden Black Brew",
        "Hardware Diagnostic Sensor",
        "Harma Silver Sea Rum",
        "Havasupai Dream Catcher",
        "Heatsink Interlink",
        "Helvetitj Pearls",
        "H.E. Suits",
        "HIP 10175 Bush Meat",
        "HIP 118311 Swarm",
        "HIP Organophosphates",
        "HIP Proto-Squid",
        "HN Shock Mount",
        "Holva Duelling Blades",
        "Honesty Pills",
        "Hostages",
        "HR 7221 Wheat",
        "Hydrogen Fuel",
        "Hydrogen Peroxide",
        "Imperial Slaves",
        "Impure Spire Mineral",
        "Indi Bourbon",
        "Indite",
        "Indium",
        "Insulating Membrane",
        "Ion Distributor",
        "Jadeite",
        "Jaques Quinentian Still",
        "Jaradharre Puzzle Box",
        "Jaroua Rice",
        "Jotun Mookah",
        "Kachirigin Filter Leeches",
        "Kamitra Cigars",
        "Kamorin Historic Weapons",
        "Karetii Couture",
        "Karsuki Locusts",
        "Kinago Violins",
        "Kongga Ale",
        "Koro Kung Pellets",
        "Land Enrichment Systems",
        "Landmines",
        "Lanthanum",
        "Large Survey Data Cache",
        "Lavian Brandy",
        "Leather",
        "Leathery Eggs",
        "Leestian Evil Juice",
        "Lepidolite",
        "Liquid oxygen",
        "Liquor",
        "Lithium",
        "Lithium Hydroxide",
        "Live Hecate Sea Worms",
        "Low Temperature Diamonds",
        "LTT Hyper Sweet",
        "Lucan Onionhead",
        "Lyrae Weed",
        "Magnetic Emitter Coil",
        "Marine Equipment",
        "Master Chefs",
        "Mechucos High Tea",
        "Medb Starlube",
        "Medical Diagnostic Equipment",
        "Meta-Alloys",
        "Methane Clathrate",
        "Methanol Monohydrate Crystals",
        "Microbial Furnaces",
        "Micro Controllers",
        "Micro-weave Cooling Hoses",
        "Military Grade Fabrics",
        "Military Intelligence",
        "Military Plans",
        "Mineral Extractors",
        "Mineral Oil",
        "Modular Terminals",
        "Moissanite",
        "Mokojing Beast Feast",
        "Mollusc Brain Tissue",
        "Mollusc Fluid",
        "Mollusc Membrane",
        "Mollusc Mycelium",
        "Mollusc Soft Tissue",
        "Mollusc Spores",
        "Momus Bog Spaniel",
        "Monazite",
        "Motrona Experience Jelly",
        "Mukusubii Chitin-os",
        "Mulachi Giant Fungus",
        "Muon Imager",
        "Musgravite",
        "Mysterious Idol",
        "Nanobreakers",
        "Nanomedicines",
        "Narcotics",
        "Natural Fabrics",
        "Neofabric Insulation",
        "Neritus Berries",
        "Nerve Agents",
        "Ngadandari Fire Opals",
        "Nguna Modern Antiques",
        "Njangari Saddles",
        "Non Euclidian Exotanks",
        "Non-Lethal Weapons",
        "Occupied Escape Pod",
        "Ochoeng Chillies",
        "Onionhead",
        "Onionhead Alpha Strain",
        "Onionhead Beta Strain",
        "Onionhead Gamma Strain",
        "Ophiuch Exino Artefacts",
        "Organ Sample",
        "Orrerian Vicious Brew",
        "Osmium",
        "Painite",
        "Palladium",
        "Pantaa Prayer Sticks",
        "Pavonis Ear Grubs",
        "Performance Enhancers",
        "Personal Effects",
        "Personal Gifts",
        "Personal Weapons",
        "Pesticides",
        "Platinum",
        "Platinum Alloy",
        "Pod Core Tissue",
        "Pod Dead Tissue",
        "Pod Mesoglea",
        "Pod Outer Tissue",
        "Pod Shell Tissue",
        "Pod Surface Tissue",
        "Pod Tissue",
        "Political Prisoners",
        "Polymers",
        "Power Converter",
        "Power Generators",
        "Power Transfer Bus",
        "Praseodymium",
        "Precious Gems",
        "Progenitor Cells",
        "Prohibited Research Materials",
        "Protective Membrane Scrap",
        "Prototype Tech",
        "Pyrophyllite",
        "Radiation Baffle",
        "Rajukru Multi-Stoves",
        "Rapa Bao Snake Skins",
        "Rare Artwork",
        "Reactive Armour",
        "Rebel Transmissions",
        "Reinforced Mounting Plate",
        "Resonating Separators",
        "Rhodplumsite",
        "Robotics",
        "Rockforth Fertiliser",
        "Rusani Old Smokey",
        "Rutile",
        "Samarium",
        "Sanuma Decorative Meat",
        "SAP 8 Core Container",
        "Saxon Wine",
        "Scientific Research",
        "Scientific Samples",
        "Scrap",
        "Semiconductors",
        "Semi-Refined Spire Mineral",
        "Serendibite",
        "Shan's Charis Orchid",
        "Silver",
        "Skimmer Components",
        "Slaves",
        "Small Survey Data Cache",
        "Soontill Relics",
        "Sothis Crystalline Gold",
        "Space Pioneer Relics",
        "Structural Regulators",
        "Superconductors",
        "Surface Stabilisers",
        "Survival Equipment",
        "Synthetic Fabrics",
        "Synthetic Meat",
        "Synthetic Reagents",
        "Taaffeite",
        "Tactical Data",
        "Tanmark Tranquil Tea",
        "Tantalum",
        "Tarach Spice",
        "Tauri Chimes",
        "Tea",
        "Technical Blueprints",
        "Telemetry Suite",
        "Terra Mater Blood Bores",
        "Thallium",
        "Thargoid Basilisk Tissue Sample",
        "Thargoid Biological Matter",
        "Thargoid Cyclops Tissue Sample",
        "Thargoid Glaive Tissue Sample",
        "Thargoid Heart",
        "Thargoid Hydra Tissue Sample",
        "Thargoid Link",
        "Thargoid Medusa Tissue Sample",
        "Thargoid Orthrus Tissue Sample",
        "Thargoid Probe",
        "Thargoid Resin",
        "Thargoid Scout Tissue Sample",
        "Thargoid Scythe Tissue Sample",
        "Thargoid Sensor",
        "Thargoid Technology Samples",
        "The Hutton Mug",
        "Thermal Cooling Units",
        "The Waters of Shintara",
        "Thorium",
        "Thrutis Cream",
        "Tiegfries Synth Silk",
        "Time Capsule",
        "Tiolce Waste2Paste Units",
        "Titan Deep Tissue Sample",
        "Titan Drive Component",
        "Titanium",
        "Titan Maw Deep Tissue Sample",
        "Titan Maw Partial Tissue Sample",
        "Titan Maw Tissue Sample",
        "Titan Partial Tissue Sample",
        "Titan Tissue Sample",
        "Tobacco",
        "Toxandji Virocide",
        "Toxic Waste",
        "Trade Data",
        "Trinkets of Hidden Fortune",
        "Tritium",
        "Ultra-Compact Processor Prototypes",
        "Unclassified Relic",
        "Unoccupied Escape Pod",
        "Unstable Data Core",
        "Uraninite",
        "Uranium",
        "Uszaian Tree Grub",
        "Utgaroar Millennial Eggs",
        "Uzumoku Low-G Wings",
        "Vanayequi Ceratomorpha Fur",
        "Vega Slimweed",
        "V Herculis Body Rub",
        "Vidavantian Lace",
        "Void Extract Coffee",
        "Void Opal",
        "Volkhab Bee Drones",
        "Water",
        "Water Purifiers",
        "Wheemete Wheat Cakes",
        "Wine",
        "Witchhaul Kobe Beef",
        "Wolf Fesh",
        "Wreckage Components",
        "Wulpa Hyperbore Systems",
        "Wuthielo Ku Froth",
        "Xenobiological Prison Pod",
        "Xihe Biomorphic Companions",
        "Yaso Kondi Leaf",
        "Zeessze Ant Grub Glue",
    ],
    "ships": [
        "Adder",
        "Alliance Challenger",
        "Alliance Chieftain",
        "Alliance Crusader",
        "Anaconda",
        "Asp Explorer",
        "Asp Scout",
        "Beluga Liner",
        "Cobra MkIII",
        "Cobra MkIV",
        "Diamondback Explorer",
        "Diamondback Scout",
        "Dolphin",
        "Eagle",
        "Federal Assault Ship",
        "Federal Corvette",
        "Federal Dropship",
        "Federal Gunship",
        "Fer-de-Lance",
        "Hauler",
        "Imperial Clipper",
        "Imperial Courier",
        "Imperial Cutter",
        "Imperial Eagle",
        "Keelback",
        "Krait MkII",
        "Krait Phantom",
        "Mamba",
        "Orca",
        "Python",
        "Python MkII",
        "Sidewinder",
        "Type-10 Defender",
        "Type-6 Transporter",
        "Type-7 Transporter",
        "Type-8 Transporter",
        "Type-9 Heavy",
        "Viper MkIII",
        "Viper MkIV",
        "Vulture",
    ],
    "services": [
        "Apex Interstellar",
        "Bartender",
        "Black Market",
        "Crew Lounge",
        "Fleet Carrier Administration",
        "Fleet Carrier Fuel",
        "Fleet Carrier Management",
        "Fleet Carrier Vendor",
        "Frontline Solutions",
        "Interstellar Factors Contact",
        "Market",
        "Material Trader",
        "Missions",
        "Outfitting",
        "Pioneer Supplies",
        "Powerplay",
        "Redemption Office",
        "Refuel",
        "Repair",
        "Restock",
        "Search and Rescue",
        "Shipyard",
        "Shop",
        "Social Space",
        "Technology Broker",
        "Universal Cartographics",
        "Vista Genomics",
    ],
    "allegiances": [
        "Alliance",
        "Empire",
        "Federation",
        "Independent",
        "Pilots Federation",
        "Thargoid",
    ],
    "securities": ["High", "Medium", "Low", "Anarchy"],
    "economies": [
        "Agriculture",
        "Colony",
        "Damaged",
        "Engineering",
        "Extraction",
        "High Tech",
        "Industrial",
        "Military",
        "Prison",
        "Private Enterprise",
        "Refinery",
        "Repair",
        "Rescue",
        "Service",
        "Terraforming",
        "Tourism",
    ],
    "governments": [
        "Anarchy",
        "Communism",
        "Confederacy",
        "Cooperative",
        "Corporate",
        "Democracy",
        "Dictatorship",
        "Engineer",
        "Feudal",
        "Patronage",
        "Prison",
        "Prison Colony",
        "Private Ownership",
        "Theocracy",
    ],
    "powers": [
        "A. Lavigny-Duval",
        "Aisling Duval",
        "Archon Delaine",
        "Denton Patreus",
        "Edmund Mahon",
        "Felicia Winters",
        "Jerome Archer",
        "Li Yong-Rui",
        "Nakato Kaine",
        "Pranav Antal",
        "Yuri Grom",
        "Zachary Hudson",
        "Zemina Torval",
    ],
    "power_states": [
        "Contested",
        "Controlled",
        "Exploited",
        "Fortified",
        "In Prepare Radius",
        "Prepared",
        "Stronghold",
        "Turmoil",
        "Unoccupied",
    ],
    "faction_states": [
        "Expansion",
        "Retreat",
        "Election",
        "Civil War",
        "Outbreak",
        "Infrastructure Failure",
        "Pirate Attack",
        "Civil Liberty",
        "Lockdown",
        "Drought",
        "Boom",
        "Civil Unrest",
        "Natural Disaster",
        "Bust",
        "Investment",
        "War",
        "Terrorist Attack",
        "Famine",
        "Blight",
        "Public Holiday",
    ],
}
