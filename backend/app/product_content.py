"""Curated catalog copy derived from reviewed manufacturer sources.

Configuration fields from Alfil's physical inventory take precedence over
family-level manufacturer capabilities. Statements that depend on a printer,
switch, fiber plant or installed option are worded as compatibility checks.
"""


def faq(question, answer):
    return {"question": question, "answer": answer}


def equipment(description, specs, *, used=False, compatibility="la configuración indicada"):
    condition_answer = (
        "Sí. Es una unidad usada del inventario de Alfil. Antes de cotizar se confirma su estado, accesorios incluidos y condición física."
        if used else
        "La publicación corresponde al número de parte y a la configuración registrada por Alfil. La disponibilidad final se confirma en la cotización."
    )
    return {
        "description": description,
        "specs": specs,
        "highlights": ["Configuración identificada por número de parte", "Stock físico registrado por Alfil", "Cotización y soporte con un asesor"],
        "faqs": [
            faq("¿La configuración publicada corresponde al equipo disponible?", condition_answer),
            faq("¿Se puede ampliar o personalizar el equipo?", f"Depende de {compatibility} y de los componentes homologados por el fabricante. Un asesor puede validar memoria, almacenamiento y accesorios antes de cotizar."),
            faq("¿Alfil ofrece preparación e instalación?", "Sí. La cotización puede incluir configuración, puesta en marcha, integración y soporte postventa según el alcance solicitado."),
        ],
    }


def transceiver(description, specs, compatibility_answer, distance_answer):
    return {
        "description": description,
        "specs": specs,
        "highlights": ["Módulo identificado por referencia", "Compatibilidad sujeta al equipo anfitrión", "Stock físico disponible para cotizar"],
        "faqs": [
            faq("¿Con qué equipos es compatible?", compatibility_answer),
            faq("¿Qué distancia de enlace admite?", distance_answer),
            faq("¿Qué debe validarse antes de instalarlo?", "Se debe confirmar el tipo de puerto, velocidad, conector, fibra o cable, longitud de onda y soporte del sistema operativo del equipo anfitrión."),
        ],
    }


def toner(description, specs, compatibility_answer, *, starter=False):
    yield_answer = (
        "Es un consumible inicial; su capacidad puede ser menor que la de un cartucho comercial. Alfil confirma la condición y procedencia en la cotización."
        if starter else
        "El rendimiento real depende de la cobertura, tipo de documento y condiciones de impresión. Se confirma la referencia exacta antes de cotizar."
    )
    return {
        "description": description,
        "specs": specs,
        "highlights": ["Referencia identificada en inventario", "Compatibilidad validable antes de la entrega", "Cotización por cantidad disponible"],
        "faqs": [
            faq("¿Con qué impresoras es compatible?", compatibility_answer),
            faq("¿Cuál es su rendimiento?", yield_answer),
            faq("¿Cómo debe almacenarse?", "Debe conservarse cerrado, en un lugar seco, fresco y protegido de luz directa, humedad y cambios bruscos de temperatura."),
        ],
    }


