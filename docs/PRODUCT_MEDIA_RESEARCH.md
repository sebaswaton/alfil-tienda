# Investigación de imágenes y PDF pendientes

Fecha de verificación: 22 de julio de 2026.

Este registro reúne fuentes revisadas para los 26 SKU reportados sin imagen y
los 20 SKU reportados sin PDF. La columna **Alcance** distingue una coincidencia
exacta de una referencia de familia. Las imágenes deben descargarse y
almacenarse en MinIO; no se recomienda enlazarlas directamente desde la web de
terceros.

## Resumen

- Imágenes: 23 coincidencias exactas, 2 referencias de familia para cartuchos
  de inicio y 1 referencia pendiente de confirmar.
- PDF: 16 documentos con identificación exacta del modelo o número de parte,
  2 documentos de familia y 2 pendientes.
- `HP-W1950X` no aparece en catálogos de HP ni de distribuidores consultados.
  Antes de publicar una imagen o compatibilidad se necesita una foto legible de
  la etiqueta física.
- `HUAWEI-KA11-KB11` tiene página de producto y matriz de compatibilidad exactas,
  pero no se encontró un PDF público independiente. Puede generarse una ficha
  interna a partir de esas dos fuentes, identificándola como documento de Alfil.

## Fuentes revisadas

