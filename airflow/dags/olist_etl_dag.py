from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import os
from airflow.providers.postgres.hooks.postgres import PostgresHook

base_path = '/opt/airflow/csv/'
path = '/opt/airflow/dags/data/'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 5, 7),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id="olist_etl_dag",
    description="DAG para pipeline ETL da Olist",
    schedule="@daily",  
    start_date=datetime(2023, 1, 1),
    catchup=False
)


def criar_tabelas_postgres(**context):
    hook = PostgresHook(postgres_conn_id='postgres_etl')
    tabelas_sql = [
        """
        CREATE TABLE IF NOT EXISTS fato_vendas (
            order_id TEXT,  -- IDs alfanuméricos, use TEXT
            order_item_id BIGINT,  -- Para suportar números maiores
            product_id TEXT,  -- IDs de produtos, use TEXT
            seller_id TEXT,  -- IDs de vendedores, use TEXT
            customer_id TEXT,  -- IDs de clientes, use TEXT
            shipping_limit_date TIMESTAMP,  -- Para data e hora
            price NUMERIC(15, 2),  -- Para suportar valores grandes com 2 casas decimais
            freight_value NUMERIC(15, 2),  -- Para suportar valores grandes com 2 casas decimais
            payment_type TEXT,  -- Tipo de pagamento, use TEXT
            payment_value NUMERIC(15, 2),  -- Para suportar valores grandes com 2 casas decimais
            review_score NUMERIC(3, 1),  -- Para suportar avaliações com 1 casa decimal
            order_status TEXT,  -- Status do pedido, use TEXT
            data_id DATE  -- Data do pedido
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_produto (
            product_id VARCHAR(50) PRIMARY KEY,
            product_category_name VARCHAR(100),
            product_category_name_english VARCHAR(100),
            product_name_lenght FLOAT,
            product_description_lenght FLOAT,
            product_photos_qty FLOAT,
            product_weight_g FLOAT,
            product_length_cm FLOAT,
            product_height_cm FLOAT,
            product_width_cm FLOAT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_cliente (
            customer_id VARCHAR(50) PRIMARY KEY,
            customer_unique_id VARCHAR(50),
            customer_zip_code_prefix INTEGER,
            customer_city VARCHAR(100),
            customer_state VARCHAR(10)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_vendedor (
            seller_id VARCHAR(50) PRIMARY KEY,
            seller_zip_code_prefix INTEGER,
            seller_city VARCHAR(100),
            seller_state VARCHAR(10)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_tempo (
            data_id DATE PRIMARY KEY,
            ano INTEGER,
            mes INTEGER,
            dia INTEGER,
            dia_da_semana VARCHAR(20)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_pagamento (
            order_id VARCHAR(50),
            payment_sequential INTEGER,
            payment_type VARCHAR(50),
            payment_installments INTEGER,
            payment_value FLOAT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_avaliacao (
            review_id VARCHAR(50) PRIMARY KEY,
            order_id VARCHAR(50),
            review_score INTEGER,
            review_comment_title TEXT,
            review_comment_message TEXT,
            review_creation_date TIMESTAMP,
            review_answer_timestamp TIMESTAMP
        );
        """
    ]
    for sql in tabelas_sql:
        hook.run(sql)

def extract_data(**kwargs):
    os.makedirs(path, exist_ok=True)
    datasets = {
        'df_customers': 'olist_customers_dataset.csv',
        'df_geolocation': 'olist_geolocation_dataset.csv',
        'df_order_items': 'olist_order_items_dataset.csv',
        'df_order_payments': 'olist_order_payments_dataset.csv',
        'df_order_reviews': 'olist_order_reviews_dataset.csv',
        'df_orders': 'olist_orders_dataset.csv',
        'df_products': 'olist_products_dataset.csv',
        'df_sellers': 'olist_sellers_dataset.csv',
        'df_category_translation': 'product_category_name_translation.csv',
    }
    for name, file in datasets.items():
        df = pd.read_csv(base_path + file)
        df.to_csv(path + name + '.csv', index=False)