PRODUCT_CONTENT = {
    "3E3T0LS-USED": equipment(
        "PC empresarial ultracompacta HP ProDesk 600 G6 Mini, diseñada para puestos con poco espacio y administración corporativa. La unidad disponible integra procesador Intel Core i5, 16 GB de memoria y SSD de 256 GB.",
        {"Familia": "HP ProDesk 600 G6 Desktop Mini", "Formato": "Desktop Mini", "Procesador instalado": "Intel Core i5", "Memoria instalada": "16 GB", "Almacenamiento instalado": "SSD de 256 GB", "Uso recomendado": "Oficina, atención y puestos empresariales"},
        used=True,
    ),
    "6Q0G1LS-USED": equipment(
        "Workstation compacta HP Z2 G8 SFF para flujos profesionales que requieren expansión y rendimiento sostenido en un chasis de tamaño reducido. La unidad usada registrada por Alfil incluye Intel Core i7, 16 GB y SSD M.2 de 512 GB.",
        {"Familia": "HP Z2 Small Form Factor G8", "Formato": "Small Form Factor", "Procesador instalado": "Intel Core i7", "Memoria instalada": "16 GB", "Almacenamiento instalado": "SSD M.2 de 512 GB", "Plataforma": "Compatible con expansión PCIe Gen 4 según configuración"},
        used=True,
    ),
    "6V9T9LS-USED": equipment(
        "Desktop empresarial HP ProDesk 400 G7 SFF de formato compacto. Combina plataforma Intel Core de décima generación, conectividad para oficina y posibilidades de ampliación; esta unidad usada incorpora 16 GB y SSD M.2 de 250 GB.",
        {"Familia": "HP ProDesk 400 G7 SFF", "Formato": "Small Form Factor", "Procesador instalado": "Intel Core i5", "Memoria instalada": "16 GB", "Almacenamiento instalado": "SSD M.2 de 250 GB", "Video de la familia": "DisplayPort 1.4 y HDMI 1.4"},
        used=True,
    ),
    "HP-P24-G4": equipment(
        "Monitor empresarial HP P24 G4 de 23.8 pulgadas, orientado a productividad diaria y despliegues de oficina. Su formato Full HD ofrece un área de trabajo cómoda para aplicaciones administrativas y puestos múltiples.",
        {"Modelo": "HP P24 G4", "Tamaño de pantalla": "23.8 pulgadas", "Resolución": "Full HD (1920 × 1080)", "Relación de aspecto": "16:9", "Uso recomendado": "Oficina y productividad"},
        compatibility="el soporte VESA, entradas de video y accesorios del monitor",
    ),
    "HP-P27H-G5": equipment(
        "Monitor HP P27h G5 FHD de 27 pulgadas para espacios de trabajo que requieren mayor superficie visual. Su diseño empresarial prioriza lectura, productividad y una instalación ordenada en escritorio.",
        {"Modelo": "HP P27h G5", "Tamaño de pantalla": "27 pulgadas", "Resolución": "Full HD (1920 × 1080)", "Relación de aspecto": "16:9", "Uso recomendado": "Productividad empresarial"},
        compatibility="las entradas de video, montaje y ergonomía de esta referencia",
    ),
    "HP-P224": equipment(
        "Monitor empresarial HP P224 de 21.5 pulgadas para puestos administrativos y estaciones de trabajo. Su panel Full HD antirreflejo ofrece una imagen nítida y conexiones de video habituales en entornos corporativos.",
        {"Modelo": "HP P224", "Tamaño de pantalla": "21.5 pulgadas", "Resolución nativa": "Full HD (1920 × 1080)", "Brillo": "250 nits", "Superficie": "Antirreflejo", "Entradas de video": "DisplayPort 1.2, HDMI 1.4 y VGA"},
        compatibility="las entradas de video, el montaje VESA y los accesorios del monitor",
    ),
    "HP-P204V": equipment(
        "Monitor HP P204v de 19.5 pulgadas orientado a tareas de oficina, atención y operación diaria. Su resolución HD+ mantiene una presentación compacta y clara para aplicaciones empresariales.",
        {"Modelo": "HP P204v", "Tamaño de pantalla": "19.5 pulgadas", "Resolución nativa": "HD+ (1600 × 900)", "Brillo": "200 nits", "Superficie": "Antirreflejo", "Relación de aspecto": "16:9"},
        compatibility="las entradas de video, el montaje y los accesorios de esta referencia",
    ),
    "HP-P22V-G4": equipment(
        "Monitor HP P22v G4 de 21.5 pulgadas para productividad diaria. Ofrece resolución Full HD, tratamiento antirreflejo y modo de luz azul baja en un formato adecuado para escritorios corporativos.",
        {"Modelo": "HP P22v G4", "Tamaño de pantalla": "21.5 pulgadas", "Resolución nativa": "Full HD (1920 × 1080)", "Brillo": "250 nits", "Contraste": "1000:1", "Funciones de pantalla": "Antirreflejo y modo de luz azul baja"},
        compatibility="las entradas de video, el soporte y el entorno de instalación",
    ),
    "HP-PROONE-400-G4-AIO": equipment(
        "Equipo All-in-One empresarial HP ProOne 400 G4 con pantalla de 23.8 pulgadas. Integra los componentes del computador y la pantalla en una sola unidad para simplificar puestos de oficina y reducir el cableado.",
        {"Familia": "HP ProOne 400 G4", "Formato": "All-in-One", "Pantalla registrada": "23.8 pulgadas", "Tipo de pantalla": "No táctil", "Número de parte de inventario": "5DV82LA#ABM", "Configuración interna": "Se confirma por número de serie antes de cotizar"},
        compatibility="la configuración exacta identificada por número de serie y las opciones homologadas por HP",
    ),
    "HP-PROONE-440-G9-AIO": equipment(
        "Equipo All-in-One HP ProOne 440 G9 de 23.8 pulgadas para espacios empresariales. La familia combina pantalla Full HD, plataforma administrable y componentes internos reemplazables según la configuración adquirida.",
        {"Familia": "HP ProOne 440 G9", "Formato": "All-in-One", "Pantalla de la familia": "23.8 pulgadas Full HD IPS", "Chipset de la familia": "Intel Q670", "Ranuras de memoria": "2 SODIMM", "Número de parte de inventario": "787M0LA#ABM", "Configuración interna": "Se confirma por número de serie antes de cotizar"},
        compatibility="la configuración exacta del número de parte 787M0LA#ABM y los accesorios homologados",
    ),
    "HP-250-G8": equipment(
        "Laptop HP 250 G8 de 15.6 pulgadas para trabajo móvil, estudio y productividad general. La familia admite distintas combinaciones de procesador, memoria, almacenamiento y pantalla; Alfil confirma la configuración de cada unidad antes de cotizar.",
        {"Familia": "HP 250 G8 Notebook PC", "Tamaño de pantalla": "15.6 pulgadas", "Formato": "Laptop", "Configuraciones": "Variables según número de producto", "Identificación disponible": "Por número de serie del inventario"},
        compatibility="el número de producto asociado a cada serie, la memoria instalada y las opciones de almacenamiento",
    ),
    "HP-240-G9": equipment(
        "Laptop HP 240 G9 de 14 pulgadas, diseñada como equipo compacto para productividad y movilidad. La documentación de servicio de la familia contempla memoria DDR4, almacenamiento SATA o NVMe y conectividad empresarial según configuración.",
        {"Familia": "HP 240 14 inch G9 Notebook PC", "Tamaño de pantalla": "14 pulgadas", "Formato": "Laptop", "Memoria de la familia": "DDR4", "Almacenamiento de la familia": "SATA o PCIe NVMe según configuración", "Batería de la familia": "3 celdas, 41 Wh", "Configuración instalada": "Se confirma por número de serie"},
        compatibility="el número de producto asociado a cada serie y los componentes instalados de fábrica",
    ),
    "HP-240-G10": equipment(
        "Laptop HP 240 G10 de 14 pulgadas para productividad cotidiana y despliegues empresariales. La familia ofrece pantalla compacta, memoria DDR4 y almacenamiento de estado sólido, con variantes que deben verificarse por número de producto.",
        {"Familia": "HP 240 14 inch G10 Notebook PC", "Tamaño de pantalla": "14 pulgadas", "Formato": "Laptop", "Memoria de la familia": "DDR4", "Conectividad de la familia": "Wi-Fi y Bluetooth según configuración", "Configuración instalada": "Se confirma por número de serie"},
        compatibility="el número de producto asociado a cada serie y las opciones instaladas por HP",
    ),
    "HUAWEI-MATEPAD-11-5": equipment(
        "Tablet HUAWEI MatePad 11.5 en configuración de 8 GB de memoria y 256 GB de almacenamiento. Está pensada para trabajo móvil, lectura, colaboración y consumo de contenido dentro del ecosistema Huawei.",
        {"Modelo": "HUAWEI MatePad 11.5", "Código de modelo": "TXZ-W09", "Memoria": "8 GB", "Almacenamiento": "256 GB", "Conectividad": "Wi-Fi", "Color registrado": "Gris"},
        compatibility="las aplicaciones, accesorios y versión de sistema disponibles para TXZ-W09",
    ),
    "HUAWEI-KA11-KB11": equipment(
        "Teclado magnético HUAWEI Smart Keyboard para convertir la MatePad 11.5 en una estación de escritura más cómoda. La referencia KA11-KB11 está documentada para equipos de la familia TXZ.",
        {"Modelo": "HUAWEI Smart Keyboard", "Referencia": "KA11-KB11", "Compatibilidad documentada": "HUAWEI MatePad 11.5 / familia TXZ", "Color": "Negro", "Tipo": "Teclado y cubierta magnética"},
        compatibility="la variante exacta de la MatePad 11.5 y la distribución del teclado",
    ),
    "HP-ZB16G10-I7": equipment(
        "Workstation móvil HP ZBook Firefly 16 G10 para profesionales que necesitan rendimiento certificado en un equipo transportable. La configuración disponible combina Intel Core i7, 16 GB DDR5, SSD de 1 TB y gráficos NVIDIA RTX A500.",
        {"Familia": "HP ZBook Firefly 16 G10", "Procesador": "Intel Core i7", "Memoria": "16 GB DDR5-5200", "Almacenamiento": "SSD de 1 TB", "Gráficos": "NVIDIA RTX A500 de 4 GB", "Pantalla de la familia": "16 pulgadas, relación 16:10", "Sistema": "Windows 11 Pro"},
    ),
    "HP-Z4-G4T": equipment(
        "Workstation HP Z4 G4 Tower para visualización, ingeniería y cargas profesionales ampliables. El inventario corresponde a una configuración con Intel Xeon W-2295, 32 GB de memoria y 1 TB de almacenamiento.",
        {"Familia": "HP Z4 G4 Workstation", "Formato": "Torre", "Procesador": "Intel Xeon W-2295", "Memoria instalada": "32 GB", "Almacenamiento instalado": "1 TB", "Plataforma": "Workstation profesional de un socket"},
    ),
    "HP-Z2-G8-SFF": equipment(
        "Workstation HP Z2 G8 SFF que concentra potencia profesional y capacidad de expansión en un chasis compacto. La configuración registrada integra Intel Core i7-11700, 16 GB y SSD M.2 de 512 GB.",
        {"Familia": "HP Z2 Small Form Factor G8", "Formato": "Small Form Factor", "Procesador": "Intel Core i7-11700", "Memoria": "16 GB", "Almacenamiento": "SSD M.2 de 512 GB", "Expansión de la familia": "PCIe Gen 4"},
    ),
    "HP-Z2-TOWER-G9": equipment(
        "Workstation HP Z2 Tower G9 para diseño, ingeniería y creación de contenido con una arquitectura de torre ampliable. Esta configuración incorpora Intel Core i7, 32 GB, 2 TB y gráficos dedicados de 12 GB.",
        {"Familia": "HP Z2 Tower G9", "Formato": "Torre", "Procesador": "Intel Core i7", "Memoria": "32 GB", "Almacenamiento": "2 TB", "Memoria gráfica": "12 GB", "Sistema": "Windows 11 Pro"},
    ),
    "HP-400-G7-SFF": equipment(
        "PC empresarial HP ProDesk 400 G7 SFF para operación administrativa y puestos corporativos. La configuración disponible amplía la plataforma con Intel Core i5, 32 GB de memoria y 1 TB de almacenamiento.",
        {"Familia": "HP ProDesk 400 G7 SFF", "Formato": "Small Form Factor", "Procesador": "Intel Core i5", "Memoria": "32 GB", "Almacenamiento": "1 TB", "Video de la familia": "DisplayPort 1.4 y HDMI 1.4"},
    ),
    "HP-MINI-260-G4": equipment(
        "Desktop Mini HP 260 G4 para puestos de atención, oficina y espacios reducidos. El equipo disponible utiliza Intel Core i3, 4 GB de memoria y 1 TB de almacenamiento en un chasis compacto.",
        {"Familia": "HP 260 G4 Desktop Mini", "Formato": "Desktop Mini", "Procesador": "Intel Core i3", "Memoria": "4 GB", "Almacenamiento": "1 TB", "Uso recomendado": "Oficina y puestos compactos"},
    ),
    "HP-MINI-400-G9": equipment(
        "PC empresarial HP Pro Mini 400 G9 de tamaño reducido, con puertos flexibles y plataforma preparada para despliegues corporativos. La configuración disponible integra Intel Core i5, 16 GB, 512 GB y Windows 11 Pro.",
        {"Familia": "HP Pro Mini 400 G9", "Formato": "Desktop Mini", "Procesador": "Intel Core i5", "Memoria": "16 GB", "Almacenamiento": "512 GB", "Sistema": "Windows 11 Pro", "Seguridad de la familia": "HP Wolf Security for Business"},
    ),
    "CISCO-C2960X-USED": equipment(
        "Switch de acceso Cisco Catalyst WS-C2960X-48FPD-L para redes empresariales. Ofrece 48 puertos Gigabit Ethernet con PoE+ y enlaces ascendentes SFP+ de 10 Gb; las unidades disponibles son usadas.",
        {"Modelo": "Cisco Catalyst WS-C2960X-48FPD-L", "Puertos de acceso": "48 × 10/100/1000 con PoE+", "Uplinks": "2 × SFP+ de 10 Gigabit", "Presupuesto PoE de la referencia": "740 W", "Condición": "Usado", "Observación de inventario": "Una unidad sin orejas de montaje"},
        used=True,
        compatibility="la versión de IOS, licenciamiento, ópticas y alimentación PoE requerida",
    ),
    "SALICRU-SLC-2000-TWIN": equipment(
        "UPS Salicru SLC-2000-TWIN PRO2 IEC de doble conversión on-line para proteger servidores, comunicaciones y cargas sensibles. La referencia 699CA000017 entrega 2000 VA / 1800 W y dispone de cuatro salidas IEC C13.",
        {"Modelo": "SLC-2000-TWIN PRO2 IEC", "Código": "699CA000017", "Tecnología": "On-line de doble conversión", "Potencia": "2000 VA / 1800 W", "Salidas": "4 × IEC C13", "Factor de potencia de salida": "0.9", "Formato": "Torre"},
        used=True,
        compatibility="la carga total, autonomía requerida, baterías y accesorios de comunicación",
    ),
    "CISCO-GLC-SX-MMD-USED": transceiver(
        "Transceiver Cisco GLC-SX-MMD para enlaces Gigabit Ethernet 1000BASE-SX sobre fibra multimodo. Incorpora conector LC dúplex, operación a 850 nm y monitoreo óptico digital.",
        {"Estándar": "1000BASE-SX", "Formato": "SFP", "Conector": "LC dúplex", "Fibra": "Multimodo", "Longitud de onda": "850 nm", "Monitoreo": "DOM/DDM", "Condición": "Usado"},
        "Debe usarse en puertos SFP que admitan GLC-SX-MMD y la versión de software del equipo Cisco correspondiente.",
        "Hasta 550 m según el tipo y ancho de banda de la fibra multimodo empleada.",
    ),
    "CISCO-GLC-SX-MM": transceiver(
        "Módulo Cisco GLC-SX-MM para conectividad 1000BASE-SX sobre fibra multimodo. Utiliza longitud de onda de 850 nm y conector LC dúplex para enlaces Gigabit Ethernet de corta distancia.",
        {"Estándar": "1000BASE-SX", "Formato": "SFP", "Conector": "LC dúplex", "Fibra": "Multimodo", "Longitud de onda": "850 nm", "Velocidad": "1 Gbit/s"},
        "Es compatible con equipos que admitan el módulo Cisco GLC-SX-MM o una óptica 1000BASE-SX equivalente autorizada.",
        "Hasta 550 m, condicionado por la categoría y calidad de la fibra multimodo.",
    ),
    "CISCO-SFP-10G-SR": transceiver(
        "Transceiver Cisco SFP-10G-SR para enlaces 10 Gigabit Ethernet de corto alcance sobre fibra multimodo. Usa conector LC dúplex y óptica de 850 nm en formato SFP+.",
        {"Estándar": "10GBASE-SR", "Formato": "SFP+", "Conector": "LC dúplex", "Fibra": "Multimodo", "Longitud de onda": "850 nm", "Velocidad": "10 Gbit/s", "Monitoreo": "DOM/DDM"},
        "Debe verificarse que el switch, router o servidor admita SFP-10G-SR y que su software reconozca la referencia instalada.",
        "Hasta 300 m con OM3 y hasta 400 m con OM4, de acuerdo con el cableado y presupuesto óptico.",
    ),
    "CISCO-GLC-T": transceiver(
        "Transceiver Cisco GLC-T para llevar un puerto SFP Gigabit a cobre 1000BASE-T. Utiliza conector RJ-45 y cableado Ethernet de par trenzado para enlaces dentro del rack o la sala técnica.",
        {"Estándar": "1000BASE-T", "Formato": "SFP", "Conector": "RJ-45", "Medio": "Cobre de par trenzado", "Velocidad": "1 Gbit/s"},
        "Requiere un puerto SFP compatible con módulos de cobre GLC-T; no todos los puertos aceptan transceivers 1000BASE-T.",
        "Hasta 100 m con cableado de categoría compatible y correctamente certificado.",
    ),
    "CISCO-GLC-LH-SM": transceiver(
        "Módulo Cisco GLC-LH-SM para 1000BASE-LX/LH sobre fibra monomodo, con posibilidad de uso multimodo bajo las condiciones indicadas por Cisco. Trabaja a 1310 nm con conector LC dúplex.",
        {"Estándar": "1000BASE-LX/LH", "Formato": "SFP", "Conector": "LC dúplex", "Fibra principal": "Monomodo", "Longitud de onda": "1310 nm", "Velocidad": "1 Gbit/s"},
        "Debe instalarse en un puerto SFP compatible con GLC-LH-SM. En fibra multimodo puede requerir cable de acondicionamiento de modo.",
        "Hasta 10 km sobre fibra monomodo; en multimodo la distancia depende del tipo de fibra y acondicionamiento.",
    ),
    "HUAWEI-SFP-GE-SX-MM850": transceiver(
        "Transceiver Huawei eSFP-GE-SX-MM850 para Gigabit Ethernet sobre fibra multimodo. Opera a 850 nm, usa conector LC y está orientado a enlaces ópticos de corta distancia.",
        {"Modelo": "eSFP-GE-SX-MM850", "Número de parte": "02315204", "Formato": "SFP/eSFP", "Conector": "LC", "Fibra": "Multimodo", "Longitud de onda": "850 nm", "Velocidad": "1.25 Gbit/s"},
        "Debe verificarse el soporte del número de parte 02315204 en el equipo Huawei y su versión de software.",
        "La documentación de la familia indica enlaces multimodo de hasta aproximadamente 500 m, según la fibra utilizada.",
    ),
    "HP-X130-10G-SR": transceiver(
        "Transceiver HPE Networking X130 10G SFP+ LC SR para conexiones 10 Gigabit de corto alcance sobre fibra multimodo. La referencia comercial de la familia es JD092B; la etiqueta física registra AFBR-703SDZ-HP8.",
        {"Familia": "HPE Networking X130", "Referencia comercial": "JD092B", "Identificador físico": "AFBR-703SDZ-HP8", "Estándar": "10GBASE-SR", "Formato": "SFP+", "Conector": "LC dúplex", "Fibra": "Multimodo", "Longitud de onda": "850 nm"},
        "Se debe consultar la matriz de transceivers del switch HPE para confirmar soporte de JD092B y la versión de software.",
        "Hasta 300 m sobre fibra OM3, sujeto al presupuesto óptico y calidad del enlace.",
    ),
    "AVAGO-AFBR-57F5MZ": transceiver(
        "Transceiver óptico Avago/Broadcom de la familia AFBR-57F5xMZ, utilizado en enlaces Fibre Channel de corto alcance sobre fibra multimodo. La variante física del inventario está identificada como AFBR-57F5MZ-ELX.",
        {"Familia": "Broadcom AFBR-57F5xMZ", "Referencia registrada": "AFBR-57F5MZ-ELX", "Formato": "SFP+", "Aplicación": "Fibre Channel de corto alcance", "Conector": "LC dúplex", "Fibra": "Multimodo", "Longitud de onda": "850 nm"},
        "La compatibilidad debe confirmarse contra la HBA, switch Fibre Channel y firmware que acepten la variante -ELX.",
        "La distancia depende de la velocidad Fibre Channel y de si la fibra es OM2, OM3 u OM4; debe calcularse con la matriz del fabricante.",
    ),
    "BROCADE-32G-SW-SEC": transceiver(
        "Transceiver Brocade 32G Fibre Channel de onda corta para redes SAN. El componente 57-1000485-01 corresponde a un SFP+ SWL de 32G destinado a fibra multimodo.",
        {"Número de parte": "57-1000485-01", "Aplicación": "32G Fibre Channel", "Formato": "SFP+", "Óptica": "Short Wave Length (SWL)", "Fibra": "Multimodo", "Longitud de onda": "850 nm"},
        "Debe validarse en la matriz de soporte del switch Brocade y de la versión de Fabric OS utilizada.",
        "La distancia depende de la categoría de fibra y la velocidad negociada; para 32G se valida normalmente sobre OM3 u OM4.",
    ),
    "LENOVO-1000BASE-T": transceiver(
        "Módulo Lenovo/IBM 1000BASE-T identificado con la referencia 78P3824 para conectividad Gigabit Ethernet sobre cobre. Convierte un puerto compatible a una interfaz RJ-45.",
        {"Referencia": "78P3824", "Estándar": "1000BASE-T", "Conector": "RJ-45", "Medio": "Cobre", "Velocidad": "1 Gbit/s"},
        "La referencia debe contrastarse con la lista de opciones admitidas por el servidor, adaptador o switch Lenovo/IBM donde se instalará.",
        "Hasta 100 m sobre cableado de cobre de categoría compatible.",
    ),
    "HUAWEI-10G-02310MNW": transceiver(
        "Transceiver Huawei SFP-10G-USR para enlaces 10 Gigabit Ethernet ultracortos sobre fibra multimodo. El número de parte 02310MNW opera a 850 nm, utiliza LC y está documentado para 100 m.",
        {"Modelo": "SFP-10G-USR", "Número de parte": "02310MNW", "Estándar": "10GBASE-USR", "Formato": "SFP+", "Conector": "LC", "Fibra": "Multimodo", "Longitud de onda": "850 nm", "Distancia objetivo": "100 m"},
        "Debe confirmarse el soporte de 02310MNW en el modelo de switch Huawei y su versión de software.",
        "Hasta 100 m sobre fibra multimodo compatible, conforme a la especificación oficial del módulo.",
    ),
    "HP-W9085MC": toner(
        "Consumible HP Managed identificado como W9085MC para plataformas de impresión empresarial compatibles. Está destinado a reposición por volumen y su uso debe validarse contra el modelo exacto de la impresora.",
        {"Referencia": "W9085MC", "Tipo": "Cartucho de tóner administrado", "Control de inventario": "Por cantidad", "Familia de impresora documentada": "HP LaserJet Managed MFP E826"},
        "La fuente oficial consultada relaciona esta familia de consumibles con equipos HP LaserJet Managed MFP E826. Debe confirmarse el sufijo exacto del equipo antes de instalarlo.",
    ),
    "HP-W9085-STARTER": toner(
        "Cartucho inicial HP W9085 procedente de una plataforma HP LaserJet Managed. Está orientado a la puesta en marcha del equipo y no debe confundirse con una referencia comercial de reposición.",
        {"Referencia de inventario": "W9085", "Tipo": "Cartucho inicial / starter", "Control de inventario": "Por cantidad", "Familia asociada": "HP LaserJet Managed MFP E826"},
        "Debe utilizarse únicamente en la plataforma HP para la que fue suministrado. Alfil confirma la etiqueta y el modelo de impresora antes de cotizar.",
        starter=True,
    ),
    "HP-W9065MC": toner(
        "Consumible HP Managed W9065MC para equipos de impresión empresarial compatibles. La referencia se administra por cantidad y está asociada a la familia HP LaserJet Managed MFP E731.",
        {"Referencia": "W9065MC", "Tipo": "Cartucho de tóner administrado", "Control de inventario": "Por cantidad", "Familia de impresora documentada": "HP LaserJet Managed MFP E731"},
        "La compatibilidad debe confirmarse con el modelo y región exactos de la HP LaserJet Managed MFP E731 antes de abrir el cartucho.",
    ),
    "HP-W1950X": toner(
        "Cartucho de tóner HP registrado físicamente por Alfil con la referencia W1950X. Al no existir todavía una coincidencia oficial verificable para esa lectura, su compatibilidad se validará con la etiqueta del producto antes de cotizar.",
        {"Referencia leída en inventario": "W1950X", "Tipo": "Cartucho de tóner", "Control de inventario": "Por cantidad", "Estado de verificación": "Pendiente de confirmar etiqueta física"},
        "La compatibilidad aún no debe asumirse. Es necesario revisar una fotografía legible de la etiqueta y el modelo de impresora del cliente.",
    ),
    "HP-145X": toner(
        "Cartucho de tóner negro HP 145X de alto rendimiento, identificado oficialmente como W1450X. Está diseñado para impresoras HP LaserJet compatibles que utilicen esta familia de consumibles.",
        {"Nombre comercial": "HP 145X", "Número de parte": "W1450X", "Color": "Negro", "Tipo": "Alto rendimiento", "Tecnología": "Láser"},
        "Debe verificarse que la impresora indique compatibilidad con HP 145X / W1450X; no basta con que pertenezca a la marca HP.",
    ),
    "HP-145X-STARTER": toner(
        "Cartucho inicial de la familia HP 145X suministrado para puesta en marcha. No corresponde a una presentación comercial W1450X de alto rendimiento y puede tener una capacidad distinta.",
        {"Familia": "HP 145X", "Referencia interna": "145X-STARTER", "Color": "Negro", "Tipo": "Cartucho inicial / starter"},
        "Debe validarse con la impresora que originó el consumible y con su etiqueta física, ya que los cartuchos iniciales no siempre se comercializan por separado.",
        starter=True,
    ),
    "CANON-GPR-63": toner(
        "Tóner negro Canon GPR-63 para equipos imageRUNNER ADVANCE DX compatibles. Es un consumible empresarial identificado por la familia GPR-63 y documentado por Canon para plataformas de impresión de alto volumen.",
        {"Familia": "Canon GPR-63", "Color": "Negro", "Tipo": "Tóner para equipo multifunción", "Código comercial documentado": "4766C003", "Control de inventario": "Por cantidad"},
        "Canon lista GPR-63 para modelos imageRUNNER ADVANCE DX compatibles, entre ellos la familia 6870i. Se debe confirmar el modelo exacto del equipo.",
    ),
}
