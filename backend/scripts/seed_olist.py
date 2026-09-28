import io
import os
import urllib.request
import zipfile
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

DATA_DIR = Path("data/raw")
KAGGLE_URL = "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce"

def download_and_extract():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not (DATA_DIR / "olist_orders_dataset.csv").exists():
        print("⏳ Downloading Olist dataset from Kaggle...")
        req = urllib.request.Request(KAGGLE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            with zipfile.ZipFile(io.BytesIO(resp.read())) as z:
                z.extractall(DATA_DIR)
        print("✅ Download & extraction complete!")
    else:
        print("✅ Raw CSV files already exist in data/raw/")
load_dotenv()

def get_engine():
    user = os.getenv("POSTGRES_USER", "olist_admin")
    password = os.getenv("POSTGRES_PASSWORD", "olist_secure_password_123")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "olist_db")
    
    url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)

def seed_database(engine):
    print("🚀 Seeding database...")

    # 1. Customers
    print("Loading customers...")
    df_customers = pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")
    df_customers = df_customers.rename(
        columns={
            "customer_zip_code_prefix": "zip_code_prefix",
            "customer_city": "city",
            "customer_state": "state",
        }
    )
    df_customers = df_customers[
        ["customer_id", "customer_unique_id", "zip_code_prefix", "city", "state"]
    ]
    df_customers.to_sql(
        "customers",
        engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )
    print(f"  ✓ customers: {len(df_customers):,} rows")

    # 2. Sellers
    print("Loading sellers...")
    df_sellers = pd.read_csv(DATA_DIR / "olist_sellers_dataset.csv")
    df_sellers = df_sellers.rename(
        columns={
            "seller_zip_code_prefix": "zip_code_prefix",
            "seller_city": "city",
            "seller_state": "state",
        }
    )
    df_sellers = df_sellers[["seller_id", "zip_code_prefix", "city", "state"]]
    df_sellers.to_sql(
        "sellers",
        engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )
    print(f"  ✓ sellers: {len(df_sellers):,} rows")

    # 3. Products
    print("Loading products...")
    df_products = pd.read_csv(DATA_DIR / "olist_products_dataset.csv")
    df_trans = pd.read_csv(DATA_DIR / "product_category_name_translation.csv")
    df_products = df_products.merge(df_trans, on="product_category_name", how="left")
    df_products = df_products.rename(
        columns={
            "product_category_name_english": "category_name",
            "product_name_lenght": "name_length",
            "product_description_lenght": "description_length",
            "product_photos_qty": "photos_qty",
            "product_weight_g": "weight_g",
        }
    )
    df_products = df_products[
        [
            "product_id",
            "category_name",
            "name_length",
            "description_length",
            "photos_qty",
            "weight_g",
        ]
    ]
    df_products = df_products.where(pd.notnull(df_products), None)
    df_products.to_sql(
        "products",
        engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )
    print(f"  ✓ products: {len(df_products):,} rows")

    # 4. Orders
    print("Loading orders...")
    df_orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")
    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        df_orders[col] = pd.to_datetime(df_orders[col])

    df_orders = df_orders.rename(
        columns={
            "order_purchase_timestamp": "purchase_timestamp",
            "order_approved_at": "approved_at",
            "order_delivered_carrier_date": "delivered_carrier_date",
            "order_delivered_customer_date": "delivered_customer_date",
            "order_estimated_delivery_date": "estimated_delivery_date",
        }
    )
    cols_orders = [
        "order_id",
        "customer_id",
        "order_status",
        "purchase_timestamp",
        "approved_at",
        "delivered_carrier_date",
        "delivered_customer_date",
        "estimated_delivery_date",
    ]
    df_orders = df_orders[cols_orders]
    df_orders.to_sql(
        "orders",
        engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )
    print(f"  ✓ orders: {len(df_orders):,} rows")

    # 5. Order Items
    print("Loading order_items...")
    df_items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")
    df_items["shipping_limit_date"] = pd.to_datetime(df_items["shipping_limit_date"])
    cols_items = [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ]
    df_items = df_items[cols_items]
    df_items.to_sql(
        "order_items",
        engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )
    print(f"  ✓ order_items: {len(df_items):,} rows")

    # 6. Order Payments
    print("Loading order_payments...")
    df_payments = pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")
    cols_payments = [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ]
    df_payments = df_payments[cols_payments]
    df_payments.to_sql(
        "order_payments",
        engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )
    print(f"  ✓ order_payments: {len(df_payments):,} rows")

    # 7. Order Reviews
    print("Loading order_reviews...")
    df_reviews = pd.read_csv(DATA_DIR / "olist_order_reviews_dataset.csv")
    df_reviews["review_creation_date"] = pd.to_datetime(
        df_reviews["review_creation_date"]
    )
    df_reviews["review_answer_timestamp"] = pd.to_datetime(
        df_reviews["review_answer_timestamp"]
    )
    df_reviews = df_reviews.drop_duplicates(subset=["review_id", "order_id"])
    cols_reviews = [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ]
    df_reviews = df_reviews[cols_reviews]
    df_reviews = df_reviews.where(pd.notnull(df_reviews), None)
    df_reviews.to_sql(
        "order_reviews",
        engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )
    print(f"  ✓ order_reviews: {len(df_reviews):,} rows")

    print("\n🎉 Database seeded successfully!")


if __name__ == "__main__":
    download_and_extract()
    engine = get_engine()
    seed_database(engine)