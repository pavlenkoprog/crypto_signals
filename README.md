# crypto_signals

Минималистичный бот сигналов и автоторговли для Bybit Spot.

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

Создайте `.env` в корне проекта и добавьте:

```env
BYBIT_API_KEY=your_key
BYBIT_API_SECRET=your_secret
```

## Запуск

```bash
python runner.py --once
python trade_bot.py --once
python server.py
```