def transform_data(**kwargs):
    df_customers = pd.read_csv(path + 'df_customers.csv')
    df_order_items = pd.read_csv(path + 'df_order_items.csv')
    df_order_payments = pd.read_csv(path + 'df_order_payments.csv')
    df_order_reviews = pd.read_csv(path + 'df_order_reviews.csv')
    df_orders = pd.read_csv(path + 'df_orders.csv')
    df_products = pd.read_csv(path + 'df_products.csv')
    df_sellers = pd.read_csv(path + 'df_sellers.csv')
    df_category_translation = pd.read_csv(path + 'df_category_translation.csv')

    df_fato_vendas = df_order_items.merge(df_orders, on='order_id', how='left') \
        .merge(df_order_payments.groupby('order_id').agg({'payment_type': 'first', 'payment_value': 'sum'}).reset_index(), on='order_id', how='left') \
        .merge(df_order_reviews[['order_id', 'review_score']], on='order_id', how='left')
    df_fato_vendas['data_id'] = pd.to_datetime(df_fato_vendas['order_purchase_timestamp']).dt.date
    df_fato_vendas = df_fato_vendas[['order_id', 'order_item_id', 'product_id', 'seller_id', 'customer_id',
                                      'shipping_limit_date', 'price', 'freight_value', 'payment_type', 'payment_value',
                                      'review_score', 'order_status', 'data_id']]

    df_dim_produto = df_products.merge(df_category_translation, on='product_category_name', how='left')[
        ['product_id', 'product_category_name', 'product_category_name_english',
         'product_name_lenght', 'product_description_lenght', 'product_photos_qty',
         'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm']].drop_duplicates()

    df_dim_cliente = df_customers[['customer_id', 'customer_unique_id', 'customer_zip_code_prefix',
                                   'customer_city', 'customer_state']].drop_duplicates()

    df_dim_vendedor = df_sellers[['seller_id', 'seller_zip_code_prefix', 'seller_city', 'seller_state']].drop_duplicates()

    df_dim_tempo = df_orders[['order_purchase_timestamp']].drop_duplicates()
    df_dim_tempo['data_id'] = pd.to_datetime(df_dim_tempo['order_purchase_timestamp']).dt.date
    df_dim_tempo['ano'] = pd.to_datetime(df_dim_tempo['order_purchase_timestamp']).dt.year
    df_dim_tempo['mes'] = pd.to_datetime(df_dim_tempo['order_purchase_timestamp']).dt.month
    df_dim_tempo['dia'] = pd.to_datetime(df_dim_tempo['order_purchase_timestamp']).dt.day
    df_dim_tempo['dia_da_semana'] = pd.to_datetime(df_dim_tempo['order_purchase_timestamp']).dt.day_name()
    df_dim_tempo = df_dim_tempo[['data_id', 'ano', 'mes', 'dia', 'dia_da_semana']]

    df_dim_pagamento = df_order_payments[['order_id', 'payment_sequential', 'payment_type',
                                          'payment_installments', 'payment_value']]

    df_dim_avaliacao = df_order_reviews[['review_id', 'order_id', 'review_score', 'review_comment_title',
                                         'review_comment_message', 'review_creation_date', 'review_answer_timestamp']].drop_duplicates()

    df_fato_vendas.to_csv(path + 'df_fato_vendas.csv', index=False)
    df_dim_produto.to_csv(path + 'df_dim_produto.csv', index=False)
    df_dim_cliente.to_csv(path + 'df_dim_cliente.csv', index=False)
    df_dim_vendedor.to_csv(path + 'df_dim_vendedor.csv', index=False)
    df_dim_tempo.to_csv(path + 'df_dim_tempo.csv', index=False)
    df_dim_pagamento.to_csv(path + 'df_dim_pagamento.csv', index=False)
    df_dim_avaliacao.to_csv(path + 'df_dim_avaliacao.csv', index=False)

def load_data(**kwargs):
    hook = PostgresHook(postgres_conn_id='postgres_etl')
    conn = hook.get_conn()
    cursor = conn.cursor()

    df_fato_vendas = pd.read_csv(path + 'df_fato_vendas.csv')
    df_dim_produto = pd.read_csv(path + 'df_dim_produto.csv')
    df_dim_cliente = pd.read_csv(path + 'df_dim_cliente.csv')
    df_dim_vendedor = pd.read_csv(path + 'df_dim_vendedor.csv')
    df_dim_tempo = pd.read_csv(path + 'df_dim_tempo.csv')
    df_dim_pagamento = pd.read_csv(path + 'df_dim_pagamento.csv')
    df_dim_avaliacao = pd.read_csv(path + 'df_dim_avaliacao.csv')

    cursor.executemany("""
        INSERT INTO fato_vendas 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, df_fato_vendas.values.tolist())

    cursor.executemany("""
        INSERT INTO dim_produto 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_id) DO NOTHING
    """, df_dim_produto.values.tolist())

    cursor.executemany("""
        INSERT INTO dim_cliente 
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (customer_id) DO NOTHING
    """, df_dim_cliente.values.tolist())

    cursor.executemany("""
        INSERT INTO dim_vendedor 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (seller_id) DO NOTHING
    """, df_dim_vendedor.values.tolist())

    cursor.executemany("""
        INSERT INTO dim_tempo 
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (data_id) DO NOTHING
    """, df_dim_tempo.values.tolist())

    cursor.executemany("""
        INSERT INTO dim_pagamento 
        VALUES (%s, %s, %s, %s, %s)
    """, df_dim_pagamento.values.tolist())

    cursor.executemany("""
        INSERT INTO dim_avaliacao 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (review_id) DO NOTHING
    """, df_dim_avaliacao.values.tolist())

    conn.commit()

criar_tabelas = PythonOperator(
    task_id='criar_tabelas_postgres',
    python_callable=criar_tabelas_postgres,
    dag=dag
)

extrair = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    dag=dag
)

transformar = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag
)

carregar = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=dag
)

criar_tabelas >> extrair >> transformar >> carregar
