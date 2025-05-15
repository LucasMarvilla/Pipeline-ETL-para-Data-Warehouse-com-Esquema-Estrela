# 📊 Projeto: Pipeline + Data Warehouse

**Tecnologias utilizadas:** Python · SQL · Apache Airflow · PostgreSQL · pgAdmin · Data Warehouse

## 📝 Descrição do Projeto

Este projeto teve como objetivo a construção de um mini **Data Warehouse** a partir do conjunto de dados da [Olist (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), que contém informações completas sobre um e-commerce brasileiro.

Os dados estavam originalmente **distribuídos em diversos arquivos CSV separados**, representando entidades como pedidos, produtos, pagamentos, avaliações, clientes, entre outros. A partir disso:

- Analisei o **data esquema original** para entender as relações entre os arquivos;
- Modelei um **Data Warehouse com esquema estrela**, consolidando as principais entidades em tabelas dimensão e fato;
- Realizei a **limpeza, transformação e integração dos dados** utilizando Python;
- Estruturei o banco de dados relacional no **PostgreSQL**;
- Utilize o **pgAdmin** para **criar o diagrama ERD** (Entidade-Relacionamento) do modelo implementado;
- Automatizei o processo de carga com um pipeline criado em **Apache Airflow**.

## 🗂️ Data Esquema Original

Abaixo está o diagrama do esquema original dos dados disponíveis nos arquivos CSV da Olist:

![Data Esquema Original](Diagramas\Data_Schema.png)

## 🌟 Modelagem Estrela

Transformei o esquema anterior em um modelo estrela com foco na análise de vendas:

### 🔸 Tabela Fato: `fato_vendas`
Contém informações transacionais sobre cada item vendido:
- `order_id`, `order_item_id`
- `product_id`, `seller_id`, `customer_id`, `data_id`
- `price`, `freight_value`, `payment_value`
- `payment_type`, `review_score`, `order_status`
- `shipping_limit_date`

### 🔹 Tabelas Dimensão:
- `dim_cliente`: Dados geográficos dos clientes
- `dim_produto`: Características dos produtos
- `dim_vendedor`: Localização e identificação dos vendedores
- `dim_tempo`: Detalhes de datas (ano, mês, dia, dia da semana)
- `dim_pagamento`: Tipo e valor de pagamento
- `dim_avaliacao`: Notas e comentários dos clientes

## 🧭 Diagrama ERD (PostgreSQL via pgAdmin)

O diagrama abaixo foi gerado a partir das tabelas criadas no **pgAdmin** com o modelo estrela:

![ERD - Modelo Estrela](Diagramas\diagrama_ERD.png)

## 🎯 Resultados

Com a transformação dos dados para o modelo estrela, foi possível:

- Realizar análises mais eficientes com consultas SQL otimizadas;
- Cruzar métricas de negócio com diferentes dimensões (tempo, localização, produto, etc.);
- Ter uma base preparada para futuras integrações com ferramentas de BI.



Este guia explica a sequência correta de comandos para subir o Apache Airflow utilizando Docker Compose.

## Pré-requisitos

- Docker e Docker Compose instalados
- Projeto do Airflow com o arquivo `docker-compose.yaml` devidamente configurado

## Passo a passo

### 1. Inicializar o ambiente do Airflow

```bash
cd airflow/
```
Antes de subir os containers, é necessário inicializar o Airflow. Esse passo prepara o banco de dados, aplica as migrações e cria o usuário admin padrão.

```bash
docker compose up airflow-init
```

> ⚠️ Este comando deve ser executado **somente na primeira vez** ou sempre que os volumes forem removidos.

### 2. Subir os containers

Depois que a inicialização for concluída com sucesso, você pode subir todos os serviços normalmente:

```bash
docker-compose up -d
```

### 3. Acessar a interface Web do Airflow
1. criar conexão do airflow com postgresql

```bash
docker exec -it projetoairflow-airflow-scheduler-1 airflow connections add 'postgres_etl' --conn-uri 'postgresql+psycopg2://airflow:airflow@postgres:5432/airflow'
```

2. A interface web geralmente estará disponível no seguinte endereço:


[http://localhost:8080]


Use as credenciais criadas durante a inicialização (`airflow-init`) para fazer login.
3. Faça login com as credenciais
   - **Username:** `airflow`
   - **Password:** `airflow`

### 🔗 Conexão ao PostgreSQL via pgAdmin

1. Acesse o pgAdmin no navegador:  
   [http://localhost:8081]

2. Faça login com as credenciais
   - **Email:** `admin@admin.com`
   - **Senha:** `admin`

3. Clique com o botão direito em “Servers” > **Create** > **Server**.

4. Na aba **General**, defina um nome como:
   - `Projeto` ou o que preferir.

5. Na aba **Connection**, insira:
   - **Host name/address:** `postgres`  
   - **Port:** `5432`  
   - **Username:** `airflow`  
   - **Password:** `airflow`
   - **database:** `airflow`  
   - Marque a opção **Save Password**.

6. Clique em **Save**. Agora você pode acessar o banco `Projeto`.

### 🔗 visualização no PostgreSQL via pgAdmin

1. expende servers -> airflow -> schemas -> tables -> 
- `dim_cliente`: Dados geográficos dos clientes
- `dim_produto`: Características dos produtos
- `dim_vendedor`: Localização e identificação dos vendedores
- `dim_tempo`: Detalhes de datas (ano, mês, dia, dia da semana)
- `dim_pagamento`: Tipo e valor de pagamento
- `dim_avaliacao`: Notas e comentários dos clientes