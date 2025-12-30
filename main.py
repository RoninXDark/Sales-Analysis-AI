import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
import random
from datetime import datetime, timedelta

def generate_data():
    print("Generating synthetic data...")
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(365)]
    products = ['Laptop', 'Mouse', 'Monitor', 'Keyboard', 'Headphones']
    data = []

    for date in dates:
        for _ in range(random.randint(1,15)):
            product = random.choice(products)
            price = {
                'Laptop': 1000, 'Mouse': 25, 'Monitor': 300, 
                'Keyboard': 50, 'Headphones': 80
            }[product]
            final_price = price * random.uniform(0.9 , 1.1)
            data.append([date, product, round(final_price,2)])
    df = pd.DataFrame(data, columns=['Date', 'Product', 'Revenue'])
    df.to_csv('sales_data.csv', index=False)
    print("Data generation complete. Data saved to 'sales_data.csv'.")
    return df

def analyze_data(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')

    monthly_sales = df.groupby('Month')['Revenue'].sum().reset_index()
    monthly_sales['Month'] = monthly_sales['Month'].astype(str)

   
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=monthly_sales, x='Month', y='Revenue', marker='o', color='b')
    plt.title('Sales Trend 2023')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.savefig('sales_trend.png')
    print("Graph saved as 'sales_trend.png'")
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x='Product', y='Revenue', estimator=sum, palette='viridis')
    plt.title('Total Revenue by Product')
    plt.savefig('product_revenue.png')
    print(" Graph of products saved as 'product_revenue.png'")

    return monthly_sales

def predict_sales(monthly_sales):
    print("Teaching model to predict next month's sales...")

    monthly_sales['Month_Num'] = range(len(monthly_sales))
    X = monthly_sales[['Month_Num']]
    y = monthly_sales['Revenue']

    model = LinearRegression()
    model.fit(X , y)

    next_month = [[len(monthly_sales)]]
    prediction = model.predict(next_month)

    print(f"Predicted sales for next month: ${prediction[0]:.2f}")

if __name__ == '__main__':
    try:
        df = pd.read_csv('sales_data.csv')
    except FileNotFoundError:
        df = generate_data()

    monthly_data = analyze_data(df)
    predict_sales(monthly_data)
    print("Analysis complete.")
