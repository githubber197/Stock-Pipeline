CREATE TABLE IF NOT EXISTS stock_prices (
    id          SERIAL PRIMARY KEY,
    symbol      VARCHAR(10) NOT NULL,
    avg_price   DECIMAL(10, 2),
    latest_price DECIMAL(10, 2),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);