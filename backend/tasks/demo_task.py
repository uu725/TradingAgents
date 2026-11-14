import time


def demo_task(ticker: str):
    print(f"开始处理股票：{ticker}")

    # 模拟耗时任务
    time.sleep(3)

    print(f"股票 {ticker} 处理完成")

    return {
        "ticker": ticker,
        "status": "completed",
        "message": "模拟分析成功"
    }
