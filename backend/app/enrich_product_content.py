"""Apply reviewed descriptions, technical specifications and FAQs."""

from sqlalchemy import select

from app import models
from app.database import SessionLocal
from app.product_content import PRODUCT_CONTENT


def run() -> tuple[int, list[str]]:
    updated = 0
    missing = []
    with SessionLocal() as db:
        products = {product.sku: product for product in db.scalars(select(models.Product)).all()}
        for sku, content in PRODUCT_CONTENT.items():
            product = products.get(sku)
            if product is None:
                missing.append(sku)
                continue

            product.description = content["description"]
            # Preserve inventory facts such as condition and installed parts,
            # while allowing the reviewed labels to add or refine information.
            product.specs = {**(product.specs or {}), **content["specs"]}
            product.highlights = content["highlights"]
            product.faqs.clear()
            for sort_order, faq_data in enumerate(content["faqs"]):
                product.faqs.append(models.ProductFAQ(
                    question=faq_data["question"],
                    answer=faq_data["answer"],
                    sort_order=sort_order,
                ))
            updated += 1
        db.commit()
    return updated, missing


if __name__ == "__main__":
    count, missing_skus = run()
    print(f"Contenido actualizado: {count} productos")
    if missing_skus:
        print("SKU no encontrados:", ", ".join(missing_skus))
