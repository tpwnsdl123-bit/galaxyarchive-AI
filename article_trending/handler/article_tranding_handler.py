from consumer.worker import handler


@handler("article-tranding-calculated")
def article_trending_calculated_handler(msg)->None:
    print(msg)