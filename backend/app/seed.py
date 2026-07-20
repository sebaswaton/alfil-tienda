"""Carga inicial del catálogo e inventario real de Alfil."""

from app.database import Base, SessionLocal, engine
from app import models
from app.inventory_data import INVENTORY_PRODUCTS
from app.product_content import PRODUCT_CONTENT


CATEGORIES = [
    dict(name="Laptops", slug="laptops", icon="▤", image_url="/categories/laptops.jpg",
         description="Alto rendimiento para trabajo y estudio."),
    dict(name="Computadoras", slug="computadoras", icon="▥", image_url="/categories/computadoras.jpg",
         description="Equipos de escritorio para cada necesidad."),
    dict(name="Impresoras", slug="impresoras", icon="▦", image_url="/categories/impresoras.jpg",
         description="Impresión de calidad para tu negocio."),
    dict(name="Toners y Suministros", slug="toners-y-suministros", icon="▧", image_url="/categories/toners.jpg",
         description="Toners originales y más suministros de impresión."),
    dict(name="Componentes", slug="componentes", icon="◫", image_url="/categories/componentes.jpg",
         description="Componentes, monitores, periféricos y respaldo de energía."),
    dict(name="Aires Acondicionados", slug="aires-acondicionados", icon="❄", image_url="/categories/aires-acondicionados.jpg",
         description="Climatización eficiente para tu espacio."),
    dict(name="Grupos Electrógenos", slug="grupos-electrogenos", icon="⚡", image_url="/categories/grupos-electrogenos.jpg",
         description="Energía confiable para tu negocio."),
    dict(name="Redes y Conectividad", slug="redes-y-conectividad", icon="◈", image_url="/categories/redes-y-conectividad.jpg",
         description="Switches, transceivers y conectividad empresarial."),
]


BRANDS = [
    dict(name="HP", slug="hp", accent_color="#087f6f", logo_url="/brands/hp.png", description="Cómputo, monitores y suministros."),
    dict(name="Dell", slug="dell", accent_color="#007db8", logo_url="/brands/dell.png", description="Infraestructura y equipos empresariales."),
    dict(name="Lenovo", slug="lenovo", accent_color="#e2231a", logo_url="/brands/lenovo.png", description="Cómputo y conectividad empresarial."),
    dict(name="Epson", slug="epson", accent_color="#004b93", logo_url="/brands/epson.png", description="Soluciones de impresión."),
    dict(name="Intel", slug="intel", accent_color="#0071c5", logo_url="/brands/intel.png", description="Procesadores y plataformas de cómputo."),
    dict(name="ASUS", slug="asus", accent_color="#003366", logo_url="/brands/asus.png", description="Laptops y componentes."),
    dict(name="Cisco", slug="cisco", accent_color="#049fd9", logo_url="/brands/cisco.png", description="Switching y conectividad empresarial."),
    dict(name="APC", slug="apc", accent_color="#e2001a", logo_url="/brands/apc.png", description="Respaldo de energía."),
    dict(name="Huawei", slug="huawei", accent_color="#cf0a2c", logo_url="/brands/huawei.png", description="Tablets y conectividad."),
    dict(name="Salicru", slug="salicru", accent_color="#e31e24", logo_url="/brands/salicru.png", description="Sistemas UPS."),
    dict(name="Canon", slug="canon", accent_color="#cc0000", logo_url="/brands/canon.png", description="Suministros de impresión."),
    dict(name="Avago", slug="avago", accent_color="#e76f00", logo_url="/brands/avago.png", description="Componentes ópticos."),
    dict(name="Brocade", slug="brocade", accent_color="#a51c30", logo_url="/brands/brocade.png", description="Conectividad de almacenamiento."),
]


WAREHOUSES = [
    dict(name="San Luis", slug="san-luis"),
    dict(name="San Borja", slug="san-borja"),
    dict(name="Callao", slug="callao"),
]


SUPPLIERS = [
    dict(name="Ingram", slug="ingram"),
    dict(name="Nexsys", slug="nexsys"),
    dict(name="Deltron", slug="deltron"),
    dict(name="HDST", slug="hdst"),
    dict(name="Huawei", slug="huawei"),
]


def run(reset=False):
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Brand).count() > 0:
            print("Seed omitido: ya existen datos. Usa --reset para cargar el inventario real.")
            return

        brand_map = {}
        for data in BRANDS:
            brand = models.Brand(**data)
            db.add(brand)
            db.flush()
            brand_map[data["slug"]] = brand

        category_map = {}
        for data in CATEGORIES:
            category = models.Category(**data)
            db.add(category)
            db.flush()
            category_map[data["slug"]] = category

        warehouse_map = {}
        for data in WAREHOUSES:
            warehouse = models.Warehouse(**data)
            db.add(warehouse)
            db.flush()
            warehouse_map[data["slug"]] = warehouse

        supplier_map = {}
        for data in SUPPLIERS:
            supplier = models.Supplier(**data)
            db.add(supplier)
            db.flush()
            supplier_map[data["slug"]] = supplier

        for data in INVENTORY_PRODUCTS:
            quantity = sum(balance["quantity"] for balance in data["balances"])
            if quantity <= 0:
                continue
            curated = PRODUCT_CONTENT.get(data["sku"], {})
            product = models.Product(
                sku=data["sku"],
                name=data["name"],
                slug=data["sku"].lower(),
                brand_id=brand_map[data["brand"]].id,
                category_id=category_map[data["category"]].id,
                part_number=data["part_number"],
                short_description=data["short_description"],
                description=curated.get("description", data["description"]),
                specs={**data["specs"], **curated.get("specs", {})},
                highlights=curated.get("highlights", data["highlights"]),
                available_stock=quantity,
                stock_type=data["stock_type"],
                is_used=data["is_used"],
                stock_note=f"{quantity} unidad{'es' if quantity != 1 else ''} disponible{'s' if quantity != 1 else ''}",
                status="active",
            )
            db.add(product)
            db.flush()

            for sort_order, faq_data in enumerate(curated.get("faqs", [])):
                db.add(models.ProductFAQ(
                    product_id=product.id,
                    question=faq_data["question"],
                    answer=faq_data["answer"],
                    sort_order=sort_order,
                ))

            for balance_data in data["balances"]:
                warehouse = warehouse_map[balance_data["warehouse"]]
                supplier_slug = balance_data.get("supplier")
                supplier = supplier_map.get(supplier_slug) if supplier_slug else None
                quantity_at_warehouse = balance_data["quantity"]
                db.add(models.InventoryBalance(
                    product_id=product.id,
                    warehouse_id=warehouse.id,
                    supplier_id=supplier.id if supplier else None,
                    quantity=quantity_at_warehouse,
                    condition="used" if data["is_used"] else "new",
                    source_sheet=data["source_sheet"],
                    source_reference=balance_data.get("reference", ""),
                ))
                db.add(models.StockMovement(
                    product_id=product.id,
                    to_warehouse_id=warehouse.id,
                    movement_type="initial_import",
                    quantity=quantity_at_warehouse,
                    reference=balance_data.get("reference", ""),
                    notes=f"Importado desde hoja: {data['source_sheet']}",
                ))

        db.commit()
        print(
            f"Seed completo: {len(CATEGORIES)} categorías, "
            f"{len(INVENTORY_PRODUCTS)} productos con stock y "
            f"{sum(p['quantity'] for p in INVENTORY_PRODUCTS)} unidades."
        )
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    run(reset="--reset" in sys.argv)