| SKU | Fuente de imagen | Alcance imagen | Fuente PDF o técnica | Alcance PDF | Estado / observación |
|---|---|---:|---|---:|---|
| AVAGO-AFBR-57F5MZ | [Foto real AFBR-57F5MZ-ELX](https://www.ebay.com/itm/201533384278) | Exacto | [Datasheet AFBR-57F5MZ-ELX](https://www.genuinemodules.com/image/catalog/pdf/1/AFBR-57F5MZ-ELX.pdf) | Exacto | El PDF identifica expresamente el sufijo `-ELX`. |
| BROCADE-32G-SW-SEC | [Brocade XBR-000412 / 57-1000485-01](https://www.genuinemodules.com/xbr-000412) | Exacto | [Matriz de transceivers Broadcom/Brocade](https://docs.broadcom.com/doc/GA-MX-460) | Exacto | La matriz oficial relaciona `XBR-000412`, `57-1000485-01` y 32G FC SWL. |
| CISCO-C2960X-USED | [WS-C2960X-48FPD-L](https://it-planet.com/en/p/cisco-ws-c2960x-48fpd-l-18930.html) | Exacto | [Cisco Catalyst 2960-X Data Sheet](https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-2960-x-series-switches/datasheet_c78-728232.pdf) | Exacto | Modelo exacto incluido en la tabla de pedidos. |
| CISCO-GLC-LH-SM | [Cisco GLC-LH-SM](https://www.directitsource.com/Glc-Lh-Sm-SFP-LC-Connector-LX-Lh-Transceiver-p/glc-lh-sm-ds2.htm) | Exacto | [Datasheet GLC-LH-SM](https://www.genuinemodules.com/image/catalog/pdf/1/GLC-LH-SM.pdf) | Exacto | Producto legado; no confundir con `GLC-LH-SMD`. |
| CISCO-GLC-SX-MM | [Cisco 30-1301-02 / GLC-SX-MM](https://zw.wiautomation.com/cisco/industrial-communication/other/30130102) | Exacto | [Ficha descargable GLC-SX-MM](https://cisco.manymanuals.com/network-media-converters/glc-sx-mm/datasheet-10379) | Exacto | La foto identifica el P/N físico `30-1301-02`. |
| CISCO-GLC-SX-MMD-USED | [Cisco 10-2626-01 / GLC-SX-MMD](https://www.disctech.com/Cisco-GLC-SX-MMD-1000BASE-SX-SFP-GBIC-with-DOM) | Exacto | [Datasheet compatible GLC-SX-MMD](https://edgeoptic.com/products/cisco/glc-sx-mmd) | Exacto | La imagen corresponde a la revisión física inventariada. |
| CISCO-GLC-T | [Cisco GLC-T](https://www.locacaocisco.com/loja/p/glc-t) | Exacto | [Cisco Gigabit Ethernet SFP Modules](https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/gigabit-ethernet-gbic-sfp-modules/datasheet-c78-366584.pdf) | Exacto | La ficha oficial incluye `GLC-T`. |
| HP-MINI-260-G4 | [HP 260 G4, P/N 246F4LT#ABM](https://www.computo.com.pe/productos/mini-computadora-de-escritorio-hp-260-g4-intel-core-i3-10110u-210ghz-4gb-ddr4/384188/246f4ltabm) | Exacto | [Ficha HP 246F4LT](https://h20195.www2.hp.com/v2/GetPDF.aspx/c06711625.pdf) | Modelo exacto | La configuración de imagen coincide con i3, 4 GB y 1 TB. |
| 3E3T0LS-USED | [HP ProDesk 600 G6 Desktop Mini](https://support.hp.com/us-en/product/setup-user-guides/hp-prodesk-600-g6-desktop-mini-pc/35719299) | Modelo exacto | [Ficha HP 3E3T0LS](https://pcb.inc.hp.com/dc/api/spec-sheet/us-en/35719299/pdf/3E3T0LS.pdf) | P/N exacto | PDF oficial validado como archivo descargable. |
| HP-Z2-TOWER-G9 | [HP Z2 G9 823G8LA#ABM](https://www.panacompu.com/panama/en/product-information/hp-z2-g9-workstation-high-performance-desktop-intel-i7-13700-520ghz-nvidia-rtx-a2000-32gb-ram-2tb-ssd-windows-11-pro) | P/N exacto | [Ficha HP 823G8LA](https://pcb.inc.hp.com/dc/api/spec-sheet/us-en/2100987204/pdf/823G8LA.pdf) | P/N exacto | Coincide con i7, 32 GB, 2 TB y Windows 11 Pro. |
| HP-P24-G4 | [HP P24 G4 1A7E5AA#ABA](https://www.bhphotovideo.com/c/product/1623055-REG/hp_1a7e5aa_aba_p24_g4_23_8_ips.html) | P/N exacto | [Ficha HP 1A7E5AA](https://pcb.inc.hp.com/dc/api/spec-sheet/us-en/2100001050/pdf/1A7E5AA.pdf) | P/N exacto | PDF oficial validado como archivo descargable. |
| HP-P27H-G5 | [HP P27h G5 64W41AA](https://www.hp.com/il-he/products/monitors/product-details/2101242343) | P/N exacto | [QuickSpecs HP P27h G5](https://h20195.www2.hp.com/v2/getpdf.aspx/c08310350.pdf) | P/N exacto | El PDF identifica el modelo `64W41AA`. |
| HP-145X | [HP 145X W1450X](https://www.hp.com/cl-es/shop/cartucho-de-toner-original-hp-laserjet-145x-de-alto-rendimiento-negro-w1450x.html) | P/N exacto | [Brochure W1450X](https://objects.icecat.biz/objects/mmo_94577106_1698131571_1581_9214.pdf) | P/N exacto | Fuente secundaria; la página HP confirma producto, rendimiento y compatibilidad. |
| HP-145X-STARTER | [Familia HP 145X W1450X](https://www.hp.com/emea_middle_east-en/products/ink-toner/product-details/35832602) | Familia | [Especificaciones de la familia HP 145X](https://www.hp.com/sa-en/products/ink-toner/product-details/product-specifications/35832602) | Familia | El starter no tiene empaque ni página comercial independiente; mostrar como imagen referencial. |
| HP-W1950X | — | Pendiente | — | Pendiente | No existe coincidencia verificable. Solicitar foto frontal, lateral, código de barras y modelo de impresora asociado. |
| HP-W9085-STARTER | [Familia W9085MC](https://infoconsumibles.com/tienda/consumibles-contractuales-hp/17214-hp-toner-laserjet-managed-w9085mc-negro-193424356843.html) | Familia | [HP LaserJet Managed Supplies](https://h20195.www2.hp.com/v2/getpdf.aspx/4AA5-4602ENW.pdf) | Familia | El starter no tiene referencia comercial; no presentarlo como W9085MC de reposición. |
| HUAWEI-KA11-KB11 | [Matriz Huawei con imagen KA11-KB11](https://consumer.huawei.com/ae-en/support/content/en-us15905486/) | Exacto | [Producto Huawei Smart Keyboard](https://consumer.huawei.com/pe/accessories/smart-keyboard-compatible-with-matepad-11-5/) | Página exacta, sin PDF | Generar PDF interno solo si se rotula “Ficha elaborada por Alfil”. |
| HUAWEI-10G-02310MNW | [Huawei SFP-10G-USR 02310MNW](https://www.cignal.com.ar/transceivers-sfp/2702-modulo-transceiver-sfp-huawei-ebg-sfp-10g-usr-02310mnw.html) | Exacto | [Datasheet 02310MNW](https://www.genuinemodules.com/image/catalog/pdf/1/02310MNW.pdf) | Exacto | La documentación Huawei confirma 10GBASE-USR, 850 nm y MMF. |
| LENOVO-1000BASE-T | [IBM/Lenovo 78P3824](https://www.networktigers.com/products/78p3824-ibm-sfp) | Exacto | [Guía IBM que identifica 78P3824](https://www.ibm.com/support/pages/system/files/support/swg/swgdocs.nsf/0/9ef2d0143cdc3b1785257d650058232e/%24FILE/ibm_now_factory_analytics_appliance_pdsgv1.0.pdf) | Exacto dentro de guía | La pieza es el IBM legacy P/N que Lenovo mantuvo después de la adquisición. |
| SALICRU-SLC-2000-TWIN | [Salicru SLC-2000-TWIN PRO2 IEC](https://www.pccomponentes.com/salicru-slc-twin-pro-2-2000va-iec-sai) | Exacto | [Manual SLC TWIN PRO2](https://manuals.plus/m/60f42eace7f01e997decc106c6e756fd8b81b59a038756365262dee718c2d34b) | Modelo exacto | La página del manual menciona expresamente `699CA000017`. |
| CANON-GPR-63 | [Canon GPR-63 4766C003](https://www.gmsupplies.com/products/canon/imagerunner-advance-dx-series/canon-imagerunner-advance-dx-6870i/toner-cartridges/canon-4766c003-gpr-63-black-toner-cartridge/) | Exacto | Ya disponible | — | Solo faltaba imagen. |
| CISCO-SFP-10G-SR | [Cisco SFP-10G-SR 10-2415-03](https://techmikeny.com/products/cisco-sfp-10g-sr-10gbe-sff-transceiver-module-gbic-10-2415-03) | Exacto | Ya disponible | — | Solo faltaba imagen. |
| HP-W9065MC | [HP W9065MC original](https://odemis.pe/products/toner-hp-w9065mc-negro-e73130dn-e73140dn-48-000-pag-original) | Exacto | Ya disponible | — | Solo faltaba imagen. |
| HP-W9085MC | [HP W9085MC original](https://infoconsumibles.com/tienda/consumibles-contractuales-hp/17214-hp-toner-laserjet-managed-w9085mc-negro-193424356843.html) | Exacto | Ya disponible | — | Solo faltaba imagen. |
| HUAWEI-MATEPAD-11-5 | [Huawei MatePad 11.5 2025](https://consumer.huawei.com/pe/tablets/matepad-11-5-2025/) | Modelo exacto | Ya disponible | — | El PDF existente identifica `TXZ-W09`. |
| HUAWEI-SFP-GE-SX-MM850 | [Biblioteca de imagen Huawei 02315204](https://info.support.huawei.com/info-finder/imagelib/getPreviewImages?category=1Gbps+eSFP%E5%85%89%E6%A8%A1%E5%9D%97&domain=0&lang=zh&partNumber=02315204) | P/N exacto | Ya disponible | — | Huawei advierte que la foto es referencial de la categoría física, pero la búsqueda está filtrada por `02315204`. |

## Reglas para la importación

1. Descargar el archivo y comprobar que el contenido sea una imagen válida o
   empiece por la firma `%PDF-`; no confiar únicamente en la extensión.
2. Guardar cada objeto bajo
   `products/<sku-en-minusculas>/images/` o `documents/` en el bucket de MinIO.
3. Registrar la URL de origen, fecha de verificación, alcance (`exact` o
   `family`) y si la fuente es oficial en `product_sources`.
4. No marcar un PDF de distribuidor como oficial. El fabricante del producto
   puede seguir siendo HP, Cisco, Huawei, etc., pero `is_official` describe al
   propietario del sitio que publicó el archivo.
5. Para equipos usados, la foto puede ser referencial del modelo; la condición
   “usado” debe seguir visible en la ficha del catálogo.
6. No importar `HP-W1950X` hasta validar físicamente la referencia.

