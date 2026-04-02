import json
import time
from datetime import datetime
from kafka import KafkaProducer
import yfinance as yf

#Configuration
KAFKA_BROKER = "localhost:9093"
TOPIC = "stock-prices"
STOCKS = ["AAPL", "GOOGL", "MSFT"]
FETCH_INTERVAL = 10 

def create_producer():
    """Create and return a Kafka producer instance."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        #Kafka messages are bytes, we serialize Python dicts to JSON bytes
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

def fetch_price(symbol):
    """Fetch the latest price for a stock symbol."""
    ticker = yf.Ticker(symbol)
    #fast_info doesn't pull full history
    price = ticker.fast_info.last_price
    return round(price, 2)

def build_message(symbol, price):
    """Build the message dict we'll send to Kafka."""
    return {
        "symbol": symbol,
        "price": price,
        "timestamp": datetime.utcnow().isoformat()
    }

def run():
    producer = create_producer()
    print(f"Producer started. Sending to topic: {TOPIC}")

    while True:
        for symbol in STOCKS:
            try:
                price = fetch_price(symbol)
                message = build_message(symbol, price)

                producer.send(TOPIC, value=message)
                print(f"Sent: {message}")

            except Exception as e:
                print(f"Error fetching {symbol}: {e}")

        #Flush ensures buffered messages are actually sent
        producer.flush()
        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    run()