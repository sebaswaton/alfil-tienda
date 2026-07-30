"""Reviewed manufacturer sources for catalog products.

Only URLs owned by the manufacturer are accepted here. ``match_scope`` is
``exact`` when the source identifies the listed model/part and ``family`` when
it documents a product family or a starter consumable without a retail page.
"""

OFFICIAL_SOURCES = {
    "HP-MINI-260-G4": [
        {"title": "HP 260 G4 Desktop Mini - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-260-g4-desktop-mini-pc/35719341", "import_og_image": True},
        {"title": "HP 260 G4 Desktop Mini - QuickSpecs", "url": "https://h20195.www2.hp.com/v2/GetPDF.aspx/c06711625.pdf", "source_type": "datasheet", "extract_image_page": 1, "extract_image_index": 1},
    ],
    "HP-MINI-400-G9": [
        {"title": "HP Pro Mini 400 G9 - especificaciones", "url": "https://support.hp.com/us-en/document/ish_6181857-6182018-16"},
        {"title": "HP Pro Mini 400 G9 - ficha técnica", "url": "https://h20195.www2.hp.com/v2/GetPDF.aspx/c08015293.pdf", "source_type": "datasheet", "extract_image_index": 0},
    ],
    "6V9T9LS-USED": [
        {"title": "HP ProDesk 400 G7 SFF - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-prodesk-400-g7-small-form-factor-pc/35719304"},
        {"title": "HP ProDesk 400 G7 SFF - ficha técnica", "url": "https://h20195.www2.hp.com/v2/GetDocument.aspx?docname=c06709328", "source_type": "datasheet", "extract_image_index": 0},
    ],
    "HP-400-G7-SFF": [
        {"title": "HP ProDesk 400 G7 SFF - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-prodesk-400-g7-small-form-factor-pc/35719304"},
        {"title": "HP ProDesk 400 G7 SFF - ficha técnica", "url": "https://h20195.www2.hp.com/v2/GetDocument.aspx?docname=c06709328", "source_type": "datasheet", "extract_image_index": 0},
    ],
    "3E3T0LS-USED": [
        {"title": "HP ProDesk 600 G6 Mini - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-prodesk-600-g6-desktop-mini-pc/35719299", "import_og_image": True},
        {"title": "HP ProDesk 600 G6 Mini - ficha por número de parte", "url": "https://pcb.inc.hp.com/dc/api/spec-sheet/us-en/35719299/pdf/3E3T0LS.pdf", "source_type": "datasheet", "extract_image_page": 1, "extract_image_index": 1},
    ],
    "6Q0G1LS-USED": [
        {"title": "HP Z2 G8 SFF - soporte y manuales", "url": "https://support.hp.com/us-en/product/setup-user-guides/hp-z2-small-form-factor-g8-workstation/model/2100619347"},
        {"title": "HP Z2 G8 SFF - ficha técnica", "url": "https://h20195.www2.hp.com/v2/getpdf.aspx/4AA7-9822ENUC.pdf", "source_type": "datasheet", "extract_image_index": 0},
    ],
    "HP-Z2-G8-SFF": [
        {"title": "HP Z2 G8 SFF - soporte y manuales", "url": "https://support.hp.com/us-en/product/setup-user-guides/hp-z2-small-form-factor-g8-workstation/model/2100619347"},
        {"title": "HP Z2 G8 SFF - ficha técnica", "url": "https://h20195.www2.hp.com/v2/getpdf.aspx/4AA7-9822ENUC.pdf", "source_type": "datasheet", "extract_image_index": 0},
    ],
    "HP-Z2-TOWER-G9": [
        {"title": "HP Z2 Tower G9 - especificaciones", "url": "https://support.hp.com/emea_middle_east-en/product/product-specs/hp-z2-g9-tower-workstation-adesktop-pc/2100987204", "import_og_image": True},
        {"title": "HP Z2 Tower G9 - ficha por número de parte", "url": "https://pcb.inc.hp.com/dc/api/spec-sheet/us-en/2100987204/pdf/823G8LA.pdf", "source_type": "datasheet"},
    ],
    "HP-Z4-G4T": [
        {"title": "HP Z4 G4 - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-z4-g4-workstation/model/16449894"},
        {"title": "HP Z4 G4 - ficha técnica", "url": "https://h20195.www2.hp.com/v2/getpdf.aspx/4AA7-0828ENUC.pdf", "source_type": "datasheet", "extract_image_index": 0},
    ],
    "HP-ZB16G10-I7": [
        {"title": "HP ZBook Firefly 16 G10 - especificaciones", "url": "https://support.hp.com/gb-en/document/ish_7819564-7819608-16"},
        {"title": "HP ZBook Firefly 16 G10 - ficha técnica", "url": "https://h20195.www2.hp.com/v2/getpdf.aspx/c08521929.pdf", "source_type": "datasheet", "extract_image_index": 0},
    ],
    "HP-250-G8": [
        {"title": "HP 250 G8 - soporte y manuales", "url": "https://support.hp.com/us-en/product/setup-user-guides/hp-250-g8-notebook-pc/38151396", "import_og_image": True},
        {"title": "HP 250 G8 - guía de usuario", "url": "https://kaas.hpcloud.hp.com/pdf-public/pdf_15147036_en-US-1.pdf", "source_type": "manual", "extract_image_page": 16, "extract_image_index": 0, "notes": "Guía de usuario publicada por HP desde la página oficial de manuales de la familia HP 250 G8."},
    ],
    "HP-240-G9": [
        {"title": "HP 240 G9 - soporte y manuales", "url": "https://support.hp.com/us-en/product/setup-user-guides/hp-240-14-inch-g9-notebook-pc/2101122434", "import_og_image": True},
        {"title": "HP 240 G9 - guía de usuario", "url": "https://kaas.hpcloud.hp.com/pdf-public/pdf_12012614_en-US-1.pdf", "source_type": "manual", "extract_image_page": 15, "extract_image_index": 0, "notes": "Manual actual publicado por el servicio oficial de soporte HP para la familia HP 240 G9."},
    ],
    "HP-240-G10": [
        {"title": "HP 240 G10 - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-240-14-inch-g10-notebook-pc/model/2101618557", "import_og_image": True},
        {"title": "HP 240 G10 - guía de usuario", "url": "https://kaas.hpcloud.hp.com/pdf-public/pdf_6887266_en-US-1.pdf", "source_type": "manual", "extract_image_page": 13, "extract_image_index": 0, "notes": "Manual actual publicado por el servicio oficial de soporte HP para la familia HP 240 G10."},
    ],
    "HP-P24-G4": [
        {"title": "Monitor HP P24 G4 - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-p24-g4-24-fhd-monitor-series/2100001050", "import_og_image": True},
        {"title": "Monitor HP P24 G4 - ficha por número de parte", "url": "https://pcb.inc.hp.com/dc/api/spec-sheet/us-en/2100001050/pdf/1A7E5AA.pdf", "source_type": "datasheet", "extract_image_page": 1, "extract_image_index": 1},
    ],
    "HP-P27H-G5": [
        {"title": "Monitor HP P27h G5 - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-p27h-g5-fhd-monitor/2101312771", "import_og_image": True},
        {"title": "Monitor HP P27h G5 - QuickSpecs", "url": "https://h20195.www2.hp.com/v2/getpdf.aspx/c08310350.pdf", "source_type": "datasheet", "extract_image_page": 1, "extract_image_index": 1},
    ],
    "HP-P224": [
        {"title": "Monitor HP P224 - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-p224-21.5-inch-monitor/26575345", "import_og_image": True},
        {"title": "Monitor HP P224 - guía de usuario", "url": "http://h10032.www1.hp.com/ctg/Manual/c06250664.pdf", "source_type": "manual", "extract_image_page": 9, "extract_image_index": 0, "notes": "Manual enlazado actualmente por el servicio oficial de soporte HP."},
    ],
    "HP-P204V": [
        {"title": "Monitor HP P204v - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-p204v-19.5-inch-monitor/26609842", "import_og_image": True},
        {"title": "Monitor HP P204v - guía de usuario", "url": "http://h10032.www1.hp.com/ctg/Manual/c06403487.pdf", "source_type": "manual", "extract_image_page": 9, "extract_image_index": 34, "notes": "Manual enlazado actualmente por el servicio oficial de soporte HP."},
    ],
    "HP-P22V-G4": [
        {"title": "Monitor HP P22v G4 - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-p22v-g4-monitor/34513921", "import_og_image": True},
        {"title": "Monitor HP P22v G4 - guía de usuario", "url": "http://h10032.www1.hp.com/ctg/Manual/c06615739.pdf", "source_type": "manual", "extract_image_page": 11, "extract_image_index": 0, "notes": "Manual enlazado actualmente por el servicio oficial de soporte HP."},
    ],
    "HP-PROONE-400-G4-AIO": [
        {"title": "HP ProOne 400 G4 23.8 - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-proone-400-g4-23.8-inch-non-touch-all-in-one-business-pc/21351228", "import_og_image": True},
        {"title": "HP ProOne 400 G4 - guía de referencia de hardware", "url": "http://h10032.www1.hp.com/ctg/Manual/c06412859.pdf", "source_type": "manual", "extract_image_page": 9, "extract_image_index": 0, "notes": "Manual enlazado actualmente por el servicio oficial de soporte HP."},
    ],
    "HP-PROONE-440-G9-AIO": [
        {"title": "HP ProOne 440 G9 23.8 - especificaciones", "url": "https://support.hp.com/us-en/product/product-specs/hp-proone-440-23.8-inch-g9-all-in-one-desktop-pc/model/2101121148", "import_og_image": True},
        {"title": "HP ProOne 440 G9 - ficha técnica", "url": "https://h20195.www2.hp.com/v2/GetDocument.aspx?docname=c08086557", "source_type": "datasheet", "extract_image_index": 0},
    ],
    "HP-X130-10G-SR": [
        {"title": "HPE Networking X130 10G SFP+ LC SR - ficha técnica", "url": "https://www.hpe.com/psnow/generateDDS/Ficha%20t%C3%A9cnica%20de%20HPE%20Networking%20X130%2010G%20SFP%2B%20LC%20SR%20Transceiver-PSN4179912MXES.pdf?cc=MX&lc=ES&oid=4179912", "source_type": "datasheet", "extract_image_index": 0, "notes": "El número comercial HPE es JD092B; AFBR-703SDZ-HP8 identifica el componente físico."},
    ],
    "HP-145X": [
        {"title": "Cartucho de tóner HP 145X (W1450X)", "url": "https://www.hp.com/py-es/products/ink-toner/product-details/35832602", "import_og_image": True},
    ],
    "HP-145X-STARTER": [
        {"title": "Familia de tóner HP 145X (W1450X)", "url": "https://www.hp.com/py-es/products/ink-toner/product-details/35832602", "match_scope": "family", "notes": "El cartucho inicial no tiene una página comercial independiente."},
    ],
    "HP-W9065MC": [
        {"title": "Impresora compatible HP LaserJet Managed E731z", "url": "https://support.hp.com/in-en/product/product-specs/hp-laserjet-managed-mfp-e731z-printer-series/model/38350986", "match_scope": "family"},
        {"title": "HP LaserJet Managed Supplies - W9065MC", "url": "https://h20195.www2.hp.com/v2/getpdf.aspx/4AA5-4602ENW.pdf", "source_type": "datasheet", "notes": "El folleto oficial de consumibles HP incluye la referencia W9065MC."},
    ],
    "HP-W9085MC": [
        {"title": "Impresora compatible HP LaserJet Managed E826z", "url": "https://support.hp.com/hk-en/product/product-specs/hp-laserjet-managed-mfp-e826z-printer-series/model/38350978", "match_scope": "family"},
        {"title": "HP LaserJet Managed Supplies - W9085MC", "url": "https://h20195.www2.hp.com/v2/getpdf.aspx/4AA5-4602ENW.pdf", "source_type": "datasheet", "notes": "El folleto oficial de consumibles HP incluye la referencia W9085MC."},
    ],
    "HP-W9085-STARTER": [
        {"title": "Familia HP LaserJet Managed E826z", "url": "https://support.hp.com/hk-en/product/product-specs/hp-laserjet-managed-mfp-e826z-printer-series/model/38350978", "match_scope": "family", "notes": "Consumible inicial sin página comercial independiente."},
    ],
    "CISCO-C2960X-USED": [
        {"title": "Cisco Catalyst 2960-X Series - ficha técnica", "url": "https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-2960-x-series-switches/datasheet_c78-728232.html"},
        {"title": "Cisco Catalyst 2960-X Series - PDF", "url": "https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-2960-x-series-switches/datasheet_c78-728232.pdf", "source_type": "datasheet"},
    ],
    "CISCO-GLC-LH-SM": [
        {"title": "Cisco Gigabit Ethernet SFP Modules", "url": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/gigabit-ethernet-gbic-sfp-modules/datasheet-c78-366584.html"},
        {"title": "Cisco Gigabit Ethernet SFP Modules - PDF", "url": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/gigabit-ethernet-gbic-sfp-modules/datasheet-c78-366584.pdf", "source_type": "datasheet"},
    ],
    "CISCO-GLC-SX-MM": [
        {"title": "Cisco Gigabit Ethernet SFP Modules", "url": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/gigabit-ethernet-gbic-sfp-modules/datasheet-c78-366584.html"},
        {"title": "Cisco Gigabit Ethernet SFP Modules - PDF", "url": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/gigabit-ethernet-gbic-sfp-modules/datasheet-c78-366584.pdf", "source_type": "datasheet"},
    ],
    "CISCO-GLC-SX-MMD-USED": [
        {"title": "Cisco Gigabit Ethernet SFP Modules", "url": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/gigabit-ethernet-gbic-sfp-modules/datasheet-c78-366584.html"},
        {"title": "Cisco Gigabit Ethernet SFP Modules - PDF", "url": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/gigabit-ethernet-gbic-sfp-modules/datasheet-c78-366584.pdf", "source_type": "datasheet"},
    ],
    "CISCO-GLC-T": [
        {"title": "Cisco Gigabit Ethernet SFP Modules", "url": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/gigabit-ethernet-gbic-sfp-modules/datasheet-c78-366584.html"},
        {"title": "Cisco Gigabit Ethernet SFP Modules - PDF", "url": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/gigabit-ethernet-gbic-sfp-modules/datasheet-c78-366584.pdf", "source_type": "datasheet"},
    ],
    "CISCO-SFP-10G-SR": [
        {"title": "Cisco 10GBASE SFP+ Modules", "url": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/data_sheet_c78-455693.html"},
        {"title": "Cisco 10GBASE SFP+ Modules - PDF", "url": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/data_sheet_c78-455693.pdf", "source_type": "datasheet"},
    ],
    "HUAWEI-MATEPAD-11-5": [
        {"title": "HUAWEI MatePad 11.5 - producto", "url": "https://consumer.huawei.com/pe/tablets/matepad-11-5-2025/", "import_og_image": True},
        {"title": "HUAWEI MatePad 11.5 TXZ-W09 - ficha energética", "url": "https://consumer.huawei.com/dam/content/dam/huawei-cbg-site/weu/fr/online-materials/offerpage/August-2025/MP-11.5-launch/energy-class/fiche.pdf", "source_type": "datasheet"},
    ],
    "HUAWEI-KA11-KB11": [
        {"title": "HUAWEI Smart Keyboard para MatePad 11.5", "url": "https://consumer.huawei.com/pe/accessories/smart-keyboard-compatible-with-matepad-11-5/", "import_og_image": True},
        {"title": "Compatibilidad oficial TXZ y KA11-KB11", "url": "https://consumer.huawei.com/ca/support/content/en-us15905486/", "source_type": "support"},
    ],
    "HUAWEI-SFP-GE-SX-MM850": [
        {"title": "Huawei eKitEngine Optical Module Datasheet", "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/fb2741d084534101bb40779b815da2ca/M3T1A590N1134411421645103302/Huawei%20ekitEngine%20Optical%20Module%20Datasheet.pdf", "source_type": "datasheet"},
    ],
    "HUAWEI-10G-02310MNW": [
        {"title": "Huawei SFP-10G-USR (02310MNW) - especificaciones", "url": "https://support.huawei.com/enterprise/en/doc/EDOC1100202470/e8d96397/pluggable-modules-for-ports", "source_type": "support", "notes": "La documentación oficial identifica 02310MNW como SFP-10G-USR, SFP+ 10GBASE-USR MMF de 850 nm y 100 m."},
    ],
    "SALICRU-SLC-2000-TWIN": [
        {"title": "Salicru SLC-2000-TWIN PRO2 IEC", "url": "https://www.salicru.com/slc-2000-twin-pro2-iec.html", "import_og_image": True},
    ],
    "CANON-GPR-63": [
        {"title": "Canon GPR-63 - accesorios oficiales", "url": "https://www.usa.canon.com/shop/view-all-accessories/imagerunner-advance-dx-6870i"},
        {"title": "Canon GPR-63 - ficha de seguridad", "url": "https://downloads.canon.com/MSDS2/TCW2141.pdf", "source_type": "safety_sheet"},
    ],
    "AVAGO-AFBR-57F5MZ": [
        {"title": "Broadcom AFBR-57F5xMZ", "url": "https://www.broadcom.com/products/fiber-optic-modules-components/networking/optical-transceivers/sfpplus/afbr-57f5xmz", "match_scope": "family"},
    ],
    "BROCADE-32G-SW-SEC": [
        {"title": "Brocade Transceiver Support Matrix", "url": "https://docs.broadcom.com/doc/GA-MX-460", "source_type": "support"},
    ],
    "LENOVO-1000BASE-T": [
        {"title": "IBM/Lenovo 78P3824 - guía de servicio que identifica la pieza", "url": "https://www.ibm.com/support/pages/system/files/support/swg/swgdocs.nsf/0/9ef2d0143cdc3b1785257d650058232e/%24FILE/ibm_now_factory_analytics_appliance_pdsgv1.0.pdf", "source_type": "manual", "notes": "La guía oficial lista 78P3824 como IBM SFP 1000Base-T (RJ-45) Transceiver."},
    ],
}


CORRECTIONS = {
    "HP-145X": {"part_number": "W1450X"},
    "SALICRU-SLC-2000-TWIN": {"name": "UPS Salicru SLC-2000-TWIN PRO2 IEC"},
    "HUAWEI-10G-02310MNW": {"name": "Transceiver Huawei SFP-10G-USR", "part_number": "02310MNW"},
}


RETIRED_SOURCE_URLS = {
    # Salicru retiró este archivo; la página exacta del producto sigue vigente.
    "https://www.salicru.com/files/documentacion/jm97403%281%29.pdf",
    # Rutas heredadas de HP reemplazadas por manuales vigentes del servicio de soporte.
    "https://h10032.www1.hp.com/ctg/Manual/c08137963.pdf",
    "https://h20195.www2.hp.com/v2/GetPDF.aspx/c08514065.pdf",
    "https://h20195.www2.hp.com/v2/GetPDF.aspx/4AA7-4231EEAP.pdf",
    "https://h20195.www2.hp.com/v2/GetDocument.aspx?docname=c06275004",
    "https://h20195.www2.hp.com/v2/GetPDF.aspx/4aa7-7748eeap.pdf",
    "https://h20195.www2.hp.com/v2/getpdf.aspx/c06043763.pdf",
}
