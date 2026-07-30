"""Reviewed non-catalog media sources awaiting import into MinIO.

These URLs were manually matched against the product model or part number.
Unlike ``official_sources.py``, this registry may contain distributor and
documentation-mirror pages, so every entry declares whether its publisher is
the manufacturer.  Do not add search-result or category pages here.
"""

REVIEWED_MEDIA_SOURCES = {
    "AVAGO-AFBR-57F5MZ": {
        "image_page_url": "https://www.ebay.com/itm/201533384278",
        "image_url": "https://img.genuinemodules.com/cache/catalog/products/AFBR-57F5MZ-ELX/AFBR-57F5MZ-ELX-1-800x800.jpg",
        "image_title": "AFBR-57F5MZ-ELX — fotografía del producto",
        "pdf_url": "https://www.genuinemodules.com/image/catalog/pdf/1/AFBR-57F5MZ-ELX.pdf",
        "pdf_title": "Datasheet AFBR-57F5MZ-ELX",
        "match_scope": "exact",
    },
    "BROCADE-32G-SW-SEC": {
        "image_page_url": "https://www.genuinemodules.com/xbr-000412",
        "image_url": "https://img.genuinemodules.com/cache/catalog/products/XBR-000412/XBR-000412-1-800x800.jpg",
        "image_title": "Brocade XBR-000412 / 57-1000485-01",
        "match_scope": "exact",
    },
    "CISCO-C2960X-USED": {
        "image_page_url": "https://it-planet.com/en/p/cisco-ws-c2960x-48fpd-l-18930.html",
        "image_title": "Cisco WS-C2960X-48FPD-L",
        "match_scope": "exact",
    },
    "CISCO-GLC-LH-SM": {
        "image_page_url": "https://www.networktigers.com/products/glc-lh-sm-cisco-sfp",
        "image_url": "https://www.networktigers.com/cdn/shop/files/cisco-GLC-LH-SM_ac7d693a-61a4-4954-ab09-fc8047d6f823_463x.progressive.jpg?v=1779060769",
        "image_title": "Cisco GLC-LH-SM",
        "match_scope": "exact",
    },
    "CISCO-GLC-SX-MM": {
        "image_page_url": "https://zw.wiautomation.com/cisco/industrial-communication/other/30130102",
        "image_url": "https://www.serversupply.com/images/WebPImage/415115.webp?v=GtpCEZC11bRrfOK_gRTa23g00HAqo1EohJAqDy-DsOs",
        "image_title": "Cisco 30-1301-02 / GLC-SX-MM",
        "match_scope": "exact",
    },
    "CISCO-GLC-SX-MMD-USED": {
        "image_page_url": "https://www.disctech.com/Cisco-GLC-SX-MMD-1000BASE-SX-SFP-GBIC-with-DOM",
        "image_title": "Cisco 10-2626-01 / GLC-SX-MMD",
        "match_scope": "exact",
    },
    "CISCO-GLC-T": {
        "image_page_url": "https://www.locacaocisco.com/loja/p/glc-t",
        "image_title": "Cisco GLC-T",
        "match_scope": "exact",
    },
    "HP-MINI-260-G4": {
        "image_page_url": "https://www.computo.com.pe/productos/mini-computadora-de-escritorio-hp-260-g4-intel-core-i3-10110u-210ghz-4gb-ddr4/384188/246f4ltabm",
        "image_title": "HP 260 G4 246F4LT#ABM",
        "match_scope": "exact",
    },
    "3E3T0LS-USED": {
        "image_page_url": "https://support.hp.com/us-en/product/setup-user-guides/hp-prodesk-600-g6-desktop-mini-pc/35719299",
        "image_title": "HP ProDesk 600 G6 Desktop Mini",
        "image_is_official": True,
        "match_scope": "exact",
    },
    "HP-Z2-TOWER-G9": {
        "image_page_url": "https://www.panacompu.com/panama/en/product-information/hp-z2-g9-workstation-high-performance-desktop-intel-i7-13700-520ghz-nvidia-rtx-a2000-32gb-ram-2tb-ssd-windows-11-pro",
        "image_title": "HP Z2 G9 823G8LA#ABM",
        "match_scope": "exact",
    },
    "HP-P24-G4": {
        "image_page_url": "https://www.bhphotovideo.com/c/product/1623055-REG/hp_1a7e5aa_aba_p24_g4_23_8_ips.html",
        "image_title": "HP P24 G4 1A7E5AA#ABA",
        "match_scope": "exact",
    },
    "HP-P27H-G5": {
        "image_page_url": "https://www.hp.com/il-he/products/monitors/product-details/2101242343",
        "image_title": "HP P27h G5 64W41AA",
        "image_is_official": True,
        "match_scope": "exact",
    },
    "HP-145X": {
        "image_page_url": "https://www.hp.com/cl-es/shop/cartucho-de-toner-original-hp-laserjet-145x-de-alto-rendimiento-negro-w1450x.html",
        "image_title": "HP 145X W1450X",
        "image_is_official": True,
        "pdf_url": "https://objects.icecat.biz/objects/mmo_94577106_1698131571_1581_9214.pdf",
        "pdf_title": "Ficha de producto HP 145X W1450X",
        "match_scope": "exact",
    },
    "HP-145X-STARTER": {
        "image_page_url": "https://www.hp.com/emea_middle_east-en/products/ink-toner/product-details/35832602",
        "image_title": "Familia HP 145X W1450X — imagen referencial",
        "image_is_official": True,
        "match_scope": "family",
    },
    "HP-W9085-STARTER": {
        "image_page_url": "https://tonermarket.com.au/genuine-hp-laserjet-w9085mc-high-yield-black-toner-60-000-pages/",
        "image_url": "https://cdn11.bigcommerce.com/s-w8w4jvvp08/images/stencil/500x500/products/75834/73021/w9085mc__20739.1740635371.png?c=3",
        "image_title": "Familia W9085MC — imagen referencial",
        "match_scope": "family",
    },
    "HUAWEI-KA11-KB11": {
        "image_page_url": "https://consumer.huawei.com/ae-en/support/content/en-us15905486/",
        "image_title": "Huawei Smart Keyboard KA11-KB11",
        "image_is_official": True,
        "match_scope": "exact",
    },
    "HUAWEI-10G-02310MNW": {
        "image_page_url": "https://www.cignal.com.ar/transceivers-sfp/2702-modulo-transceiver-sfp-huawei-ebg-sfp-10g-usr-02310mnw.html",
        "image_title": "Huawei SFP-10G-USR 02310MNW",
        "pdf_url": "https://www.genuinemodules.com/image/catalog/pdf/1/02310MNW.pdf",
        "pdf_title": "Datasheet Huawei 02310MNW",
        "match_scope": "exact",
    },
    "LENOVO-1000BASE-T": {
        "image_page_url": "https://www.networktigers.com/products/78p3824-ibm-sfp",
        "image_title": "IBM/Lenovo 78P3824",
        "match_scope": "exact",
    },
    "SALICRU-SLC-2000-TWIN": {
        "image_page_url": "https://ultimainformatica.com/salicru-slc-2000-twin-pro2-iec-b1.html",
        "image_url": "https://ultimainformatica.com/2572320-thickbox_default/salicru-slc-2000-twin-pro2-iec-b1.jpg",
        "image_title": "Salicru SLC-2000-TWIN PRO2 IEC",
        "pdf_url": "https://www.sicotec.ch/pdf/slc-twin-pro2_user-manual-en-v20-06.pdf",
        "pdf_page_url": "https://www.sicotec.ch/pdf/slc-twin-pro2_user-manual-en-v20-06.pdf",
        "pdf_title": "Manual SLC TWIN PRO2",
        "match_scope": "exact",
    },
    "CANON-GPR-63": {
        "image_page_url": "https://www.gmsupplies.com/products/canon/imagerunner-advance-dx-series/canon-imagerunner-advance-dx-6870i/toner-cartridges/canon-4766c003-gpr-63-black-toner-cartridge/",
        "image_title": "Canon GPR-63 4766C003",
        "match_scope": "exact",
    },
    "CISCO-SFP-10G-SR": {
        "image_page_url": "https://techmikeny.com/products/cisco-sfp-10g-sr-10gbe-sff-transceiver-module-gbic-10-2415-03",
        "image_title": "Cisco SFP-10G-SR 10-2415-03",
        "match_scope": "exact",
    },
    "HP-W9065MC": {
        "image_page_url": "https://odemis.pe/products/toner-hp-w9065mc-negro-e73130dn-e73140dn-48-000-pag-original",
        "image_title": "HP W9065MC original",
        "match_scope": "exact",
    },
    "HP-W9085MC": {
        "image_page_url": "https://tonermarket.com.au/genuine-hp-laserjet-w9085mc-high-yield-black-toner-60-000-pages/",
        "image_url": "https://cdn11.bigcommerce.com/s-w8w4jvvp08/images/stencil/500x500/products/75834/73021/w9085mc__20739.1740635371.png?c=3",
        "image_title": "HP W9085MC original",
        "match_scope": "exact",
    },
    "HUAWEI-MATEPAD-11-5": {
        "image_page_url": "https://consumer.huawei.com/pe/tablets/matepad-11-5-2025/",
        "image_title": "Huawei MatePad 11.5 (2025)",
        "image_is_official": True,
        "match_scope": "exact",
    },
    "HUAWEI-SFP-GE-SX-MM850": {
        "image_page_url": "https://info.support.huawei.com/info-finder/imagelib/getPreviewImages?category=1Gbps+eSFP%E5%85%89%E6%A8%A1%E5%9D%97&domain=0&lang=zh&partNumber=02315204",
        "image_url": "https://img.genuinemodules.com/cache/catalog/products/02315204/02315204-1-800x800.jpg",
        "image_title": "Huawei 02315204 SFP-GE-SX-MM850",
        "image_is_official": True,
        "match_scope": "exact",
    },
}
